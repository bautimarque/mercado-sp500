"""
Seccion Gastos en dolares (gastos/index.html): cuanto se paga en pesos un
juego, una suscripcion o un gasto en el exterior con tarjeta argentina,
pagando el resumen en pesos o con dolares propios.

Los impuestos cambian seguido: estan todos aca arriba, con la fecha en que se
verificaron. Si cambia una norma, se actualiza este bloque y nada mas.
"""

from . import comun
from .comun import a_json

DOLARAPI = "https://dolarapi.com/v1/dolares"

VERIFICADO = "06/10/2026"
IVA = 21            # IVA sobre servicios digitales del exterior
PERCEPCION = 30     # RG 5617/2024 de ARCA, a cuenta de Ganancias o Bienes Personales
IIBB = 2            # percepcion de Ingresos Brutos de CABA y Provincia de Buenos Aires; varia por provincia

# (clave, nombre, ejemplos, lleva IVA, lleva percepcion 30%, lleva IIBB)
TIPOS = [
    ("servicio", "Servicio digital", "Netflix, Spotify, ChatGPT, Apple, Google, apps", True, True, True),
    ("juego", "Juego digital", "PlayStation, Steam, Xbox, Nintendo, Epic", True, False, True),
    ("exterior", "Gasto en el exterior", "Viajes, pasajes, hoteles, compras en tiendas del exterior", False, True, False),
]

# Ejemplos para cargar la calculadora con un clic: montos tipicos, no precios oficiales
EJEMPLOS = [
    ("Juego nuevo de consola", 69.99, "juego"),
    ("Suscripción de US$ 9,99", 9.99, "servicio"),
    ("Suscripción de US$ 20", 20, "servicio"),
    ("Gasto de US$ 100 en un viaje", 100, "exterior"),
]


def generar():
    dolares = {d["casa"]: d for d in comun.pedir_json(DOLARAPI)}
    if "oficial" not in dolares:
        raise RuntimeError("dolarapi no devolvio el dolar oficial")
    oficial = float(dolares["oficial"]["venta"])
    mep = float(dolares["bolsa"]["venta"]) if dolares.get("bolsa") else None

    datos = {
        "oficial": oficial, "mep": mep, "f": dolares["oficial"].get("fechaActualizacion"),
        "iva": IVA, "percepcion": PERCEPCION, "iibb": IIBB, "verificado": VERIFICADO,
        "tipos": [{"k": k, "n": n, "ej": ej, "iva": iva, "per": per, "iibb": iibb} for k, n, ej, iva, per, iibb in TIPOS],
        "ejemplos": [{"n": n, "p": p, "k": k} for n, p, k in EJEMPLOS],
    }
    comun.escribir("gastos", comun.pagina(
        "gastos", "Gastos en dólares",
        "Calculadora de cuánto se paga en pesos un juego, una suscripción o un gasto en el exterior con tarjeta argentina, con los impuestos vigentes.",
        CUERPO.replace("__ACTUALIZADO__", comun.sello()), css=CSS, js=JS.replace("__DATOS__", a_json(datos)),
        fuentes=f"Dólar oficial y MEP: dolarapi.com. Impuestos verificados el {VERIFICADO}; pueden cambiar.",
    ))

    def efectivo(iva, per, iibb):
        return round(oficial * (1 + (IVA * iva + PERCEPCION * per + IIBB * iibb) / 100), 2)

    return {
        "actualizado": comun.sello(),
        "oficial": oficial,
        "efectivo": {k: efectivo(iva, per, iibb) for k, _, _, iva, per, iibb in TIPOS},
    }


