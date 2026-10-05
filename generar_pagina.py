"""
Genera index.html: tabla del S&P 500 con distancia al maximo historico
y a la SMA de 200 semanas. Se baja todo con yfinance y queda embebido en
el HTML, asi el archivo funciona offline, sin internet y sin servidor.

Uso:
  pip install yfinance pandas lxml requests
  python generar_pagina.py
"""

import json
from io import StringIO
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import yfinance as yf

ARG = timezone(timedelta(hours=-3))
SALIDA = "index.html"
LOTE = 50

WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def lista_sp500():
    """Tickers, nombre y sector del S&P 500 desde Wikipedia."""
    r = requests.get(WIKI, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    tablas = pd.read_html(StringIO(r.text))
    df = tablas[0]
    df = df.rename(
        columns={
            "Symbol": "ticker",
            "Security": "nombre",
            "GICS Sector": "sector",
        }
    )
    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
    return df[["ticker", "nombre", "sector"]].to_dict("records")


def bajar_semanal(tickers):
    """Historico semanal completo para una lista de tickers."""
    return yf.download(
        tickers,
        period="max",
        interval="1wk",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def calcular(empresas):
    filas = []
    for i in range(0, len(empresas), LOTE):
        lote = empresas[i:i + LOTE]
        simbolos = [e["ticker"] for e in lote]
        print(f"Bajando {i + 1} a {i + len(lote)} de {len(empresas)}")
        try:
            data = bajar_semanal(simbolos)
        except Exception as e:
            print(f"  error en el lote: {e}")
            continue

        for emp in lote:
            t = emp["ticker"]
            try:
                df = data[t].dropna(subset=["Close"])
            except Exception:
                continue
            if df.empty or len(df) < 20:
                continue

            precio = float(df["Close"].iloc[-1])
            ath = float(df["High"].max())
            fecha_ath = df["High"].idxmax().date().isoformat()
            dist_ath = (precio - ath) / ath * 100

            if len(df) >= 200:
                ma200 = float(df["Close"].rolling(200).mean().iloc[-1])
                dist_ma = (precio - ma200) / ma200 * 100
            else:
                ma200 = None
                dist_ma = None

            filas.append(
                {
                    "t": t,
                    "n": emp["nombre"],
                    "s": emp["sector"],
                    "p": round(precio, 2),
                    "a": round(ath, 2),
                    "fa": fecha_ath,
                    "da": round(dist_ath, 1),
                    "m": round(ma200, 2) if ma200 else None,
                    "dm": round(dist_ma, 1) if dist_ma is not None else None,
                }
            )

    filas.sort(key=lambda f: f["da"])
    return filas


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S&amp;P 500 - distancia al maximo y a la 200 semanal</title>
<style>
:root{color-scheme:light dark;--bg:#0f1115;--card:#171a21;--txt:#e7e9ee;
--mut:#9aa3b2;--bd:#262b36;--verde:#3fb950;--rojo:#f85149;--ama:#d29922}
*{box-sizing:border-box}
body{margin:0;padding:16px;background:var(--bg);color:var(--txt);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
h1{font-size:19px;margin:0 0 4px}
.sub{color:var(--mut);font-size:13px;margin-bottom:16px}
.panel{background:var(--card);border:1px solid var(--bd);border-radius:10px;
padding:12px;margin-bottom:14px}
label{display:block;font-size:12px;color:var(--mut);margin-bottom:4px}
input,select,textarea{width:100%;padding:8px;border-radius:7px;
border:1px solid var(--bd);background:var(--bg);color:var(--txt);font-size:14px}
textarea{min-height:52px;resize:vertical;font-family:ui-monospace,monospace}
.fila{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.fila>div{flex:1;min-width:130px}
.chk{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--txt)}
.chk input{width:auto}
.cont{overflow-x:auto;border:1px solid var(--bd);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:620px}
th{background:var(--card);padding:9px 8px;text-align:right;cursor:pointer;
white-space:nowrap;position:sticky;top:0;font-weight:600}
th:first-child,th:nth-child(2),th:nth-child(3){text-align:left}
td{padding:8px;border-top:1px solid var(--bd);text-align:right;
font-variant-numeric:tabular-nums}
td:first-child{text-align:left;font-weight:600}
td:nth-child(2),td:nth-child(3){text-align:left;color:var(--mut)}
tr:hover td{background:rgba(255,255,255,.03)}
.pos{color:var(--verde)}.neg{color:var(--rojo)}.war{color:var(--ama)}
.pie{color:var(--mut);font-size:12px;margin-top:14px;line-height:1.6}
.cnt{color:var(--mut);font-size:12px;margin:8px 0}
@media(max-width:600px){body{padding:10px}td:nth-child(2){display:none}
th:nth-child(2){display:none}}
</style>
</head>
<body>
<h1>S&amp;P 500</h1>
<div class="sub">Distancia al maximo historico y a la media de 200 semanas.
Datos al __FECHA__.</div>

<div class="panel">
  <div class="fila">
    <div>
      <label>Buscar (ticker o nombre)</label>
      <input id="q" placeholder="NVDA, Johnson...">
    </div>
    <div>
      <label>Sector</label>
      <select id="sec"><option value="">Todos</option></select>
    </div>
  </div>
  <div class="fila">
    <div>
      <label>Caida minima desde el maximo (%)</label>
      <input id="mincaida" type="number" placeholder="ej: 30">
    </div>
    <div>
      <label>Distancia maxima a la 200 sem (%)</label>
      <input id="maxma" type="number" placeholder="ej: 10">
    </div>
  </div>
  <div class="fila">
    <div style="flex:3">
      <label>Mis tickers (separados por coma, se guardan en este navegador)</label>
      <textarea id="mios" placeholder="NVDA, GOOGL, MCD"></textarea>
    </div>
  </div>
  <label class="chk"><input type="checkbox" id="ocultar" checked>
    Ocultar las empresas que ya tengo</label>
</div>

<div class="cnt" id="cnt"></div>
<div class="cont">
<table>
<thead><tr>
<th data-k="t">Ticker</th><th data-k="n">Empresa</th><th data-k="s">Sector</th>
<th data-k="p">Precio</th><th data-k="da">vs ATH</th>
<th data-k="dm">vs 200 sem</th><th data-k="fa">Fecha ATH</th>
</tr></thead>
<tbody id="cuerpo"></tbody>
</table>
</div>

<div class="pie">
vs ATH: cuanto esta por debajo (o encima) de su maximo historico.<br>
vs 200 sem: distancia al promedio de las ultimas 200 semanas (casi 4 anios).
Negativo significa que cotiza por debajo de ese promedio.<br>
Precios sin ajustar por dividendos. Fuente: Yahoo Finance.
Esto no es una recomendacion de compra: un precio bajo no implica valor.
</div>

<script>
const D = __DATOS__;
let orden = "da", asc = true;

const sectores = [...new Set(D.map(r => r.s))].sort();
const sel = document.getElementById("sec");
sectores.forEach(s => {
  const o = document.createElement("option");
  o.value = s; o.textContent = s; sel.appendChild(o);
});

const mios = document.getElementById("mios");
try { mios.value = localStorage.getItem("misTickers") || ""; } catch (e) {}

function listaMios() {
  return mios.value.toUpperCase().split(/[\\s,;]+/).filter(Boolean);
}

function fmt(v, suf) {
  if (v === null || v === undefined) return "<span style='color:#9aa3b2'>n/d</span>";
  const c = v >= 0 ? "pos" : "neg";
  return "<span class='" + c + "'>" + (v > 0 ? "+" : "") + v.toFixed(1) + suf + "</span>";
}

function pintar() {
  const q = document.getElementById("q").value.toUpperCase();
  const s = sel.value;
  const minc = parseFloat(document.getElementById("mincaida").value);
  const maxm = parseFloat(document.getElementById("maxma").value);
  const ocultar = document.getElementById("ocultar").checked;
  const propios = listaMios();

  let f = D.filter(r => {
    if (q && !(r.t.includes(q) || r.n.toUpperCase().includes(q))) return false;
    if (s && r.s !== s) return false;
    if (!isNaN(minc) && r.da > -Math.abs(minc)) return false;
    if (!isNaN(maxm)) {
      if (r.dm === null) return false;
      if (Math.abs(r.dm) > Math.abs(maxm)) return false;
    }
    if (ocultar && propios.includes(r.t)) return false;
    return true;
  });

  f.sort((a, b) => {
    let x = a[orden], y = b[orden];
    if (x === null) return 1;
    if (y === null) return -1;
    if (typeof x === "string") return asc ? x.localeCompare(y) : y.localeCompare(x);
    return asc ? x - y : y - x;
  });

  document.getElementById("cnt").textContent =
    f.length + " empresas de " + D.length;

  document.getElementById("cuerpo").innerHTML = f.map(r =>
    "<tr><td>" + r.t + "</td><td>" + r.n + "</td><td>" + r.s + "</td><td>" +
    r.p.toLocaleString("es-AR", {minimumFractionDigits: 2}) + "</td><td>" +
    fmt(r.da, "%") + "</td><td>" + fmt(r.dm, "%") + "</td><td>" +
    r.fa + "</td></tr>"
  ).join("");
}

document.querySelectorAll("th").forEach(th => {
  th.onclick = () => {
    const k = th.dataset.k;
    asc = (orden === k) ? !asc : true;
    orden = k;
    pintar();
  };
});

["q", "sec", "mincaida", "maxma", "ocultar"].forEach(id => {
  document.getElementById(id).addEventListener("input", pintar);
  document.getElementById(id).addEventListener("change", pintar);
});

mios.addEventListener("input", () => {
  try { localStorage.setItem("misTickers", mios.value); } catch (e) {}
  pintar();
});

pintar();
</script>
</body>
</html>
"""


def main():
    empresas = lista_sp500()
    print(f"{len(empresas)} empresas en la lista")

    filas = calcular(empresas)
    print(f"{len(filas)} con datos utiles")

    fecha = datetime.now(ARG).strftime("%d/%m/%Y %H:%M") + " hs ARG"
    html = PLANTILLA.replace("__FECHA__", fecha)
    html = html.replace("__DATOS__", json.dumps(filas, ensure_ascii=False))

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{SALIDA} generado ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
