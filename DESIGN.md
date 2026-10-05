---
name: Termómetro 500
description: Las empresas del S&P 500 leídas como un parte del tiempo, cada una con su temperatura en siete bandas de azul a naranja.
colors:
  t0: "#1E4D8F"
  t1: "#3F7DC9"
  t2: "#86AEDD"
  t3: "#D3D2CD"
  t4: "#E89650"
  t5: "#CF6420"
  t6: "#9E3F0F"
  sin: "#E4E6EA"
  fondo: "#F6F7F8"
  superficie: "#FFFFFF"
  hundido: "#EDEFF2"
  tinta: "#14181E"
  tinta-2: "#474E59"
  tinta-3: "#646C78"
  linea: "#E1E4E8"
  linea-2: "#C5CAD2"
  t0-oscuro: "#93BEF5"
  t1-oscuro: "#4F8BD8"
  t2-oscuro: "#2F5C93"
  t3-oscuro: "#3A3A37"
  t4-oscuro: "#8E4A17"
  t5-oscuro: "#D9762D"
  t6-oscuro: "#FFA466"
  sin-oscuro: "#2A3038"
  fondo-oscuro: "#101317"
  superficie-oscuro: "#171B21"
  hundido-oscuro: "#20252D"
  tinta-oscuro: "#E8EAED"
  tinta-2-oscuro: "#B4BAC3"
  tinta-3-oscuro: "#8C939E"
  linea-oscuro: "#262C34"
  linea-2-oscuro: "#3A424D"
typography:
  display:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "96px"
    fontWeight: 800
    lineHeight: 0.86
    letterSpacing: "-0.02em"
    fontVariation: "'wdth' 72"
  headline:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "34px"
    fontWeight: 750
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 78"
  marca:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 88"
  title:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "19px"
    fontWeight: 750
    lineHeight: 1.25
    letterSpacing: "-0.005em"
  body:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  nota:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "12.5px"
    fontWeight: 550
    lineHeight: 1.3
  tabular:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "'tnum' 1"
rounded:
  xs: "2px"
  sm: "3px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "32px"
  seccion: "48px"
  columna: "56px"
  pie: "64px"
components:
  boton:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "38px"
  boton-hover:
    backgroundColor: "{colors.hundido}"
    textColor: "{colors.tinta}"
  boton-activo:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.fondo}"
  boton-texto:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    padding: "0 6px"
    height: "38px"
  campo:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "42px"
  lectura-boton:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    rounded: "{rounded.lg}"
    padding: "15px 10px"
  lectura-boton-hover:
    backgroundColor: "{colors.hundido}"
  lectura-boton-activo:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.fondo}"
  sector-fila:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    rounded: "{rounded.md}"
    padding: "0 8px"
    height: "36px"
  sector-fila-activa:
    backgroundColor: "{colors.hundido}"
  franja-termica:
    rounded: "{rounded.md}"
    height: "96px"
    width: "100%"
  muestra:
    rounded: "{rounded.xs}"
    size: "10px"
  tabla-caja:
    backgroundColor: "{colors.superficie}"
    rounded: "{rounded.md}"
  tabla-celda:
    typography: "{typography.tabular}"
    padding: "10px 12px"
  tooltip:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.fondo}"
    rounded: "{rounded.md}"
    padding: "6px 9px"
  regla-activa:
    backgroundColor: "{colors.hundido}"
    textColor: "{colors.tinta-2}"
    rounded: "{rounded.lg}"
    padding: "11px 14px"
  aviso:
    textColor: "{colors.tinta}"
    rounded: "{rounded.md}"
    padding: "18px 20px"
---

# Design System: Termómetro 500

## Overview

**Creative North Star: "El parte del tiempo del mercado"**

Termómetro 500 lee el S&P 500 como el informe del tiempo del diario o del Servicio Meteorológico: primero las condiciones de hoy, después las 500 lecturas. Cada empresa tiene una temperatura, su distancia al promedio de 200 semanas, y esa temperatura se dibuja siempre con la misma escala de siete isotermas, de azul a naranja, pasando por un gris templado. La escala es el sistema: la marca, la franja de las 500 empresas, las franjas por sector, el histograma de caídas y la muestra al lado de cada cifra son la misma regla repetida.

