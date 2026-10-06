"""
Seccion Bonos (bonos/index.html): riesgo pais, bonos soberanos en dolares,
letras del Tesoro y obligaciones negociables mas operadas.

Precios de data912.com, un proyecto gratuito con fines educativos: si deja de
responder, la seccion queda con su ultima version publicada.
"""

import re
from datetime import date, timedelta

from . import comun
from .comun import a_json

BONOS = "https://data912.com/live/arg_bonds"
LETRAS = "https://data912.com/live/arg_notes"
ONS = "https://data912.com/live/arg_corp"
RIESGO = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais"

# (simbolo, ley) de los bonos de la reestructuracion de 2020
SOBERANOS = [
    ("AL29", "Argentina"), ("AL30", "Argentina"), ("AL35", "Argentina"), ("AE38", "Argentina"), ("AL41", "Argentina"),
    ("GD29", "Nueva York"), ("GD30", "Nueva York"), ("GD35", "Nueva York"), ("GD38", "Nueva York"),
    ("GD41", "Nueva York"), ("GD46", "Nueva York"),
]
ONS_MOSTRADAS = 30
DIAS_RIESGO = 730

# Letras: la primera letra dice el tipo y el resto la fecha de vencimiento,
# por ejemplo S30O6 = LECAP que vence el 30 de octubre de 2026.
TIPOS_LETRA = {"S": "LECAP", "T": "BONCAP", "X": "Ajusta por CER", "D": "Dólar linked"}
MESES_LETRA = {"E": 1, "F": 2, "M": 3, "A": 4, "Y": 5, "J": 6, "L": 7, "G": 8, "S": 9, "O": 10, "N": 11, "D": 12}
PATRON_LETRA = re.compile(r"^([STXD])(\d{1,2})([EFMAYJLGSOND])(\d)$")


def vencimiento(simbolo):
    m = PATRON_LETRA.match(simbolo)
    if not m:
        return None
    tipo, dia, mes, anio = m.groups()
    try:
        return TIPOS_LETRA[tipo], date(2020 + int(anio), MESES_LETRA[mes], int(dia))
    except ValueError:
        return None


def generar():
    bonos = {b["symbol"]: b for b in comun.pedir_json(BONOS)}
    hoy = comun.ahora().date()

    soberanos = []
    for simbolo, ley in SOBERANOS:
        pesos, mep, cable = bonos.get(simbolo), bonos.get(simbolo + "D"), bonos.get(simbolo + "C")
        if not mep or not mep.get("c"):
            continue
        p = pesos["c"] if pesos and pesos.get("c") else None
        soberanos.append({
            "t": simbolo, "ley": ley,
            "d": mep["c"], "var": mep.get("pct_change"), "vol": mep.get("v"),
            "c": cable["c"] if cable and cable.get("c") else None,
            "p": p,
            "mep": round(p / mep["c"], 2) if p else None,
        })
    if not soberanos:
        raise RuntimeError("data912 no devolvio precios de los bonos soberanos")

    letras = []
    try:
        for l in comun.pedir_json(LETRAS):
            v = vencimiento(l["symbol"])
            if not v or not l.get("c") or v[1] < hoy:
                continue
            letras.append({"t": l["symbol"], "tipo": v[0], "vence": v[1].isoformat(), "dias": (v[1] - hoy).days,
                           "c": l["c"], "var": l.get("pct_change"), "vol": l.get("v")})
        letras.sort(key=lambda l: l["vence"])
    except Exception as e:
        print(f"  Sin letras ({e})")

    ons = []
    try:
        en_dolares = [o for o in comun.pedir_json(ONS) if o["symbol"].endswith("D") and o.get("c") and o.get("v")]
        en_dolares.sort(key=lambda o: o["v"], reverse=True)
        ons = [{"t": o["symbol"], "c": o["c"], "var": o.get("pct_change"), "vol": o["v"]} for o in en_dolares[:ONS_MOSTRADAS]]
    except Exception as e:
        print(f"  Sin obligaciones negociables ({e})")

    riesgo = []
    try:
        corte = (hoy - timedelta(days=DIAS_RIESGO)).isoformat()
        riesgo = [[r["fecha"], r["valor"]] for r in comun.pedir_json(RIESGO, timeout=60) if r["fecha"] >= corte]
        riesgo.sort()
    except Exception as e:
        print(f"  Sin riesgo pais ({e})")

    datos = {"sob": soberanos, "letras": letras, "ons": ons, "riesgo": riesgo}
    comun.escribir("bonos", comun.pagina(
        "bonos", "Bonos",
        "Riesgo país, precios de los bonos soberanos en dólares, letras del Tesoro y obligaciones negociables.",
        CUERPO.replace("__ACTUALIZADO__", comun.sello()), css=CSS, js=JS.replace("__DATOS__", a_json(datos)),
        fuentes="Precios: data912.com (proyecto gratuito con fines educativos, con demora). Riesgo país: argentinadatos.com.",
    ))
    print(f"  {len(soberanos)} soberanos, {len(letras)} letras, {len(ons)} ONs, riesgo pais {len(riesgo)} dias")

    por = {s["t"]: s for s in soberanos}
    ultimo = riesgo[-1] if riesgo else None
    previo = riesgo[-2] if len(riesgo) > 1 else None
    return {
        "actualizado": comun.sello(),
        "riesgo": ultimo and {"v": ultimo[1], "f": ultimo[0], "dif": previo and ultimo[1] - previo[1]},
        "al30": por.get("AL30") and {k: por["AL30"][k] for k in ("d", "var", "mep")},
        "gd30": por.get("GD30") and {k: por["GD30"][k] for k in ("d", "var")},
    }


