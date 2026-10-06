"""
Seccion Tasas (tasas/index.html): plazo fijo en cada entidad, fondos money
market, inflacion y las tasas de referencia del BCRA.
"""

import re
from datetime import date

from . import comun
from .comun import a_json

PLAZO_FIJO = "https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo"
INFLACION = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
FCI_ULTIMO = "https://api.argentinadatos.com/v1/finanzas/fci/mercadoDinero/ultimo"
FCI_PENULTIMO = "https://api.argentinadatos.com/v1/finanzas/fci/mercadoDinero/penultimo"

# Los fondos chicos (clases con poco patrimonio) meten ruido: se muestran los
# que administran al menos esto, en pesos.
FCI_PATRIMONIO_MINIMO = 1e9
# Un rendimiento diario anualizado fuera de este rango es un dato mal cargado
FCI_TNA_RANGO = (-20, 150)

# (id de la serie del BCRA, nombre, unidad)
REFERENCIAS = [
    (27, "Inflación mensual", "%"),
    (28, "Inflación interanual", "%"),
    (29, "Inflación esperada para los próximos 12 meses (REM)", "%"),
    (12, "Tasa promedio de plazo fijo a 30 días", "% TNA"),
    (7, "BADLAR de bancos privados", "% TNA"),
    (44, "TAMAR de bancos privados", "% TNA"),
    (30, "CER", "índice"),
    (31, "UVA", "$"),
    (1, "Reservas internacionales", "millones de US$"),
]

MINUSCULAS = {"de", "del", "la", "las", "los", "y", "e", "en"}
SIGLAS = {"bbva", "bica", "cmf"}
ACENTOS = {"nacion": "Nación", "cordoba": "Córdoba", "compania": "Compañía", "compañia": "Compañía", "credito": "Crédito"}
APODOS = {"INDUSTRIAL AND COMMERCIAL BANK OF CHINA (ARGENTINA) S.A.U.": "ICBC", "UALA": "Ualá"}
SUFIJOS = re.compile(r"\s+(S\.A\.U?\.?|SOCIEDAD AN[OÓ]NIMA|COOPERATIVO LIMITADO)$", re.IGNORECASE)


def prolijo(nombre):
    """BANCO DE LA NACION ARGENTINA -> Banco de la Nación Argentina; BANCO CMF S.A. -> Banco CMF"""
    if nombre in APODOS:
        return APODOS[nombre]
    if nombre != nombre.upper():
        return nombre
    nombre = SUFIJOS.sub("", nombre.strip())
    palabras = []
    for i, p in enumerate(nombre.lower().split()):
        if i and p in MINUSCULAS:
            palabras.append(p)
        elif p in SIGLAS:
            palabras.append(p.upper())
        else:
            palabras.append(ACENTOS.get(p, p[:1].upper() + p[1:]))
    return " ".join(palabras)


def plazo_fijo():
    filas = []
    for e in comun.pedir_json(PLAZO_FIJO):
        tna = e.get("tnaClientes") or 0
        if tna <= 0:
            continue
        filas.append({
            "n": prolijo(e["entidad"]),
            "tna": round(tna * 100, 2),
            "tnaNo": round(e["tnaNoClientes"] * 100, 2) if e.get("tnaNoClientes") else None,
            # tasa efectiva anual si se renueva cada 30 dias
            "tea": round(((1 + tna * 30 / 365) ** (365 / 30) - 1) * 100, 2),
        })
    return filas


def fondos():
    previos = {f["fondo"]: f for f in comun.pedir_json(FCI_PENULTIMO, timeout=60)}
    filas = []
    for f in comun.pedir_json(FCI_ULTIMO, timeout=60):
        p = previos.get(f["fondo"])
        if not p or not f.get("vcp") or not p.get("vcp") or (f.get("patrimonio") or 0) < FCI_PATRIMONIO_MINIMO:
            continue
        dias = (date.fromisoformat(f["fecha"]) - date.fromisoformat(p["fecha"])).days
        if not 1 <= dias <= 5:
            continue
        tna = (f["vcp"] / p["vcp"] - 1) * 365 / dias * 100
        if not FCI_TNA_RANGO[0] <= tna <= FCI_TNA_RANGO[1]:
            continue
        filas.append({"n": re.sub(r"\s+", " ", f["fondo"]).strip(), "tna": round(tna, 2),
                      "pat": round(f["patrimonio"] / 1e6), "f": f["fecha"]})
    return filas