El material es papel gris frío casi blanco (de noche, azul casi negro), tinta azulada, filetes finos y una sola familia tipográfica, Archivo, que se estrecha y engorda para las cifras que se leen de lejos y vuelve a su ancho normal para la interfaz. La densidad es de diario: la información se separa con filetes y aire, no con tarjetas. El color se guarda para la temperatura; la interacción habla en tinta, y lo activo se invierte a tinta llena.

Rechazos confirmados: la fila de tarjetas de indicadores sobre una tabla con verdes y rojos, las señales como píldoras de color y cualquier tono que sugiera ganar o perder. La página ordena precios con reglas fijas; nada en el sistema visual tiene que sonar a recomendación, promesa o urgencia.

**Key Characteristics:**
- Siete bandas térmicas escalonadas (tres azules, un gris templado, tres naranjas), sin verde ni rojo en ninguna parte.
- Una sola familia, Archivo, en tres anchos: 72–78% para las cifras grandes, 88% para la marca y la cifra clave de la lista, 100% para la interfaz.
- Plano: filetes de 1px y un gris hundido para dar profundidad; la sombra queda para lo que flota mientras se lee.
- Controles estándar con esquinas de 6px; lo activo se invierte a tinta llena.
- Íconos SVG de trazo a 16px; las señales son ícono más palabra, en tinta.
- Claro y oscuro con la escala recalibrada: en oscuro, la intensidad crece hacia lo claro.

## Colors

Una escala térmica de siete pasos sobre papel y tinta neutros de matiz azulado; el color existe para medir temperatura y nada más.

### Primary

La escala térmica. Cada banda tiene su palabra fija, que siempre la acompaña. Los cortes se toman sobre la distancia del precio a su promedio de 200 semanas.

