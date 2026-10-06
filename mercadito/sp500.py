"""
Seccion S&P 500 (sp500/index.html): las ~500 empresas del indice con su
distancia al maximo historico, al promedio de 200 semanas y su variacion en
12 meses. Se baja todo con yfinance y queda embebido en la pagina.
"""

import time
from io import StringIO
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf

from . import comun
from .comun import ARG, NY, DIAS, a_json

LOTE = 50
INTENTOS = 3
INDICE = "^GSPC"

# El indice tiene ~503 empresas. Con menos que esto la falla es de la descarga,
# no del indice, y se corta sin pisar la pagina publicada.
MINIMO = 475

# Un ticker cuyo ultimo precio tiene mas dias que esto respecto del resto
# esta suspendido o deslistado: su precio ya no dice nada.
DIAS_VIEJO = 5

# Yahoo a veces trae un maximo diario erroneo (por ejemplo sin ajustar por
# split). Se ignora el que supera en mas de esto a la apertura, el cierre
# y los cierres vecinos.
SALTO_MAXIMO = 1.5

# Los patrones describen el precio con reglas fijas; no son recomendaciones.
# Patron "En su promedio o debajo": el precio no esta mas de 5% arriba de su
# promedio de 200 semanas (puede estar por debajo), el maximo historico es de
# los ultimos años y el promedio sube.
PROMEDIO_BANDA = 5        # tope: hasta +5% arriba de la 200 semanal (o por debajo)
PROMEDIO_ANIOS = 2        # antiguedad maxima del maximo historico
PROMEDIO_PENDIENTE = 26   # semanas hacia atras para ver si la 200 semanal sube

# Patron "Subió fuerte": subio mucho en un año y sigue cerca del maximo.
# +50% suele dejar adentro al 10% del indice que mas subio.
SUBA_12M = 50
SUBA_CERCA = 10           # % maximo de distancia al maximo historico

WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Directorio oficial de Nasdaq con la bolsa de cada accion de EE.UU. Sirve para
# armar el simbolo de TradingView (NYSE:F y no F, que existe en otras bolsas).
NASDAQ_DIR = "https://www.nasdaqtrader.com/dynamic/SymDir/"
PREFIJOS = {"N": "NYSE", "A": "AMEX", "P": "AMEX", "Z": "CBOE"}

# Buscador de nasdaq.com: capitalizacion de todas las acciones de EE.UU. en un
# solo pedido. Ordena la tabla de la empresa mas grande a la mas chica.
NASDAQ_BUSCADOR = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=10000&download=true"

# Sectores GICS en castellano; uno nuevo que no este aca queda en ingles
SECTORES = {
    "Communication Services": "Comunicaciones",
    "Consumer Discretionary": "Consumo discrecional",
    "Consumer Staples": "Consumo básico",
    "Energy": "Energía",
    "Financials": "Finanzas",
    "Health Care": "Salud",
    "Industrials": "Industria",
    "Information Technology": "Tecnología",
    "Materials": "Materiales",
    "Real Estate": "Inmobiliario",
    "Utilities": "Servicios públicos",
}


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
    df["sector"] = df["sector"].map(lambda s: SECTORES.get(s, s))
    return df[["ticker", "nombre", "sector"]].to_dict("records")


def bolsas():
    """{simbolo: prefijo de TradingView}. Si el directorio no se puede bajar
    los links van sin bolsa y TradingView elige la cotizacion mas comun."""
    mapa = {}
    # (archivo, columna de la bolsa, columna de "Test Issue")
    for archivo, col_bolsa, col_prueba in (("nasdaqlisted.txt", None, 3), ("otherlisted.txt", 2, 6)):
        try:
            r = requests.get(NASDAQ_DIR + archivo, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"Sin {archivo} de Nasdaq ({e}): esos links a TradingView van sin bolsa")
            continue
        for linea in r.text.splitlines()[1:]:
            c = linea.split("|")
            if len(c) <= col_prueba or c[col_prueba] != "N":
                continue
            prefijo = "NASDAQ" if col_bolsa is None else PREFIJOS.get(c[col_bolsa])
            if prefijo:
                mapa[c[0]] = prefijo
    return mapa