CSS = r"""
#precio{height:60px;font-size:34px;font-weight:800;font-stretch:72%;width:min(100%,240px)}
#iibb{width:min(100%,140px)}
.tipos-gasto{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}
.tipos-gasto label:nth-of-type(-n+3){border-top:1px solid var(--linea-2)}
.tipos-gasto label{position:relative;display:flex;flex-direction:column;gap:3px;padding:12px 14px 13px;cursor:pointer;
  border-bottom:1px solid var(--linea-2);border-left:1px solid var(--linea);transition:background-color .15s,color .15s}
.tipos-gasto label:nth-of-type(3n+1){border-left:0}
.tipos-gasto label:hover{background:var(--hundido)}
.tipos-gasto label:has(input:checked){background:var(--tinta);color:var(--fondo)}
.tipos-gasto label:has(input:checked) small{color:color-mix(in srgb,var(--fondo) 75%,var(--tinta))}
.tipos-gasto input{position:absolute;opacity:0;pointer-events:none}
.tipos-gasto b{font-size:15.5px;font-weight:700}
.tipos-gasto small{font-size:12.5px;color:var(--tinta-3);line-height:1.4}
.tipos-gasto label:focus-within{outline:2px solid var(--tinta);outline-offset:2px}
#ejemplos{align-items:center}
.resultados{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:0 40px;margin-top:28px;border-top:3px solid var(--tinta)}
.resultado{padding:14px 0 6px}
.resultado+.resultado{border-left:1px solid var(--linea);padding-left:20px;margin-left:-20px}
.controles:has(#precio){align-items:flex-start}
.campo:has(#iibb){min-width:260px}
.resultado h3{margin:0;font-size:15px;font-weight:700}
.resultado .total{font-size:52px;font-weight:800;font-stretch:68%;line-height:.95;margin-top:8px;font-variant-numeric:normal}
.resultado:first-child .total{font-size:80px;font-stretch:64%;line-height:.9}
.resultado .por{font-size:14px;color:var(--tinta-2);margin-top:8px}
.resultados>.nota{grid-column:1 / -1;padding-top:14px}
.desglose{margin-top:14px;font-size:14px}
.desglose li{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-top:1px solid var(--linea)}
.desglose li span:last-child{font-variant-numeric:tabular-nums;white-space:nowrap}
.desglose li.no{color:var(--tinta-3)}
@media (max-width:899px){
  /* el total, más cerca del precio: los ejemplos pasan abajo de los resultados y su nota */
  section[aria-labelledby="t-calc"]{display:flex;flex-direction:column}
  section[aria-labelledby="t-calc"]>.controles:has(#ejemplos){order:5;margin-top:18px}
  #resultados{order:3}
  #nota-res{order:4}
  .tipos-gasto{grid-template-columns:1fr}
  .tipos-gasto label{padding:9px 12px 10px}
  .tipos-gasto small{font-size:12px}
  .campo:has(#iibb){min-width:0}
  .tipos-gasto label{border-left:0}
  .tipos-gasto label:nth-of-type(-n+3){border-top:0}
  .tipos-gasto label:first-of-type{border-top:1px solid var(--linea-2)}
  .resultados{grid-template-columns:1fr}
  .resultado+.resultado{border-left:0;padding-left:0;margin-left:0;border-top:1px solid var(--linea-2);margin-top:18px;padding-top:14px}
  .resultado:first-child .total{font-size:64px}
  .resultado .total{font-size:44px}
}
@media (max-width:640px){
  #tabla-imp td:nth-child(5){order:2;margin-left:auto;font-size:16px;font-weight:700;color:var(--tinta);text-align:right}
  #tabla-imp td:nth-child(2)::before{content:"IVA "}
  #tabla-imp td:nth-child(3)::before{content:"Percepción "}
  #tabla-imp td:nth-child(4)::before{content:"Ingresos Brutos "}
}
"""


