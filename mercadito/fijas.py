"""
Paginas fijas: "Como se calcula" (metodologia/) y "Aviso legal" (legal/).
Se regeneran en cada corrida para que el menu y el pie sean los mismos.
"""

from . import comun


METODOLOGIA = """
<div class="titulo">
  <h1>Cómo se calcula</h1>
  <p class="bajada">De dónde sale cada dato de Mercadito y qué cuenta se hace con él.</p>
</div>

<section class="bloque texto">
  <h2>Cuándo se actualiza</h2>
  <p>El dólar, los gastos en dólares, las tasas, el Merval y los bonos se actualizan cada 30 minutos, de lunes a viernes entre las 10 y las 17:30.
  A las 18:30 se actualiza todo, incluido el S&amp;P 500. Cada página dice a qué hora se armó y, cuando la fuente lo informa,
  de qué fecha es cada dato. Si una fuente no responde, esa sección queda con su última versión.</p>
</section>

<section class="bloque texto">
  <h2>Dólar</h2>
  <ul>
    <li><b>Cotizaciones:</b> dolarapi.com. Compra es lo que se recibe al vender un dólar; venta, lo que se paga por comprarlo.</li>
    <li><b>Variación diaria:</b> precio de venta actual contra el último cierre anterior publicado por argentinadatos.com.</li>
    <li><b>Brecha:</b> venta de cada tipo ÷ venta del oficial − 1.</li>
    <li><b>Banda cambiaria:</b> piso, techo y tipo de cambio mayorista de referencia (Comunicación A 3500) publicados por el BCRA.</li>
    <li><b>Por entidad:</b> comparadolar.ar, con los precios que informa cada banco, billetera o broker. Diferencia = venta ÷ compra − 1.</li>
    <li><b>Calculadora:</b> monto ÷ venta (de pesos a dólares) o monto × compra (de dólares a pesos), sin comisiones ni impuestos adicionales.</li>
  </ul>
</section>

<section class="bloque texto">
  <h2>Gastos en dólares</h2>
  <ul>
    <li><b>Pagando el resumen en pesos:</b> precio × dólar oficial, más los impuestos que correspondan, calculados sobre ese monto:
      IVA 21% (servicios digitales y juegos), percepción del 30% a cuenta de Ganancias (RG 5617/2024 de ARCA; no se cobra en juegos
      desde abril de 2025 ni en compras pagadas con dólares propios) e Ingresos Brutos de la provincia (2% en CABA y Provincia de Buenos Aires).</li>
    <li><b>Pagando con dólares propios:</b> precio × dólar MEP, más el IVA y los Ingresos Brutos en pesos.</li>
    <li><b>Dólar efectivo:</b> total en pesos ÷ precio en dólares.</li>
    <li>Las normas cambian: la fecha en que se verificaron figura en la página. El resumen de la tarjeta tiene el detalle exacto.</li>
  </ul>
</section>

<section class="bloque texto">
  <h2>Tasas</h2>
  <ul>
    <li><b>Plazo fijo:</b> TNA para clientes de cada entidad, según argentinadatos.com con datos del BCRA.</li>
    <li><b>Interés a 30 días:</b> TNA × 30 ÷ 365.</li>
    <li><b>TEA:</b> (1 + TNA × 30 ÷ 365)<sup>365 ÷ 30</sup> − 1, es decir, renovando cada 30 días con la misma tasa.</li>
    <li><b>Frente a la inflación:</b> (1 + interés a 30 días) ÷ (1 + inflación del último mes publicado) − 1.</li>
    <li><b>Fondos money market:</b> TNA del último día = (valor de la cuotaparte del último día ÷ la del día anterior − 1) × 365 ÷ días entre ambas.
      Se muestran los fondos con al menos $ 1.000 millones de patrimonio y se descartan valores fuera de −20% y 150%, que suelen ser errores de carga.</li>
    <li><b>Inflación y referencias:</b> series del BCRA (inflación del INDEC, expectativas del REM, BADLAR, TAMAR, CER, UVA y reservas).</li>
  </ul>
</section>

<section class="bloque texto">
  <h2>Merval</h2>
  <ul>
    <li><b>Precios:</b> cierres diarios de Yahoo Finance del índice S&amp;P Merval y de cada acción en BYMA.</li>
    <li><b>En dólares CCL:</b> precio en pesos ÷ dólar contado con liqui del mismo día (o del día hábil anterior), con la serie de argentinadatos.com, que empieza en 2013.</li>
    <li><b>Desde su máximo:</b> precio en dólares ÷ mayor cierre en dólares desde 2013 − 1.</li>
    <li><b>Vs. 200 semanas:</b> precio en dólares ÷ promedio de los últimos 200 cierres semanales (viernes) en dólares − 1.</li>
    <li><b>12 meses:</b> contra el último cierre de hace 365 días o más.</li>
    <li><b>Acciones:</b> lista de componentes de Wikipedia; puede no coincidir exactamente con la composición vigente del índice.</li>
  </ul>
</section>

<section class="bloque texto">
  <h2>S&amp;P 500</h2>
  <ul>
    <li><b>Empresas:</b> lista de Wikipedia. Precios diarios de Yahoo Finance, sin ajustar por dividendos; las semanas se arman con los datos diarios.</li>
    <li><b>Máximo:</b> mayor precio intradiario. Se descarta un máximo diario que supere en más de 50% la apertura, el cierre y los cierres vecinos, porque suele ser un error de la fuente.</li>
    <li><b>Vs. 200 semanas:</b> precio ÷ promedio de los últimos 200 cierres semanales − 1.</li>
    <li><b>En su promedio o debajo:</b> precio como máximo 5% arriba de su promedio de 200 semanas (puede estar por debajo, sin límite), máximo histórico de los últimos 2 años y ese promedio más alto que hace 26 semanas.</li>
    <li><b>Subió fuerte:</b> subió 50% o más en 12 meses y está a menos de 10% de su máximo.</li>
    <li><b>Tamaño:</b> valor en bolsa según nasdaq.com. <b>Bolsa de cada ticker:</b> directorio oficial de Nasdaq, para armar el símbolo de TradingView.</li>
    <li>Si llegan datos de menos de 475 empresas, la página no se actualiza.</li>
  </ul>
</section>

<section class="bloque texto">
  <h2>Bonos</h2>
  <ul>
    <li><b>Precios:</b> data912.com, un proyecto gratuito con fines educativos y precios con demora.</li>
    <li><b>Dólar implícito:</b> precio del bono en pesos ÷ precio del mismo bono en dólares MEP.</li>
    <li><b>Letras:</b> el tipo y el vencimiento salen del símbolo (por ejemplo, S30O6 es una LECAP que vence el 30/10/2026).</li>
    <li><b>Obligaciones negociables:</b> las 30 con más volumen del día entre las que cotizan en dólares MEP.</li>
    <li><b>Riesgo país:</b> serie de argentinadatos.com.</li>
  </ul>
</section>
"""