def tamanos():
    """{simbolo: capitalizacion en US$}, con las clases como BRK/B. Si falla,
    la tabla arranca ordenada por caida en vez de por tamaño."""
    try:
        r = requests.get(
            NASDAQ_BUSCADOR,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        filas = r.json()["data"]["rows"]
    except Exception as e:
        print(f"Sin capitalizaciones de nasdaq.com ({e}): la tabla arranca ordenada por caida")
        return {}
    mapa = {}
    for f in filas:
        try:
            valor = float(f["marketCap"])
        except (KeyError, TypeError, ValueError):
            continue
        if valor > 0:
            mapa[f["symbol"]] = valor
    return mapa


def bajar_diario(tickers):
    """Historico diario completo. Devuelve {ticker: DataFrame} con los que
    trajeron datos; los que fallan se reintentan, con pausas crecientes."""
    datos = {}
    pendientes = list(tickers)
    for intento in range(INTENTOS):
        if intento:
            print(f"Reintento {intento}: faltan {len(pendientes)}")
            time.sleep(15 * intento)
        for i in range(0, len(pendientes), LOTE):
            lote = pendientes[i:i + LOTE]
            print(f"Bajando {i + 1} a {i + len(lote)} de {len(pendientes)}")
            try:
                data = yf.download(
                    lote,
                    period="max",
                    interval="1d",
                    auto_adjust=False,
                    group_by="ticker",
                    threads=True,
                    progress=False,
                )
            except Exception as e:
                print(f"  error en el lote: {e}")
                continue
            for t in lote:
                try:
                    df = data[t].dropna(subset=["Close"])
                except KeyError:
                    continue
                if not df.empty:
                    datos[t] = df
        pendientes = [t for t in tickers if t not in datos]
        if not pendientes:
            break
    return datos


def medir(df, fecha_datos):
    """Precio, maximo, 200 semanal, rendimiento a 12 meses y patron de una
    serie diaria. None si tiene menos de 20 semanas de historia."""
    # Las semanas se arman aca y no se piden a Yahoo: sus barras semanales
    # a veces vienen corridas de dia, sin la semana actual o con maximos
    # que no aparecen en los datos diarios.
    semanal = df["Close"].resample("W-FRI").last().dropna()
    if len(semanal) < 20:
        return None

    vecinos = pd.concat(
        [df["Open"], df["Close"], df["Close"].shift(1), df["Close"].shift(-1)],
        axis=1,
    ).max(axis=1)
    maximos = df["High"].where(df["High"] <= vecinos * SALTO_MAXIMO, vecinos)

    precio = float(df["Close"].iloc[-1])
    ath = float(maximos.max())
    fecha_ath = maximos.idxmax()
    dist_ath = (precio - ath) / ath * 100

    ma200 = dist_ma = None
    sube = False
    if len(semanal) >= 200:
        ma200 = float(semanal.iloc[-200:].mean())
        dist_ma = (precio - ma200) / ma200 * 100
        previa = semanal.iloc[-200 - PROMEDIO_PENDIENTE:-PROMEDIO_PENDIENTE]
        sube = len(previa) == 200 and ma200 > previa.mean()

    rend = None
    hace_un_anio = df["Close"].loc[:fecha_datos - pd.Timedelta(days=365)]
    if not hace_un_anio.empty:
        rend = (precio / float(hace_un_anio.iloc[-1]) - 1) * 100

    patron = None
    if rend is not None and rend >= SUBA_12M and dist_ath >= -SUBA_CERCA:
        patron = "g"
    elif (dist_ma is not None and dist_ma <= PROMEDIO_BANDA and sube
          and (fecha_datos - fecha_ath).days / 365.25 <= PROMEDIO_ANIOS):
        patron = "c"

    return {
        "p": round(precio, 2),
        "a": round(ath, 2),
        "fa": fecha_ath.date().isoformat(),
        "da": round(dist_ath, 1),
        "m": round(ma200, 2) if ma200 is not None else None,
        "dm": round(dist_ma, 1) if dist_ma is not None else None,
        "r": round(rend, 1) if rend is not None else None,
        "sg": patron,
    }


def calcular(empresas, datos):
    """Devuelve las filas de la tabla, la fecha del ultimo precio y los
    tickers que quedaron afuera con el motivo."""
    fecha_datos = pd.Series([df.index[-1] for df in datos.values()]).mode()[0]
    filas, afuera = [], []
    for emp in empresas:
        t = emp["ticker"]
        df = datos.get(t)
        if df is None:
            afuera.append(f"{t} (sin datos)")
            continue
        if (fecha_datos - df.index[-1]).days > DIAS_VIEJO:
            afuera.append(f"{t} (ultimo precio {df.index[-1].date()})")
            continue
        m = medir(df, fecha_datos)
        if m is None:
            afuera.append(f"{t} (menos de 20 semanas)")
            continue
        filas.append({"t": t, "n": emp["nombre"], "s": emp["sector"], **m})

    filas.sort(key=lambda f: f["da"])
    return filas, fecha_datos, afuera


def texto_fecha(fecha_datos):
    """Dice de cuando son los precios: cierre o mitad de rueda."""
    ahora_ny = datetime.now(NY)
    dia = f"{DIAS[fecha_datos.weekday()]} {fecha_datos:%d/%m/%Y}"
    if fecha_datos.date() == ahora_ny.date() and ahora_ny.hour < 16:
        texto = f"Precios del {dia} a las {ahora_ny:%H:%M} de Nueva York, con el mercado abierto"
    else:
        texto = f"Precios al cierre del {dia}"
    ahora_arg = datetime.now(ARG)
    if f"{ahora_arg:%d/%m/%Y}" == f"{fecha_datos:%d/%m/%Y}":
        sello = f"{ahora_arg:%H:%M}"
    else:
        sello = f"{ahora_arg:%d/%m/%Y %H:%M}"
    return texto + " · actualizado " + sello + " hs ARG"


CSS = r"""
/* hoy: cifra de tapa arriba, termómetro plegable debajo */
.hoy{display:flex;flex-direction:column}
.hoy>.lecturas,.hoy>.fecha{order:-1}
.hoy>.fecha{padding-top:10px;border-top:1px solid var(--linea-2)}
.lecturas{padding-bottom:16px}
.franja:not(.leyendo-ya) .franja-lectura span{white-space:normal;right:0;overflow:visible}
.franja{position:relative}
.franja-lectura{position:relative;height:30px;font-size:13.5px;color:var(--tinta-2)}
.franja-lectura span{position:absolute;left:0;bottom:6px;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.franja-lectura b{color:var(--tinta);font-weight:700}
.leyendo-ya .franja-lectura span{color:var(--tinta);background:var(--superficie);padding:3px 8px;
  border-radius:4px;bottom:4px;box-shadow:0 1px 2px rgba(10,14,20,.08),0 3px 12px rgba(10,14,20,.10)}
.franja-zona{position:relative;height:96px;cursor:crosshair;touch-action:pan-y;
  -webkit-user-select:none;user-select:none;border-radius:6px}
.franja-zona:focus-visible{outline-offset:4px;border-radius:8px}
.franja-zona svg{display:block;width:100%;height:100%;clip-path:inset(0 round 3px)}
.franja-zona rect,.sector-franja rect{transition:opacity .2s ease-out}
rect.off{opacity:.14}
.franja-prom{position:absolute;top:-5px;bottom:-9px;width:2px;margin-left:-1px;background:var(--tinta);pointer-events:none}
.franja-cursor{position:absolute;top:-6px;bottom:-6px;width:3px;margin-left:-1.5px;border-radius:2px;
  background:var(--tinta);box-shadow:0 0 0 1.5px var(--fondo);display:none;pointer-events:none}
.leyendo-ya .franja-cursor{display:block}
.franja-eje{position:relative;height:30px;font-size:12.5px;color:var(--tinta-3)}
.franja-eje>span{position:absolute;top:10px;white-space:nowrap}
#eje-izq{left:0} #eje-der{right:0}
#eje-prom{transform:translateX(-50%);color:var(--tinta);font-weight:600}
.plegable{margin:30px 0 10px}
.plegable>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;font-size:15px;font-weight:700;color:var(--tinta);
  padding:10px 0 8px;border-top:1px solid var(--linea-2);user-select:none}
.plegable>summary::-webkit-details-marker{display:none}
.plegable>summary::before{content:"";width:7px;height:7px;margin:0 2px 3px 2px;border-right:1.6px solid currentColor;border-bottom:1.6px solid currentColor;
  transform:rotate(-45deg);transition:transform .15s;color:var(--tinta-2)}
.plegable[open]>summary::before{transform:rotate(45deg)}
.plegable>summary::after{content:"Mostrar";margin-left:auto;font-size:13px;font-weight:600;color:var(--tinta);background:var(--superficie);border:1px solid var(--linea-2);border-radius:4px;padding:5px 12px}
.plegable[open]>summary::after{content:"Ocultar"}
.plegable>summary:hover{color:var(--tinta)}
.plegable>summary:hover::after{color:var(--tinta);background:var(--hundido)}
.plegable>summary:focus-visible{outline:2px solid var(--tinta-3);outline-offset:3px;border-radius:6px}
.leyenda{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:4px;font-size:12.5px;color:var(--tinta-2)}
.leyenda li{display:flex;align-items:center;gap:6px;white-space:nowrap}
.leyenda small{color:var(--tinta-3);font-size:12px;font-variant-numeric:tabular-nums}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;flex:none}

/* hoy: lecturas */
.lecturas{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);grid-template-areas:"temp lect" "res lect";
  grid-template-rows:auto 1fr;gap:0 56px;margin-top:26px;align-items:start;border-top:3px solid var(--tinta);padding-top:18px;
  background:linear-gradient(var(--tinta),var(--tinta)) 0 3px / 100% 1px no-repeat}
.panel,.emp-cab,.pie{background:linear-gradient(var(--tinta),var(--tinta)) 0 3px / 100% 1px no-repeat}
.panel,.emp-cab,.pie{padding-top:12px}
.temp{grid-area:temp} .lect-col{grid-area:lect}
.temp-val{font-size:76px;font-weight:800;font-stretch:66%;line-height:.92;letter-spacing:-.01em}
.temp-et{font-size:19px;font-weight:550;line-height:1.3;max-width:20ch;margin-top:12px}
.temp-sub{font-size:13.5px;color:var(--tinta-2);margin-top:6px}
.resumen{grid-area:res;font-size:15px;color:var(--tinta-2);max-width:42ch;margin-top:18px;padding-top:14px;border-top:1px solid var(--linea)}
.resumen b{color:var(--tinta);font-weight:650}
.lect{border-top:0}
.lect>li{border-bottom:1px solid var(--linea)}
.lect-fila{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 20px;align-items:center;
  width:100%;padding:15px 10px;text-align:left}
.lect-boton{grid-template-columns:minmax(0,1fr) auto 16px;border:0;background:transparent;border-radius:4px;cursor:pointer;
  transition:background-color .15s,color .15s}
.lect-boton:hover{background:var(--hundido)}
.lect-boton[aria-pressed="true"]{background:var(--tinta);color:var(--fondo)}
.lect-boton[aria-pressed="true"] .lect-sub,.lect-boton[aria-pressed="true"] .lect-uni,
.lect-boton[aria-pressed="true"] .chev{color:color-mix(in srgb,var(--fondo) 72%,var(--tinta))}
.lect-txt,.lect-num{display:flex;flex-direction:column;min-width:0}
.lect-nom{display:flex;align-items:center;gap:8px;font-size:16.5px;font-weight:650;line-height:1.3}
.lect-sub{font-size:13.5px;color:var(--tinta-2);margin-top:3px;line-height:1.45}
.lect-cond{display:flex;align-items:center;gap:9px;font-size:30px;font-weight:750;font-stretch:76%;line-height:1.05;margin-top:3px}
.lect-cond:empty{display:none}
.lect-cond .sw{width:14px;height:14px;border-radius:3px}
.lect-num{align-items:flex-end;text-align:right}
.lect-val{font-size:34px;font-weight:750;font-stretch:78%;line-height:1;letter-spacing:-.01em}
.lect-uni{font-size:12.5px;color:var(--tinta-3);margin-top:4px;white-space:nowrap}
.chev{color:var(--tinta-3)}
.aviso-corto{font-size:13.5px;color:var(--tinta-2);margin-top:12px;max-width:70ch}

/* paneles */
.paneles{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px 56px;margin-top:48px}
.panel{position:relative;display:flex;flex-direction:column;border-top:3px solid var(--tinta);padding-top:10px}
.panel>h2,.emp-cab h2,.pie>h2{font-size:24px;font-weight:850;font-stretch:72%;line-height:1.1;letter-spacing:-.005em}
.panel-nota{font-size:13.5px;color:var(--tinta-2);margin:5px 0 16px;max-width:60ch}
.sectores-cab,.sector{display:grid;grid-template-columns:minmax(0,10.5em) minmax(0,1fr) 3.4em;gap:14px;align-items:center}
.sectores-cab{font-size:12px;color:var(--tinta-3);padding:0 8px 6px}
.sectores-cab span:last-child{text-align:right}
.sector{width:100%;height:36px;padding:0 8px;border:0;background:transparent;border-radius:4px;cursor:pointer;text-align:left;
  transition:background-color .15s}
.sector:hover{background:var(--hundido)}
.sector[aria-pressed="true"]{background:var(--hundido);box-shadow:inset 0 0 0 2px var(--tinta)}
.sector-nom{font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sector-n{color:var(--tinta-3);font-size:12.5px;font-variant-numeric:tabular-nums;margin-left:3px}
.sector-franja{display:block;width:100%;height:16px;clip-path:inset(0 round 3px)}
.sector-pct{font-size:14px;font-weight:650;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.sector-arr{display:none;font-weight:400;color:var(--tinta-2)}
.histo{position:relative;display:flex;align-items:flex-end;gap:3px;flex:1;min-height:176px;border-bottom:1px solid var(--linea-2)}
.barra{position:relative;flex:1;height:100%;padding:0;border:0;background:transparent;cursor:pointer;
  display:flex;align-items:flex-end;border-radius:3px 3px 0 0}
.barra:focus-visible{outline-offset:1px}
.barra-total{position:absolute;left:0;right:0;bottom:0;background:var(--hundido);border-radius:3px 3px 0 0;
  transition:background-color .15s}
.barra:hover .barra-total,.barra:focus-visible .barra-total{background:var(--linea-2)}
.barra-pila{position:relative;width:100%;display:flex;flex-direction:column-reverse;gap:1px;
  border-radius:3px 3px 0 0;overflow:hidden;transition:height .2s ease-out}
.barra-pila i{display:block;min-height:1px}
.histo-eje{position:relative;height:24px;font-size:12px;color:var(--tinta-3);font-variant-numeric:tabular-nums}
.histo-eje span{position:absolute;top:6px;transform:translateX(-50%);white-space:nowrap}
.histo-eje span:first-child{transform:none}
.histo-eje span:last-child{transform:translateX(-100%)}
.tip{position:absolute;z-index:3;pointer-events:none;background:var(--tinta);color:var(--fondo);
  font-size:12.5px;line-height:1.4;padding:6px 9px;border-radius:4px;max-width:230px;display:none;
  box-shadow:0 2px 10px rgba(10,14,20,.18)}
.tip.ver{display:block}

/* empresas */
.empresas{margin-top:52px;scroll-margin-top:12px}
.emp-cab{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:3px solid var(--tinta);padding-top:10px}
.cuenta{font-size:14px;color:var(--tinta-2);font-variant-numeric:tabular-nums}
.cuenta b{color:var(--tinta);font-weight:650}
.filtros{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1.2fr);gap:12px;margin-top:16px}
.campo label{display:block;font-size:12.5px;font-weight:550;color:var(--tinta-2);margin-bottom:5px}
.control{position:relative;display:flex;align-items:center}
.control .ico{position:absolute;pointer-events:none;color:var(--tinta-3)}
.control-buscar .ico{left:12px}
.control-select .ico{right:12px}
input,select{font:inherit;font-size:15px;height:44px;width:100%;padding:0 12px;border:1px solid var(--linea-2);
  border-radius:4px;background:var(--superficie);color:var(--tinta);transition:border-color .15s}
input::placeholder{color:var(--tinta-3);opacity:1}
input:hover,select:hover{border-color:var(--tinta-3)}
input:focus-visible,select:focus-visible{outline:2px solid var(--tinta);outline-offset:1px;border-color:var(--tinta);border-radius:4px}
.control-buscar input{padding-left:36px}
input[type=search]::-webkit-search-decoration{-webkit-appearance:none}
select{-webkit-appearance:none;appearance:none;padding-right:36px;cursor:pointer}
select option{background:var(--superficie);color:var(--tinta)}
input[type=number]{-moz-appearance:textfield;appearance:textfield;padding-right:52px}
input[type=number]::-webkit-inner-spin-button,input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}
.unidad{position:absolute;right:12px;font-size:14px;color:var(--tinta-3);pointer-events:none}
.campo-orden{display:none}
.atajos{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.atajos .ico{margin-left:-2px}
.mas{margin-top:12px}
.mas summary{display:inline-flex;align-items:center;gap:8px;padding:8px 2px;font-size:14px;font-weight:550;
  cursor:pointer;list-style:none;border-radius:6px}
.mas summary::-webkit-details-marker{display:none}
.mas summary .ico{transition:transform .2s ease-out;color:var(--tinta-3)}
.mas[open] summary .ico{transform:rotate(180deg)}
.mas-n{font-size:12px;font-weight:650;background:var(--tinta);color:var(--fondo);border-radius:9px;
  min-width:18px;height:18px;line-height:18px;text-align:center;padding:0 5px}
.mas-n:empty{display:none}
.numeros{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:6px 0 4px}
.ayuda{display:block;font-size:12.5px;color:var(--tinta-3);margin-top:5px;line-height:1.4}
.regla-activa{display:flex;gap:10px;align-items:flex-start;margin-top:14px;padding:11px 14px;
  background:var(--hundido);border-radius:4px;font-size:14px;color:var(--tinta-2);max-width:90ch}
.regla-activa b{color:var(--tinta);font-weight:650}
.regla-activa .ico{margin-top:2px;color:var(--tinta)}

.tabla-caja{margin-top:16px;border-top:2px solid var(--tinta);overflow:clip}
.tabla-caja.desborda{overflow-x:auto}
.ver-mas{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 16px;margin-top:14px}
.ver-mas[hidden]{display:none}
.ver-mas p{font-size:14px;color:var(--tinta-2)}
.ver-mas-acc{display:flex;flex-wrap:wrap;gap:8px}
.tabla{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}
.tabla thead th{position:sticky;top:0;z-index:2;background:var(--fondo);padding:0;text-align:left;
  font-size:12.5px;font-weight:550;line-height:1.3;color:var(--tinta-2);white-space:nowrap;vertical-align:bottom;border-bottom:1px solid var(--linea-2)}
.tabla th button{display:flex;align-items:flex-end;gap:5px;width:100%;padding:12px 12px 10px;border:0;background:transparent;
  font:inherit;color:inherit;cursor:pointer;text-align:inherit;border-radius:0}
.tabla th button:hover{color:var(--tinta)}
.tabla th button:focus-visible{outline-offset:-3px;border-radius:6px}
.tabla th.c-num{white-space:normal}
.tabla th.c-num button{justify-content:flex-end;text-align:right}
.flecha{width:12px;height:12px;flex:none;margin-bottom:1px;opacity:0;transition:transform .15s}
th[aria-sort] .flecha{opacity:1}
th[aria-sort="descending"] .flecha{transform:rotate(180deg)}
th[aria-sort]{color:var(--tinta)}
.tabla td{padding:10px 12px;border-bottom:1px solid var(--linea);vertical-align:middle}
.tabla td:first-child,.tabla th:first-child button{padding-left:0}
.tabla td:last-child,.tabla th:last-child button{padding-right:0}
.tabla tbody tr:last-child td{border-bottom:0}
.fila{cursor:pointer}
.fila:hover td{background:var(--hundido)}
.c-num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.abrir{display:flex;align-items:baseline;gap:10px;min-width:0;max-width:100%;padding:0;border:0;background:transparent;
  cursor:pointer;text-align:left;border-radius:3px}
.tk{font-weight:700;min-width:3.7em}
.nom{color:var(--tinta-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
td.c-emp{max-width:270px}
.c-sec{color:var(--tinta-2);white-space:nowrap;font-size:13.5px}
.c-dm .sw{margin-right:8px;vertical-align:-1px}
.c-da{font-weight:650;font-stretch:88%}
.c-fa{white-space:nowrap;font-variant-numeric:tabular-nums}
.fa-hace{color:var(--tinta-3)}
.patron{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;white-space:nowrap}
.nd{color:var(--tinta-3);font-size:13px}
.m-et{display:none}
.tabla .detalle td{background:var(--hundido);padding:14px 18px 16px}
.detalle p{max-width:78ch;font-size:14.5px;color:var(--tinta-2);line-height:1.55}
.detalle p+p{margin-top:6px}
.detalle b{color:var(--tinta);font-weight:650}
.det-acc{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin-top:12px}
.det-acc a.boton{text-decoration:none}

/* gráfico de TradingView */
.grafico{width:min(1120px,calc(100vw - 32px));height:min(800px,calc(100vh - 32px));max-width:none;max-height:none;
  padding:0;border:1px solid var(--linea-2);border-top:3px solid var(--tinta);border-radius:4px;background:var(--superficie);color:var(--tinta)}
.grafico[open]{display:flex;flex-direction:column}
.grafico::backdrop{background:rgba(10,12,16,.6)}
.graf-cab{display:flex;flex-wrap:wrap;align-items:center;gap:10px 12px;padding:12px 14px 12px 18px;border-bottom:1px solid var(--linea)}
.graf-tit{margin-right:auto;min-width:0;font-size:17px;font-weight:750;line-height:1.25}
.graf-tit small{margin-left:8px;font-size:14px;font-weight:450;color:var(--tinta-2)}
.graf-int{display:inline-flex;gap:6px}
.graf-cab a.boton{text-decoration:none}
.graf-ind{padding:9px 18px;border-bottom:1px solid var(--linea);font-size:13.5px;color:var(--tinta-2)}
.graf-caja{flex:1;min-height:0}
.graf-caja .tradingview-widget-container,.graf-caja .tradingview-widget-container__widget{height:100%}
.tabla .vacio td{padding:40px 16px;text-align:center;color:var(--tinta-2);cursor:default}
.vacio:hover td{background:transparent}
.vacio .boton{margin-top:12px}

/* pie */
.pie{margin-top:64px;padding-top:10px;border-top:3px solid var(--tinta)}
.pie-grilla{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:24px 56px;margin-top:10px}
.glosario>div{padding:12px 0;border-bottom:1px solid var(--linea)}
.glosario dt{font-weight:650}
.glosario dd{color:var(--tinta-2);font-size:14.5px;margin-top:2px;max-width:65ch}
h3{font-size:15px;font-weight:700;margin:14px 0 8px}
.escala li{display:grid;grid-template-columns:10px minmax(0,7.5em) minmax(0,1fr) auto;gap:10px;align-items:center;
  padding:6px 0;border-bottom:1px solid var(--linea);font-size:14px}
.escala small{color:var(--tinta-2);font-size:13px;font-variant-numeric:tabular-nums}
.escala .n{color:var(--tinta-3);font-size:13px;font-variant-numeric:tabular-nums;text-align:right}
.fuente{font-size:14px;color:var(--tinta-2);max-width:65ch}

@media (max-width:1279px){
  .c-sec{display:none}
}
@media (max-width:1099px){
  .fa-hace{display:none}
}
@media (max-width:899px){
  .franja-zona{height:64px}
  .lecturas{grid-template-columns:1fr;grid-template-areas:"temp" "lect" "res";grid-template-rows:auto;margin-top:22px;gap:18px}
  .leyenda{gap:5px 14px}
  .sectores-cab{display:none}
  .sector{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"nom pct" "fr fr";height:auto;gap:7px 12px;padding:9px 8px 11px}
  .sector-nom{grid-area:nom} .sector-pct{grid-area:pct} .sector-franja{grid-area:fr;height:12px}
  .sector-arr{display:inline}
  .lect-cond{font-size:26px}
  .temp{display:block}
  .temp-val{font-size:64px}
  .temp-et{font-size:16.5px;margin-top:10px;max-width:none}
  .franja-lectura{height:44px}
  .temp-sub{margin-top:4px}
  .resumen{max-width:none;margin-top:0}
  .lect-fila{padding:13px 6px}
  .lect-val{font-size:30px}
  .paneles{grid-template-columns:1fr;margin-top:36px;gap:36px}
  .panel{padding-top:16px}
  .empresas{margin-top:40px}
  .filtros{grid-template-columns:1fr 1fr}
  .campo-buscar{grid-column:1 / -1}
  .campo-orden{display:block}
  input,select{font-size:16px}
  .numeros{grid-template-columns:1fr}
  .tabla-caja{margin-left:0;margin-right:0}
  .tabla thead{display:none}
  .tabla,.tabla tbody{display:block}
  .tabla tr.fila{display:grid;grid-template-columns:6.9em 5.8em minmax(0,1fr) auto;
    grid-template-areas:"emp emp emp da" "dm r fa fa" "sg sg sg sg";gap:3px 12px;align-items:center;
    padding:11px 0 12px;border-bottom:1px solid var(--linea)}
  .tabla tr.fila td{display:block;padding:0;border:0;background:transparent}
  .fila:hover{background:var(--hundido)}
  .c-emp{grid-area:emp} .c-da{grid-area:da;font-weight:650;font-size:15px}
  .c-dm{grid-area:dm} .c-r{grid-area:r} .c-fa{grid-area:fa} .c-sg{grid-area:sg}
  .c-dm,.c-r,.c-fa{font-size:13px;color:var(--tinta-2);text-align:left}
  .tabla tr.fila td.c-pre,.tabla tr.fila td.c-sec{display:none}
  td.c-emp{max-width:none;min-width:0}
  .tk{min-width:0;font-size:15px}
  .nom{font-size:14px}
  .m-et{display:inline;color:var(--tinta-3)}
  .fa-hace{display:none}
  .tabla tr.fila td.c-sg:empty{display:none}
  .tabla tr.fila td.c-sg{padding-top:3px}
  .c-dm .sw{margin-right:6px}
  .tabla tr.detalle,.tabla tr.vacio{display:block;border-bottom:1px solid var(--linea)}
  .tabla tr.detalle td,.tabla tr.vacio td{display:block;border:0}
  .tabla .detalle td{padding:12px 16px 14px}
  .grafico{width:100vw;height:100%;border:0;border-radius:0}
  .graf-cab{padding:10px 12px 10px 16px}
  .graf-tit{flex:1 1 calc(100% - 64px)}
  .graf-tit small{display:block;margin:2px 0 0}
  #graf-cerrar{order:1}
  .graf-int{order:2}
  .graf-cab a.boton{order:3}
  .graf-ind{padding:8px 16px;font-size:13px}
  .pie{margin-top:48px}
  .pie-grilla{grid-template-columns:1fr}
  }
@media (max-width:520px){
  .filtros{grid-template-columns:1fr}
}
@media (max-width:420px){
  .largo{display:none}
  .temp-val{font-size:58px}
}

"""


CUERPO = r"""
<div class="titulo">
  <h1>S&amp;P 500</h1>
  <p class="bajada">Las 500 empresas más grandes de Estados Unidos: cuánto les falta para volver a su máximo, qué tan lejos están de su promedio de 200 semanas y cuánto cambiaron en 12 meses.</p>
</div>
<section class="hoy" aria-labelledby="t-hoy">
  <h2 id="t-hoy" class="oculto">Cómo está el mercado</h2>
  <details class="plegable" id="dfranja" open>
    <summary class="plegable-tit">Termómetro del índice y gráficos</summary>
  <figure class="franja">
    <div class="franja-lectura" aria-hidden="true"><span id="lectura">Pasar el dedo o el mouse por la franja para ver cada empresa</span></div>
    <div class="franja-zona" id="franja" tabindex="0" role="slider" aria-valuemin="1" aria-valuenow="1"
      aria-label="Las empresas del índice, de la que está más debajo de su promedio de 200 semanas a la que está más arriba">
      <svg id="franja-svg" preserveAspectRatio="none" aria-hidden="true"></svg>
      <span class="franja-prom" id="franja-prom"></span>
      <span class="franja-cursor" id="franja-cursor"></span>
    </div>
    <figcaption class="franja-eje">
      <span id="eje-izq">Más frías</span>
      <span id="eje-prom">Promedio<span class="largo"> de 200 semanas</span></span>
      <span id="eje-der">Más calientes</span>
    </figcaption>
  </figure>
  <ul class="leyenda" id="leyenda" aria-label="Escala de temperatura según la distancia al promedio de 200 semanas"></ul>
  </details>

  <div class="lecturas">
    <div class="temp">
      <p class="temp-val" id="k-amp-val"></p>
      <p class="temp-et">de las empresas cotiza arriba de su promedio de 200 semanas</p>
      <p class="temp-sub" id="k-amp-sub"></p>
    </div>
    <p class="resumen" id="resumen"></p>
    <div class="lect-col">
      <ul class="lect">
        <li id="k-idx">
          <div class="lect-fila">
            <span class="lect-txt"><span class="lect-nom">Índice S&amp;P 500</span><span class="lect-cond" id="k-idx-cond"></span><span class="lect-sub" id="k-idx-sub"></span></span>
            <span class="lect-num"><span class="lect-val" id="k-idx-val"></span><span class="lect-uni">desde su máximo</span></span>
          </div>
        </li>
        <li>
          <button class="lect-fila lect-boton" type="button" data-p="promedio" aria-pressed="false">
            <span class="lect-txt"><span class="lect-nom" id="k-c-nom">En su promedio o debajo</span><span class="lect-sub" id="k-c-sub"></span></span>
            <span class="lect-num"><span class="lect-val" id="k-c-val"></span><span class="lect-uni">empresas</span></span>
            <svg class="ico chev" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3.5 4.5 4.5L6 12.5"/></svg>
          </button>
        </li>
        <li>
          <button class="lect-fila lect-boton" type="button" data-p="suba" aria-pressed="false">
            <span class="lect-txt"><span class="lect-nom" id="k-g-nom">Subió fuerte</span><span class="lect-sub" id="k-g-sub"></span></span>
            <span class="lect-num"><span class="lect-val" id="k-g-val"></span><span class="lect-uni">empresas</span></span>
            <svg class="ico chev" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3.5 4.5 4.5L6 12.5"/></svg>
          </button>
        </li>
      </ul>
      <p class="aviso-corto">Los dos patrones describen el precio con reglas fijas, explicadas al pie de la página. Son datos, no recomendaciones de inversión.</p>
    </div>
  </div>
  <p class="fecha">__FECHA__</p>
</section>

<div class="paneles">
  <section class="panel" aria-labelledby="t-sec">
    <h2 id="t-sec">Temperatura por sector</h2>
    <p class="panel-nota">Cada franja ordena las empresas del sector de la más fría a la más caliente. Tocar un sector filtra la lista.</p>
    <div class="sectores-cab" aria-hidden="true"><span>Sector y empresas</span><span>De la más fría a la más caliente</span><span>Arriba</span></div>
    <ul class="sectores" id="sectores"></ul>
  </section>
  <section class="panel" aria-labelledby="t-caida">
    <h2 id="t-caida">Cuánto les falta para volver a su máximo</h2>
    <p class="panel-nota">Cada barra agrupa las empresas según su caída desde el máximo, con el color de su temperatura. El 0% es estar en el máximo. Tocar una barra muestra las que cayeron al menos eso.</p>
    <div class="histo" id="histo"></div>
    <div class="histo-eje" aria-hidden="true"><span style="left:0">−100%</span><span style="left:25%">−75%</span><span style="left:50%">−50%</span><span style="left:75%">−25%</span><span style="left:100%">0%</span></div>
    <div class="tip" id="tip"></div>
  </section>
</div>

<section class="empresas" id="empresas" aria-labelledby="t-emp">
  <div class="emp-cab">
    <h2 id="t-emp">Empresas</h2>
    <p class="cuenta" id="cuenta" aria-live="polite"></p>
  </div>
  <div class="filtros">
    <div class="campo campo-buscar">
      <label for="q">Buscar</label>
      <span class="control control-buscar">
        <svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.5"/><path d="m10.4 10.4 3.6 3.6"/></svg>
        <input id="q" type="search" placeholder="Ticker o nombre, por ejemplo AAPL" autocomplete="off" spellcheck="false">
      </span>
    </div>
    <div class="campo">
      <label for="sec">Sector</label>
      <span class="control control-select">
        <select id="sec"><option value="">Todos los sectores</option></select>
        <svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>
      </span>
    </div>
    <div class="campo campo-orden">
      <label for="orden">Ordenar</label>
      <span class="control control-select">
        <select id="orden"></select>
        <svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg>
      </span>
    </div>
  </div>
  <div class="atajos" role="group" aria-label="Atajos">
    <button class="boton" type="button" data-p="promedio" aria-pressed="false"><svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 12.5h13"/><circle cx="8" cy="8.6" r="3.1"/></svg>En su promedio o debajo</button>
    <button class="boton" type="button" data-p="suba" aria-pressed="false"><svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 2.5h11M8 14V6.2M4.8 9.4 8 6.2l3.2 3.2"/></svg>Subió fuerte</button>
    <button class="boton" type="button" data-p="recientes" aria-pressed="false">Cayeron fuerte hace poco</button>
    <button class="boton" type="button" data-p="maximos" aria-pressed="false">En zona de máximos</button>
    <button class="boton boton-texto" type="button" id="limpiar">Limpiar filtros</button>
  </div>
  <details class="mas" id="mas">
    <summary>Filtros por número <span class="mas-n" id="mas-n"></span><svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary>
    <div class="numeros">
      <div class="campo">
        <label for="mincaida">Cayó al menos</label>
        <span class="control"><input id="mincaida" type="number" inputmode="decimal" min="0" max="100" step="1" placeholder="Ej.: 30"><span class="unidad">%</span></span>
        <span class="ayuda">Desde su máximo histórico.</span>
      </div>
      <div class="campo">
        <label for="maxma">A menos de</label>
        <span class="control"><input id="maxma" type="number" inputmode="decimal" min="0" step="1" placeholder="Ej.: 5"><span class="unidad">%</span></span>
        <span class="ayuda">De su promedio de 200 semanas, por arriba o por debajo.</span>
      </div>
      <div class="campo">
        <label for="maxanios">Máximo hace menos de</label>
        <span class="control"><input id="maxanios" type="number" inputmode="decimal" min="0" step="1" placeholder="Ej.: 2"><span class="unidad">años</span></span>
        <span class="ayuda">Deja afuera a las que hace mucho no vuelven a su máximo.</span>
      </div>
    </div>
  </details>
  <p class="regla-activa" id="regla-activa" hidden></p>
  <div class="tabla-caja">
    <table class="tabla">
      <caption class="oculto">Empresas del S&amp;P 500 con su distancia al máximo, al promedio de 200 semanas, su variación en 12 meses y su patrón de precio</caption>
      <thead><tr>
        <th scope="col" class="c-emp" data-k="t"><button type="button">Empresa<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-sec" data-k="s"><button type="button">Sector<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-num c-pre" data-k="p"><button type="button">Precio (US$)<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-num c-da" data-k="da"><button type="button">Desde su máximo<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-num c-dm" data-k="dm"><button type="button">Vs. 200 semanas<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-num c-r" data-k="r"><button type="button">12 meses<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-fa" data-k="fa"><button type="button">Máximo<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
        <th scope="col" class="c-sg" data-k="sg"><button type="button">Patrón<svg class="ico flecha" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3.5M4.5 7 8 3.5 11.5 7"/></svg></button></th>
      </tr></thead>
      <tbody id="cuerpo"></tbody>
    </table>
  </div>
  <div class="ver-mas" id="ver-mas" hidden>
    <p id="ver-mas-txt"></p>
    <div class="ver-mas-acc">
      <button type="button" class="boton" id="ver-mas-btn"></button>
      <button type="button" class="boton boton-texto" id="ver-todas">Ver todas</button>
    </div>
  </div>
</section>

<section class="pie" aria-labelledby="t-pie">
  <h2 id="t-pie">Cómo leer esta página</h2>
  <div class="pie-grilla">
    <dl class="glosario">
      <div><dt>Desde su máximo</dt><dd>Cuánto le falta al precio para volver al mayor valor que alcanzó esa acción.</dd></div>
      <div><dt>Promedio de 200 semanas</dt><dd>El precio promedio de las últimas 200 semanas, casi cuatro años. La distancia del precio a ese promedio es lo que esta página llama temperatura: debajo del promedio, fría; muy por arriba, caliente.</dd></div>
      <div><dt>12 meses</dt><dd>Cuánto subió o bajó el precio en el último año.</dd></div>
      <div><dt>Máximo</dt><dd>Cuándo marcó su máximo. Permite distinguir una caída reciente de un precio que no volvió a ese nivel en muchos años.</dd></div>
      <div><dt>En su promedio o debajo</dt><dd id="def-c"></dd></div>
      <div><dt>Subió fuerte</dt><dd id="def-g"></dd></div>
    </dl>
    <div>
      <h3>Escala de temperatura</h3>
      <ul class="escala" id="escala"></ul>
      <h3>De dónde salen los datos</h3>
      <p class="fuente">Precios diarios de Yahoo Finance, sin ajustar por dividendos, en dólares. La lista de empresas del índice sale de Wikipedia y el tamaño de cada una (su valor en bolsa), de nasdaq.com. Los datos se actualizan de lunes a viernes, después del cierre de Nueva York. El gráfico de cada empresa es de TradingView y se carga solo cuando lo abrís.</p>
    </div>
  </div>
</section>

<dialog class="grafico" id="grafico" aria-labelledby="graf-tit">
  <div class="graf-cab">
    <h2 class="graf-tit" id="graf-tit"></h2>
    <div class="graf-int" role="group" aria-label="Velas">
      <button type="button" class="boton" data-int="D" aria-pressed="true">Diario</button>
      <button type="button" class="boton" data-int="W" aria-pressed="false">Semanal</button>
    </div>
    <a class="boton" id="graf-tv" target="_blank" rel="noopener">Abrir en TradingView<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M9.5 2.5h4v4M13.5 2.5 7.5 8.5M11.5 9.5v4h-9v-9h4"/></svg></a>
    <button type="button" class="boton" id="graf-cerrar" aria-label="Cerrar el gráfico"><svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>
  </div>
  <p class="graf-ind" id="graf-ind"></p>
  <div class="graf-caja" id="graf-caja"></div>
</dialog>
"""


JS = r"""
const D = __DATOS__;
const IDX = __INDICE__;
const R = __REGLAS__;
const HOY = new Date();

const $ = id => document.getElementById(id);
const PATRON = {c: "En su promedio o debajo", g: "Subió fuerte"};
const BANDAS = ["Muy frío", "Frío", "Fresco", "Templado", "Cálido", "Caluroso", "Muy caluroso"];
const ICO = {
  c: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 12.5h13"/><circle cx="8" cy="8.6" r="3.1"/></svg>',
  g: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 2.5h11M8 14V6.2M4.8 9.4 8 6.2l3.2 3.2"/></svg>',
  graf: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 2.5v11h11M5 10.5l2.5-3 2.2 1.8 3.3-4.3"/></svg>',
  ext: '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M9.5 2.5h4v4M13.5 2.5 7.5 8.5M11.5 9.5v4h-9v-9h4"/></svg>',
};

// La banda templada es la misma de la regla "En su promedio o debajo"
function banda(v) {
  if (v === null) return -1;
  if (v < -50) return 0;
  if (v < -20) return 1;
  if (v < -R.cb) return 2;
  if (v <= R.cb) return 3;
  if (v <= 20) return 4;
  if (v <= 50) return 5;
  return 6;
}
const RANGOS = ["Más de 50% debajo", "Entre 20% y 50% debajo", "Entre " + R.cb + "% y 20% debajo",
  "A menos de " + R.cb + "%", "Entre " + R.cb + "% y 20% arriba", "Entre 20% y 50% arriba", "Más de 50% arriba"];

D.forEach((r, i) => {
  r.i = i;
  r.an = (HOY - new Date(r.fa)) / 31557600000;
  r.b = banda(r.dm);
  r.k = Math.max(0, Math.min(19, Math.floor((100 + r.da) / 5)));
});

// Nombres y sectores vienen de Wikipedia, que edita cualquiera
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";");
}
function num(v, dec) {
  const x = Number(v.toFixed(dec));
  return (x === 0 ? 0 : x).toLocaleString("es-AR", {minimumFractionDigits: dec, maximumFractionDigits: dec})
    .replace("-", "−");
}
function pct(v, dec) {
  return (Number(v.toFixed(dec)) > 0 ? "+" : "") + num(v, dec) + "%";
}
function abs(v, dec) {
  return num(Math.abs(v), dec) + "%";
}
function hace(an) {
  if (an >= 1) {
    const a = Math.floor(an);
    return "hace " + a + (a === 1 ? " año" : " años");
  }
  const m = Math.floor(an * 12);
  return m < 1 ? "este mes" : "hace " + m + (m === 1 ? " mes" : " meses");
}
function fechaLarga(iso) {
  const [a, m, d] = iso.split("-");
  return d + "/" + m + "/" + a;
}

/* ---------- reglas ---------- */
const reglaC = "hasta " + R.cb + "% arriba de su promedio de 200 semanas o por debajo, con máximo hace " +
  R.ca + " años o menos y el promedio subiendo";
const reglaG = "subió " + R.g12 + "% o más en 12 meses y sigue a menos de " + R.gc + "% de su máximo";
$("def-c").textContent = "El precio no está más de " + R.cb + "% arriba de su promedio de 200 semanas " +
  "(puede estar por debajo, sin límite), marcó su " +
  "máximo histórico hace " + R.ca + " años o menos y ese promedio es más alto que hace " +
  Math.round(R.cs / 4.345) + " meses.";
$("def-g").textContent = "El precio subió " + R.g12 + "% o más en los últimos 12 meses y está a menos de " +
  R.gc + "% de su máximo histórico.";

/* ---------- lecturas ---------- */
const conMA = D.filter(r => r.dm !== null);
const arriba = conMA.filter(r => r.dm >= 0).length;
const parte = conMA.length ? Math.round(arriba / conMA.length * 100) : 0;
$("k-amp-val").textContent = parte + "%";
$("k-amp-sub").textContent = arriba + " de " + conMA.length + " empresas" +
  (D.length > conMA.length ? " · " + (D.length - conMA.length) + " sin 200 semanas de historia" : "");

const caidas = D.map(r => r.da).sort((a, b) => a - b);
const mediana = caidas[Math.floor(caidas.length / 2)];
$("resumen").innerHTML = "La mitad de las " + D.length + " empresas está <b>" + abs(mediana, 0) +
  "</b> o más debajo de su máximo histórico.";

if (IDX) {
  $("k-idx-val").textContent = pct(IDX.da, 1);
  let sub = num(IDX.p, 0) + " puntos";
  if (IDX.dm !== null) {
    const b = banda(IDX.dm);
    $("k-idx-cond").innerHTML = "<span class='sw b" + b + "'></span>" + BANDAS[b];
    sub += " · " + abs(IDX.dm, 0) + (IDX.dm >= 0 ? " arriba" : " debajo") + " de su promedio de 200 semanas";
  }
  if (IDX.r !== null) sub += " · " + pct(IDX.r, 0) + " en 12 meses";
  $("k-idx-sub").innerHTML = sub;
} else {
  $("k-idx").hidden = true;
}

function prueba(filas) {
  if (!filas.length) return "Hoy ninguna empresa cumple este patrón.";
  const tk = filas.slice(0, 3).map(r => r.t).join(", ");
  return filas.length > 3 ? tk + " y " + (filas.length - 3) + " más" : tk;
}
const listaC = D.filter(r => r.sg === "c").sort((a, b) => a.da - b.da);
const listaG = D.filter(r => r.sg === "g").sort((a, b) => b.r - a.r);
$("k-c-nom").insertAdjacentHTML("afterbegin", ICO.c);
$("k-g-nom").insertAdjacentHTML("afterbegin", ICO.g);
$("k-c-val").textContent = listaC.length;
$("k-g-val").textContent = listaG.length;
$("k-c-sub").textContent = prueba(listaC);
$("k-g-sub").textContent = prueba(listaG);

/* ---------- leyenda y escala ---------- */
const porBanda = new Array(7).fill(0);
conMA.forEach(r => porBanda[r.b]++);
const RANGOS_CORTOS = ["< −50%", "−50 a −20%", "−20 a −" + R.cb + "%", "±" + R.cb + "%", "+" + R.cb + " a +20%", "+20 a +50%", "> +50%"];
$("leyenda").innerHTML = BANDAS.map((n, b) =>
  "<li><span class='sw b" + b + "'></span>" + n + " <small>" + RANGOS_CORTOS[b] + "</small></li>").join("");
$("escala").innerHTML = BANDAS.map((n, b) =>
  "<li><span class='sw b" + b + "'></span><span>" + n + "</span><small>" + RANGOS[b] +
  "</small><span class='n'>" + porBanda[b] + " hoy</span></li>").join("") +
  "<li><span class='sw bx'></span><span>Sin dato</span><small>Menos de 200 semanas de historia</small><span class='n'>" +
  (D.length - conMA.length) + " hoy</span></li>";

/* ---------- franja térmica ---------- */
const franjaOrden = conMA.slice().sort((a, b) => a.dm - b.dm);
const N = franjaOrden.length;
const franjaSvg = $("franja-svg");
const zona = $("franja");
const lectura = $("lectura");
const LECTURA_INICIAL = lectura.textContent;
franjaSvg.setAttribute("viewBox", "0 0 " + N + " 1");
franjaSvg.innerHTML = franjaOrden.map((r, j) =>
  "<rect x='" + j + "' width='1.08' height='1' class='b" + r.b + "'/>").join("");
const marcasFranja = [];
[...franjaSvg.children].forEach((el, j) => { marcasFranja[franjaOrden[j].i] = el; });

const corte = N ? (N - arriba) / N * 100 : 50;
$("franja-prom").style.left = corte + "%";
$("eje-prom").style.left = corte + "%";
// las puntas del eje se esconden si chocan con la marca del promedio
function acomodarEje() {
  const p = $("eje-prom").getBoundingClientRect();
  ["eje-izq", "eje-der"].forEach(id => {
    const e = $(id);
    e.style.visibility = "";
    const c = e.getBoundingClientRect();
    if (c.right > p.left - 10 && c.left < p.right + 10) e.style.visibility = "hidden";
  });
}
acomodarEje();
addEventListener("resize", acomodarEje);
const dfranja = $("dfranja");
const paneles = document.querySelector(".paneles");
function plegar() {
  if (paneles) paneles.hidden = !dfranja.open;
  if (dfranja.open) acomodarEje();
}
dfranja.addEventListener("toggle", plegar);
plegar();
if (document.fonts) document.fonts.ready.then(acomodarEje);
zona.setAttribute("aria-valuemax", N);

let cursor = -1;
function leer(j) {
  if (!N) return;
  cursor = Math.max(0, Math.min(N - 1, j));
  const r = franjaOrden[cursor];
  $("franja-cursor").style.left = ((cursor + 0.5) / N * 100) + "%";
  zona.parentNode.classList.add("leyendo-ya");
  const texto = abs(r.dm, 0) + (r.dm >= 0 ? " arriba" : " debajo") + " de su promedio · " + BANDAS[r.b].toLowerCase();
  lectura.innerHTML = "<b>" + esc(r.t) + "</b> " + esc(r.n) + " · " + texto;
  const ancho = zona.clientWidth, w = lectura.offsetWidth;
  const x = (cursor + 0.5) / N * ancho - w / 2;
  lectura.style.left = Math.max(0, Math.min(ancho - w, x)) + "px";
  zona.setAttribute("aria-valuenow", cursor + 1);
  zona.setAttribute("aria-valuetext", r.t + ", " + r.n + ": " + texto);
}
function soltar() {
  zona.parentNode.classList.remove("leyendo-ya");
  lectura.textContent = LECTURA_INICIAL;
  lectura.style.left = "0px";
}
function posicion(e) {
  const caja = zona.getBoundingClientRect();
  leer(Math.floor((e.clientX - caja.left) / caja.width * N));
}
zona.addEventListener("pointerdown", e => {
  if (e.pointerType !== "mouse") zona.setPointerCapture(e.pointerId);
  posicion(e);
});
zona.addEventListener("pointermove", e => {
  if (e.pointerType === "mouse" || zona.hasPointerCapture(e.pointerId)) posicion(e);
});
zona.addEventListener("pointerleave", e => { if (e.pointerType === "mouse") soltar(); });
zona.addEventListener("blur", soltar);
zona.addEventListener("keydown", e => {
  const pasos = {ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 10, PageDown: -10};
  let j = cursor < 0 ? N - arriba : cursor;
  if (e.key in pasos) j += pasos[e.key];
  else if (e.key === "Home") j = 0;
  else if (e.key === "End") j = N - 1;
  else return;
  e.preventDefault();
  leer(j);
});

/* ---------- sectores ---------- */
const sel = $("sec");
const sectores = [...new Set(D.map(r => r.s))].sort((a, b) => a.localeCompare(b, "es"));
const infoSec = sectores.map(s => {
  const filas = D.filter(r => r.s === s);
  const cm = filas.filter(r => r.dm !== null).sort((a, b) => a.dm - b.dm);
  const ar = cm.filter(r => r.dm >= 0).length;
  return {s, n: filas.length, cm, parte: cm.length ? ar / cm.length : 0};
});
infoSec.forEach(x => {
  const o = document.createElement("option");
  o.value = x.s; o.textContent = x.s + " (" + x.n + ")";
  sel.appendChild(o);
});
infoSec.sort((a, b) => b.parte - a.parte);
$("sectores").innerHTML = infoSec.map(x => {
  const p = Math.round(x.parte * 100);
  return "<li><button type='button' class='sector' data-s='" + esc(x.s) + "' aria-pressed='false'" +
    " aria-label='" + esc(x.s) + ": " + x.n + " empresas, " + p + "% arriba de su promedio. Filtrar la lista por este sector.'>" +
    "<span class='sector-nom'>" + esc(x.s) + "<span class='sector-n'>" + x.n + "</span></span>" +
    "<svg class='sector-franja' viewBox='0 0 " + Math.max(1, x.cm.length) + " 1' preserveAspectRatio='none' aria-hidden='true'>" +
    x.cm.map((r, j) => "<rect x='" + j + "' width='1.08' height='1' class='b" + r.b + "'/>").join("") + "</svg>" +
    "<span class='sector-pct'>" + p + "%<span class='sector-arr'> arriba</span></span></button></li>";
}).join("");
const marcasSector = [];
document.querySelectorAll(".sector").forEach((b, n) => {
  [...b.querySelector("svg").children].forEach((el, j) => { marcasSector[infoSec[n].cm[j].i] = el; });
  b.addEventListener("click", () => {
    sel.value = sel.value === b.dataset.s ? "" : b.dataset.s;
    pintar();
  });
});

/* ---------- histograma de caídas ---------- */
const CUBOS = 20;
const totalCubo = new Array(CUBOS).fill(0);
D.forEach(r => totalCubo[r.k]++);
const topeCubo = Math.max(...totalCubo);
const histo = $("histo");
histo.innerHTML = totalCubo.map((c, k) => {
  const desde = -100 + k * 5, hasta = desde + 5;
  const etiqueta = c + (c === 1 ? " empresa" : " empresas") + " con una caída de entre " + Math.abs(hasta) +
    "% y " + Math.abs(desde) + "% desde su máximo. " +
    (hasta === 0 ? "Mostrar todas." : "Mostrar las que cayeron al menos " + Math.abs(hasta) + "%.");
  return "<button type='button' class='barra' data-k='" + k + "' aria-label='" + etiqueta + "'>" +
    "<span class='barra-total' style='height:" + (c / topeCubo * 100) + "%'></span>" +
    "<span class='barra-pila'></span></button>";
}).join("");
const barras = [...histo.children];
const tip = $("tip");
let filtradoCubo = totalCubo.slice();
function verTip(b) {
  const k = +b.dataset.k, desde = -100 + k * 5, hasta = desde + 5;
  const c = totalCubo[k];
  tip.textContent = c + (c === 1 ? " empresa" : " empresas") + " entre " + num(desde, 0) + "% y " + num(hasta, 0) +
    "% de su máximo" + (filtradoCubo[k] !== c ? " · " + filtradoCubo[k] + " con los filtros actuales" : "");
  tip.classList.add("ver");
  const panel = histo.parentNode.getBoundingClientRect();
  const caja = b.getBoundingClientRect();
  const x = caja.left - panel.left + caja.width / 2 - tip.offsetWidth / 2;
  tip.style.left = Math.max(8, Math.min(panel.width - tip.offsetWidth - 8, x)) + "px";
  tip.style.top = (histo.offsetTop - tip.offsetHeight - 6) + "px";
}
barras.forEach(b => {
  b.addEventListener("pointerenter", () => verTip(b));
  b.addEventListener("pointerleave", () => tip.classList.remove("ver"));
  b.addEventListener("focus", () => verTip(b));
  b.addEventListener("blur", () => tip.classList.remove("ver"));
  b.addEventListener("click", () => {
    const v = String(Math.abs(-100 + (+b.dataset.k + 1) * 5));
    $("mincaida").value = $("mincaida").value === v ? "" : v;
    pintar();
    verTip(b);
  });
});

/* ---------- orden ---------- */
// Si no llegó la capitalización, la tabla arranca por caída como antes
const HAY_TAMANO = D.some(r => r.mc);
D.filter(r => r.mc).sort((a, b) => b.mc - a.mc).forEach((r, i) => { r.rk = i + 1; });
const ORDEN_INICIAL = HAY_TAMANO ? ["mc", false] : ["da", true];
const ORDENES = [
  ...(HAY_TAMANO ? [["mc", false, "Más grandes primero"]] : []),
  ["da", true, "Más lejos de su máximo"],
  ["da", false, "Más cerca de su máximo"],
  ["dm", true, "Más debajo de su 200 semanal"],
  ["dm", false, "Más arriba de su 200 semanal"],
  ["r", false, "Lo que más subió en 12 meses"],
  ["r", true, "Lo que más bajó en 12 meses"],
  ["fa", false, "Máximo más reciente"],
  ["fa", true, "Máximo más antiguo"],
  ["t", true, "Ticker, de la A a la Z"],
  ["s", true, "Sector, de la A a la Z"],
  ["p", false, "Precio más alto"],
  ["sg", true, "Con patrón primero"],
];
const selOrden = $("orden");
selOrden.innerHTML = ORDENES.map(o => "<option value='" + o[0] + ":" + (o[1] ? "a" : "d") + "'>" + o[2] + "</option>").join("");
const PRIMERO_ASC = {t: true, s: true, da: true, dm: true, sg: true, p: false, r: false, fa: false, mc: false};
let [orden, asc] = ORDEN_INICIAL, preset = "", patron = "";
const abiertas = new Set();

// La lista se muestra de a tramos; vuelve al primero cuando cambia un filtro o el orden
const PAGINA = 25;
let visibles = PAGINA, firmaLista = "";

/* ---------- lista ---------- */
function filtrar() {
  const q = $("q").value.trim().toUpperCase();
  const s = sel.value;
  const minc = parseFloat($("mincaida").value);
  const maxm = parseFloat($("maxma").value);
  const maxa = parseFloat($("maxanios").value);
  return D.filter(r => {
    if (q && !(r.t.includes(q) || r.n.toUpperCase().includes(q))) return false;
    if (s && r.s !== s) return false;
    if (patron && r.sg !== patron) return false;
    if (!isNaN(minc) && r.da > -Math.abs(minc)) return false;
    if (!isNaN(maxa) && r.an > maxa) return false;
    if (!isNaN(maxm)) {
      if (r.dm === null) return false;
      if (Math.abs(r.dm) > Math.abs(maxm)) return false;
    }
    return true;
  });
}

// mc viene en millones de dólares; un billón son un millón de millones
function valorBolsa(mc) {
  return mc >= 1e6 ? "US$ " + num(mc / 1e6, 2) + " billones" : "US$ " + num(mc, 0) + " millones";
}

function detalle(r) {
  const p = [];
  let t = "<b>" + esc(r.t) + "</b> (" + esc(r.n) + ") cotiza a US$ " + num(r.p, 2) + ". ";
  t += r.da > -0.5
    ? "Está en su máximo histórico o muy cerca: US$ " + num(r.a, 2) + ", del " + fechaLarga(r.fa) + "."
    : "Está " + abs(r.da, 1) + " debajo de su máximo histórico de US$ " + num(r.a, 2) + ", que marcó el " +
      fechaLarga(r.fa) + " (" + hace(r.an) + ").";
  if (r.rk) t += " Es la número " + r.rk + " del índice por tamaño: vale " + valorBolsa(r.mc) + " en bolsa.";
  p.push(t);
  let u = r.dm === null
    ? "No tiene 200 semanas de historia para calcular su promedio."
    : "Cotiza " + abs(r.dm, 1) + (r.dm >= 0 ? " arriba" : " debajo") + " de su promedio de 200 semanas (US$ " +
      num(r.m, 2) + "): " + BANDAS[r.b].toLowerCase() + ".";
  u += r.r === null ? " No tiene un año de historia." : " En 12 meses " + (r.r >= 0 ? "subió " : "bajó ") + abs(r.r, 1) + ".";
  p.push(u);
  if (r.sg) p.push("Cumple el patrón <b>" + PATRON[r.sg] + "</b>: " + (r.sg === "c" ? reglaC : reglaG) +
    ". Es un dato sobre el precio, no una recomendación.");
  const acc = "<div class='det-acc'>" +
    "<button type='button' class='boton' data-graf='" + esc(r.t) + "'>" + ICO.graf + "Ver gráfico con indicadores</button>" +
    "<a class='boton' href='" + esc(urlTV(r)) + "' target='_blank' rel='noopener'>Abrir en TradingView" + ICO.ext + "</a></div>";
  return "<tr class='detalle'><td colspan='8'>" + p.map(x => "<p>" + x + "</p>").join("") + acc + "</td></tr>";
}

// Gráfico de TradingView: se pide recién cuando alguien lo abre
function ma(n) {
  return {id: "MASimple@tv-basicstudies", inputs: {length: n}};
}
const VELAS = {
  D: {texto: "Velas diarias con promedios de 20, 50 y 200 días, volumen, RSI y MACD.",
      estudios: [ma(20), ma(50), ma(200), {id: "RSI@tv-basicstudies"}, {id: "MACD@tv-basicstudies"}]},
  W: {texto: "Velas semanales con promedios de 50 y 200 semanas (el de la tabla), volumen, RSI y MACD.",
      estudios: [ma(50), ma(200), {id: "RSI@tv-basicstudies"}, {id: "MACD@tv-basicstudies"}]},
};
function simboloTV(r) {
  const s = r.t.replace(/-/g, ".");
  return r.x ? r.x + ":" + s : s;
}
function urlTV(r) {
  return "https://www.tradingview.com/chart/?symbol=" + encodeURIComponent(simboloTV(r));
}

const dlg = $("grafico");
let grafR = null;
function cargarGrafico(velas) {
  dlg.querySelectorAll("[data-int]").forEach(b => b.setAttribute("aria-pressed", b.dataset.int === velas));
  $("graf-ind").textContent = VELAS[velas].texto + " Podés sumar otros desde «Indicadores».";
  const caja = $("graf-caja");
  caja.innerHTML = "<div class='tradingview-widget-container'><div class='tradingview-widget-container__widget'></div></div>";
  const oscuro = Mercadito.oscuroAhora();
  const s = document.createElement("script");
  s.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
  s.async = true;
  s.textContent = JSON.stringify({
    autosize: true, symbol: simboloTV(grafR), interval: velas, timezone: "America/New_York",
    theme: oscuro ? "dark" : "light", backgroundColor: oscuro ? "#171B21" : "#FFFFFF",
    style: "1", locale: "es", allow_symbol_change: false, hide_side_toolbar: innerWidth < 900,
    studies: VELAS[velas].estudios, support_host: "https://www.tradingview.com",
  });
  caja.firstChild.appendChild(s);
}
function abrirGrafico(r) {
  grafR = r;
  $("graf-tit").innerHTML = esc(r.t) + "<small>" + esc(r.n) + "</small>";
  $("graf-tv").href = urlTV(r);
  dlg.showModal();
  cargarGrafico("D");
}
dlg.querySelectorAll("[data-int]").forEach(b => b.addEventListener("click", () => cargarGrafico(b.dataset.int)));
$("graf-cerrar").addEventListener("click", () => dlg.close());
dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
dlg.addEventListener("close", () => { $("graf-caja").innerHTML = ""; });

function fila(r) {
  const abierta = abiertas.has(r.t);
  return "<tr class='fila' data-t='" + esc(r.t) + "'>" +
    "<td class='c-emp'><button type='button' class='abrir' aria-expanded='" + abierta + "'>" +
      "<span class='tk'>" + esc(r.t) + "</span><span class='nom'>" + esc(r.n) + "</span></button></td>" +
    "<td class='c-sec'>" + esc(r.s) + "</td>" +
    "<td class='c-num c-pre'>" + num(r.p, 2) + "</td>" +
    "<td class='c-num c-da'>" + pct(r.da, 1) + "</td>" +
    "<td class='c-num c-dm'>" + (r.dm === null ? "<span class='nd'>sin dato</span>"
      : "<span class='sw b" + r.b + "' aria-hidden='true'></span><span class='m-et'>prom. </span>" + pct(r.dm, 0) + "<span class='oculto'>, " + BANDAS[r.b].toLowerCase() + "</span>") + "</td>" +
    "<td class='c-num c-r'>" + (r.r === null ? "<span class='nd'>sin dato</span>" : "<span class='m-et'>12m </span>" + pct(r.r, 0)) + "</td>" +
    "<td class='c-fa'><span class='m-et'>máx. </span>" + r.fa.slice(0, 4) + "<span class='fa-hace'> · " + hace(r.an) + "</span></td>" +
    "<td class='c-sg'>" + (r.sg ? "<span class='patron' title='" + PATRON[r.sg] + "'>" + ICO[r.sg] + "<span class='patron-txt'>" + PATRON[r.sg] + "</span></span>" : "") + "</td>" +
    "</tr>" + (abierta ? detalle(r) : "");
}

function hayFiltros() {
  return !!($("q").value.trim() || sel.value || patron || preset ||
    $("mincaida").value || $("maxma").value || $("maxanios").value);
}

function pintar() {
  const f = filtrar();
  f.sort((a, b) => {
    const x = a[orden], y = b[orden];
    if (x === y) return 0;
    if (x === null) return 1;
    if (y === null) return -1;
    if (typeof x === "string") return asc ? x.localeCompare(y) : y.localeCompare(x);
    return asc ? x - y : y - x;
  });

  const nombreOrden = ORDENES.find(o => o[0] === orden && o[1] === asc);
  $("cuenta").innerHTML = (f.length === D.length ? "<b>" + f.length + "</b> empresas"
    : "<b>" + f.length + "</b> de " + D.length + " empresas") +
    (nombreOrden ? " · " + nombreOrden[2].toLowerCase() : "");

  const firma = [$("q").value.trim().toUpperCase(), sel.value, patron, $("mincaida").value,
    $("maxma").value, $("maxanios").value, orden, asc].join("|");
  if (firma !== firmaLista) {
    firmaLista = firma;
    visibles = PAGINA;
  }
  const muestra = f.slice(0, visibles);
  $("cuerpo").innerHTML = f.length === 0
    ? "<tr class='vacio'><td colspan='8'>Ninguna empresa cumple con estos filtros.<br>" +
      "<button type='button' class='boton' id='limpiar-vacio'>Limpiar filtros</button></td></tr>"
    : muestra.map(fila).join("");
  const resto = f.length - muestra.length;
  $("ver-mas").hidden = resto <= 0;
  if (resto > 0) {
    $("ver-mas-txt").textContent = "Mostrando " + muestra.length + " de " + f.length + " empresas";
    $("ver-mas-btn").textContent = "Mostrar " + Math.min(PAGINA, resto) + " más";
  }
  const lv = $("limpiar-vacio");
  if (lv) lv.addEventListener("click", () => aplicarPreset("limpiar"));

  // la franja, los sectores y el histograma muestran qué parte del mercado queda en la lista
  const filtrando = hayFiltros();
  const dentro = new Uint8Array(D.length);
  f.forEach(r => { dentro[r.i] = 1; });
  conMA.forEach(r => {
    const off = filtrando && !dentro[r.i];
    marcasFranja[r.i].classList.toggle("off", off);
    if (marcasSector[r.i]) marcasSector[r.i].classList.toggle("off", off);
  });
  filtradoCubo = new Array(CUBOS).fill(0);
  const pilas = Array.from({length: CUBOS}, () => new Array(8).fill(0));
  f.forEach(r => { filtradoCubo[r.k]++; pilas[r.k][r.b + 1]++; });
  barras.forEach((b, k) => {
    const pila = b.lastChild;
    pila.style.height = (filtradoCubo[k] / topeCubo * 100) + "%";
    pila.innerHTML = pilas[k].map((c, j) => c ? "<i class='" + (j ? "b" + (j - 1) : "bx") + "' style='flex:" + c + "'></i>" : "").join("");
  });

  document.querySelectorAll(".sector").forEach(b => b.setAttribute("aria-pressed", b.dataset.s === sel.value));
  const nNum = ["mincaida", "maxma", "maxanios"].filter(id => $(id).value !== "").length;
  $("mas-n").textContent = nNum || "";
  $("limpiar").disabled = !filtrando;
  selOrden.value = orden + ":" + (asc ? "a" : "d");

  const ra = $("regla-activa");
  const textos = {
    promedio: ICO.c + "<span><b>En su promedio o debajo:</b> " + reglaC + ". Es un dato sobre el precio, no una recomendación.</span>",
    suba: ICO.g + "<span><b>Subió fuerte:</b> " + reglaG + ". Ordenadas de la que más subió a la que menos.</span>",
    recientes: "<span><b>Cayeron fuerte hace poco:</b> cayeron 30% o más desde un máximo que marcaron hace menos de 2 años.</span>",
    maximos: "<span><b>En zona de máximos:</b> todas las empresas, de la más cerca de su máximo a la más lejos.</span>",
  };
  ra.hidden = !preset;
  ra.innerHTML = preset ? textos[preset] : "";
}

function marcarOrden() {
  document.querySelectorAll(".tabla th").forEach(th => {
    if (th.dataset.k === orden) th.setAttribute("aria-sort", asc ? "ascending" : "descending");
    else th.removeAttribute("aria-sort");
  });
}

document.querySelectorAll(".tabla th").forEach(th => {
  th.querySelector("button").addEventListener("click", () => {
    const k = th.dataset.k;
    asc = orden === k ? !asc : PRIMERO_ASC[k];
    orden = k;
    marcarOrden();
    pintar();
  });
});
selOrden.addEventListener("change", () => {
  const [k, d] = selOrden.value.split(":");
  orden = k; asc = d === "a";
  marcarOrden();
  pintar();
});

$("cuerpo").addEventListener("click", e => {
  const g = e.target.closest("[data-graf]");
  if (g) {
    abrirGrafico(D.find(r => r.t === g.dataset.graf));
    return;
  }
  const tr = e.target.closest("tr.fila");
  if (!tr) return;
  const t = tr.dataset.t;
  if (abiertas.has(t)) abiertas.delete(t); else abiertas.add(t);
  pintar();
  const b = $("cuerpo").querySelector("tr[data-t='" + t + "'] .abrir");
  if (b && e.target.closest(".abrir")) b.focus();
});

const PRESETS = {
  promedio: {patron: "c"},
  suba: {patron: "g", orden: "r", asc: false},
  recientes: {mincaida: 30, maxanios: 2},
  maximos: {orden: "da", asc: false},
};

function aplicarPreset(p) {
  const quitar = p === "limpiar" || p === preset;
  $("mincaida").value = ""; $("maxma").value = ""; $("maxanios").value = "";
  preset = ""; patron = ""; [orden, asc] = ORDEN_INICIAL;
  if (quitar) {
    $("q").value = ""; sel.value = "";
  } else {
    const c = PRESETS[p];
    preset = p;
    patron = c.patron || "";
    if (c.mincaida) $("mincaida").value = c.mincaida;
    if (c.maxanios) $("maxanios").value = c.maxanios;
    if (c.orden) { orden = c.orden; asc = c.asc; }
  }
  document.querySelectorAll("[data-p]").forEach(b => b.setAttribute("aria-pressed", b.dataset.p === preset));
  marcarOrden();
  pintar();
}

document.querySelectorAll("[data-p]").forEach(b => {
  b.addEventListener("click", () => {
    aplicarPreset(b.dataset.p);
    if (b.classList.contains("lect-boton") && preset) {
      $("empresas").scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"});
    }
  });
});
$("limpiar").addEventListener("click", () => aplicarPreset("limpiar"));

// Al cargar más, el foco va a la primera empresa nueva para seguir con el teclado
function mostrarMas(todas) {
  const desde = visibles;
  visibles = todas ? D.length : visibles + PAGINA;
  pintar();
  const nueva = $("cuerpo").querySelectorAll("tr.fila .abrir")[desde];
  if (nueva) nueva.focus({preventScroll: true});
}
$("ver-mas-btn").addEventListener("click", () => mostrarMas(false));
$("ver-todas").addEventListener("click", () => mostrarMas(true));

["q", "sec", "mincaida", "maxma", "maxanios"].forEach(id => {
  $(id).addEventListener("input", pintar);
  $(id).addEventListener("change", pintar);
});

function medirTabla() {
  const caja = document.querySelector(".tabla-caja");
  caja.classList.remove("desborda");
  caja.classList.toggle("desborda", document.querySelector(".tabla").offsetWidth > caja.clientWidth + 1);
}
addEventListener("resize", medirTabla);
if (document.fonts) document.fonts.ready.then(medirTabla);

if (matchMedia("(min-width: 900px)").matches) $("mas").open = true;
marcarOrden();
pintar();
medirTabla();
"""


def generar():
    """Escribe sp500/index.html y devuelve el resumen para el inicio. Si los
    datos no alcanzan, corta con error y deja la pagina anterior."""
    empresas = lista_sp500()
    print(f"{len(empresas)} empresas en la lista")

    datos = bajar_diario([e["ticker"] for e in empresas] + [INDICE])
    if not datos:
        raise RuntimeError("Yahoo no devolvio ningun dato. No se publica.")

    filas, fecha_datos, afuera = calcular(empresas, datos)
    print(f"{len(filas)} con datos utiles")
    if afuera:
        print(f"Quedaron afuera {len(afuera)}: " + ", ".join(afuera[:20]))
    if len(filas) < MINIMO:
        raise RuntimeError(f"Solo {len(filas)} empresas con datos (minimo {MINIMO}). No se publica.")

    mercados = bolsas()
    capitalizaciones = tamanos()
    for f in filas:
        f["x"] = mercados.get(f["t"].replace("-", "."))
        mc = capitalizaciones.get(f["t"].replace("-", "/"))
        f["mc"] = round(mc / 1e6) if mc else None  # en millones de US$
    sin_bolsa = [f["t"] for f in filas if not f["x"]]
    if sin_bolsa:
        print(f"Sin bolsa para TradingView {len(sin_bolsa)}: " + ", ".join(sin_bolsa[:20]))
    sin_tamano = [f["t"] for f in filas if f["mc"] is None]
    if sin_tamano:
        print(f"Sin capitalizacion {len(sin_tamano)}: " + ", ".join(sin_tamano[:20]))

    indice = medir(datos[INDICE], fecha_datos) if INDICE in datos else None
    if indice is None:
        print(f"Sin datos de {INDICE}: la pagina sale sin el recuadro del indice")
    reglas = {
        "cb": PROMEDIO_BANDA,
        "ca": PROMEDIO_ANIOS,
        "cs": PROMEDIO_PENDIENTE,
        "g12": SUBA_12M,
        "gc": SUBA_CERCA,
    }

    cuerpo = CUERPO.replace("__FECHA__", texto_fecha(fecha_datos))
    js = JS.replace("__INDICE__", a_json(indice))
    js = js.replace("__REGLAS__", a_json(reglas))
    js = js.replace("__DATOS__", a_json(filas))
    comun.escribir("sp500", comun.pagina(
        "sp500", "S&P 500",
        "Las empresas del S&P 500 según cuánto les falta para volver a su máximo, qué tan lejos están de su "
        "promedio de 200 semanas y cuánto cambiaron en 12 meses. Datos sobre el precio, no recomendaciones.",
        cuerpo, css=CSS, js=js,
        fuentes="Precios: Yahoo Finance. Lista del índice: Wikipedia. Tamaño de cada empresa: nasdaq.com. Gráficos: TradingView.",
    ))

    con_ma = [f for f in filas if f["dm"] is not None]
    return {
        "actualizado": comun.sello(),
        "datos_al": fecha_datos.date().isoformat(),
        "indice": indice and {k: indice[k] for k in ("p", "da", "dm", "r")},
        "empresas": len(filas),
        "arriba_200s": round(100 * sum(f["dm"] >= 0 for f in con_ma) / len(con_ma)) if con_ma else None,
        "en_promedio": sum(f["sg"] == "c" for f in filas),
        "subio_fuerte": sum(f["sg"] == "g" for f in filas),
    }