- **Azul Polar Profundo**, «Muy frío» (#1E4D8F; oscuro #93BEF5): más de 50% debajo del promedio.
- **Azul Frente Frío**, «Frío» (#3F7DC9; oscuro #4F8BD8): entre 20% y 50% debajo.
- **Celeste Brisa**, «Fresco» (#86AEDD; oscuro #2F5C93): entre la banda de la regla y 20% debajo.
- **Gris Templado**, «Templado» (#D3D2CD; oscuro #3A3A37): a menos de la banda de la regla «Posible compra» (hoy ±5%) del promedio. Es un gris apenas cálido, casi sin croma: la ausencia de temperatura, el centro silencioso de la escala.
- **Naranja Tibio**, «Cálido» (#E89650; oscuro #8E4A17): entre la banda de la regla y 20% arriba.
- **Naranja Ola de Calor**, «Caluroso» (#CF6420; oscuro #D9762D): entre 20% y 50% arriba.
- **Ladrillo Tórrido**, «Muy caluroso» (#9E3F0F; oscuro #FFA466): más de 50% arriba.
- **Gris Sin Lectura**, «Sin dato» (#E4E6EA; oscuro #2A3038): empresas con menos de 200 semanas de historia. Queda fuera de la escala, no es una octava banda.

Cada brazo es una rampa ordinal: la luminosidad cambia en un solo sentido desde el centro hacia los extremos, y los pares simétricos (Fresco y Cálido, Frío y Caluroso, Muy frío y Muy caluroso) tienen luminosidad parecida para que ningún lado pese más. El paso más suave de cada brazo mantiene al menos 2:1 contra la superficie en los dos modos; Templado queda cerca de 1,5:1 a propósito.

### Neutral

- **Papel Gris Frío** (#F6F7F8; oscuro, Noche Azul #101317): fondo de la página y color del texto invertido en lo activo.
- **Hoja Blanca** (#FFFFFF; oscuro #171B21): superficie de controles, tabla y lectura flotante.
- **Gris Hundido** (#EDEFF2; oscuro #20252D): hover de filas y botones, fila desplegada, nota de regla activa, barra fantasma del histograma.
- **Tinta Azulada** (#14181E; oscuro #E8EAED): texto principal, cifras, marcas de promedio y cursor, estados activos, contornos de foco.
- **Tinta Media** (#474E59; oscuro #B4BAC3): texto secundario, notas, nombres en la lista.
- **Tinta Tenue** (#646C78; oscuro #8C939E): ejes, unidades, ayudas, íconos de campo. Mantiene cerca de 5:1 o más sobre el fondo en los dos modos, así que sirve para texto chico.
- **Filete** (#E1E4E8; oscuro #262C34): divisiones entre filas y entre ítems.
- **Filete Marcado** (#C5CAD2; oscuro #3A424D): borde de controles, filete superior de secciones y paneles, base del histograma.

### Named Rules

**La Regla de las Siete Isotermas.** La temperatura se dibuja con exactamente siete bandas escalonadas: tres azules, un gris templado y tres naranjas, con cortes en ±(banda de «Posible compra»), ±20% y ±50% de la distancia al promedio de 200 semanas. Nunca un degradado continuo, nunca tonos intermedios, nunca verde ni rojo. La escala solo codifica temperatura; su única aparición fuera de los datos es la marca, que es la escala misma.

**La Regla de la Tinta.** El texto nunca se viste de color térmico. El color lo lleva una muestra cuadrada o una franja; la palabra y la cifra que la acompañan van siempre en tinta.

**La Regla de la Escala Recalibrada.** En oscuro la escala no se reutiliza: se recalibra para que la intensidad siga siendo contraste contra la superficie. En claro los extremos son los más oscuros; en oscuro, los más claros, y Templado pasa a ser el tono más oscuro de la escala.

## Typography

**Display Font:** Archivo (con -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif)
**Body Font:** Archivo, la misma familia variable (ancho 62–125, peso 100–900), cargada desde Google Fonts
**Label/Mono Font:** Archivo con cifras tabulares; no hay monoespaciada

**Character:** una grotesca argentina de Omnibus-Type que funciona como titular de diario cuando se estrecha y como letra de formulario cuando vuelve a su ancho normal. Una sola voz, tres anchos.

### Hierarchy
- **Display** (800, 96px; 76px bajo 900px; 64px bajo 420px; interlineado 0,86; ancho 72%): la cifra grande del porcentaje de empresas arriba de su promedio. Una sola por página; su rótulo la acompaña a 19px peso 550 (16,5px en el celular).
- **Headline** (750, 34px; 30px en el celular; interlineado 1; ancho 78%): las cifras de las lecturas (índice desde su máximo, cantidad de empresas en cada señal). La palabra de estado del índice usa la misma voz a 30px (26px en el celular), ancho 76%, junto a una muestra de 14px.
- **Marca** (800, 20px, ancho 88%): el nombre en la cabecera.
- **Title** (750, 19px, interlineado 1,25): títulos de sección. Los subtítulos del pie bajan a 15px peso 700; el nombre de cada lectura va a 16,5px peso 650.
- **Body** (400, 15px, interlineado 1,5): texto corrido. El detalle desplegado de una empresa va a 14,5px con interlineado 1,55 y un máximo de 78ch; el glosario, 65ch.
- **Nota** (400, 13,5px, interlineado cerca de 1,45, en tinta media): fecha, subtítulos de lecturas, notas de panel, aviso corto.
- **Label** (550, 12,5px, interlineado 1,3, en tinta media): rótulos de campos y encabezados de la tabla. Ejes y leyendas van a 12–12,5px en tinta tenue. Sin mayúsculas sostenidas ni espaciado abierto.
- **Tabular** (400, 14px, cifras tabulares): celdas de la tabla. La columna «Desde su máximo» sube a peso 650 y ancho 88%.

En el código, el ancho se aplica con `font-stretch` (72%, 76%, 78%, 88%), que la familia variable traduce a su eje `wdth`. Los pesos intermedios (550, 650, 750) son parte del sistema, no redondeos.

### Named Rules

**La Regla de una Sola Familia.** Todo es Archivo. La jerarquía sale del ancho y el peso: condensado y pesado para lo que se lee de lejos, ancho normal entre 400 y 650 para la interfaz. Ninguna segunda familia, ninguna fuente de íconos.

**La Regla del Signo Menos.** Toda cifra que se compara en columna usa cifras tabulares; los números van en formato es-AR (coma decimal, punto de miles), con «+» explícito en las variaciones positivas y el signo menos tipográfico (−), nunca el guion.

## Layout

Una sola columna de lectura de hasta 1200px, centrada, con 32px de margen lateral (16px bajo 900px) y 64px al pie (48px en el celular). El orden va de las condiciones a la exploración: cabecera con marca y botón de tema, fecha de los precios, la franja térmica a todo el ancho con su eje y su leyenda, la cifra grande y las tres lecturas en una grilla 5:7, dos paneles a mitades (temperatura por sector y caídas desde el máximo), la lista de empresas, el pie con glosario y escala en una grilla 1,35:1, y el aviso.

El ritmo es de diario, no una escala estricta: 56px entre columnas, 48–64px entre bloques mayores, 12–16px dentro de un grupo de controles, 8px entre botones de un mismo grupo. Los valores intermedios que aparecen (14, 18, 22, 34, 52px) son ajustes ópticos y no pasos nuevos.

Cortes responsivos: bajo 1280px se oculta la columna Sector de la tabla; bajo 1100px, el «hace N años» del máximo; bajo 900px todo pasa a una columna (franja de 64px de alto, cifra grande al lado de su rótulo, lecturas apiladas, paneles uno debajo del otro, buscador a lo ancho y aparece el selector «Ordenar»); bajo 520px los filtros quedan en una columna; bajo 420px la cifra grande baja a 64px, el botón de tema queda solo con ícono y se acortan los rótulos largos.

### Named Rules

**La Regla del Pulgar.** En el celular cada empresa es un registro de dos líneas a sangre (arriba, ticker y nombre con su caída a la derecha; debajo, temperatura, 12 meses y año del máximo; la señal, si la hay, en una tercera línea), los campos van a 16px para que el teléfono no haga zoom y la franja se recorre con el dedo sin bloquear el desplazamiento vertical.

## Elevation & Depth

El sistema es plano. La profundidad se arma con filetes de 1px y un único escalón tonal: el gris hundido, que marca hover, fila desplegada y notas. Las secciones se separan con un filete superior y aire. La sombra aparece solo en lo que flota sobre los datos mientras alguien los está leyendo; los anillos dibujados con `box-shadow` son trazos, no elevación.

### Shadow Vocabulary
- **Lectura flotante** (`box-shadow: 0 1px 2px rgba(10,14,20,.08), 0 3px 12px rgba(10,14,20,.10)`): la etiqueta que sigue al cursor sobre la franja térmica.
- **Tooltip** (`box-shadow: 0 2px 10px rgba(10,14,20,.18)`): la cifra de cada barra del histograma, sobre tinta llena.
- **Halo del cursor** (`box-shadow: 0 0 0 1.5px var(--fondo)`): separa el cursor de tinta de las franjas que tiene debajo.
- **Anillo de sector activo** (`box-shadow: inset 0 0 0 2px var(--tinta)`): marca el sector que filtra la lista.

### Named Rules

**La Regla de lo Plano.** Ninguna superficie se levanta en reposo. Si algo necesita separarse, lleva filete o pasa al gris hundido; la sombra de elevación es solo para la lectura flotante y el tooltip.

## Shapes

Esquinas estándar y discretas. 6px para todo lo que se toca o contiene datos: botones, campos, la franja térmica (recortada con esquinas redondeadas), la caja de la tabla, el tooltip y el aviso. 8px para las filas-botón de las lecturas y la nota de regla activa. 3px para las franjas de sector, las barras del histograma (solo arriba) y la muestra grande; 2px para las muestras de 10px y el logo. Los filetes son de 1px; el único marco grueso es el del aviso, de 1,5px en tinta. El único elemento redondo es el contador de filtros por número.

El logo y el favicon son la escala misma: siete barras verticales de 2px de ancho, de Muy frío a Muy caluroso.

### Named Rules

**La Regla de los Seis Píxeles.** Controles y contenedores de datos usan 6px; ni esquinas vivas ni píldoras. Las formas chicas que llevan color térmico bajan a 2–3px para seguir leyéndose como muestras, no como botones.

## Components

Todo vive en un solo archivo: la cadena `PLANTILLA` de `generar_pagina.py`. `index.html` lo regenera un bot cada día hábil y no se edita a mano; cualquier cambio de diseño va en `PLANTILLA`. Los marcadores `__FECHA__`, `__DATOS__`, `__INDICE__` y `__REGLAS__` se reemplazan con datos reales y tienen que quedar intactos. Sin frameworks ni build; ningún pedido externo al abrir la página salvo Google Fonts. Los umbrales de las reglas, incluida la banda templada, llegan por `__REGLAS__`.

### Buttons
- **Shape:** esquinas de 6px, 38px de alto, filete de 1px en filete marcado.
- **Base:** superficie blanca, texto en tinta, 14px peso 550, 0 14px de relleno, ícono de 16px a 7px del texto.
- **Hover / Focus:** pasa al gris hundido con borde en tinta tenue (150ms). Foco: contorno de 2px en tinta, separado 2px.
- **Activo:** con `aria-pressed`, se invierte a tinta llena con texto en color de fondo.
- **Deshabilitado:** opacidad 0,45 y fondo transparente.
- **Botón de texto:** sin borde ni fondo, subrayado de 1px a 3px del texto; en hover el subrayado engorda a 2px. Se usa para «Limpiar filtros».
- **Botón de tema:** botón base con luna o sol; bajo 420px queda solo el ícono.

### Leyenda y muestras
- **Muestra:** cuadrado de 10px con esquinas de 2px en el color de la banda, delante de la palabra. En la palabra de estado del índice crece a 14px con esquinas de 3px.
- **Leyenda:** muestra, palabra en tinta media a 12,5px y rango en tinta tenue a 12px con cifras tabulares, en una línea que se parte en el celular.
- **Escala del pie:** la misma muestra en una grilla de cuatro columnas (muestra, palabra, rango, cuántas empresas hay hoy), con filete entre filas y la fila «Sin dato» al final.

### Cards / Containers
- **Corner Style:** no hay tarjetas. Los únicos contenedores son la caja de la tabla (6px), la nota de regla activa (8px) y el aviso (6px).
- **Background:** la caja de la tabla es superficie blanca con filete; la nota de regla activa y la fila desplegada usan el gris hundido.
- **Shadow Strategy:** ninguna; ver Elevation & Depth.
- **Border:** filete de 1px en la tabla; marco de 1,5px en tinta en el aviso, que es parte del producto y no letra chica.
- **Internal Padding:** 11px 14px en la nota de regla activa; 18px 20px en el aviso (16px en el celular); 14px 18px 16px en la fila desplegada.

### Inputs / Fields
- **Style:** 42px de alto, superficie blanca, filete marcado, esquinas de 6px, 0 12px de relleno, texto de 15px (16px en el celular). Rótulo arriba en Label; ayuda abajo a 12,5px en tinta tenue. La lupa va a la izquierda (el texto empieza a 36px), el chevron del selector y la unidad («%», «años») van a la derecha, todo en tinta tenue.
- **Focus:** borde y contorno de 2px en tinta, separado 1px; el hover oscurece el borde a tinta tenue.
- **Selectores:** sin apariencia nativa, con chevron SVG dibujado.

### Cabecera
- **Style:** marca (logo de siete barras y nombre) a la izquierda, botón de tema a la derecha, fecha de los precios debajo en Nota. No hay navegación: es una sola página. El enlace para saltar a la lista aparece al recibir foco, en tinta llena con esquinas de 6px.

### Franja térmica
La pieza firma. Cada empresa con dato es una franja vertical de igual ancho, ordenadas de la más fría a la más caliente, a todo el ancho, 96px de alto (64px en el celular) y esquinas de 6px. El corte del promedio es una línea de tinta de 2px que sobresale arriba y abajo, con su rótulo en el eje; las puntas del eje («Más frías», «Más calientes») se esconden si chocan con él. Se recorre con el mouse, el dedo o el teclado (flechas, Re Pág, Av Pág, Inicio, Fin): un cursor de tinta de 3px con halo del color del fondo marca la empresa y la línea de arriba pasa a ser una lectura flotante con ticker, nombre, distancia y banda. Con cualquier filtro activo, las franjas que quedan fuera bajan al 14% de opacidad (200ms).

### Lecturas
Al lado de la cifra grande, una lista con filete superior marcado y filetes entre filas: el índice (cifra Headline, palabra de estado con muestra y subtítulo en Nota) y las dos señales como filas-botón con esquinas de 8px, ícono, nombre, ejemplos de tickers, cantidad y chevron. En hover pasan al gris hundido; activas, a tinta llena con los textos secundarios mezclados al 72% hacia el fondo. Al activarlas filtran la lista y la llevan a la vista.

### Sectores e histograma
- **Fila de sector:** botón de 36px con esquinas de 6px: nombre con su cantidad en tinta tenue, una franja térmica chica (16px de alto, 12px en el celular, esquinas de 3px) y el porcentaje arriba del promedio con cifras tabulares. Activa: gris hundido con anillo interior de 2px en tinta. En el celular, nombre y porcentaje arriba y la franja debajo.
- **Histograma de caídas:** 20 barras de 5% cada una, de −100% a 0%, separadas 3px. Detrás, una barra fantasma en gris hundido con el total; delante, la pila de las empresas que pasan los filtros, apilada por banda térmica con 1px entre bandas y esquinas de 3px arriba. Al pasar o enfocar una barra aparece el tooltip en tinta; al tocarla filtra por caída mínima.

### Lista de empresas
Caja blanca con filete y esquinas de 6px; encabezados en Label que quedan fijos al desplazarse y ordenan al tocarlos (flecha de 12px). Filas de 14px con 10px 12px de relleno y filete entre filas; ticker en peso 700, nombre en tinta media, cifras a la derecha con cifras tabulares, la temperatura como muestra más cifra con signo. En hover la fila pasa al gris hundido; al tocarla se despliega un párrafo explicativo sobre gris hundido.

### Señales
**La Regla de la Señal Dibujada.** Una señal es un ícono SVG de trazo de 16px más su palabra, en tinta, a 13px peso 600: «Posible compra» es un sol sobre la línea del horizonte, «Tomar ganancias» una flecha que sube hasta un techo. Nunca una píldora, una etiqueta de color ni una insignia.

**La Regla del Activo en Tinta.** Lo seleccionado se invierte a tinta llena (fondo en tinta, texto en color de fondo). La única excepción es la fila de sector, que usa gris hundido con anillo interior de tinta para no tapar su franja de colores.

**La Regla de la Franja que Responde.** La franja principal, las franjas de sector y el histograma muestran siempre qué parte del mercado queda en la lista: con filtros activos, lo que queda afuera se atenúa al 14% o sale de la pila. Ningún filtro cambia la lista sin que la franja lo refleje.

Íconos: SVG en línea de 16px, trazo de 1,6 con puntas redondeadas y color heredado del texto. Movimiento: 150ms para color, fondo y borde de controles y filas; 200ms con salida suave para la opacidad de las franjas, la altura de las pilas y el giro del chevron. Con `prefers-reduced-motion` se apagan las transiciones y el salto a la lista es instantáneo.

## Do's and Don'ts

### Do:
- **Do** usar siempre las variables del sistema (`--fondo`, `--superficie`, `--hundido`, `--tinta`, `--tinta-2`, `--tinta-3`, `--linea`, `--linea-2`, `--t0` a `--t6`, `--sin`) y definir cada valor nuevo en los tres bloques: claro, oscuro por preferencia del sistema y oscuro forzado con `data-tema="oscuro"`.
- **Do** asignar la banda con los cortes de la escala: ±(banda de «Posible compra», hoy 5%), ±20% y ±50% de la distancia al promedio de 200 semanas, para que Templado sea siempre la misma banda de la regla.
- **Do** acompañar cada color térmico con su palabra (Muy frío, Frío, Fresco, Templado, Cálido, Caluroso, Muy caluroso) y cada cifra con su unidad dicha en palabras («desde su máximo», «empresas», «arriba»).
- **Do** reservar Archivo condensado (72–78%) y pesado (750–800) para las cifras que se leen de lejos; la interfaz va a ancho normal, entre 400 y 650.
- **Do** alinear toda columna numérica con cifras tabulares, formato es-AR y signo menos tipográfico (−).
- **Do** marcar lo activo invirtiendo a tinta llena, y los sectores activos con gris hundido y anillo interior de tinta de 2px.
- **Do** atenuar al 14% las franjas de las empresas que quedan fuera de los filtros, en la franja principal y en las de sector, y recalcular las pilas del histograma.
- **Do** mantener sincronizados los valores repetidos fuera de las variables: los dos `theme-color` del `<head>` y del script de tema (#F6F7F8 y #101317) y los siete colores claros del favicon.
- **Do** apagar las transiciones con `prefers-reduced-motion` y usar desplazamiento instantáneo en ese caso.

### Don't:
- **Don't** usar verde ni rojo para subas, bajas, señales o estados, ni un degradado continuo entre azul y naranja, ni una octava banda.
- **Don't** pintar texto con colores térmicos: el color lo lleva la muestra o la franja; cifras y palabras van en tinta.
- **Don't** armar una fila de tarjetas de indicadores sobre una tabla ni apilar tarjetas con sombra; las secciones se separan con filetes y aire.
- **Don't** mostrar las señales como píldoras, etiquetas de color o insignias: son ícono de trazo más palabra, en tinta.
- **Don't** sumar una segunda familia tipográfica, fuentes de íconos, emoji ni recursos externos fuera de Google Fonts.
- **Don't** usar sombra para jerarquía de secciones; la sombra de elevación queda para la lectura flotante de la franja y el tooltip del histograma.
- **Don't** agregar acentos de alerta, urgencia o celebración (destellos, insignias de «oportunidad», colores de aviso): la página ordena precios con reglas, no recomienda.
