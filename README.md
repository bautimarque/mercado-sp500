# Mercadito

Dólar, tasas, acciones y bonos de Argentina y Estados Unidos en un solo lugar.
Datos para mirar el mercado, no recomendaciones.

**Ver la página:** https://bautimarque.github.io/mercado-sp500/

## Secciones

| Sección | Qué muestra | Se actualiza |
|---|---|---|
| **Inicio** | Los números clave de cada sección, con su fecha | Con cada sección |
| **Dólar** | Todos los tipos de cambio, brecha, historia de 2 años, banda cambiaria del BCRA, precio en cada banco, billetera y broker, calculadora | Cada 30 min |
| **Gastos en US$** | Calculadora de cuánto se paga en pesos un juego, una suscripción o un gasto en el exterior, en pesos o con dólares propios, con los impuestos vigentes | Cada 30 min |
| **Tasas** | Plazo fijo en cada entidad (con calculadora y comparación con la inflación), fondos money market, inflación y referencias del BCRA | Cada 30 min |
| **Merval** | El índice y sus principales acciones en pesos y en dólares contado con liqui | Cada 30 min |
| **S&P 500** | Las ~500 empresas: distancia al máximo, al promedio de 200 semanas, 12 meses, patrones de precio y gráfico de TradingView | 18:30 |
| **Bonos** | Riesgo país, soberanos en dólares, letras del Tesoro y obligaciones negociables | Cada 30 min |

"Cada 30 min" es de lunes a viernes entre las 10 y las 17:30 de Argentina. A las
18:30 se actualiza todo. **Cómo se calcula** (`metodologia/`) explica cada dato y
su fuente; **Aviso legal** (`legal/`) aclara qué es y qué no es el sitio.

## Patrones de precio (S&P 500)

Son descripciones del precio calculadas con reglas fijas. No son
recomendaciones ni sugieren operar.

- **En su promedio o debajo**: el precio está como máximo 5% arriba de su
  promedio de 200 semanas (puede estar por debajo, sin límite), el máximo
  histórico es de los últimos 2 años y ese promedio es más alto que hace 6 meses.
- **Subió fuerte**: el precio subió 50% o más en los últimos 12 meses y está a
  menos de 10% de su máximo histórico.

## Cómo está armado

```
generar.py              arma el sitio: todo, "rapido" o secciones sueltas
mercadito/comun.py      menú, pie, aviso legal y lectura de fuentes
mercadito/<seccion>.py  datos, cuentas y página de cada sección
mercadito/inicio.py     el tablero del inicio
mercadito/fijas.py      "Cómo se calcula" y "Aviso legal"
assets/base.css         estilos compartidos
assets/base.js          modo claro/oscuro, formatos y gráfico de líneas
datos/<seccion>.json    resumen de cada sección para el inicio
```

Las páginas son archivos estáticos con los datos ya calculados adentro. Lo
único externo que se carga es el gráfico de TradingView, y recién cuando
alguien lo abre.

Cada sección es independiente: si una fuente falla, las demás se publican
igual y esa sección queda con su última versión. El bot de GitHub Actions
(`.github/workflows/pagina.yml`) termina en error para que GitHub avise.

### Fuentes

dolarapi.com, comparadolar.ar, argentinadatos.com, API del BCRA, Yahoo Finance
(yfinance), Wikipedia, Nasdaq (directorio de símbolos y buscador), data912.com
y TradingView. Son servicios de terceros, gratuitos y sin garantía; data912.com
es un proyecto con fines educativos. Antes de cualquier uso comercial hay que
revisar los términos de cada uno.

### Correrlo en local

```
python -m venv .venv
.venv\Scripts\activate          # en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python generar.py               # todo (~1,5 minutos)
python generar.py rapido        # sin el S&P 500 (~15 segundos)
python generar.py dolar         # una sola sección
```

## Aviso

Información con fines educativos e informativos. No es una recomendación de
inversión ni asesoramiento financiero, y quienes hacen esta página no están
registrados ante la CNV. Los datos son de terceros y pueden tener errores o
demoras. Invertir implica riesgos, incluida la pérdida del capital.

S&P 500 y S&P Merval son marcas de S&P Dow Jones Indices LLC. Este proyecto no
está afiliado ni avalado por S&P Dow Jones Indices, BYMA, Nasdaq, Yahoo,
TradingView ni los proveedores de datos.
