"""
Seccion Merval (merval/index.html): el indice S&P Merval y sus principales
acciones, medidos en pesos y en dolares contado con liqui (CCL).

En pesos, los maximos historicos no dicen nada por la inflacion; por eso la
distancia al maximo, el promedio de 200 semanas y la variacion anual se miden
en dolares CCL, que hay desde 2013.
"""

from io import StringIO

import pandas as pd
import requests
import yfinance as yf

from . import comun
from .comun import a_json

INDICE = "^MERV"
CCL = "https://api.argentinadatos.com/v1/cotizaciones/dolares/contadoconliqui"
WIKI = "https://es.wikipedia.org/wiki/S%26P_Merval"

# Si Wikipedia cambia o no responde: acciones lideres al 2026-10
RESPALDO = [
    ("YPFD", "YPF"), ("GGAL", "Grupo Financiero Galicia"), ("BMA", "Banco Macro"), ("TECO2", "Telecom Argentina"),
    ("PAMP", "Pampa Energía"), ("BBAR", "BBVA Argentina"), ("TGSU2", "Transportadora de Gas del Sur"),
    ("TXAR", "Ternium Argentina"), ("CEPU", "Central Puerto"), ("ALUA", "Aluar"), ("EDN", "Edenor"),
    ("BYMA", "Bolsas y Mercados Argentinos"), ("LOMA", "Loma Negra"), ("SUPV", "Grupo Supervielle"),
    ("CVH", "Cablevisión Holding"), ("TRAN", "Transener"), ("CRES", "Cresud"), ("HARG", "Holcim Argentina"),
    ("COME", "Sociedad Comercial del Plata"), ("MIRG", "Mirgor"), ("TGNO4", "Transportadora de Gas del Norte"),
    ("VALO", "Banco de Valores"),
]


def acciones():
    """[(ticker, nombre)] de la tabla de componentes de Wikipedia en castellano."""
    try:
        r = requests.get(WIKI, headers=comun.UA, timeout=30)
        r.raise_for_status()
        for t in pd.read_html(StringIO(r.text)):
            if "Símbolo" in t.columns and "Compañía" in t.columns:
                lista = []
                for _, fila in t.iterrows():
                    simbolo = str(fila["Símbolo"])
                    if "BCBA:" in simbolo:
                        lista.append((simbolo.split("BCBA:")[1].split()[0].strip(), str(fila["Compañía"]).strip()))
                if len(lista) >= 10:
                    return lista
    except Exception as e:
        print(f"  Sin lista de Wikipedia ({e}): uso la de respaldo")
    return RESPALDO


def serie_ccl():
    datos = comun.pedir_json(CCL, timeout=60)
    s = pd.Series({pd.Timestamp(d["fecha"]): float(d["venta"]) for d in datos if d.get("venta")})
    return s.sort_index()


def medir(cierres, ccl):
    """Metricas de una serie diaria de cierres en pesos, en pesos y en dolares CCL."""
    cierres = cierres.dropna()
    if len(cierres) < 30:
        return None
    usd = (cierres / ccl.reindex(cierres.index, method="ffill")).dropna()
    usd = usd[usd.index >= ccl.index[0]]
    precio, previo = float(cierres.iloc[-1]), float(cierres.iloc[-2])
    m = {
        "p": round(precio, 2),
        "var": round((precio / previo - 1) * 100, 2),
        "f": cierres.index[-1].date().isoformat(),
        "pu": None, "da": None, "fa": None, "dm": None, "ru": None, "rp": None,
    }
    hace = cierres.index[-1] - pd.Timedelta(days=365)
    anio = cierres.loc[:hace]
    if not anio.empty:
        m["rp"] = round((precio / float(anio.iloc[-1]) - 1) * 100, 1)
    if usd.empty:
        return m
    pu = float(usd.iloc[-1])
    m["pu"] = round(pu, 2)
    m["da"] = round((pu / float(usd.max()) - 1) * 100, 1)
    m["fa"] = usd.idxmax().date().isoformat()
    semanal = usd.resample("W-FRI").last().dropna()
    if len(semanal) >= 200:
        m["dm"] = round((pu / float(semanal.iloc[-200:].mean()) - 1) * 100, 1)
    anio_usd = usd.loc[:hace]
    if not anio_usd.empty:
        m["ru"] = round((pu / float(anio_usd.iloc[-1]) - 1) * 100, 1)
    return m