def generar():
    pf = plazo_fijo()
    if not pf:
        raise RuntimeError("argentinadatos no devolvio tasas de plazo fijo")

    try:
        fci = fondos()
    except Exception as e:
        print(f"  Sin fondos money market ({e})")
        fci = []

    try:
        infl = [[i["fecha"], i["valor"]] for i in comun.pedir_json(INFLACION) if i["fecha"] >= "2017-01-01"]
    except Exception as e:
        print(f"  Sin serie de inflacion ({e})")
        infl = []

    refs = []
    try:
        b = comun.bcra()
        refs = [{"n": n, "u": u, "v": b[i]["valor"], "f": b[i]["fecha"], "id": i} for i, n, u in REFERENCIAS if i in b]
    except Exception as e:
        print(f"  Sin datos del BCRA ({e})")

    datos = {"pf": pf, "fci": fci, "infl": infl, "refs": refs}
    comun.escribir("tasas", comun.pagina(
        "tasas", "Tasas",
        "Tasas de plazo fijo en cada entidad, rendimiento de los fondos money market, inflación y tasas de referencia del BCRA.",
        CUERPO.replace("__ACTUALIZADO__", comun.sello()), css=CSS, js=JS.replace("__DATOS__", a_json(datos)),
        fuentes="Plazo fijo, fondos e inflación: argentinadatos.com (con datos del BCRA y la CAFCI). Tasas de referencia: BCRA.",
    ))
    print(f"  {len(pf)} entidades de plazo fijo, {len(fci)} fondos, {len(refs)} referencias del BCRA")

    ref = {r["id"]: r for r in refs}
    nacion = next((f for f in pf if "nacion" in f["n"].lower().replace("ó", "o")), None)
    maximo = max(pf, key=lambda f: f["tna"])
    return {
        "actualizado": comun.sello(),
        "plazo_fijo_nacion": nacion and nacion["tna"],
        "plazo_fijo_max": {"n": maximo["n"], "tna": maximo["tna"]},
        "inflacion_mensual": ref.get(27) and {"v": ref[27]["v"], "f": ref[27]["f"]},
        "inflacion_interanual": ref.get(28) and {"v": ref[28]["v"], "f": ref[28]["f"]},
        "tamar": ref.get(44) and {"v": ref[44]["v"], "f": ref[44]["f"]},
    }


CSS = r"""
.calc-pf{margin-top:12px}
#pf-monto{height:56px;font-size:30px;font-weight:750;font-stretch:76%;width:min(100%,280px)}
@media (max-width:899px){
  /* a la vista: entidad, TNA e interés del monto (plazo fijo) o TNA (fondos); lo demás, al tocar la fila */
  #tabla-pf tr:not(.abierta) td:is(:nth-child(3),:nth-child(4)),
  #tabla-pf tr:not(.abierta) td:first-child .sub,
  #tabla-fci tr:not(.abierta) td:is(:nth-child(3),:nth-child(4)){display:none}
  #tabla-pf td:nth-child(2),#tabla-fci td:nth-child(2),#tabla-ref td:nth-child(2){order:2;margin-left:auto;font-size:16px;font-weight:700;color:var(--tinta);text-align:right}
  #tabla-pf td:nth-child(3)::before{content:"TEA "}
  #tabla-pf td:nth-child(4)::before{content:"En 30 días "}
  #tabla-pf td:nth-child(5)::before{content:"Interés "}
  #tabla-fci td:nth-child(3)::before{content:"Patrimonio "}
  #pf-monto{width:100%}
}
"""


