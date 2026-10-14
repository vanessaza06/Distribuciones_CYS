/* =========================================================
   CYS Licorera — Marcas
   Todo con delegación de eventos sobre `document` (fase de captura).
   Modal crear/editar, filtros, fechas, ordenamiento y exportación.
   Sin librerías externas: todo abre al instante.
   ========================================================= */

(function () {
  "use strict";

  window.CYS_MARCAS_OK = true;

  function $id(id) { return document.getElementById(id); }

  /* ---------------- Modal ---------------- */

  function mostrarOverlay(overlay) {
    overlay.classList.add("cys-modal-overlay--open");
    overlay.style.setProperty("display", "flex", "important");
  }

  function ocultarOverlay(overlay) {
    if (!overlay) return;
    overlay.classList.remove("cys-modal-overlay--open");
    overlay.style.setProperty("display", "none", "important");
  }

  function actualizarEstadoSeleccionado() {
    var activo = $id("fieldEstadoActivo");
    var valor = $id("fieldEstadoValue");
    if (!activo || !valor) return;
    var esActiva = activo.checked;
    valor.value = esActiva ? "activo" : "inactivo";
    var cardA = $id("cysEstadoActivaCard");
    var cardI = $id("cysEstadoInactivaCard");
    if (cardA) cardA.classList.toggle("cys-estado-card--selected", esActiva);
    if (cardI) cardI.classList.toggle("cys-estado-card--selected", !esActiva);
  }

  function setEstado(esActivo) {
    var a = $id("fieldEstadoActivo");
    var i = $id("fieldEstadoInactivo");
    if (a) a.checked = esActivo;
    if (i) i.checked = !esActivo;
    actualizarEstadoSeleccionado();
  }

  function actualizarContador() {
    var desc = $id("fieldDescripcion");
    var cont = $id("cysCharCount");
    if (desc && cont) cont.textContent = desc.value.length + "/200";
  }

  function resetBotonGuardar() {
    var btn = $id("cysGuardarBtn");
    if (btn) btn.disabled = false;
  }

  function abrirModalNueva() {
    var overlay = $id("cysModalOverlay");
    var form = $id("cysMarcaForm");
    if (!overlay || !form) return;

    var page = document.querySelector(".cys-marcas-page");
    $id("cysModalTitle").textContent = "Nueva marca";
    $id("cysModalSubtitle").textContent = "Registra una nueva marca de productos";
    form.reset();
    if (page && page.dataset.urlCrear) form.action = page.dataset.urlCrear;
    setEstado(true);
    actualizarContador();
    resetBotonGuardar();
    mostrarOverlay(overlay);
    var nombre = $id("fieldNombre");
    if (nombre) nombre.focus();
  }

  function abrirModalEditar(btn) {
    var overlay = $id("cysModalOverlay");
    var form = $id("cysMarcaForm");
    if (!overlay || !form) return;

    $id("cysModalTitle").textContent = "Editar marca";
    $id("cysModalSubtitle").textContent = "Actualiza los datos de la marca";
    $id("fieldNombre").value = btn.dataset.nombre || "";
    $id("fieldDescripcion").value = btn.dataset.descripcion || "";
    setEstado(btn.dataset.estado === "activo");
    actualizarContador();
    resetBotonGuardar();
    form.action = btn.dataset.url;   // URL propia de cada marca
    mostrarOverlay(overlay);
    $id("fieldNombre").focus();
  }

  function cerrarModal() {
    ocultarOverlay($id("cysModalOverlay"));
  }

  /* ---------------- Select de estado (Todos los estados) ----------------
     Se controla con estilo en línea (!important) para que ningún CSS
     externo pueda dejarlo siempre oculto o siempre visible. */

  function setSelectAbierto(abrir) {
    var sel = $id("cysEstadoSelect");
    var menu = $id("cysEstadoMenu");
    if (!sel || !menu) return;
    sel.classList.toggle("cys-select--open", abrir);
    menu.style.setProperty("display", abrir ? "block" : "none", "important");
  }

  function selectAbierto() {
    var sel = $id("cysEstadoSelect");
    return !!(sel && sel.classList.contains("cys-select--open"));
  }

  function cerrarSelect() { setSelectAbierto(false); }

  /* ---------------- Exportar ---------------- */

  function cerrarExport() {
    var box = $id("cysExport");
    if (box) box.classList.remove("cys-export--open");
  }

  // URL de exportación con los filtros actuales (incluye Desde/Hasta aunque no se hayan aplicado)
  function urlExportacion(tipo) {
    var page = document.querySelector(".cys-marcas-page");
    if (!page || !page.dataset.urlLista) return null;

    var form = $id("cysFiltroForm");
    var params = new URLSearchParams();
    if (form) {
      new FormData(form).forEach(function (valor, clave) {
        if (valor !== "" && clave !== "page") params.append(clave, valor);
      });
    }
    params.set("export", tipo);
    return page.dataset.urlLista + "?" + params.toString();
  }

  function exportar(tipo) {
    var url = urlExportacion(tipo);
    if (!url) return;

    if (tipo === "imprimir") {
      window.open(url, "_blank");
      return;
    }

    // Excel / PDF: aviso visual mientras el servidor genera el archivo
    var label = $id("cysExportLabel");
    var trigger = $id("cysExportTrigger");
    if (label) label.textContent = "Generando…";
    if (trigger) trigger.disabled = true;
    window.location.href = url;   // descarga directa (attachment): la página no se recarga
    setTimeout(function () {
      if (label) label.textContent = "Exportar";
      if (trigger) trigger.disabled = false;
    }, 3500);
  }

  /* ---------------- Fechas ---------------- */

  function validarRangoFechas(cambiado) {
    var desde = $id("fieldDesde");
    var hasta = $id("fieldHasta");
    if (!desde || !hasta) return;

    hasta.min = desde.value || "";
    desde.max = hasta.value || "";

    if (desde.value && hasta.value && desde.value > hasta.value) {
      if (cambiado === desde) hasta.value = desde.value;
      else desde.value = hasta.value;
    }
  }

  /* ---------------- Ordenar tabla (sin librerías) ---------------- */

  var orden = { col: null, asc: true };

  function ordenarTabla(th) {
    var tbody = $id("cysTableBody");
    if (!tbody) return;

    var col = parseInt(th.dataset.col, 10);
    var esNum = th.dataset.type === "num";
    orden.asc = (orden.col === col) ? !orden.asc : true;
    orden.col = col;

    var filas = Array.prototype.slice.call(tbody.rows);
    filas.sort(function (a, b) {
      var x = a.cells[col].textContent.trim();
      var y = b.cells[col].textContent.trim();
      var r = esNum
        ? (parseFloat(x) || 0) - (parseFloat(y) || 0)
        : x.localeCompare(y, "es", { sensitivity: "base" });
      return orden.asc ? r : -r;
    });

    var frag = document.createDocumentFragment();
    filas.forEach(function (tr) { frag.appendChild(tr); });
    tbody.appendChild(frag);

    document.querySelectorAll("#tablaMarcas th.cys-sortable").forEach(function (h) {
      h.classList.remove("cys-sort-asc", "cys-sort-desc");
    });
    th.classList.add(orden.asc ? "cys-sort-asc" : "cys-sort-desc");
  }

  /* ---------------- Clicks (fase de captura) ---------------- */

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;

    if (t.closest("#btnNuevaMarca")) { abrirModalNueva(); return; }

    var btnEditar = t.closest(".cys-action-btn--edit");
    if (btnEditar) { abrirModalEditar(btnEditar); return; }

    if (t.closest("#cysModalClose") || t.closest("#cysCancelBtn")) { cerrarModal(); return; }
    if (t.id === "cysModalOverlay") { cerrarModal(); return; }

    /* Exportar */
    if (t.closest("#cysExportTrigger")) {
      var box = $id("cysExport");
      if (box) box.classList.toggle("cys-export--open");
      cerrarSelect();
      return;
    }

    var itemExport = t.closest("#cysExportMenu li");
    if (itemExport) {
      cerrarExport();
      exportar(itemExport.dataset.export);
      return;
    }

    /* Select de estado: abrir / cerrar */
    if (t.closest("#cysEstadoTrigger")) {
      e.preventDefault();
      setSelectAbierto(!selectAbierto());
      cerrarExport();
      return;
    }

    /* Select de estado: elegir una opción */
    var item = t.closest("#cysEstadoMenu li");
    if (item) {
      var hidden = $id("fieldEstadoFiltro");
      var label = $id("cysEstadoLabel");
      var form = $id("cysFiltroForm");
      if (hidden) hidden.value = item.dataset.value;
      if (label) label.textContent = item.textContent.trim();
      cerrarSelect();
      if (form) form.submit();
      return;
    }

    /* Ordenar por columna */
    var th = t.closest("#tablaMarcas th.cys-sortable");
    if (th) { ordenarTabla(th); return; }

    /* Clic fuera: cerrar menús */
    if (!t.closest("#cysEstadoSelect")) cerrarSelect();
    if (!t.closest("#cysExport")) cerrarExport();
  }, true);

  /* ---------------- Change / Input / Submit / Keydown ---------------- */

  var debounceTimer = null;

  document.addEventListener("change", function (e) {
    var t = e.target;
    if (!t) return;

    if (t.name === "estado_radio") actualizarEstadoSeleccionado();

    if (t.id === "fieldDesde" || t.id === "fieldHasta") {
      validarRangoFechas(t);
      var form = $id("cysFiltroForm");
      if (form) form.submit();
    }
  });

  document.addEventListener("input", function (e) {
    var t = e.target;
    if (!t) return;

    if (t.id === "fieldDescripcion") actualizarContador();

    if (t.id === "inputBuscar") {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        var form = $id("cysFiltroForm");
        if (form) form.submit();
      }, 400);
    }
  });

  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (!f) return;

    if (f.id === "cysMarcaForm") {
      actualizarEstadoSeleccionado();
      var g = $id("cysGuardarBtn");
      // se desactiva después del envío para evitar doble clic
      if (g) setTimeout(function () { g.disabled = true; }, 0);
      return;
    }

    // Activar / desactivar: evita doble envío
    if (f.matches && f.matches(".cys-row-actions form")) {
      var b = f.querySelector("button");
      if (b) setTimeout(function () { b.disabled = true; }, 0);
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    cerrarModal();
    cerrarSelect();
    cerrarExport();
  });

  /* ---------------- Inicio ---------------- */

  function alListo() {
    // Mover el modal al <body> para que ningún contenedor lo recorte
    var ov = $id("cysModalOverlay");
    if (ov && ov.parentElement !== document.body) document.body.appendChild(ov);

    cerrarSelect();               // menú de estados cerrado al cargar
    validarRangoFechas(null);
    actualizarEstadoSeleccionado();

    // Si venimos de una búsqueda, dejar el cursor al final del texto
    var buscar = $id("inputBuscar");
    if (buscar && buscar.value && new URLSearchParams(window.location.search).has("q")) {
      buscar.focus();
      var len = buscar.value.length;
      try { buscar.setSelectionRange(len, len); } catch (err) { /* noop */ }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", alListo);
  } else {
    alListo();
  }
})();