def generar():
    ccl = serie_ccl()
    lista = acciones()
    tickers = [INDICE] + [f"{t}.BA" for t, _ in lista]
    data = yf.download(tickers, period="max", interval="1d", auto_adjust=False,
                       group_by="ticker", threads=True, progress=False)

    def cierres(t):
        try:
            return data[t]["Close"]
        except KeyError:
            return pd.Series(dtype=float)

    indice = medir(cierres(INDICE), ccl)
    if not indice:
        raise RuntimeError("Yahoo no devolvio el S&P Merval")

    filas, afuera = [], []
    for t, nombre in lista:
        m = medir(cierres(f"{t}.BA"), ccl)
        if m:
            filas.append({"t": t, "n": nombre, **m})
        else:
            afuera.append(t)
    if afuera:
        print(f"  Sin datos: {', '.join(afuera)}")

    # historia del indice: semanal en pesos y en dolares, desde que hay CCL
    m = cierres(INDICE).dropna()
    semanal = m.resample("W-FRI").last().dropna()
    semanal = semanal[semanal.index >= ccl.index[0]]
    usd = (semanal / ccl.reindex(semanal.index, method="ffill")).dropna()
    hist = {
        "ars": [[d.date().isoformat(), round(float(v))] for d, v in semanal.items()],
        "usd": [[d.date().isoformat(), round(float(v), 1)] for d, v in usd.items()],
    }

    datos = {"indice": indice, "filas": filas, "hist": hist, "ccl": round(float(ccl.iloc[-1]), 2),
             "fccl": ccl.index[-1].date().isoformat()}
    comun.escribir("merval", comun.pagina(
        "merval", "Merval",
        "El índice S&P Merval y las principales acciones argentinas, en pesos y en dólares contado con liqui.",
        CUERPO.replace("__ACTUALIZADO__", comun.sello()), css=CSS, js=JS.replace("__DATOS__", a_json(datos)),
        fuentes="Precios: Yahoo Finance. Dólar contado con liqui: argentinadatos.com. Lista de acciones: Wikipedia.",
    ))
    print(f"  {len(filas)} acciones; Merval {indice['p']:,.0f} ({indice['pu']} US$)")

    return {
        "actualizado": comun.sello(),
        "datos_al": indice["f"],
        **{k: indice[k] for k in ("p", "var", "pu", "da", "fa", "ru", "rp")},
    }


CSS = r"""
.tv{font-size:12.5px;color:var(--tinta-2)}
#tabla td:first-child b{margin-right:4px}
@media (max-width:899px){
  /* a la vista: acción, precio en pesos y variación del día; lo demás, al tocar la fila */
  #tabla tr:not(.abierta) td:nth-child(n+4),
  #tabla tr:not(.abierta) td:first-child .sub{display:none}
  #tabla td:nth-child(2){order:2;margin-left:auto;font-size:16px;font-weight:700;color:var(--tinta);text-align:right}
  #tabla td:nth-child(2)::before{content:"$ "}
  #tabla td:nth-child(3)::before{content:"Día "}
  #tabla td:nth-child(4)::before{content:"US$ "}
  #tabla td:nth-child(5)::before{content:"Desde su máximo "}
  #tabla td:nth-child(6)::before{content:"Vs. 200 sem. "}
  #tabla td:nth-child(7)::before{content:"12 meses US$ "}
  #tabla td:nth-child(8)::before{content:"12 meses $ "}
}
"""


CUERPO = r"""
<div class="titulo">
  <h1>Merval</h1>
  <p class="bajada">El índice de las principales acciones argentinas, en pesos y en dólares contado con liqui.</p>
</div>
<section aria-label="El índice"><div class="cifras" id="cifras"></div></section>
<p class="fecha" id="fecha">Actualizado el __ACTUALIZADO__ hs</p>

<section class="bloque" aria-labelledby="t-hist">
  <h2 id="t-hist">Cómo vino el índice</h2>
  <p class="nota">Cierre de cada semana desde 2013. En dólares, dividido por el contado con liqui de ese día.</p>
  <div class="controles">
    <div class="grupo" role="group" aria-label="Moneda" id="monedas"></div>
    <div class="grupo" role="group" aria-label="Período" id="rangos"></div>
  </div>
  <div id="grafico"></div>
</section>

<section class="bloque" aria-labelledby="t-acc">
  <h2 id="t-acc">Principales acciones</h2>
  <p class="nota">Lista de componentes publicada en Wikipedia; puede no coincidir exactamente con la composición vigente del índice. Máximo, promedio de 200 semanas y 12 meses en dólares CCL.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla" data-ficha>
    <thead><tr>
      <th data-k="t" data-asc="1"><button type="button">Empresa</button></th>
      <th class="der" data-k="p"><button type="button">Precio ($)</button></th>
      <th class="der" data-k="var"><button type="button">Día</button></th>
      <th class="der" data-k="pu"><button type="button">Precio (US$ CCL)</button></th>
      <th class="der" data-k="da" data-asc="1"><button type="button">Desde su máximo</button></th>
      <th class="der" data-k="dm" data-asc="1"><button type="button">Vs. 200 semanas</button></th>
      <th class="der" data-k="ru"><button type="button">12 meses (US$)</button></th>
      <th class="der" data-k="rp"><button type="button">12 meses ($)</button></th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<details class="bloque plegado">
  <summary><h2 id="t-glos">Cómo leer esta página</h2></summary>
  <dl class="glosario">
    <div><dt>En dólares CCL</dt><dd>Precio en pesos dividido por el dólar contado con liqui del mismo día. Permite comparar precios de distintos años sin el efecto de la inflación y las devaluaciones.</dd></div>
    <div><dt>Desde su máximo</dt><dd>Cuánto le falta al precio en dólares para volver al mayor valor que tuvo desde 2013, cuando empieza la serie del contado con liqui.</dd></div>
    <div><dt>Vs. 200 semanas</dt><dd>Distancia del precio en dólares a su promedio de las últimas 200 semanas, casi cuatro años.</dd></div>
    <div><dt>12 meses</dt><dd>Variación del precio en el último año, en dólares y en pesos.</dd></div>
  </dl>
</details>
"""