CUERPO = r"""
<div class="titulo">
  <h1>Tasas</h1>
  <p class="bajada">Cuánto paga cada entidad por un plazo fijo, cuánto rinden los fondos money market y cómo viene la inflación.</p>
</div>
<section aria-label="Datos principales"><div class="cifras" id="cifras"></div></section>
<p class="fecha">Actualizado el __ACTUALIZADO__ hs</p>

<section class="bloque" aria-labelledby="t-pf">
  <h2 id="t-pf">Plazo fijo a 30 días</h2>
  <p class="nota" id="pf-nota"></p>
  <div class="controles">
    <label class="campo">Monto a invertir <input id="pf-monto" type="number" inputmode="decimal" min="0" step="any" value="1000000"></label>
  </div>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-pf" data-ficha>
    <thead><tr>
      <th data-k="n" data-asc="1"><button type="button">Entidad</button></th>
      <th class="der" data-k="tna"><button type="button">TNA</button></th>
      <th class="der" data-k="tea"><button type="button">TEA</button></th>
      <th class="der">En 30 días</th>
      <th class="der">Interés del monto</th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-fci" id="bloque-fci">
  <h2 id="t-fci">Fondos money market</h2>
  <p class="nota">Fondos de liquidez inmediata en pesos con al menos $ 1.000 millones de patrimonio. La TNA es el rendimiento del último día hábil llevado a un año: cambia todos los días.</p>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-fci" data-ficha>
    <thead><tr>
      <th data-k="n" data-asc="1"><button type="button">Fondo</button></th>
      <th class="der" data-k="tna"><button type="button">TNA del último día</button></th>
      <th class="der" data-k="pat"><button type="button">Patrimonio</button></th>
      <th class="der" data-k="f"><button type="button">Fecha</button></th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section class="bloque" aria-labelledby="t-infl" id="bloque-infl">
  <h2 id="t-infl">Inflación mensual</h2>
  <p class="nota">Variación del índice de precios al consumidor (INDEC) de cada mes.</p>
  <div class="controles"><div class="grupo" role="group" aria-label="Período" id="rangos"></div></div>
  <div id="grafico"></div>
</section>

<details class="bloque plegado" id="bloque-ref">
  <summary><h2 id="t-ref">Referencias del BCRA</h2></summary>
  <div class="caja-tabla"><table class="tabla-datos" id="tabla-ref">
    <thead><tr><th>Dato</th><th class="der">Valor</th><th class="der">Fecha</th></tr></thead>
    <tbody></tbody>
  </table></div>
</details>

<details class="bloque plegado">
  <summary><h2 id="t-glos">Cómo leer esta página</h2></summary>
  <dl class="glosario">
    <div><dt>TNA</dt><dd>Tasa nominal anual: la que publica cada entidad. Para un plazo fijo a 30 días, el interés del mes es TNA × 30 / 365.</dd></div>
    <div><dt>TEA</dt><dd>Tasa efectiva anual: lo que rendiría en un año si se renovara cada 30 días con la misma TNA, sumando los intereses.</dd></div>
    <div><dt>Frente a la inflación</dt><dd>Diferencia entre lo que rinde el plazo fijo en 30 días y la inflación del último mes publicado. Es una comparación con el pasado: la inflación de los próximos meses puede ser distinta.</dd></div>
    <div><dt>Money market</dt><dd>Fondos comunes de inversión que invierten en instrumentos de muy corto plazo y permiten retirar el dinero en el día. El rendimiento no está garantizado.</dd></div>
  </dl>
</details>
"""


