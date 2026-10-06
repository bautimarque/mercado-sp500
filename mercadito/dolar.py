"""
Seccion Dolar (dolar/index.html): todos los tipos de cambio, su historia,
la banda cambiaria del BCRA y la cotizacion de cada banco, billetera y broker.
"""

from datetime import date, timedelta

from . import comun
from .comun import a_json

DOLARAPI = "https://dolarapi.com/v1/dolares"
ENTIDADES = "https://api.comparadolar.ar/usd"
HISTORIA = "https://api.argentinadatos.com/v1/cotizaciones/dolares"
DIAS_HISTORIA = 730

# (casa en las fuentes, nombre en la pagina, que es)
TIPOS = [
    ("oficial", "Oficial", "Precio minorista en bancos para personas."),
    ("bolsa", "MEP", "Dólar que se obtiene comprando un bono en pesos y vendiéndolo en dólares en el país (dólar bolsa)."),
    ("contadoconliqui", "Contado con liqui", "Igual que el MEP, pero los dólares quedan en una cuenta del exterior (CCL)."),
    ("blue", "Blue", "Cotización del mercado informal que publican medios y agencias."),
    ("cripto", "Cripto", "Precio de las monedas estables en dólares (como USDT) en plataformas cripto."),
    ("tarjeta", "Tarjeta", "Oficial más la percepción del 30% a cuenta de Ganancias. Es lo que se paga en gastos en el exterior; en servicios digitales se suman IVA e Ingresos Brutos, y en juegos no se cobra la percepción."),
    ("mayorista", "Mayorista", "Precio entre bancos y grandes empresas. Es el que usa el BCRA como referencia."),
]
NOMBRES = {casa: nombre for casa, nombre, _ in TIPOS}

# Series del BCRA: tipo de cambio mayorista de referencia y la banda cambiaria
BCRA_MAYORISTA, BCRA_PISO, BCRA_TECHO = 5, 1187, 1188


def historia():
    """{casa: [[fecha, venta], ...]} de los ultimos DIAS_HISTORIA dias."""
    corte = (date.today() - timedelta(days=DIAS_HISTORIA)).isoformat()
    series = {}
    for f in comun.pedir_json(HISTORIA, timeout=60):
        if f["casa"] in NOMBRES and f["fecha"] >= corte and f.get("venta"):
            series.setdefault(f["casa"], []).append([f["fecha"], round(float(f["venta"]), 2)])
    for s in series.values():
        s.sort()
    return series


def entidades():
    filas = []
    for e in comun.pedir_json(ENTIDADES):
        try:
            compra, venta = float(e["bid"]), float(e["ask"])
        except (KeyError, TypeError, ValueError):
            continue
        if compra <= 0 or venta <= 0:
            continue
        filas.append({
            "n": e.get("prettyName") or e.get("name"),
            "c": round(compra, 2),
            "v": round(venta, 2),
            "d": round((venta / compra - 1) * 100, 2),
            "var": e.get("pct_variation"),
            "banco": bool(e.get("isBank")),
            "h24": bool(e.get("is24x7")),
            "cond": e.get("conditions") or "",
        })
    return filas


