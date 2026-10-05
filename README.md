# S&P 500: distancia al máximo y a la 200 semanal

Una tabla con las 500 empresas del índice S&P 500 que muestra, para cada una,
cuánto le falta al precio para volver a su máximo histórico y qué tan lejos
está del promedio de las últimas 200 semanas (casi cuatro años).

**Ver la página:** https://bautimarque.github.io/mercado-sp500/

## Para qué sirve

Para encontrar rápido qué empresas están castigadas y cuáles están en zona de
máximos, sin abrir 500 gráficos. Se puede filtrar por sector, por cuánto cayó,
por distancia a la 200 semanal y por antigüedad del máximo, que es el dato que
separa una caída reciente de una empresa que nunca se recuperó.

## Señales

- **Posible compra**: el precio está a ±5% de su promedio de 200 semanas, el
  máximo histórico es de los últimos 2 años y ese promedio viene subiendo en
  los últimos 6 meses. Es una empresa que venía fuerte y corrigió hasta su
  promedio largo, no una que nunca se recuperó.
- **Tomar ganancias**: subió 50% o más en los últimos 12 meses y sigue a menos
  de 10% de su máximo. Quien la tenga desde hace un año gana al menos eso.

Los umbrales están al principio de `generar_pagina.py` y la página los toma de
ahí, así que cambiarlos no requiere tocar el HTML.

## La lista

Arranca con las 25 empresas más grandes del índice y se cargan de a 25 más
(o todas de una). Cualquier filtro u orden vuelve a mostrar las primeras 25.
El tamaño de cada empresa (su valor en bolsa) sale del buscador de nasdaq.com;
si no responde, la lista arranca ordenada por caída desde el máximo.

## Gráfico de cada empresa

Al abrir una empresa aparecen dos botones:

- **Ver gráfico con indicadores**: abre un gráfico de TradingView con velas
  diarias (promedios de 20, 50 y 200 días, volumen, RSI y MACD) o semanales
  (promedios de 50 y 200 semanas, volumen, RSI y MACD).
- **Abrir en TradingView**: lleva al gráfico completo en tradingview.com. Los
  links de TradingView no aceptan indicadores; si tenés cuenta, se abre con
  tu última plantilla guardada.

La bolsa de cada ticker (NYSE, NASDAQ, CBOE) sale del directorio oficial de
Nasdaq, así TradingView no la confunde con una acción de otro país.

## Cómo funciona

Un workflow de GitHub Actions corre `generar_pagina.py` de lunes a viernes a
las 18:30 de Argentina, después del cierre de Nueva York. El script toma la
lista del índice de Wikipedia, baja el histórico diario de cada ticker con
yfinance, arma las semanas para el promedio de 200 y escribe `index.html` con
los datos ya calculados adentro. La página no consulta nada al abrirse: es un
archivo estático. Lo único externo es el gráfico de TradingView, que se carga
recién cuando alguien lo abre.

Si Yahoo falla, los tickers que no llegaron se piden de nuevo. Si igual quedan
menos de 475 empresas con datos, el script termina con error y no publica nada:
sigue online la última página buena y GitHub avisa por mail que falló.

Para correrlo en local:

```
python -m venv .venv
.venv\Scripts\activate          # en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python generar_pagina.py
```

## Aviso

Esto ordena precios, no mide calidad. Una acción barata puede estar barata con
razón. No es una recomendación de compra ni asesoramiento financiero.
