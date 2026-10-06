/* Mercadito: funciones compartidas por todas las páginas.
   Todo cuelga de window.Mercadito para no chocar con el código de cada sección. */
(function () {
  "use strict";

  /* ---------- abierto desde el disco ----------
     En la web, un link a "dolar/" abre dolar/index.html. Abriendo los archivos
     directo (file://) el navegador muestra el listado de la carpeta, así que
     ahí se completa el nombre del archivo. */
  if (location.protocol === "file:") {
    document.querySelectorAll("a[href]").forEach(a => {
      const h = a.getAttribute("href");
      if (/^[a-z]+:|^#/i.test(h)) return;
      if (h === "" || h.endsWith("/")) a.setAttribute("href", (h || "./") + "index.html");
    });
  }

  /* ---------- modo claro / oscuro ---------- */
  const raiz = document.documentElement;
  const sistemaOscuro = matchMedia("(prefers-color-scheme: dark)");
  const boton = document.getElementById("tema");
  const reacciones = [];

  function oscuroAhora() {
    const t = raiz.getAttribute("data-tema");
    return t === "oscuro" || (!t && sistemaOscuro.matches);
  }
  function pintarTema() {
    const o = oscuroAhora();
    if (boton) {
      document.getElementById("tema-txt").textContent = o ? "Modo claro" : "Modo oscuro";
      boton.setAttribute("aria-label", o ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
      boton.classList.toggle("es-oscuro", o);
    }
    const t = raiz.getAttribute("data-tema");
    // la barra del navegador toma el color del cabezal
    document.querySelectorAll("meta[name=theme-color]").forEach(m => {
      m.content = t ? (o ? "#050607" : "#111317") : (m.media.includes("dark") ? "#050607" : "#111317");
    });
    reacciones.forEach(f => f());
  }
  if (boton) {
    boton.addEventListener("click", () => {
      const nuevo = oscuroAhora() ? "claro" : "oscuro";
      raiz.setAttribute("data-tema", nuevo);
      try { localStorage.setItem("tema", nuevo); } catch (e) {}
      pintarTema();
    });
  }
  sistemaOscuro.addEventListener("change", pintarTema);
  pintarTema();

  /* ---------- formato ---------- */
  // Textos que vienen de fuentes externas: se escapan siempre antes de ir al HTML
  function esc(s) {
    return String(s).replace(/[&<>"']/g, c => "&#" + c.charCodeAt(0) + ";");
  }
  function num(v, dec) {
    if (v === null || v === undefined || isNaN(v)) return "—";
    const x = Number(Number(v).toFixed(dec));
    return (x === 0 ? 0 : x).toLocaleString("es-AR", {minimumFractionDigits: dec, maximumFractionDigits: dec})
      .replace("-", "−");
  }
  function pct(v, dec) {
    if (v === null || v === undefined || isNaN(v)) return "—";
    return (Number(Number(v).toFixed(dec)) > 0 ? "+" : "") + num(v, dec) + "%";
  }
  function pesos(v, dec) {
    return v === null || v === undefined ? "—" : "$ " + num(v, dec === undefined ? 2 : dec);
  }
  function dolares(v, dec) {
    return v === null || v === undefined ? "—" : "US$ " + num(v, dec === undefined ? 2 : dec);
  }
  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  function fecha(iso) {
    if (!iso) return "—";
    const [a, m, d] = iso.slice(0, 10).split("-");
    return d + "/" + m + "/" + a;
  }

  /* ---------- tabla ordenable ----------
     columnas: [{clave, asc}] alineadas con los <th> que tienen <button>. pintar(orden, asc) redibuja. */
  function ordenable(tabla, inicial, pintar) {
    let [orden, asc] = inicial;
    const marcar = () => tabla.querySelectorAll("th[data-k]").forEach(th => {
      if (th.dataset.k === orden) th.setAttribute("aria-sort", asc ? "ascending" : "descending");
      else th.removeAttribute("aria-sort");
    });
    tabla.querySelectorAll("th[data-k] button").forEach(b => b.addEventListener("click", () => {
      const k = b.parentElement.dataset.k;
      asc = orden === k ? !asc : b.parentElement.dataset.asc === "1";
      orden = k;
      marcar();
      pintar(orden, asc);
    }));
    marcar();
    pintar(orden, asc);
    return {estado: () => [orden, asc]};
  }
  function comparar(clave, asc) {
    return (a, b) => {
      const x = a[clave], y = b[clave];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      if (typeof x === "string") return asc ? x.localeCompare(y, "es") : y.localeCompare(x, "es");
      return asc ? x - y : y - x;
    };
  }

  /* ---------- gráfico de líneas ----------
     series: [{nombre, color: "var(--s1)", puntos: [["2026-01-02", 123.4], ...]}] ordenados por fecha.
     op: {formato(v), titulo, alto} */
  function linea(caja, series, op) {
    op = op || {};
    const formato = op.formato || (v => num(v, 2));
    const dibujar = () => {
      caja.innerHTML = "";
      caja.classList.add("grafico-linea");
      const conDatos = series.filter(s => s.puntos.length);
      if (!conDatos.length) {
        caja.innerHTML = "<p class='nota'>No hay datos para este período.</p>";
        return;
      }
      const W = Math.max(280, caja.clientWidth), H = op.alto || (W < 600 ? 220 : 280);
      const m = {i: 64, d: 14, a: 10, b: 26};
      const t = s => Date.parse(s + "T12:00:00");
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      conDatos.forEach(s => s.puntos.forEach(([f, v]) => {
        const x = t(f);
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (v < y0) y0 = v; if (v > y1) y1 = v;
      }));
      if (y0 === y1) { y0 -= 1; y1 += 1; }
      const pad = (y1 - y0) * 0.06; y0 -= pad; y1 += pad;
      if (x0 === x1) x1 = x0 + 86400000;
      const X = x => m.i + (x - x0) / (x1 - x0) * (W - m.i - m.d);
      const Y = y => m.a + (1 - (y - y0) / (y1 - y0)) * (H - m.a - m.b);

      // cuatro marcas "redondas" en el eje vertical
      const paso = (() => {
        const bruto = (y1 - y0) / 4, p = Math.pow(10, Math.floor(Math.log10(bruto))), f = bruto / p;
        return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
      })();
      let svg = "<svg viewBox='0 0 " + W + " " + H + "' role='img' aria-label='" + esc(op.titulo || "Gráfico") + "'>";
      for (let v = Math.ceil(y0 / paso) * paso; v <= y1; v += paso) {
        svg += "<line class='grilla' x1='" + m.i + "' x2='" + (W - m.d) + "' y1='" + Y(v) + "' y2='" + Y(v) + "'/>" +
          "<text class='eje' x='" + (m.i - 8) + "' y='" + (Y(v) + 4) + "' text-anchor='end'>" + esc(formato(v)) + "</text>";
      }
      const dias = (x1 - x0) / 86400000;
      const marcas = Math.max(2, Math.min(6, Math.floor(W / 120)));
      for (let k = 0; k <= marcas; k++) {
        const x = x0 + (x1 - x0) * k / marcas, d = new Date(x);
        const txt = dias > 370 ? MESES[d.getMonth()] + " " + String(d.getFullYear()).slice(2)
          : dias > 60 ? MESES[d.getMonth()] + (d.getMonth() === 0 ? " " + String(d.getFullYear()).slice(2) : "")
          : d.getDate() + " " + MESES[d.getMonth()];
        svg += "<text class='eje' x='" + X(x) + "' y='" + (H - 6) + "' text-anchor='" +
          (k === 0 ? "start" : k === marcas ? "end" : "middle") + "'>" + txt + "</text>";
      }
      conDatos.forEach(s => {
        const d = s.puntos.map(([f, v], i) => (i ? "L" : "M") + X(t(f)).toFixed(1) + " " + Y(v).toFixed(1)).join("");
        svg += "<path class='serie' d='" + d + "' style='stroke:" + s.color + "'/>";
      });
      // el último dato de cada serie, marcado con un punto
      conDatos.forEach(s => {
        const [f, v] = s.puntos[s.puntos.length - 1];
        svg += "<circle class='ultimo' cx='" + X(t(f)).toFixed(1) + "' cy='" + Y(v).toFixed(1) + "' r='4' style='fill:" + s.color + "'/>";
      });
      svg += "<line class='cursor' y1='" + m.a + "' y2='" + (H - m.b) + "' visibility='hidden'/>";
      svg += "<rect x='" + m.i + "' y='0' width='" + (W - m.i - m.d) + "' height='" + H + "' fill='transparent'/>";
      svg += "</svg>";
      caja.insertAdjacentHTML("beforeend", svg);
      if (conDatos.length > 1) {
        caja.insertAdjacentHTML("beforeend", "<div class='leyenda-graf'>" + conDatos.map(s =>
          "<span><i style='background:" + s.color + "'></i>" + esc(s.nombre) + "</span>").join("") + "</div>");
      }
      const tip = document.createElement("div");
      tip.className = "grafico-tip";
      tip.hidden = true;
      caja.appendChild(tip);

      // al pasar el mouse o el dedo: el valor de cada serie en la fecha más cercana
      const el = caja.querySelector("svg"), cursor = el.querySelector(".cursor");
      const cerca = (pts, x) => {
        let a = 0, b = pts.length - 1;
        while (b - a > 1) { const c = (a + b) >> 1; if (t(pts[c][0]) < x) a = c; else b = c; }
        return Math.abs(t(pts[a][0]) - x) <= Math.abs(t(pts[b][0]) - x) ? pts[a] : pts[b];
      };
      const mover = e => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width * W;
        if (px < m.i || px > W - m.d) { soltar(); return; }
        const x = x0 + (px - m.i) / (W - m.i - m.d) * (x1 - x0);
        const ref = cerca(conDatos[0].puntos, x);
        const xr = X(t(ref[0]));
        cursor.setAttribute("x1", xr); cursor.setAttribute("x2", xr); cursor.setAttribute("visibility", "visible");
        tip.innerHTML = "<b>" + fecha(ref[0]) + "</b><br>" + conDatos.map(s => {
          const p = cerca(s.puntos, t(ref[0]));
          return (conDatos.length > 1 ? esc(s.nombre) + ": " : "") + esc(formato(p[1]));
        }).join("<br>");
        tip.hidden = false;
        const izq = xr / W * r.width;
        tip.style.left = Math.min(Math.max(0, izq + 12), r.width - tip.offsetWidth) + "px";
      };
      const soltar = () => { tip.hidden = true; cursor.setAttribute("visibility", "hidden"); };
      el.addEventListener("pointermove", mover);
      el.addEventListener("pointerdown", mover);
      el.addEventListener("pointerleave", soltar);
    };
    dibujar();
    let ancho = caja.clientWidth;
    new ResizeObserver(() => {
      if (Math.abs(caja.clientWidth - ancho) > 4) { ancho = caja.clientWidth; dibujar(); }
    }).observe(caja);
  }

  // Recorta una serie [["aaaa-mm-dd", v], ...] a los últimos n días
  function desde(puntos, dias) {
    if (!puntos.length || !dias) return puntos;
    const fin = Date.parse(puntos[puntos.length - 1][0]);
    const corte = new Date(fin - dias * 86400000).toISOString().slice(0, 10);
    return puntos.filter(p => p[0] >= corte);
  }

  window.Mercadito = {
    oscuroAhora, alCambiarTema: f => reacciones.push(f),
    esc, num, pct, pesos, dolares, fecha, ordenable, comparar, linea, desde,
  };
})();