CUERPO = r"""
<div class="titulo">
  <h1>Gastos en dólares</h1>
  <p class="bajada">Cuánto pagás en pesos un juego, una suscripción o un gasto en el exterior con tarjeta argentina.</p>
</div>
<p class="fecha" id="fecha">Actualizado el __ACTUALIZADO__ hs</p>

<section aria-labelledby="t-calc">
  <h2 id="t-calc" class="oculto">Calculadora</h2>
  <div class="controles">
    <label class="campo">Precio en dólares <input id="precio" type="number" inputmode="decimal" min="0" step="any" value="69.99"></label>
    <label class="campo">Ingresos Brutos de tu provincia (%) <input id="iibb" type="number" inputmode="decimal" min="0" max="10" step="0.1"></label>
  </div>
  <fieldset class="tipos-gasto" id="tipos" style="border:0;padding:0;margin:14px 0 0">
    <legend class="nota" style="padding:0;margin-bottom:6px">¿Qué estás pagando?</legend>
  </fieldset>
  <div class="controles"><div class="grupo" role="group" aria-label="Ejemplos" id="ejemplos"></div></div>
  <div class="resultados" id="resultados" aria-live="polite"></div>
  <p class="nota" id="nota-res" style="margin-top:12px"></p>
</section>

<section class="bloque" aria-labelledby="t-imp">
  <h2 id="t-imp">Qué impuestos se pagan</h2>
  <p class="nota" id="verificado"></p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-imp">
    <thead><tr><th>Qué pagás</th><th class="der">IVA</th><th class="der">Percepción a cuenta de Ganancias</th><th class="der">Ingresos Brutos</th><th class="der">Dólar efectivo hoy</th></tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-glos">
  <h2 id="t-glos">Cómo leer esta página</h2>
  <dl class="glosario">
    <div><dt>Dólar tarjeta</dt><dd>Dólar oficial más la percepción del 30%. Es lo que se paga en un gasto en el exterior; en servicios digitales se suman además el IVA y los Ingresos Brutos.</dd></div>
    <div><dt>Percepción del 30%</dt><dd>Figura en el resumen como «RG 5617». Es un pago a cuenta de Ganancias o Bienes Personales: quien paga esos impuestos la descuenta, y quien no, puede pedir la devolución a ARCA. Desde abril de 2025 no se cobra en las plataformas de juegos.</dd></div>
    <div><dt>Pagar con dólares propios</dt><dd>Si el saldo en dólares del resumen se paga con dólares (por ejemplo comprados por MEP) y no en pesos, no se cobra la percepción del 30%. El IVA y los Ingresos Brutos se cobran igual. Si el resumen está en débito automático en pesos, se paga en pesos.</dd></div>
    <div><dt>Ingresos Brutos</dt><dd>Percepción provincial sobre servicios digitales del exterior. En CABA y Provincia de Buenos Aires es 2%; en otras provincias cambia. Figura en el resumen.</dd></div>
    <div><dt>Servicios que cobran en pesos</dt><dd>Algunos servicios publican su precio en pesos. En ese caso esta cuenta no aplica tal cual: revisá en tu resumen qué impuestos se suman.</dd></div>
  </dl>
</section>
"""


