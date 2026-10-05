# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Personas de Argentina que invierten por su cuenta en acciones de EE.UU., en general a través de CEDEARs. Entran un par de veces por semana, mayormente desde el celular, para ver qué está barato, qué está muy estirado y cómo viene el mercado en general. No son profesionales ni buscan una plataforma de trading: buscan una referencia rápida.

## Product Purpose

Un tablero en castellano con las ~500 empresas del S&P 500. Para cada una muestra cuánto le falta para volver a su máximo histórico, qué tan lejos está de su promedio de 200 semanas, cuánto subió o bajó en 12 meses, y dos señales basadas en reglas fijas sobre el precio: "Posible compra" y "Tomar ganancias".

En 5 segundos tiene que resolver: cómo está el índice, qué tan sano está el mercado (% de empresas arriba de su promedio de 200 semanas) y cuántas empresas entran en cada señal. Después, explorar la tabla con filtros.

Éxito: alguien abre la página, entiende en un vistazo cómo vienen las cosas y encuentra en segundos las empresas que le interesan mirar más a fondo.

## Positioning

Es una herramienta para entrar y ver cómo vienen las cosas, para usar de guía. No ofrece nada: ni trading, ni recomendaciones, ni asesoramiento. Quienes la hacen no se presentan como expertos. Ordena precios con reglas públicas y explicadas; no mide calidad de empresas.

## Operating Context

- Uso breve y recurrente (un par de veces por semana), casi siempre en el celular.
- Los datos se actualizan solos de lunes a viernes a las 18:30 de Argentina, después del cierre de Nueva York; si se corre con el mercado abierto, la fecha lo aclara.
- El público opera vía CEDEARs, pero la página muestra precios en dólares del mercado de EE.UU.

## Capabilities and Constraints

- Función que tiene que existir: 4 indicadores (índice vs. su máximo, % de empresas arriba de su 200 semanal, cantidad en "Posible compra", cantidad en "Tomar ganancias"), tabla ordenable, búsqueda, filtro por sector, filtros numéricos (caída mínima, distancia a la 200 semanal, antigüedad del máximo), atajos (Posible compra, Tomar ganancias, Cayeron fuerte hace poco, En zona de máximos), una vista de la distribución de caídas (hoy un histograma), modo claro/oscuro, el texto de cada regla y el aviso de que no es recomendación de inversión.
- Los datos y las reglas de las señales no se tocan. Los umbrales viven en `generar_pagina.py` y la página los recibe en `__REGLAS__`.
- `index.html` se genera y lo pisa un bot todos los días: el HTML/CSS/JS real está en la variable `PLANTILLA` de `generar_pagina.py`. Los marcadores `__FECHA__`, `__DATOS__`, `__INDICE__` y `__REGLAS__` se reemplazan con datos reales.
- Un solo archivo estático, sin frameworks ni build, publicado en GitHub Pages. Ningún pedido externo al abrir la página, salvo fuentes de Google Fonts.
- Nombres y sectores vienen de Wikipedia y se escapan antes de mostrarse.
- Abierto: el nombre propio de la página. El usuario pidió una propuesta; hasta que se decida, el título es "S&P 500".

## Brand Commitments

- Idioma: castellano neutro, sin voseo, directo y sin jerga financiera innecesaria. Explica cada número en palabras simples.
- Sin promesas, sin urgencia, sin tono de "señales" vendidas. Las señales se presentan como reglas mecánicas sobre el precio.
- El aviso de que no es recomendación de inversión ni asesoramiento es parte del producto, no letra chica.

## Evidence on Hand

- Datos reales y diarios: lista del índice desde Wikipedia, precios diarios de Yahoo Finance vía yfinance, sin ajustar por dividendos.
- No hay testimonios, usuarios, métricas de uso ni historial de aciertos de las señales. No se debe inventar ninguno, ni afirmar rendimiento de las señales.

## Product Principles

1. Guía, no consejo: la página ordena precios y explica sus reglas; nunca recomienda, promete ni se presenta como experta.
2. Primero el estado del mercado, después la exploración: lo que se entiende en 5 segundos va arriba; la tabla es para quien quiere seguir mirando.
3. Cada número se explica donde aparece: quien no sabe qué es una "200 semanal" tiene que poder entenderlo sin salir de la página.
4. Pensada para el pulgar: lectura y filtros cómodos en un celular, en visitas cortas.
5. Honestidad sobre los datos: siempre a la vista de cuándo son los precios y de dónde salen.
