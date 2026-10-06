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


def fecha(iso):
    return "—" if not iso else f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}"


def viejo(resumen):
    try:
        momento = datetime.strptime(resumen["actualizado"], "%d/%m/%Y %H:%M").replace(tzinfo=comun.ARG)
        return (comun.ahora() - momento).days > DIAS_VIEJO
    except (KeyError, ValueError):
        return True


def fila(etiqueta, valor, detalle=""):
    return (f'<li><span class="et">{etiqueta}</span><span class="val num">{valor}</span>'
            f'{f"<span class=det>{detalle}</span>" if detalle else ""}</li>')


def panel(clave, titulo, resumen, filas, link):
    carpeta = comun.CARPETAS[clave]
    if not resumen:
        cuerpo = '<p class="nota">Todavía no hay datos de esta sección.</p>'
        pie = ""
    else:
        cuerpo = f'<ul class="filas">{"".join(filas)}</ul>'
        aviso = ' · <b>desactualizado</b>' if viejo(resumen) else ""
        pie = f'<p class="act">Actualizado el {html.escape(resumen.get("actualizado", "—"))} hs{aviso}</p>'
    flecha = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>'
    return (f'<section class="panel-sec" aria-labelledby="p-{clave}"><h2 id="p-{clave}"><a href="{carpeta}">{titulo}</a></h2>'
            f'{cuerpo}{pie}<a class="ir" href="{carpeta}">{link}{flecha}</a></section>')


def filas_dolar(d):
    filas = []
    for casa in ("oficial", "bolsa", "contadoconliqui", "blue"):
        x = d["tipos"].get(casa)
        if x:
            det = pct(x["var"], 2) + " en el día" if x.get("var") is not None else ""
            filas.append(fila(html.escape(x["n"]), "$ " + n(x["v"]), det))
    return filas


def filas_gastos(g):
    e = g["efectivo"]
    return [
        fila("Juego digital", "$ " + n(e["juego"]), "por dólar, con IVA e Ingresos Brutos"),
        fila("Servicio digital", "$ " + n(e["servicio"]), "por dólar, con IVA, percepción e Ingresos Brutos"),
        fila("Gasto en el exterior", "$ " + n(e["exterior"]), "por dólar, con la percepción del 30% (dólar tarjeta)"),
    ]


def filas_tasas(t):
    filas = []
    if t.get("plazo_fijo_nacion") is not None:
        filas.append(fila("Plazo fijo Banco Nación", n(t["plazo_fijo_nacion"]) + "%", "TNA a 30 días"))
    if t.get("plazo_fijo_max"):
        filas.append(fila("Plazo fijo más alto", n(t["plazo_fijo_max"]["tna"]) + "%", html.escape(t["plazo_fijo_max"]["n"])))
    if t.get("inflacion_mensual"):
        det = f'interanual {n(t["inflacion_interanual"]["v"], 1)}%' if t.get("inflacion_interanual") else ""
        mes = MESES[int(t["inflacion_mensual"]["f"][5:7]) - 1]
        filas.append(fila(f"Inflación de {mes}", n(t["inflacion_mensual"]["v"], 1) + "%", det))
    if t.get("tamar"):
        filas.append(fila("TAMAR", n(t["tamar"]["v"]) + "%", "TNA de bancos privados"))
    return filas


def filas_merval(m):
    return [
        fila("S&amp;P Merval", n(m["p"], 0), pct(m["var"], 2) + " en el día"),
        fila("En dólares CCL", "US$ " + n(m["pu"], 0), pct(m["ru"]) + " en 12 meses" if m.get("ru") is not None else ""),
        fila("Desde su máximo en dólares", pct(m["da"]), "máximo del " + fecha(m["fa"]) if m.get("fa") else ""),
    ]


def filas_sp500(s):
    filas = []
    i = s.get("indice")
    if i:
        filas.append(fila("Índice S&amp;P 500", pct(i["da"]), "desde su máximo · " + n(i["p"], 0) + " puntos"))
        if i.get("dm") is not None:
            filas.append(fila("Vs. su promedio de 200 semanas", pct(i["dm"], 0)))
    if s.get("arriba_200s") is not None:
        filas.append(fila("Empresas arriba de su promedio de 200 semanas", f'{s["arriba_200s"]}%', f'de {s["empresas"]}'))
    # "volvio_promedio" es el nombre anterior del patron, en resumenes viejos
    en_promedio = s.get("en_promedio", s.get("volvio_promedio"))
    filas.append(fila("Patrones de precio", f'{en_promedio} · {s["subio_fuerte"]}', "en su promedio o debajo · subió fuerte"))
    return filas


def filas_bonos(b):
    filas = []
    if b.get("riesgo"):
        r = b["riesgo"]
        det = (("+" if r["dif"] > 0 else "") + n(r["dif"], 0) + " vs. el día anterior · ") if r.get("dif") is not None else ""
        filas.append(fila("Riesgo país", n(r["v"], 0) + " puntos", det + fecha(r["f"])))
    if b.get("al30"):
        filas.append(fila("AL30 en dólares MEP", "US$ " + n(b["al30"]["d"]), pct(b["al30"]["var"], 2) + " en el día"))
    if b.get("gd30"):
        filas.append(fila("GD30 en dólares MEP", "US$ " + n(b["gd30"]["d"]), pct(b["gd30"]["var"], 2) + " en el día"))
    return filas


