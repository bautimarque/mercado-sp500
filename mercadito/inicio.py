"""
Inicio (index.html): los numeros clave de cada seccion, con su fecha y un
link a la seccion. Se arma con los resumenes que deja cada una en datos/.
"""

import html
from datetime import datetime

from . import comun

# Un resumen con mas dias que esto se marca como desactualizado
DIAS_VIEJO = 4

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def n(v, dec=2):
    """Numero con formato argentino: 1.234,56"""
    if v is None:
        return "—"
    txt = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return txt.replace("-", "−")


def pct(v, dec=1):
    if v is None:
        return "—"
    return ("+" if round(v, dec) > 0 else "") + n(v, dec) + "%"


def viejo(resumen):
    try:
        momento = datetime.strptime(resumen["actualizado"], "%d/%m/%Y %H:%M").replace(tzinfo=comun.ARG)
        return (comun.ahora() - momento).days > DIAS_VIEJO
    except (KeyError, ValueError):
        return True


def cuando(resumen):
    """«Actualizado a las 15:02» si es de hoy; si no, «Actualizado el 05/10»."""
    txt = resumen.get("actualizado", "")
    try:
        momento = datetime.strptime(txt, "%d/%m/%Y %H:%M")
    except ValueError:
        return "Actualizado el " + html.escape(txt)
    if momento.date() == comun.ahora().date():
        return "Actualizado a las " + momento.strftime("%H:%M")
    return "Actualizado el " + momento.strftime("%d/%m")


def tarjeta(clave, titulo, resumen, principal, secundario):
    """Un panel del inicio: la sección, su número principal grande y como mucho uno
    secundario. principal y secundario son (etiqueta, valor). Toda la tarjeta lleva
    a la sección: el detalle está allá."""
    carpeta = comun.CARPETAS[clave]
    flecha = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>'
    if not resumen or not principal:
        cuerpo = '<span class="t-vacio">Todavía no hay datos de esta sección.</span>'
    else:
        et, val = principal
        cuerpo = f'<span class="t-et">{et}</span><span class="t-val">{val}</span>'
        if secundario:
            cuerpo += f'<span class="t-sec">{secundario[0]} <b class="num">{secundario[1]}</b></span>'
        aviso = ' · <b>desactualizado</b>' if viejo(resumen) else ""
        cuerpo += f'<span class="t-act">{cuando(resumen)}{aviso}</span>'
    return f'<li><a class="tarjeta" href="{carpeta}"><h2 class="t-tit">{titulo}{flecha}</h2>{cuerpo}</a></li>'


# Cada sección elige su número principal y, como mucho, uno secundario.
# El resto de sus datos está en su página.

def datos_dolar(d):
    t = d["tipos"]
    mep, oficial = t.get("bolsa"), t.get("oficial")
    if mep:
        return ("Dólar MEP", "$ " + n(mep["v"])), (("Oficial", "$ " + n(oficial["v"])) if oficial else None)
    return (("Dólar oficial", "$ " + n(oficial["v"])) if oficial else None), None


def datos_gastos(g):
    e = g["efectivo"]
    return ("Dólar tarjeta, gastos en el exterior", "$ " + n(e["exterior"])), ("Servicio digital", "$ " + n(e["servicio"]))


def datos_tasas(t):
    principal = None
    if t.get("plazo_fijo_max"):
        principal = ("Plazo fijo más alto, TNA", n(t["plazo_fijo_max"]["tna"]) + "%")
    elif t.get("plazo_fijo_nacion") is not None:
        principal = ("Plazo fijo Banco Nación, TNA", n(t["plazo_fijo_nacion"]) + "%")
    secundario = None
    if t.get("inflacion_mensual"):
        mes = MESES[int(t["inflacion_mensual"]["f"][5:7]) - 1]
        secundario = (f"Inflación de {mes}", n(t["inflacion_mensual"]["v"], 1) + "%")
    return principal, secundario


def datos_merval(m):
    if m.get("pu") is not None:
        principal = ("S&amp;P Merval en dólares CCL", "US$ " + n(m["pu"], 0))
    else:
        principal = ("S&amp;P Merval", n(m["p"], 0))
    secundario = ("Desde su máximo", pct(m["da"])) if m.get("da") is not None else None
    return principal, secundario


def datos_sp500(s):
    i = s.get("indice")
    principal = ("S&amp;P 500 desde su máximo", pct(i["da"])) if i else None
    if s.get("con_cedear"):
        secundario = ("Con CEDEAR", f'{s["con_cedear"]} de {s["empresas"]} empresas')
    elif s.get("arriba_200s") is not None:
        secundario = ("Arriba de su promedio de 200 semanas", f'{s["arriba_200s"]}%')
    else:
        secundario = None
    return principal, secundario