CSS = r"""
@media (max-width:899px){
  /* a la vista: instrumento, precio y un dato más; lo demás, al tocar la fila */
  #tabla-sob tr:not(.abierta) td:nth-child(n+4),
  #tabla-sob tr:not(.abierta) td:first-child .sub,
  #tabla-letras tr:not(.abierta) td:is(:nth-child(2),:nth-child(5),:nth-child(6)),
  #tabla-ons tr:not(.abierta) td:nth-child(4){display:none}
  #tabla-sob td:nth-child(2),#tabla-ons td:nth-child(2),#tabla-letras td:nth-child(4){order:2;margin-left:auto;font-size:16px;font-weight:700;color:var(--tinta);text-align:right}
  #tabla-sob td:nth-child(2)::before,#tabla-ons td:nth-child(2)::before{content:"US$ "}
  #tabla-sob td:nth-child(3)::before,#tabla-letras td:nth-child(5)::before,#tabla-ons td:nth-child(3)::before{content:"Día "}
  #tabla-sob td:nth-child(4)::before{content:"Cable "}
  #tabla-sob td:nth-child(5)::before{content:"$ "}
  #tabla-sob td:nth-child(6)::before{content:"Dólar implícito "}
  #tabla-sob td:nth-child(7)::before,#tabla-letras td:nth-child(6)::before,#tabla-ons td:nth-child(4)::before{content:"Volumen "}
  #tabla-letras td:nth-child(3)::before{content:"Vence "}
  #tabla-letras td:nth-child(3) .sub{display:inline;margin-left:4px}
}
"""


