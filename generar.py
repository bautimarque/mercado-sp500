"""
Genera el sitio Mercadito. Cada seccion es independiente: si una falla, las
demas se publican igual y la que fallo queda con su version anterior.

Uso:
  pip install -r requirements.txt
  python generar.py                 # todas las secciones
  python generar.py rapido          # las que cambian durante el dia
  python generar.py dolar tasas     # solo esas
"""

import importlib
import sys
import time
import traceback

from mercadito import comun

SECCIONES = ["dolar", "gastos", "tasas", "merval", "sp500", "bonos"]
# Las que se actualizan durante la rueda. El S&P 500 baja ~500 historicos y va
# una vez por dia, despues del cierre de Nueva York.
RAPIDAS = ["dolar", "gastos", "tasas", "merval", "bonos"]


def main(args):
    if not args or args == ["todo"]:
        pedidas = SECCIONES
    elif args == ["rapido"]:
        pedidas = RAPIDAS
    else:
        desconocidas = [a for a in args if a not in SECCIONES]
        if desconocidas:
            sys.exit(f"Secciones desconocidas: {', '.join(desconocidas)}. Opciones: {', '.join(SECCIONES)}, rapido, todo")
        pedidas = args

    fallas = []
    for nombre in pedidas:
        print(f"== {nombre}")
        inicio = time.time()
        try:
            resumen = importlib.import_module(f"mercadito.{nombre}").generar()
            comun.guardar_resumen(nombre, resumen)
        except Exception:
            traceback.print_exc()
            fallas.append(nombre)
        print(f"   {time.time() - inicio:.0f} s")

    print("== inicio y paginas fijas")
    importlib.import_module("mercadito.inicio").generar(comun.leer_resumenes())
    importlib.import_module("mercadito.fijas").generar()

    if fallas:
        print(f"Fallaron: {', '.join(fallas)}. Quedan publicadas sus versiones anteriores.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