def datos_bonos(b):
    r = b.get("riesgo")
    if not r:
        return None, None
    secundario = None
    if r.get("dif") is not None:
        secundario = ("Vs. el día anterior", ("+" if r["dif"] > 0 else "") + n(r["dif"], 0))
    return ("Riesgo país", n(r["v"], 0) + " puntos"), secundario


# (clave, titulo, elige el número principal y el secundario)
PANELES = [
    ("dolar", "Dólar", datos_dolar),
    ("gastos", "Gastos en dólares", datos_gastos),
    ("tasas", "Tasas", datos_tasas),
    ("merval", "Merval", datos_merval),
    ("sp500", "CEDEARs", datos_sp500),
    ("bonos", "Bonos", datos_bonos),
]


def generar(resumenes):
    paneles = []
    for clave, titulo, elegir in PANELES:
        r = resumenes.get(clave)
        principal = secundario = None
        if r:
            # Un resumen viejo o incompleto no rompe el inicio: ese panel sale sin datos
            try:
                principal, secundario = elegir(r)
            except Exception as e:
                print(f"  Resumen de {clave} ilegible ({e!r}): se muestra sin datos")
                r = None
        paneles.append(tarjeta(clave, titulo, r, principal, secundario))

    cuerpo = f"""
<div class="titulo">
  <h1>Mercadito</h1>
  <p class="bajada">Dólar, tasas, acciones y bonos de Argentina y Estados Unidos en un solo lugar. Datos para mirar el mercado, no recomendaciones.</p>
</div>
<ul class="tablero">
{"".join(paneles)}
</ul>
"""
    comun.escribir("inicio", comun.pagina(
        "inicio", "Mercadito",
        "Dólar, tasas, Merval, CEDEARs y bonos: los datos del mercado argentino y de Estados Unidos en un solo lugar.",
        cuerpo, css=CSS,
        fuentes="Cada panel resume su sección con su fecha. Fuentes: dolarapi.com, comparadolar.ar, argentinadatos.com, BCRA, "
                "Yahoo Finance, Wikipedia, nasdaq.com y data912.com; el detalle de cada dato está en "
                '<a href="metodologia/">Cómo se calcula</a>.',
    ))


CSS = r"""
/* el cabezal ya dice Mercadito: el título queda para lectores de pantalla y la bajada abre la página */
.titulo h1{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.titulo .bajada{margin-top:0;font-size:17px;color:var(--tinta-2);max-width:48ch;line-height:1.4}
/* seis tarjetas: la sección, un número grande y como mucho uno chico. Sin cajas ni filetes */
.tablero{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:48px 40px;margin-top:40px}
.tarjeta{display:flex;flex-direction:column;min-width:0;text-decoration:none;color:inherit;border-radius:4px}
.tarjeta:focus-visible{outline-offset:6px}
.t-tit{display:flex;align-items:center;gap:6px;font-size:15px;font-weight:700;line-height:1.2}
.t-tit .ico{width:14px;height:14px;color:var(--tinta-3);transition:transform .15s,color .15s}
.tarjeta:hover .t-tit{text-decoration:underline;text-underline-offset:3px}
.tarjeta:hover .t-tit .ico{transform:translateX(3px);color:var(--tinta)}
.t-et{font-size:13.5px;color:var(--tinta-2);margin-top:14px;line-height:1.3}
.t-val{font-size:58px;font-weight:800;font-stretch:66%;line-height:.95;letter-spacing:-.01em;margin-top:4px;white-space:nowrap}
.t-sec{font-size:14px;color:var(--tinta-2);margin-top:10px;line-height:1.35}
.t-sec b{color:var(--tinta);font-weight:650}
.t-act{font-size:12px;color:var(--tinta-3);margin-top:10px}
.t-act b{font-weight:650;color:var(--tinta-2)}
.t-vacio{font-size:14px;color:var(--tinta-3);margin-top:12px}
@media (max-width:899px){
  .titulo .bajada{font-size:15px}
  .tablero{grid-template-columns:repeat(2,minmax(0,1fr));gap:30px 18px;margin-top:26px}
  .t-tit{font-size:14px}
  .t-et{font-size:12.5px;margin-top:8px;min-height:2.6em;display:flex;align-items:flex-end}
  .t-val{font-size:36px;margin-top:3px}
  .t-sec{font-size:12.5px;margin-top:6px}
  .t-act{font-size:11.5px;margin-top:6px}
}
@media (max-width:360px){
  .t-val{font-size:31px}
}
"""
