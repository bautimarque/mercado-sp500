"""
Partes compartidas por todas las paginas de Mercadito: la cabecera con el
menu, el pie con el aviso legal, la lectura de fuentes y los resumenes que
cada seccion le deja al inicio.
"""

import html
import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

ARG = timezone(timedelta(hours=-3))
NY = ZoneInfo("America/New_York")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Carpeta raiz del sitio: las paginas se escriben relativas a esta.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (clave, nombre en el menu, carpeta). El orden es el del menu.
SECCIONES = [
    ("inicio", "Inicio", ""),
    ("dolar", "Dólar", "dolar/"),
    ("gastos", "Gastos en US$", "gastos/"),
    ("tasas", "Tasas", "tasas/"),
    ("merval", "Merval", "merval/"),
    ("sp500", "S&P 500", "sp500/"),
    ("bonos", "Bonos", "bonos/"),
]
CARPETAS = {clave: carpeta for clave, _, carpeta in SECCIONES}
CARPETAS.update({"metodologia": "metodologia/", "legal": "legal/"})

UA = {"User-Agent": "Mozilla/5.0 (Mercadito; datos de mercado)", "Accept": "application/json"}


def a_json(x):
    # "<" escapado para que un texto con "</script>" no corte el bloque de datos
    return json.dumps(x, ensure_ascii=False).replace("<", "\\u003c")


def ahora():
    return datetime.now(ARG)


def sello(momento=None):
    """dd/mm/aaaa hh:mm en hora argentina."""
    return (momento or ahora()).astimezone(ARG).strftime("%d/%m/%Y %H:%M")


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(momento=None):
    """martes 6 de octubre de 2026, para el cabezal."""
    m = (momento or ahora()).astimezone(ARG)
    return f"{DIAS[m.weekday()]} {m.day} de {MESES[m.month - 1]} de {m.year}"


def pedir_json(url, timeout=30):
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    return r.json()


BCRA_VARIABLES = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias?limit=3000"
_bcra = None


def bcra():
    """{idVariable: {"valor", "fecha", "descripcion"}} con el ultimo dato de cada
    serie del BCRA. Se pide una sola vez por corrida."""
    global _bcra
    if _bcra is None:
        filas = pedir_json(BCRA_VARIABLES)["results"]
        _bcra = {
            f["idVariable"]: {"valor": f["ultValorInformado"], "fecha": f["ultFechaInformada"], "descripcion": f["descripcion"]}
            for f in filas
            if f.get("ultValorInformado") is not None
        }
    return _bcra


def escribir(clave, contenido):
    carpeta = os.path.join(RAIZ, CARPETAS[clave])
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "index.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"  {os.path.relpath(ruta, RAIZ)} ({len(contenido) // 1024} KB)")


def guardar_resumen(clave, resumen):
    """Los numeros clave de una seccion, para el inicio. Queda el ultimo bueno."""
    carpeta = os.path.join(RAIZ, "datos")
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, f"{clave}.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=1)


def leer_resumenes():
    carpeta = os.path.join(RAIZ, "datos")
    resumenes = {}
    for clave, _, _ in SECCIONES:
        ruta = os.path.join(carpeta, f"{clave}.json")
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                resumenes[clave] = json.load(f)
    return resumenes


# El cabezal en miniatura: tinta, la M y la regla celeste
ICONO = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
    "%3Crect width='16' height='16' rx='2' fill='%23111317'/%3E"
    "%3Cpath d='M4 11V4.5l4 4 4-4V11' fill='none' stroke='%23F7F7F5' stroke-width='1.8' stroke-linejoin='round'/%3E"
    "%3Crect y='13' width='16' height='3' fill='%2374ACDF'/%3E%3C/svg%3E"
)

AVISO_CORTO = (
    "<strong>Información con fines educativos e informativos. No es una recomendación de inversión "
    "ni asesoramiento financiero.</strong> Los datos son de terceros y pueden tener errores o demoras; "
    "verificalos con tu banco, agente o broker antes de operar."
)


def pagina(clave, titulo, descripcion, cuerpo, *, css="", js="", fuentes=""):
    """HTML completo de una pagina: cabecera con menu, cuerpo y pie comun."""
    raiz = "../" * CARPETAS[clave].count("/")
    actual = ' aria-current="page"'
    # El menu suma "Como se calcula" al final: en el celular completa la grilla de 4 x 2
    entradas = [(c, nombre, carpeta) for c, nombre, carpeta in SECCIONES] + [("metodologia", "Cómo se calcula", "metodologia/")]
    menu = "".join(
        f'<li><a href="{raiz}{carpeta}"{actual if c == clave else ""}>{html.escape(nombre)}</a></li>'
        for c, nombre, carpeta in entradas
    )
    sumario = "".join(
        f'<li><a href="{raiz}{carpeta}">{html.escape(nombre)}</a></li>' for c, nombre, carpeta in entradas
    )
    titulo_completo = "Mercadito" if clave == "inicio" else f"{titulo} · Mercadito"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo_completo)}</title>
<meta name="description" content="{html.escape(descripcion)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#111317" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#050607" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{ICONO}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap" rel="stylesheet">
<script>
try {{ var t = localStorage.getItem("tema"); if (t === "claro" || t === "oscuro") document.documentElement.setAttribute("data-tema", t); }} catch (e) {{}}
</script>
<link rel="stylesheet" href="{raiz}assets/base.css">
<style>
{css}
</style>
</head>
<body>
<a class="saltar" href="#contenido">Ir al contenido</a>
<header class="sitio">
  <div class="cabezal"><div class="sitio-barra">
    <a class="marca" href="{raiz}">Mercadito</a>
    <p class="cabezal-fecha">{fecha_larga()}</p>
    <button id="tema" class="boton boton-tema" type="button" aria-label="Cambiar a modo oscuro">
      <svg class="ico ico-luna" viewBox="0 0 16 16" aria-hidden="true"><path d="M13.2 10.1A5.6 5.6 0 0 1 5.9 2.8a5.6 5.6 0 1 0 7.3 7.3Z"/></svg>
      <svg class="ico ico-sol" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.3M8 13.2v1.3M1.5 8h1.3M13.2 8h1.3M3.4 3.4l.9.9M11.7 11.7l.9.9M3.4 12.6l.9-.9M11.7 4.3l.9-.9"/></svg>
      <span id="tema-txt">Modo oscuro</span>
    </button>
  </div></div>
  <nav class="menu" aria-label="Secciones"><ul>{menu}</ul></nav>
</header>
<div class="pagina">
<main id="contenido">
{cuerpo}
</main>
<footer class="sitio-pie">
  {f'<p class="pie-fuentes"><b>Fuentes.</b> {fuentes}</p>' if fuentes else ""}
  <p class="pie-aviso">{AVISO_CORTO} <a href="{raiz}legal/">Aviso legal completo</a>.</p>
  <nav class="pie-sumario" aria-label="Secciones de Mercadito"><ul>{sumario}<li><a href="{raiz}legal/">Aviso legal</a></li></ul></nav>
</footer>
</div>
<script src="{raiz}assets/base.js"></script>
<script>
{js}
</script>
</body>
</html>
"""