def generar():
    hoy = comun.ahora().date().isoformat()
    actuales = {d["casa"]: d for d in comun.pedir_json(DOLARAPI)}
    if "oficial" not in actuales:
        raise RuntimeError("dolarapi no devolvio el dolar oficial")

    try:
        hist = historia()
    except Exception as e:
        print(f"  Sin historia de argentinadatos ({e}): sin variacion ni grafico")
        hist = {}

    oficial = float(actuales["oficial"]["venta"])
    tipos = []
    for casa, nombre, _ in TIPOS:
        d = actuales.get(casa)
        if not d or not d.get("venta"):
            continue
        venta = float(d["venta"])
        compra = float(d["compra"]) if d.get("compra") else None
        anteriores = [p for p in hist.get(casa, []) if p[0] < hoy]
        previo = anteriores[-1] if anteriores else None
        tipos.append({
            "casa": casa,
            "n": nombre,
            "c": compra,
            "v": venta,
            "var": round((venta / previo[1] - 1) * 100, 2) if previo else None,
            "prev": previo,
            "brecha": round((venta / oficial - 1) * 100, 1) if casa != "oficial" else None,
            "f": d.get("fechaActualizacion"),
        })

    try:
        ents = entidades()
    except Exception as e:
        print(f"  Sin cotizaciones por entidad ({e})")
        ents = []

    banda = None
    try:
        b = comun.bcra()
        if all(i in b for i in (BCRA_MAYORISTA, BCRA_PISO, BCRA_TECHO)):
            banda = {
                "mayorista": b[BCRA_MAYORISTA]["valor"], "fm": b[BCRA_MAYORISTA]["fecha"],
                "piso": b[BCRA_PISO]["valor"], "techo": b[BCRA_TECHO]["valor"], "fb": b[BCRA_TECHO]["fecha"],
            }
    except Exception as e:
        print(f"  Sin datos del BCRA ({e}): sin banda cambiaria")

    datos = {"tipos": tipos, "hist": hist, "ents": ents, "banda": banda,
             "glosario": [[n, t] for _, n, t in TIPOS]}
    comun.escribir("dolar", comun.pagina(
        "dolar", "Dólar",
        "Cotización de todos los tipos de dólar en Argentina, su historia, la banda cambiaria y el precio en cada banco, billetera y broker.",
        CUERPO.replace("__ACTUALIZADO__", comun.sello()), css=CSS, js=JS.replace("__DATOS__", a_json(datos)),
        fuentes="Cotizaciones: dolarapi.com. Historia: argentinadatos.com. Por entidad: comparadolar.ar. Banda cambiaria: BCRA.",
    ))
    print(f"  {len(tipos)} tipos, {len(ents)} entidades, historia de {len(hist)} tipos")

    return {
        "actualizado": comun.sello(),
        "tipos": {t["casa"]: {k: t[k] for k in ("n", "c", "v", "var", "brecha")} for t in tipos},
    }


CSS = r"""
.tipos-graf{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.tipos-graf .boton i{width:12px;height:3px;border-radius:2px;display:inline-block}
.tipos-graf .boton[aria-pressed="true"] i{outline:1.5px solid var(--fondo)}
.banda{margin-top:12px;max-width:760px}
.banda-barra{position:relative;height:12px;background:var(--hundido);border-left:2px solid var(--tinta);border-right:2px solid var(--tinta);
  margin:40px 0 34px}
.banda-marca{position:absolute;top:-32px;transform:translateX(-50%);font-size:14px;font-weight:750;font-stretch:88%;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.banda-marca::after{content:"";position:absolute;left:50%;top:24px;width:3px;height:22px;margin-left:-1.5px;background:var(--tinta)}
.banda-ext{position:absolute;top:20px;font-size:12.5px;color:var(--tinta-2);white-space:nowrap;font-variant-numeric:tabular-nums}
.calc-res{margin-top:14px}
#calc-monto{height:56px;font-size:30px;font-weight:750;font-stretch:76%;width:min(100%,260px)}
.ent-cond{display:block;font-size:12px;color:var(--tinta-3)}
@media (max-width:899px){
  /* a la vista: nombre, venta y brecha (tipos) o compra (entidades); lo demás, al tocar la fila */
  #tabla-tipos tr:not(.abierta) td:is(:nth-child(2),:nth-child(4),:nth-child(6)),
  #tabla-ent tr:not(.abierta) td:is(:nth-child(4),:nth-child(5),:nth-child(6)),
  #tabla-ent tr:not(.abierta) td:first-child .ent-cond{display:none}
  #tabla-tipos td:nth-child(3),#tabla-ent td:nth-child(3),#tabla-calc td:nth-child(3){order:2;margin-left:auto;font-size:16px;font-weight:700;color:var(--tinta);text-align:right}
  #tabla-tipos td:nth-child(2)::before,#tabla-ent td:nth-child(2)::before{content:"Compra "}
  #tabla-tipos td:nth-child(4)::before{content:"Día "}
  #tabla-tipos td:nth-child(5)::before{content:"Brecha "}
  #tabla-tipos td:nth-child(6)::before{content:"Hora "}
  #tabla-ent td:nth-child(4)::before{content:"Diferencia "}
  #tabla-ent td:nth-child(5)::before{content:"Variación "}
  #tabla-calc td:nth-child(2)::before{content:"Precio "}
  #calc-monto{width:100%}
}
"""