JS = r"""
const M = Mercadito;
const D = __DATOS__;
const $ = id => document.getElementById(id);
const porTipo = Object.fromEntries(D.tipos.map(t => [t.k, t]));
let tipo = "juego";

$("iibb").value = D.iibb;
$("fecha").textContent += " · dólar oficial " + M.pesos(D.oficial) + (D.mep ? " · MEP " + M.pesos(D.mep) : "");
$("verificado").textContent = "Con tarjeta argentina, según las normas vigentes al " + D.verificado +
  ". Los impuestos se calculan sobre el precio pasado a pesos al dólar oficial. Pueden cambiar: tu resumen tiene el detalle exacto.";

$("tipos").insertAdjacentHTML("beforeend", D.tipos.map(t =>
  "<label><input type='radio' name='tipo' value='" + t.k + "'" + (t.k === tipo ? " checked" : "") + ">" +
  "<b>" + M.esc(t.n) + "</b><small>" + M.esc(t.ej) + "</small></label>").join(""));
$("ejemplos").innerHTML = D.ejemplos.map((e, i) =>
  "<button type='button' class='boton boton-chico' data-i='" + i + "'>" + M.esc(e.n) + "</button>").join("");

// Desglose de un pago: el precio va al dólar oficial (o al MEP si se paga con dólares propios)
function desglose(precio, t, iibb, conDolares) {
  const base = precio * D.oficial;
  const filas = [];
  filas.push([conDolares ? "Precio (" + M.dolares(precio) + " comprados a " + M.pesos(D.mep) + ")" : "Precio al dólar oficial",
    conDolares ? precio * D.mep : base, true]);
  filas.push(["IVA " + D.iva + "%", t.iva ? base * D.iva / 100 : 0, t.iva]);
  filas.push(["Percepción " + D.percepcion + "% a cuenta de Ganancias", t.per && !conDolares ? base * D.percepcion / 100 : 0, t.per && !conDolares]);
  filas.push(["Ingresos Brutos " + M.num(iibb, 1) + "%", t.iibb ? base * iibb / 100 : 0, t.iibb]);
  return filas;
}

function tarjeta(titulo, filas, precio) {
  const total = filas.reduce((s, f) => s + f[1], 0);
  return "<div class='resultado'><h3>" + titulo + "</h3><p class='total num'>" + M.pesos(total) + "</p>" +
    "<p class='por'>" + M.pesos(total / precio) + " por cada dólar</p><ul class='desglose'>" +
    filas.map(f => "<li" + (f[2] ? "" : " class='no'") + "><span>" + M.esc(f[0]) + (f[2] ? "" : " · no se cobra") + "</span><span>" +
      M.pesos(f[1]) + "</span></li>").join("") + "</ul></div>";
}

function calcular() {
  const precio = parseFloat($("precio").value);
  const iibb = Math.max(0, parseFloat($("iibb").value) || 0);
  const t = porTipo[tipo];
  if (!(precio > 0)) {
    $("resultados").innerHTML = "<p class='nota'>Ingresá un precio en dólares.</p>";
    $("nota-res").textContent = "";
    return;
  }
  let html = tarjeta("Pagando el resumen en pesos", desglose(precio, t, iibb, false), precio);
  if (D.mep) html += tarjeta("Pagando el resumen con dólares propios", desglose(precio, t, iibb, true), precio);
  $("resultados").innerHTML = html;
  $("nota-res").textContent = t.per
    ? "La percepción del 30% es un pago a cuenta: se puede descontar de Ganancias o Bienes Personales, o pedir su devolución a ARCA."
    : "En " + t.n.toLowerCase() + " no se cobra la percepción del 30%: la diferencia entre pagar en pesos o con dólares propios es solo el tipo de cambio.";
  pintarTabla(iibb);
}

function pintarTabla(iibb) {
  $("tabla-imp").tBodies[0].innerHTML = D.tipos.map(t => {
    const rec = (t.iva ? D.iva : 0) + (t.per ? D.percepcion : 0) + (t.iibb ? iibb : 0);
    return "<tr><td>" + M.esc(t.n) + "<span class='sub'>" + M.esc(t.ej) + "</span></td>" +
      "<td class='der'>" + (t.iva ? D.iva + "%" : "No") + "</td><td class='der'>" + (t.per ? D.percepcion + "%" : "No") + "</td>" +
      "<td class='der'>" + (t.iibb ? M.num(iibb, 1) + "%" : "No") + "</td>" +
      "<td class='der num'><b>" + M.pesos(D.oficial * (1 + rec / 100)) + "</b><span class='sub'>oficial + " + M.num(rec, 1) + "%</span></td></tr>";
  }).join("");
}

$("tipos").addEventListener("change", e => { tipo = e.target.value; calcular(); });
["precio", "iibb"].forEach(id => $(id).addEventListener("input", calcular));
$("ejemplos").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  const ej = D.ejemplos[+b.dataset.i];
  $("precio").value = ej.p;
  tipo = ej.k;
  $("tipos").querySelectorAll("input").forEach(i => { i.checked = i.value === tipo; });
  calcular();
});
calcular();
"""