# (clave, titulo, armador de filas, texto del link)
PANELES = [
    ("dolar", "Dólar", filas_dolar, "Todos los tipos, bancos y calculadora"),
    ("gastos", "Gastos en dólares", filas_gastos, "Calculadora de juegos, suscripciones y viajes"),
    ("tasas", "Tasas", filas_tasas, "Plazo fijo por entidad, fondos e inflación"),
    ("merval", "Merval", filas_merval, "Las principales acciones argentinas"),
    ("sp500", "S&amp;P 500", filas_sp500, "Las 500 empresas, una por una"),
    ("bonos", "Bonos", filas_bonos, "Soberanos, letras y obligaciones negociables"),
]


def generar(resumenes):
    paneles = []
    for clave, titulo, armar, link in PANELES:
        r = resumenes.get(clave)
        filas = []
        if r:
            # Un resumen viejo o incompleto no rompe el inicio: ese panel sale sin datos
            try:
                filas = armar(r)
            except Exception as e:
                print(f"  Resumen de {clave} ilegible ({e!r}): se muestra sin datos")
                r = None
        paneles.append(panel(clave, titulo, r, filas, link))

    cuerpo = f"""
<div class="titulo">
  <h1>Mercadito</h1>
  <p class="bajada">Dólar, tasas, acciones y bonos de Argentina y Estados Unidos en un solo lugar. Datos para mirar el mercado, no recomendaciones.</p>
</div>
<div class="tablero">
{"".join(paneles)}
</div>
"""
    comun.escribir("inicio", comun.pagina(
        "inicio", "Mercadito",
        "Dólar, tasas, Merval, S&P 500 y bonos: los datos del mercado argentino y de Estados Unidos en un solo lugar.",
        cuerpo, css=CSS,
        fuentes="Cada panel resume su sección con su fecha. Fuentes: dolarapi.com, comparadolar.ar, argentinadatos.com, BCRA, "
                "Yahoo Finance, Wikipedia, nasdaq.com y data912.com; el detalle de cada dato está en "
                '<a href="metodologia/">Cómo se calcula</a>.',
    ))


CSS = r"""
/* el cabezal ya dice Mercadito: el título queda para lectores de pantalla y la bajada abre la tapa */
.titulo h1{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.titulo .bajada{margin-top:0;font-size:19px;font-weight:550;color:var(--tinta);max-width:52ch;line-height:1.35}
/* La tapa: el dólar al frente, a todo el ancho, y un sumario de módulos con filetes */
.tablero{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));margin-top:26px;padding-top:4px;border-top:3px solid var(--tinta);
  background:linear-gradient(var(--tinta),var(--tinta)) 0 3px / 100% 1px no-repeat}
.panel-sec{display:flex;flex-direction:column;grid-column:span 2;padding:14px 24px 20px;border-left:1px solid var(--linea);border-bottom:1px solid var(--linea-2)}
.panel-sec:nth-child(5),.panel-sec:nth-child(6){grid-column:span 3}
.panel-sec:nth-child(2),.panel-sec:nth-child(5){border-left:0;padding-left:0}
.panel-sec:nth-child(4),.panel-sec:nth-child(6){padding-right:0}
.panel-sec h2{font-size:24px;font-weight:850;font-stretch:72%;line-height:1.1}
.panel-sec h2 a{text-decoration:none}
.panel-sec h2 a:hover{text-decoration:underline}
.filas{margin-top:8px}
.filas li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1px 14px;padding:9px 0;border-bottom:1px solid var(--linea)}
.filas li:last-child{border-bottom:0}
.filas .et{font-size:14.5px;font-weight:550}
.filas .val{font-size:22px;font-weight:800;font-stretch:76%;line-height:1.1;text-align:right}
.filas .det{grid-column:1 / -1;font-size:12.5px;color:var(--tinta-3)}
.act{font-size:12.5px;color:var(--tinta-3);margin-top:8px}
.ir{display:inline-flex;align-items:center;gap:6px;margin-top:auto;padding-top:12px;font-size:14px;font-weight:650}
.ir .ico{transition:transform .15s}
.ir:hover .ico{transform:translateX(3px)}
/* el dólar, como cifra de tapa */
.panel-sec:first-child{grid-column:1 / -1;border-left:0;padding:14px 0 20px}
.panel-sec:first-child .filas{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:10px}
.panel-sec:first-child .filas li{display:flex;flex-direction:column;padding:4px 20px 6px;border-bottom:0;border-left:1px solid var(--linea)}
.panel-sec:first-child .filas li:first-child{border-left:0;padding-left:0}
.panel-sec:first-child .et{font-size:15px;font-weight:700}
.panel-sec:first-child .val{order:2;font-size:56px;font-stretch:66%;line-height:.95;text-align:left;margin-top:6px;font-variant-numeric:normal}
.panel-sec:first-child .det{order:3;font-size:13px;margin-top:6px}
@media (max-width:1023px){
  .tablero{grid-template-columns:repeat(2,minmax(0,1fr))}
  .panel-sec,.panel-sec:nth-child(n){grid-column:auto;padding:14px 0 20px 24px;border-left:1px solid var(--linea)}
  .panel-sec:nth-child(2n){border-left:0;padding-left:0;padding-right:24px}
  .panel-sec:nth-child(6){grid-column:1 / -1;border-left:0;padding-left:0;padding-right:0}
}
@media (max-width:899px){
  .tablero{grid-template-columns:1fr;margin-top:20px}
  .panel-sec,.panel-sec:nth-child(n){grid-column:auto;border-left:0;padding:14px 0 18px}
  .panel-sec:first-child .filas{grid-template-columns:1fr 1fr}
  .panel-sec:first-child .filas li{padding:10px 14px 12px}
  .panel-sec:first-child .filas li:nth-child(odd){border-left:0;padding-left:0}
  .panel-sec:first-child .filas li:nth-child(n+3){border-top:1px solid var(--linea)}
  .panel-sec:first-child .val{font-size:38px}
}
"""