JS = r"""
const M = Mercadito;
const D = __DATOS__;
const $ = id => document.getElementById(id);
const I = D.indice;

$("fecha").textContent += " · precios al " + M.fecha(I.f) + " · contado con liqui " + M.pesos(D.ccl) + " (" + M.fecha(D.fccl) + ")";
$("cifras").innerHTML = [
  ["En dólares CCL", I.pu === null ? "—" : M.dolares(I.pu, 0), I.ru !== null ? M.pct(I.ru, 1) + " en 12 meses" : ""],
  ["Desde su máximo en dólares", I.da === null ? "—" : M.pct(I.da, 1), I.fa ? "Máximo del " + M.fecha(I.fa) : ""],
  ["S&P Merval en pesos", M.num(I.p, 0), M.pct(I.var, 2) + " en el día" + (I.rp !== null ? " · " + M.pct(I.rp, 1) + " en 12 meses" : "")],
  ["Vs. su promedio de 200 semanas", I.dm === null ? "—" : M.pct(I.dm, 1), "En dólares CCL"],
].map(([e, v, s]) => "<div class='cifra'><p class='cifra-et'>" + e + "</p><p class='cifra-val num'>" + v +
  "</p><p class='cifra-sub'>" + s + "</p></div>").join("");

/* historia */
let moneda = "usd", rango = 1827;
const RANGOS = [["1 año", 366], ["3 años", 1096], ["5 años", 1827], ["Desde 2013", 0]];
function pintarGrafico() {
  const usd = moneda === "usd";
  M.linea($("grafico"), [{nombre: usd ? "En dólares CCL" : "En pesos", color: "var(--s1)", puntos: M.desde(D.hist[moneda], rango)}],
    {formato: v => usd ? "US$ " + M.num(v, 0) : M.num(v / 1000, 0) + " mil", titulo: "S&P Merval " + (usd ? "en dólares CCL" : "en pesos")});
}
function grupo(id, opciones, actual, alElegir) {
  $(id).innerHTML = opciones.map(([n, v]) =>
    "<button type='button' class='boton boton-chico' data-v='" + v + "' aria-pressed='" + (String(v) === String(actual)) + "'>" + n + "</button>").join("");
  $(id).addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    $(id).querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
    alElegir(b.dataset.v);
    pintarGrafico();
  });
}
grupo("monedas", [["En dólares", "usd"], ["En pesos", "ars"]], moneda, v => { moneda = v; });
grupo("rangos", RANGOS, rango, v => { rango = +v; });
pintarGrafico();

/* acciones */
const celda = (v, dec, signo) => "<td class='der num'>" + (v === null ? "—" : signo ? M.pct(v, dec) : M.num(v, dec)) + "</td>";
M.ordenable($("tabla"), ["da", true], (k, a) => {
  $("tabla").tBodies[0].innerHTML = D.filas.slice().sort(M.comparar(k, a)).map(r =>
    "<tr><td><b>" + M.esc(r.t) + "</b> " + M.esc(r.n) +
    "<span class='sub'><a class='tv' href='https://www.tradingview.com/chart/?symbol=" + encodeURIComponent("BCBA:" + r.t) +
    "' target='_blank' rel='noopener'>Ver en TradingView</a>" + (r.fa ? " · máximo en US$ del " + M.fecha(r.fa) : "") + "</span></td>" +
    celda(r.p, 2) + celda(r.var, 2, true) + celda(r.pu, 2) + celda(r.da, 1, true) + celda(r.dm, 1, true) +
    celda(r.ru, 1, true) + celda(r.rp, 1, true) + "</tr>").join("");
});
"""