CUERPO = r"""
<div class="titulo">
  <h1>Bonos</h1>
  <p class="bajada">Riesgo país y precios de bonos del Tesoro, letras y obligaciones negociables.</p>
</div>
<section aria-label="Datos principales"><div class="cifras" id="cifras"></div></section>
<p class="fecha">Actualizado el __ACTUALIZADO__ hs · precios con demora</p>

<section class="bloque" aria-labelledby="t-riesgo" id="bloque-riesgo">
  <h2 id="t-riesgo">Riesgo país</h2>
  <p class="nota">Diferencia, en puntos básicos, entre lo que rinden los bonos argentinos en dólares y los del Tesoro de Estados Unidos (100 puntos = 1%).</p>
  <div class="controles"><div class="grupo" role="group" aria-label="Período" id="rangos"></div></div>
  <div id="grafico"></div>
</section>

<section class="bloque" aria-labelledby="t-sob">
  <h2 id="t-sob">Bonos soberanos en dólares</h2>
  <p class="nota">Precio cada 100 dólares de valor nominal original. Los AL y el AE38 son de ley argentina; los GD, de ley de Nueva York. El dólar implícito es el precio en pesos dividido por el precio en dólares MEP.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-sob" data-ficha>
    <thead><tr>
      <th data-k="t" data-asc="1"><button type="button">Bono</button></th>
      <th class="der" data-k="d"><button type="button">Precio US$ MEP</button></th>
      <th class="der" data-k="var"><button type="button">Día</button></th>
      <th class="der" data-k="c"><button type="button">Precio US$ cable</button></th>
      <th class="der" data-k="p"><button type="button">Precio $</button></th>
      <th class="der" data-k="mep"><button type="button">Dólar implícito</button></th>
      <th class="der" data-k="vol"><button type="button">Volumen</button></th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-letras" id="bloque-letras">
  <h2 id="t-letras">Letras y bonos cortos del Tesoro</h2>
  <p class="nota">Ordenadas por vencimiento. Precio en pesos cada 100 de valor nominal.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-letras" data-ficha>
    <thead><tr>
      <th data-k="t" data-asc="1"><button type="button">Instrumento</button></th>
      <th data-k="tipo" data-asc="1"><button type="button">Tipo</button></th>
      <th class="der" data-k="vence" data-asc="1"><button type="button">Vence</button></th>
      <th class="der" data-k="c"><button type="button">Precio</button></th>
      <th class="der" data-k="var"><button type="button">Día</button></th>
      <th class="der" data-k="vol"><button type="button">Volumen</button></th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-ons" id="bloque-ons">
  <h2 id="t-ons">Obligaciones negociables más operadas</h2>
  <p class="nota">Deuda de empresas que cotiza en dólares MEP, ordenada por volumen del día. Se muestra el símbolo de BYMA.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-ons" data-ficha>
    <thead><tr>
      <th data-k="t" data-asc="1"><button type="button">Símbolo</button></th>
      <th class="der" data-k="c"><button type="button">Precio US$</button></th>
      <th class="der" data-k="var"><button type="button">Día</button></th>
      <th class="der" data-k="vol"><button type="button">Volumen</button></th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<details class="bloque plegado">
  <summary><h2 id="t-glos">Cómo leer esta página</h2></summary>
  <dl class="glosario">
    <div><dt>MEP y cable</dt><dd>El mismo bono se puede comprar o vender en pesos, en dólares en el país (MEP, símbolo terminado en D) o en dólares en el exterior (cable, terminado en C).</dd></div>
    <div><dt>LECAP y BONCAP</dt><dd>Letras y bonos del Tesoro en pesos que pagan todo al vencimiento.</dd></div>
    <div><dt>Ajusta por CER</dt><dd>Instrumentos cuyo capital se actualiza por inflación.</dd></div>
    <div><dt>Dólar linked</dt><dd>Instrumentos en pesos que se ajustan por el dólar oficial mayorista.</dd></div>
    <div><dt>Próximamente</dt><dd>Tasa interna de retorno (TIR) y duration de cada bono, que requieren su cronograma de pagos.</dd></div>
  </dl>
</details>
"""


