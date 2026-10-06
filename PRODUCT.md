# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Personas de Argentina que invierten por su cuenta (plazo fijo, fondos, dólar, acciones argentinas, CEDEARs, bonos) y que siguen el dólar para sus gastos de todos los días. Entran seguido y por poco tiempo, mayormente desde el celular, para ver cómo vienen el dólar, las tasas y los mercados, y para hacer cuentas rápidas (cuánto sale en pesos una suscripción, cuánto rinde un plazo fijo). No son profesionales ni buscan una plataforma de trading: buscan una referencia rápida y confiable.

## Product Purpose

Mercadito reúne en un solo lugar, en castellano, los datos del mercado argentino y de Estados Unidos: dólar, gastos en dólares, tasas e inflación, Merval, S&P 500 y bonos. Cada sección muestra los números con su fecha y su fuente, los explica en palabras simples y suma herramientas para hacer cuentas.

Páginas: Inicio (un panel por sección con sus números clave), Dólar, Gastos en US$, Tasas, Merval, S&P 500, Bonos, Cómo se calcula y Aviso legal.

Éxito: alguien abre cualquier página y en 5 segundos entiende el número más importante; después encuentra el detalle o hace la cuenta que vino a hacer, sin salir del celular.

## Positioning

Es una herramienta para entrar y ver cómo vienen las cosas, para usar de guía. No ofrece nada: ni trading, ni recomendaciones, ni asesoramiento. Quienes la hacen no se presentan como expertos y no están registrados ante la CNV. Ordena y explica datos públicos de terceros con reglas a la vista; no mide la calidad de ninguna inversión.

## Operating Context

- Uso breve y recurrente, casi siempre en el celular.
- Actualización automática (GitHub Actions): Dólar, Gastos, Tasas, Merval y Bonos cada 30 minutos de lunes a viernes entre las 10 y las 17:30 de Argentina; todo, incluido el S&P 500, a las 18:30, después del cierre de Nueva York.
- Cada sección es independiente: si una fuente falla, esa sección queda con su última versión y las demás se publican igual.
- El público opera en pesos y en dólares (oficial, MEP, CCL); las acciones de EE.UU. se muestran en dólares de su mercado.

## Capabilities and Constraints

- Funciones que tienen que seguir existiendo: los filtros, órdenes, calculadoras y gráficos de cada página; «Mostrar 25 más»; la ficha de cada empresa del S&P 500; el gráfico de TradingView (se carga solo al abrirlo); el plegable del termómetro; el modo claro/oscuro.
- Los datos, los cálculos, las reglas de los patrones y los textos legales no se tocan desde el diseño.
- Las páginas se generan con Python (`generar.py`) y se publican como archivos estáticos en GitHub Pages: sin frameworks ni build. El marco común (cabecera, menú, pie) está en `mercadito/comun.py`; los estilos y funciones compartidos en `assets/base.css` y `assets/base.js`; cada sección tiene sus bloques CSS, CUERPO y JS en `mercadito/<seccion>.py`. Los `index.html` se pisan en cada corrida.
- Los marcadores `__DATOS__`, `__ACTUALIZADO__`, `__FECHA__`, `__INDICE__` y `__REGLAS__` los reemplaza el script con datos reales.
- Ningún pedido externo al abrir una página, salvo Google Fonts. TradingView se pide solo cuando alguien abre el gráfico.
- Los textos que vienen de fuentes externas (Wikipedia, entidades, fondos) se escapan antes de mostrarse.
- La paleta de series de los gráficos (`--s1` a `--s7`) está validada para daltonismo: cualquier cambio se valida de nuevo.
- Decisión abierta: más adelante puede haber una parte paga (premium). Hoy todo es gratis y no se diseña nada pago.

## Brand Commitments

- Nombre: Mercadito.
- Idioma: castellano rioplatense con voseo, directo y sin jerga financiera innecesaria. Explica cada número en palabras simples. La página del S&P 500 hoy está en castellano neutro y queda como excepción hasta que se ajusten sus textos.
- Requisito legal: todo se presenta como dato, nunca como recomendación ni acción. Nada de "comprar", "vender", "tomar ganancias", "oportunidad", "barata" ni "conviene". Los patrones del S&P 500 se llaman «En su promedio o debajo» y «Subió fuerte»; la columna es «Patrón». Aplica también a comentarios de código y al README, porque el repositorio es público.
- El aviso legal del pie va en todas las páginas y a la vista: es parte del producto, no letra chica.
- Sin promesas, sin urgencia y sin tono de "señales".

## Evidence on Hand

- Datos reales de terceros, con su fuente a la vista: dolarapi.com, comparadolar.ar, argentinadatos.com, API del BCRA, Yahoo Finance (yfinance), Wikipedia, Nasdaq, data912.com (proyecto con fines educativos) y TradingView.
- No hay testimonios, usuarios, métricas de uso ni historial de aciertos de los patrones. No se debe inventar ninguno, ni afirmar rendimiento de ninguna regla.

## Product Principles

1. Guía, no consejo: el sitio ordena y explica datos; nunca recomienda, promete ni se presenta como experto.
2. Primero el número, después el detalle: en cada página lo que se entiende en 5 segundos va arriba; tablas, gráficos y calculadoras son para quien quiere seguir.
3. Cada número se explica donde aparece, con su fecha y su fuente a la vista.
4. Pensado para el pulgar: menú, tablas y calculadoras cómodos en un celular de 375 px y con una mano.
5. Un solo sitio: las nueve páginas se leen como partes de lo mismo, con el mismo lenguaje visual y los mismos controles.