CUERPO = r"""
<div class="titulo">
  <h1>Dólar</h1>
  <p class="bajada">Todos los tipos de cambio, cómo vienen y cuánto cobra cada banco, billetera y broker.</p>
</div>
<section aria-label="Principales cotizaciones"><div class="cifras cifras-parejas" id="cifras"></div></section>
<p class="fecha">Actualizado el __ACTUALIZADO__ hs</p>

<section class="bloque" aria-labelledby="t-tipos">
  <h2 id="t-tipos">Todos los tipos</h2>
  <p class="nota">Precio de venta: lo que se paga por cada dólar. La brecha compara cada tipo con el oficial. ¿Vas a pagar un juego o una suscripción? En <a href="../gastos/">Gastos en dólares</a> está la cuenta con todos los impuestos.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-tipos" data-ficha>
    <thead><tr><th>Tipo</th><th class="der">Compra</th><th class="der">Venta</th><th class="der">Variación diaria</th><th class="der">Brecha con el oficial</th><th class="der">Hora</th></tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-banda" id="bloque-banda">
  <h2 id="t-banda">Banda cambiaria</h2>
  <p class="nota" id="banda-txt"></p>
  <div class="banda" id="banda"></div>
</section>

<section class="bloque" aria-labelledby="t-hist">
  <h2 id="t-hist">Cómo vino cada tipo</h2>
  <p class="nota">Precio de venta al cierre de cada día.</p>
  <div class="controles">
    <div class="grupo" role="group" aria-label="Período" id="rangos"></div>
  </div>
  <div class="tipos-graf" role="group" aria-label="Tipos en el gráfico" id="tipos-graf"></div>
  <div id="grafico"></div>
</section>

<section class="bloque" aria-labelledby="t-ent">
  <h2 id="t-ent">En cada banco, billetera y broker</h2>
  <p class="nota">Dólar oficial en cada entidad. La diferencia es cuánto más cara es la venta que la compra.</p>
  <div class="controles">
    <label class="campo">Ordenar
      <select id="ent-orden">
        <option value="v:1">Venta, de menor a mayor</option>
        <option value="c:0">Compra, de mayor a menor</option>
        <option value="d:1">Diferencia, de menor a mayor</option>
        <option value="n:1">Nombre</option>
      </select>
    </label>
    <label class="check"><input type="checkbox" id="ent-bancos"> Solo bancos</label>
    <label class="check"><input type="checkbox" id="ent-24"> Solo las que operan las 24 horas</label>
  </div>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-ent" data-ficha>
    <thead><tr><th>Entidad</th><th class="der">Compra</th><th class="der">Venta</th><th class="der">Diferencia</th><th class="der">Variación</th><th>Tipo</th></tr></thead>
    <tbody></tbody>
  </table></div>
  <p class="nota" id="ent-nota"></p>
</section>

<section class="bloque" aria-labelledby="t-calc">
  <h2 id="t-calc">Calculadora</h2>
  <p class="nota">Cuánto da un monto en cada tipo de cambio, sin comisiones.</p>
  <div class="controles">
    <label class="campo">Monto <input id="calc-monto" type="number" inputmode="decimal" min="0" step="any" value="100000"></label>
    <label class="campo">Quiero pasar
      <select id="calc-dir">
        <option value="ad">Pesos a dólares</option>
        <option value="ap">Dólares a pesos</option>
      </select>
    </label>
  </div>
  <div class="caja-tabla calc-res"><table class="tabla-datos" id="tabla-calc">
    <thead><tr><th>Tipo</th><th class="der">Precio usado</th><th class="der">Resultado</th></tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<details class="bloque plegado">
  <summary><h2 id="t-glos">Qué es cada tipo</h2></summary>
  <dl class="glosario" id="glosario"></dl>
</details>
"""


