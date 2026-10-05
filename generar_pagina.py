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


PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>S&amp;P 500 — cuánto les falta para volver a su máximo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --papel:#FBFBF9; --tinta:#16181D; --suave:#6B6F76; --linea:#E4E4DF;
  --caida:#A4303F; --suba:#2F6B4F; --marca:#EEEDE8;
  --foco:#1F5FA8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-tema="claro"]){--papel:#14161A; --tinta:#E8E9E6; --suave:#9196A0;
        --linea:#262A31; --caida:#E06C78; --suba:#5FB58C; --marca:#1B1E24;}
}
:root[data-tema="oscuro"]{--papel:#14161A; --tinta:#E8E9E6; --suave:#9196A0;
  --linea:#262A31; --caida:#E06C78; --suba:#5FB58C; --marca:#1B1E24;}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--papel);color:var(--tinta);
 font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
 font-size:15px;line-height:1.5;padding:28px 20px 60px}
.wrap{max-width:1060px;margin:0 auto}
h1{font-size:28px;font-weight:600;letter-spacing:-.02em;margin:0}
.cab{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:6px}
#tema{font:inherit;font-size:13px;padding:6px 12px;border-radius:999px;cursor:pointer;
 border:1px solid var(--linea);background:transparent;color:var(--suave)}
#tema:hover{background:var(--marca);color:var(--tinta)}
.intro{color:var(--suave);font-size:14px;max-width:62ch;margin:0 0 22px}
.intro b{color:var(--tinta);font-weight:600}

.tira{display:flex;align-items:flex-end;gap:2px;height:46px;margin:0 0 6px}
.tira div{flex:1;background:var(--marca);border-radius:2px 2px 0 0;min-height:2px;
 position:relative;cursor:pointer}
.tira div:hover,.tira div.on{background:var(--caida)}
.tira-pie{display:flex;justify-content:space-between;color:var(--suave);
 font-size:11.5px;border-top:1px solid var(--linea);padding-top:5px;margin-bottom:24px}

.ctrl{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end;margin-bottom:14px}
.campo{display:flex;flex-direction:column;gap:4px}
.campo.ancho{flex:1;min-width:190px}
label{font-size:12px;color:var(--suave)}
input,select{font:inherit;font-size:14px;padding:7px 9px;border:1px solid var(--linea);
 border-radius:6px;background:transparent;color:var(--tinta);width:100%}
input:focus-visible,select:focus-visible,button:focus-visible{outline:2px solid var(--foco);outline-offset:1px}
input[type=number]{width:96px}
.presets{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:22px}
.presets button{font:inherit;font-size:13px;padding:6px 11px;border-radius:999px;
 border:1px solid var(--linea);background:transparent;color:var(--tinta);cursor:pointer}
.presets button:hover{background:var(--marca)}
.presets button.on{background:var(--tinta);color:var(--papel);border-color:var(--tinta)}

.cuenta{font-size:13px;color:var(--suave);margin-bottom:8px}
.tabla{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;min-width:660px}
thead th{position:sticky;top:0;background:var(--papel);text-align:right;
 font-weight:500;font-size:12.5px;color:var(--suave);padding:0 10px 8px;
 cursor:pointer;white-space:nowrap;border-bottom:1px solid var(--tinta)}
thead th:first-child,thead th:nth-child(2),thead th:nth-child(3){text-align:left}
thead th span{opacity:0}
thead th.orden span{opacity:1}
td{padding:9px 10px;border-bottom:1px solid var(--linea);text-align:right;
 font-variant-numeric:tabular-nums}
td:first-child{text-align:left;font-weight:600;letter-spacing:-.01em}
td.emp,td.sec{text-align:left;color:var(--suave);font-size:13.5px}
tbody tr:hover td{background:var(--marca)}
.val{font-weight:500;color:var(--caida)}
.val.arriba{color:var(--suba)}
.nd{color:var(--suave)}
.anio{color:var(--suave);font-size:13px}
.vacio{padding:36px 0;text-align:center;color:var(--suave)}
.pie{margin-top:26px;padding-top:14px;border-top:1px solid var(--linea);
 color:var(--suave);font-size:12.5px;max-width:70ch;line-height:1.65}
