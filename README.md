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

## Cómo funciona

Un workflow de GitHub Actions corre `generar_pagina.py` de lunes a viernes a
las 18:30 de Argentina, después del cierre de Nueva York. El script toma la
lista del índice de Wikipedia, baja el histórico semanal de cada ticker con
yfinance y escribe `index.html` con los datos ya calculados adentro. La página
no consulta nada al abrirse: es un archivo estático.

## Aviso

Esto ordena precios, no mide calidad. Una acción barata puede estar barata con
razón. No es una recomendación de compra ni asesoramiento financiero.