LEGAL = """
<div class="titulo">
  <h1>Aviso legal</h1>
  <p class="bajada">Qué es Mercadito y qué no es.</p>
</div>

<section class="bloque texto">
  <ol class="legal">
    <li><b>Qué es.</b> Información general, no personalizada, publicada con fines informativos y educativos. No es una oferta,
      una solicitud ni una recomendación para comprar, vender o mantener ningún instrumento, ni asesoramiento financiero, legal o impositivo.</li>
    <li><b>Quiénes lo hacen.</b> Quienes publican Mercadito no son asesores, agentes ni intermediarios registrados ante la
      Comisión Nacional de Valores (CNV) y no ofrecen servicios de inversión.</li>
    <li><b>Los patrones.</b> «En su promedio o debajo» y «Subió fuerte» describen condiciones del precio calculadas con reglas fijas,
      explicadas en <a href="../metodologia/">Cómo se calcula</a>. No anticipan resultados ni sugieren operar.</li>
    <li><b>Los datos.</b> Provienen de terceros (dolarapi.com, comparadolar.ar, argentinadatos.com, BCRA, Yahoo Finance, Wikipedia,
      Nasdaq, data912.com y TradingView) y se muestran sin garantía de exactitud, integridad ni actualidad: pueden tener errores o demoras.
      Antes de operar, verificá precios y condiciones con tu banco, agente o broker.</li>
    <li><b>Los riesgos.</b> Invertir implica riesgos, incluida la pérdida del capital invertido. Los resultados pasados no garantizan
      resultados futuros. Los instrumentos en moneda extranjera y los CEDEARs suman riesgo cambiario.</li>
    <li><b>Responsabilidad.</b> Quienes publican Mercadito no se responsabilizan por pérdidas o daños derivados del uso de esta información.
      Cada decisión de inversión es exclusivamente de quien la toma.</li>
    <li><b>Privacidad.</b> Mercadito no usa cookies ni herramientas de medición. Solo guarda en tu navegador si elegiste el modo claro u oscuro.
      El gráfico de TradingView se carga recién cuando lo abrís; a partir de ahí rige la política de privacidad de TradingView.</li>
    <li><b>Marcas.</b> S&amp;P 500 y S&amp;P Merval son marcas de S&amp;P Dow Jones Indices LLC y sus licenciantes. Mercadito no está afiliado,
      patrocinado ni avalado por S&amp;P Dow Jones Indices, BYMA, Nasdaq, Yahoo, TradingView, los proveedores de datos ni las empresas o entidades mencionadas.</li>
  </ol>
</section>
"""


CSS = r"""
.texto{max-width:72ch}
.texto p,.texto li{font-size:16px;line-height:1.6;color:var(--tinta-2)}
.texto p{margin-top:10px}
.texto ul,.texto ol{margin-top:10px}
.texto ul li{padding:9px 0;border-bottom:1px solid var(--linea)}
.texto ul li:last-child{border-bottom:0}
.texto b{color:var(--tinta);font-weight:700}
.legal{list-style:decimal;padding-left:24px}
.legal li{padding:7px 0 7px 4px}
.legal li::marker{font-weight:700;color:var(--tinta)}
"""


def generar():
    comun.escribir("metodologia", comun.pagina(
        "metodologia", "Cómo se calcula",
        "De dónde sale cada dato de Mercadito y qué cuenta se hace con él.", METODOLOGIA, css=CSS))
    comun.escribir("legal", comun.pagina(
        "legal", "Aviso legal",
        "Mercadito publica información con fines educativos e informativos; no es una recomendación de inversión.", LEGAL, css=CSS))