JS = r"""
const M = Mercadito;
const D = __DATOS__;
const $ = id => document.getElementById(id);
const celda = (v, dec, signo) => "<td class='der num'>" + (v === null || v === undefined ? "—" : signo ? M.pct(v, dec) : M.num(v, dec)) + "</td>";
const por = Object.fromEntries(D.sob.map(s => [s.t, s]));

/* cifras */
const cifras = [];
if (D.riesgo.length) {
  const [f, v] = D.riesgo[D.riesgo.length - 1], prev = D.riesgo.length > 1 ? D.riesgo[D.riesgo.length - 2][1] : null;
  cifras.push(["Riesgo país", M.num(v, 0) + " puntos", (prev !== null ? (v - prev > 0 ? "+" : "") + M.num(v - prev, 0) + " vs. el día anterior · " : "") + M.fecha(f)]);
}
if (por.AL30) cifras.push(["AL30 en dólares MEP", M.dolares(por.AL30.d), M.pct(por.AL30.var, 2) + " en el día"]);
if (por.GD30) cifras.push(["GD30 en dólares MEP", M.dolares(por.GD30.d), M.pct(por.GD30.var, 2) + " en el día"]);
if (por.AL30 && por.AL30.mep) cifras.push(["Dólar implícito en el AL30", M.pesos(por.AL30.mep), "Precio en pesos ÷ precio en dólares"]);
$("cifras").innerHTML = cifras.map(([e, v, s]) =>
  "<div class='cifra'><p class='cifra-et'>" + e + "</p><p class='cifra-val num'>" + v + "</p><p class='cifra-sub'>" + s + "</p></div>").join("");

/* riesgo país */
if (D.riesgo.length) {
  const RANGOS = [["3 meses", 92], ["6 meses", 183], ["1 año", 366], ["2 años", 731]];
  let rango = 366;
  const pintar = () => M.linea($("grafico"), [{nombre: "Riesgo país", color: "var(--s1)", puntos: M.desde(D.riesgo, rango)}],
    {formato: v => M.num(v, 0), titulo: "Riesgo país en puntos básicos"});
  $("rangos").innerHTML = RANGOS.map(([n, d]) =>
    "<button type='button' class='boton boton-chico' data-d='" + d + "' aria-pressed='" + (d === rango) + "'>" + n + "</button>").join("");
  $("rangos").addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    rango = +b.dataset.d;
    $("rangos").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
    pintar();
  });
  pintar();
} else {
  $("bloque-riesgo").hidden = true;
}

/* soberanos */
M.ordenable($("tabla-sob"), ["t", true], (k, a) => {
  $("tabla-sob").tBodies[0].innerHTML = D.sob.slice().sort(M.comparar(k, a)).map(s =>
    "<tr><td><b>" + M.esc(s.t) + "</b><span class='sub'>Ley " + M.esc(s.ley) + "</span></td>" +
    celda(s.d, 2) + celda(s.var, 2, true) + celda(s.c, 2) + celda(s.p, 0) + celda(s.mep, 2) + celda(s.vol, 0) + "</tr>").join("");
});

/* letras */
if (D.letras.length) {
  M.ordenable($("tabla-letras"), ["vence", true], (k, a) => {
    $("tabla-letras").tBodies[0].innerHTML = D.letras.slice().sort(M.comparar(k, a)).map(l =>
      "<tr><td><b>" + M.esc(l.t) + "</b></td><td>" + M.esc(l.tipo) + "</td>" +
      "<td class='der num'>" + M.fecha(l.vence) + "<span class='sub'>" + l.dias + " días</span></td>" +
      celda(l.c, 2) + celda(l.var, 2, true) + celda(l.vol, 0) + "</tr>").join("");
  });
} else {
  $("bloque-letras").hidden = true;
}

/* obligaciones negociables */
if (D.ons.length) {
  M.ordenable($("tabla-ons"), ["vol", false], (k, a) => {
    $("tabla-ons").tBodies[0].innerHTML = D.ons.slice().sort(M.comparar(k, a)).map(o =>
      "<tr><td><b>" + M.esc(o.t) + "</b></td>" + celda(o.c, 2) + celda(o.var, 2, true) + celda(o.vol, 0) + "</tr>").join("");
  });
} else {
  $("bloque-ons").hidden = true;
}
"""