JS = r"""
const M = Mercadito;
const D = __DATOS__;
const $ = id => document.getElementById(id);
const ref = Object.fromEntries(D.refs.map(r => [r.id, r]));
const mesDe = iso => new Date(iso + "T12:00:00").toLocaleDateString("es-AR", {month: "long", year: "numeric"});
const inflMes = ref[27] ? ref[27].v : (D.infl.length ? D.infl[D.infl.length - 1][1] : null);
const inflFecha = ref[27] ? ref[27].f : (D.infl.length ? D.infl[D.infl.length - 1][0] : null);

/* cifras */
const nacion = D.pf.find(f => f.n.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").includes("nacion"));
const maxPf = D.pf.reduce((a, b) => b.tna > a.tna ? b : a, D.pf[0]);
const cifras = [];
const maxMes = maxPf.tna * 30 / 365;
cifras.push(["Plazo fijo más alto", M.num(maxPf.tna, 2) + "%", "TNA · " + M.esc(maxPf.n) +
  (inflMes === null ? "" : "<br>" + M.num(maxMes, 2) + "% en 30 días: " +
    M.pct(((1 + maxMes / 100) / (1 + inflMes / 100) - 1) * 100, 2) + " frente a la inflación de " + mesDe(inflFecha))]);
if (inflMes !== null) cifras.push(["Inflación de " + mesDe(inflFecha), M.num(inflMes, 1) + "%",
  ref[28] ? "Interanual " + M.num(ref[28].v, 1) + "%" : ""]);
if (nacion) cifras.push(["Plazo fijo Banco Nación", M.num(nacion.tna, 2) + "%", "TNA a 30 días · TEA " + M.num(nacion.tea, 2) + "%"]);
if (ref[44]) cifras.push(["TAMAR bancos privados", M.num(ref[44].v, 2) + "%", "TNA al " + M.fecha(ref[44].f)]);
$("cifras").innerHTML = cifras.map(([e, v, s]) =>
  "<div class='cifra'><p class='cifra-et'>" + e + "</p><p class='cifra-val num'>" + v + "</p><p class='cifra-sub'>" + s + "</p></div>").join("");

/* plazo fijo */
$("pf-nota").textContent = "Tasa para clientes de cada entidad, de mayor a menor." +
  (inflMes !== null ? " La columna «En 30 días» compara el interés del mes con la inflación de " + mesDe(inflFecha) +
    " (" + M.num(inflMes, 1) + "%)." : "");
let pfOrden = ["tna", false];
function pintarPf(k, a) {
  if (k) pfOrden = [k, a];
  const monto = parseFloat($("pf-monto").value);
  $("tabla-pf").tBodies[0].innerHTML = D.pf.slice().sort(M.comparar(pfOrden[0], pfOrden[1])).map(f => {
    const mes = f.tna * 30 / 365;
    const real = inflMes === null ? "" : "<span class='sub'>" + M.pct(((1 + mes / 100) / (1 + inflMes / 100) - 1) * 100, 2) + " frente a la inflación</span>";
    return "<tr><td>" + M.esc(f.n) + (f.tnaNo ? "<span class='sub'>No clientes: " + M.num(f.tnaNo, 2) + "%</span>" : "") + "</td>" +
      "<td class='der num'><b>" + M.num(f.tna, 2) + "%</b></td><td class='der num'>" + M.num(f.tea, 2) + "%</td>" +
      "<td class='der num'>" + M.num(mes, 2) + "%" + real + "</td>" +
      "<td class='der num'>" + (isNaN(monto) ? "—" : M.pesos(monto * mes / 100)) + "</td></tr>";
  }).join("");
}
M.ordenable($("tabla-pf"), pfOrden, pintarPf);
$("pf-monto").addEventListener("input", () => pintarPf());

/* fondos */
if (D.fci.length) {
  M.ordenable($("tabla-fci"), ["pat", false], (k, a) => {
    $("tabla-fci").tBodies[0].innerHTML = D.fci.slice().sort(M.comparar(k, a)).map(f =>
      "<tr><td>" + M.esc(f.n) + "</td><td class='der num'><b>" + M.num(f.tna, 2) + "%</b></td>" +
      "<td class='der num'>" + M.pesos(f.pat, 0) + " M</td><td class='der num'>" + M.fecha(f.f) + "</td></tr>").join("");
  });
} else {
  $("bloque-fci").hidden = true;
}

/* inflación */
if (D.infl.length) {
  const RANGOS = [["1 año", 366], ["3 años", 1096], ["5 años", 1827], ["Desde 2017", 0]];
  let rango = 1096;
  const pintar = () => M.linea($("grafico"), [{nombre: "Inflación mensual", color: "var(--s2)", puntos: M.desde(D.infl, rango)}],
    {formato: v => M.num(v, 1) + "%", titulo: "Inflación mensual"});
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
  $("bloque-infl").hidden = true;
}

/* referencias */
if (D.refs.length) {
  const valor = r => r.u === "% TNA" ? M.num(r.v, 2) + "% TNA" : r.u === "%" ? M.num(r.v, 1) + "%"
    : r.u === "$" ? M.pesos(r.v) : r.u === "millones de US$" ? "US$ " + M.num(r.v, 0) + " millones" : M.num(r.v, 2);
  $("tabla-ref").tBodies[0].innerHTML = D.refs.map(r => "<tr><td>" + M.esc(r.n) + "</td><td class='der num'><b>" + valor(r) +
    "</b></td><td class='der num'>" + M.fecha(r.f) + "</td></tr>").join("");
} else {
  $("bloque-ref").hidden = true;
}
"""