@media(max-width:700px){
  body{padding:20px 14px 48px} h1{font-size:23px}
  td.sec,thead th:nth-child(3){display:none}
  td.emp,thead th:nth-child(2){max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
}
</style>
</head>
<body>
<div class="wrap">

<div class="cab">
  <h1>S&amp;P 500</h1>
  <button id="tema" type="button">Modo noche</button>
</div>
<p class="intro" id="resumen"></p>

<div class="tira" id="tira"></div>
<div class="tira-pie">
  <span>cayeron más de 60%</span><span>a mitad de camino</span><span>en su máximo</span>
</div>

<div class="ctrl">
  <div class="campo ancho">
    <label for="q">Buscar</label>
    <input id="q" placeholder="ticker o nombre">
  </div>
  <div class="campo ancho">
    <label for="sec">Sector</label>
    <select id="sec"><option value="">Todos</option></select>
  </div>
  <div class="campo">
    <label for="mincaida">Cayó al menos</label>
    <input id="mincaida" type="number" placeholder="%">
  </div>
  <div class="campo">
    <label for="maxma">A menos de la 200 sem</label>
    <input id="maxma" type="number" placeholder="%">
  </div>
  <div class="campo">
    <label for="maxanios">Máximo hace menos de</label>
    <input id="maxanios" type="number" placeholder="años">
  </div>
</div>

<div class="presets">
  <button data-p="recientes">Cayeron fuerte hace poco</button>
  <button data-p="apoyadas">Apoyadas en su promedio de 4 años</button>
  <button data-p="maximos">En zona de máximos</button>
  <button data-p="limpiar">Limpiar</button>
</div>

<div class="cuenta" id="cuenta"></div>
<div class="tabla">
<table>
<thead><tr>
<th data-k="t">Ticker <span>&#9662;</span></th>
<th data-k="n">Empresa <span>&#9662;</span></th>
<th data-k="s">Sector <span>&#9662;</span></th>
<th data-k="p">Precio <span>&#9662;</span></th>
<th data-k="da">Desde su máximo <span>&#9662;</span></th>
<th data-k="dm">vs 200 sem <span>&#9662;</span></th>
<th data-k="fa">Máximo <span>&#9662;</span></th>
</tr></thead>
<tbody id="cuerpo"></tbody>
</table>
</div>

<p class="pie">
<b>Desde su máximo</b>: cuánto le falta al precio para volver al mayor valor que
alcanzó esa acción.<br>
<b>vs 200 sem</b>: distancia al precio promedio de las últimas 200 semanas, casi
cuatro años. En rojo, las que cotizan por debajo de ese promedio.<br>
<b>Máximo</b>: cuándo lo marcó. Una caída del 80% contra un máximo del 2000 no es
una oportunidad, es una empresa que nunca volvió.<br>
Precios semanales de Yahoo Finance, sin ajustar por dividendos. Esto ordena
precios, no mide calidad: una acción barata puede estar barata con razón.
</p>

</div>
<script>
const D = __DATOS__;
const HOY = new Date();
D.forEach(r => { r.an = Math.round((HOY - new Date(r.fa)) / 31557600000); });

let orden = "da", asc = true, preset = "";
const $ = id => document.getElementById(id);

const sel = $("sec");
[...new Set(D.map(r => r.s))].sort().forEach(s => {
  const o = document.createElement("option");
  o.value = s; o.textContent = s; sel.appendChild(o);
});

const bajoMA = D.filter(r => r.dm !== null && r.dm < 0).length;
const medios = D.map(r => r.da).sort((a, b) => a - b);
const mediana = medios[Math.floor(medios.length / 2)];
$("resumen").innerHTML = "De las <b>" + D.length + "</b> empresas del índice, " +
  "la del medio está <b>" + Math.abs(mediana).toFixed(0) + "%</b> debajo de su máximo " +
  "histórico y <b>" + bajoMA + "</b> cotizan por debajo de su promedio de cuatro años. " +
  "Ordenado de la más castigada a la que está en máximos.";

const BUCKETS = 20;
const tira = $("tira");
const conteo = new Array(BUCKETS).fill(0);
D.forEach(r => {
  let i = Math.floor((100 + r.da) / 100 * BUCKETS);
  conteo[Math.max(0, Math.min(BUCKETS - 1, i))]++;
});
const tope = Math.max(...conteo);
conteo.forEach((c, i) => {
  const d = document.createElement("div");
  d.style.height = Math.max(2, c / tope * 46) + "px";
  const desde = -100 + i * (100 / BUCKETS), hasta = desde + 100 / BUCKETS;
  d.title = c + " empresas entre " + desde.toFixed(0) + "% y " + hasta.toFixed(0) + "%";
  d.onclick = () => {
    $("mincaida").value = Math.abs(hasta).toFixed(0);
    [...tira.children].forEach(x => x.classList.remove("on"));
    d.classList.add("on");
    pintar();
  };
  tira.appendChild(d);
});

function num(v, dec) {
  return v.toLocaleString("es-AR", {minimumFractionDigits: dec, maximumFractionDigits: dec});
}

function pintar() {
  const q = $("q").value.trim().toUpperCase();
  const s = sel.value;
  const minc = parseFloat($("mincaida").value);
  const maxm = parseFloat($("maxma").value);
  const maxa = parseFloat($("maxanios").value);

  const f = D.filter(r => {
    if (q && !(r.t.includes(q) || r.n.toUpperCase().includes(q))) return false;
    if (s && r.s !== s) return false;
    if (!isNaN(minc) && r.da > -Math.abs(minc)) return false;
    if (!isNaN(maxa) && r.an > maxa) return false;
    if (!isNaN(maxm)) {
      if (r.dm === null) return false;
      if (Math.abs(r.dm) > Math.abs(maxm)) return false;
    }
    return true;
  });

  f.sort((a, b) => {
    const x = a[orden], y = b[orden];
    if (x === null) return 1;
    if (y === null) return -1;
    if (typeof x === "string") return asc ? x.localeCompare(y) : y.localeCompare(x);
    return asc ? x - y : y - x;
  });

  $("cuenta").textContent = f.length === D.length
    ? f.length + " empresas"
    : f.length + " de " + D.length + " empresas";

  $("cuerpo").innerHTML = f.length === 0
    ? "<tr><td colspan='7' class='vacio'>Ningún papel cumple con esos filtros. Aflojá alguno.</td></tr>"
    : f.map(r => {
        const ma = r.dm === null
          ? "<span class='nd'>sin dato</span>"
          : "<span class='val" + (r.dm >= 0 ? " arriba" : "") + "'>" +
            (r.dm > 0 ? "+" : "") + num(r.dm, 0) + "%</span>";
        return "<tr><td>" + r.t + "</td>" +
          "<td class='emp'>" + r.n + "</td>" +
          "<td class='sec'>" + r.s + "</td>" +
          "<td>" + num(r.p, 2) + "</td>" +
          "<td><span class='val" + (r.da >= 0 ? " arriba" : "") + "'>" +
            (r.da > 0 ? "+" : "") + num(r.da, 1) + "%</span></td>" +
          "<td>" + ma + "</td>" +
          "<td class='anio'>" + r.fa.slice(0, 4) +
            (r.an >= 1 ? " · hace " + r.an + (r.an === 1 ? " año" : " años") : " · este año") +
          "</td></tr>";
      }).join("");
}

document.querySelectorAll("thead th").forEach(th => {
  th.onclick = () => {
    const k = th.dataset.k;
    asc = (orden === k) ? !asc : (k === "da" || k === "dm");
    orden = k;
    document.querySelectorAll("thead th").forEach(o => o.classList.remove("orden"));
    th.classList.add("orden");
    th.querySelector("span").textContent = asc ? "\u25BE" : "\u25B4";
    pintar();
  };
});

document.querySelectorAll(".presets button").forEach(b => {
  b.onclick = () => {
    const p = b.dataset.p;
    $("mincaida").value = ""; $("maxma").value = ""; $("maxanios").value = "";
    [...tira.children].forEach(x => x.classList.remove("on"));
    document.querySelectorAll(".presets button").forEach(o => o.classList.remove("on"));
    if (p !== "limpiar" && p !== preset) {
      b.classList.add("on");
      preset = p;
      if (p === "recientes") { $("mincaida").value = 30; $("maxanios").value = 2; }
      if (p === "apoyadas") { $("maxma").value = 5; $("mincaida").value = 15; }
      if (p === "maximos") { $("mincaida").value = ""; $("maxma").value = ""; orden = "da"; asc = false; }
    } else {
      preset = "";
      $("q").value = ""; sel.value = "";
      orden = "da"; asc = true;
    }
    pintar();
  };
});

["q", "sec", "mincaida", "maxma", "maxanios"].forEach(id => {
  $(id).addEventListener("input", pintar);
  $(id).addEventListener("change", pintar);
});

pintar();

const btn = $("tema");
function aplicarTema(t) {
  if (t) document.documentElement.setAttribute("data-tema", t);
  else document.documentElement.removeAttribute("data-tema");
  const oscuroAhora = t === "oscuro" ||
    (!t && matchMedia("(prefers-color-scheme: dark)").matches);
  btn.textContent = oscuroAhora ? "Modo día" : "Modo noche";
}
let tema = null;
try { tema = localStorage.getItem("tema"); } catch (e) {}
aplicarTema(tema);
btn.onclick = () => {
  const oscuroAhora = document.documentElement.getAttribute("data-tema") === "oscuro" ||
    (!document.documentElement.getAttribute("data-tema") &&
     matchMedia("(prefers-color-scheme: dark)").matches);
  const nuevo = oscuroAhora ? "claro" : "oscuro";
  try { localStorage.setItem("tema", nuevo); } catch (e) {}
  aplicarTema(nuevo);
};
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