JS = r"""
const M = Mercadito;
const D = __DATOS__;
const $ = id => document.getElementById(id);
const COLORES = {oficial: "var(--s1)", bolsa: "var(--s2)", contadoconliqui: "var(--s3)", blue: "var(--s4)",
  cripto: "var(--s5)", tarjeta: "var(--s6)", mayorista: "var(--s7)"};
const porCasa = Object.fromEntries(D.tipos.map(t => [t.casa, t]));
const hora = iso => iso ? new Date(iso).toLocaleString("es-AR", {hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit"}) : "—";

/* cifras principales */
$("cifras").innerHTML = ["oficial", "bolsa", "contadoconliqui", "blue"].filter(c => porCasa[c]).map(c => {
  const t = porCasa[c];
  const sub = [t.c ? "Compra " + M.pesos(t.c) : "", t.var !== null ? M.pct(t.var, 2) + " en el día" : "",
    t.brecha !== null ? "Brecha " + M.pct(t.brecha, 1) : ""].filter(Boolean).join(" · ");
  return "<div class='cifra'><p class='cifra-et'>" + M.esc(t.n) + "</p><p class='cifra-val num'>" + M.pesos(t.v) +
    "</p><p class='cifra-sub'>" + sub + "</p></div>";
}).join("");

/* todos los tipos */
$("tabla-tipos").tBodies[0].innerHTML = D.tipos.map(t => "<tr><td>" + M.esc(t.n) + "</td>" +
  "<td class='der num'>" + (t.c ? M.pesos(t.c) : "—") + "</td>" +
  "<td class='der num'><b>" + M.pesos(t.v) + "</b></td>" +
  "<td class='der num'>" + (t.var === null ? "—" : M.pct(t.var, 2)) +
    (t.prev ? "<span class='sub'>" + M.fecha(t.prev[0]) + ": " + M.pesos(t.prev[1]) + "</span>" : "") + "</td>" +
  "<td class='der num'>" + (t.brecha === null ? "—" : M.pct(t.brecha, 1)) + "</td>" +
  "<td class='der num'>" + hora(t.f) + "</td></tr>").join("");

/* banda cambiaria */
if (D.banda) {
  const b = D.banda, ancho = b.techo - b.piso, pos = v => Math.min(100, Math.max(0, (v - b.piso) / ancho * 100));
  $("banda-txt").textContent = "El BCRA fija un piso y un techo para el dólar mayorista. El mayorista está " +
    M.num((1 - b.mayorista / b.techo) * 100, 1) + "% debajo del techo y " +
    M.num((b.mayorista / b.piso - 1) * 100, 1) + "% arriba del piso (datos del " + M.fecha(b.fm) + ").";
  $("banda").innerHTML = "<div class='banda-barra'>" +
    "<span class='banda-marca' style='left:" + pos(b.mayorista) + "%'>Mayorista " + M.pesos(b.mayorista) + "</span>" +
    "<span class='banda-ext' style='left:0'>Piso " + M.pesos(b.piso) + "</span>" +
    "<span class='banda-ext' style='right:0'>Techo " + M.pesos(b.techo) + "</span></div>";
} else {
  $("bloque-banda").hidden = true;
}

/* historia */
const RANGOS = [["1 mes", 31], ["3 meses", 92], ["6 meses", 183], ["1 año", 365], ["2 años", 730]];
let rango = 183;
const visibles = new Set(["oficial", "bolsa", "contadoconliqui", "blue"]);
function pintarGrafico() {
  const series = D.tipos.filter(t => visibles.has(t.casa) && D.hist[t.casa]).map(t => ({
    nombre: t.n, color: COLORES[t.casa], puntos: M.desde(D.hist[t.casa], rango)}));
  M.linea($("grafico"), series, {formato: v => M.pesos(v, 0), titulo: "Precio de venta de cada tipo de dólar"});
}
$("rangos").innerHTML = RANGOS.map(([n, d]) =>
  "<button type='button' class='boton boton-chico' data-d='" + d + "' aria-pressed='" + (d === rango) + "'>" + n + "</button>").join("");
$("rangos").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  rango = +b.dataset.d;
  $("rangos").querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b));
  pintarGrafico();
});
$("tipos-graf").innerHTML = D.tipos.filter(t => D.hist[t.casa]).map(t =>
  "<button type='button' class='boton boton-chico' data-c='" + t.casa + "' aria-pressed='" + visibles.has(t.casa) + "'>" +
  "<i style='background:" + COLORES[t.casa] + "'></i>" + M.esc(t.n) + "</button>").join("");
$("tipos-graf").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  const c = b.dataset.c;
  if (visibles.has(c)) visibles.delete(c); else visibles.add(c);
  b.setAttribute("aria-pressed", visibles.has(c));
  pintarGrafico();
});
if (Object.keys(D.hist).length) pintarGrafico();
else $("grafico").innerHTML = "<p class='nota'>La historia no está disponible en este momento.</p>";

/* entidades */
function pintarEntidades() {
  const [k, a] = $("ent-orden").value.split(":");
  const filas = D.ents.filter(e => (!$("ent-bancos").checked || e.banco) && (!$("ent-24").checked || e.h24))
    .sort(M.comparar(k, a === "1"));
  $("tabla-ent").tBodies[0].innerHTML = filas.map(e => "<tr><td>" + M.esc(e.n) +
    (e.cond ? "<span class='ent-cond'>" + M.esc(e.cond) + "</span>" : "") + "</td>" +
    "<td class='der num'>" + M.pesos(e.c) + "</td><td class='der num'><b>" + M.pesos(e.v) + "</b></td>" +
    "<td class='der num'>" + M.num(e.d, 1) + "%</td>" +
    "<td class='der num'>" + (e.var === null || e.var === undefined ? "—" : M.pct(e.var, 2)) + "</td>" +
    "<td>" + (e.banco ? "Banco" : "Billetera o broker") + (e.h24 ? "<span class='sub'>24 horas</span>" : "") + "</td></tr>").join("") ||
    "<tr><td colspan='6'>Ninguna entidad cumple con estos filtros.</td></tr>";
  $("ent-nota").textContent = filas.length + " de " + D.ents.length + " entidades. Precios informados por cada entidad; " +
    "pueden cambiar durante el día y según el monto.";
}
["ent-orden", "ent-bancos", "ent-24"].forEach(id => $(id).addEventListener("change", pintarEntidades));
if (D.ents.length) pintarEntidades();
else $("tabla-ent").tBodies[0].innerHTML = "<tr><td colspan='6'>Las cotizaciones por entidad no están disponibles en este momento.</td></tr>";

/* calculadora */
function calcular() {
  const monto = parseFloat($("calc-monto").value);
  const aDolares = $("calc-dir").value === "ad";
  $("tabla-calc").tBodies[0].innerHTML = D.tipos.filter(t => t.casa !== "mayorista").map(t => {
    const precio = aDolares ? t.v : t.c;
    const res = isNaN(monto) || !precio ? null : aDolares ? monto / precio : monto * precio;
    return "<tr><td>" + M.esc(t.n) + "</td><td class='der num'>" + (precio ? M.pesos(precio) : "—") +
      (aDolares ? " <small>venta</small>" : " <small>compra</small>") + "</td>" +
      "<td class='der num'><b>" + (res === null ? "—" : aDolares ? M.dolares(res) : M.pesos(res)) + "</b></td></tr>";
  }).join("");
}
["calc-monto", "calc-dir"].forEach(id => $(id).addEventListener("input", calcular));
calcular();

$("glosario").innerHTML = D.glosario.map(([n, t]) => "<div><dt>" + M.esc(n) + "</dt><dd>" + M.esc(t) + "</dd></div>").join("");
"""
