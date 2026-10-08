/* =========================================================
   CYS Licorera — Marcas
   Delegación de eventos en fase de CAPTURA sobre `document`.
   Incluye: modal crear/editar, filtros, rango de fechas
   y exportación (Excel, PDF, Imprimir).
   ========================================================= */

(function () {
  "use strict";

  window.CYS_MARCAS_OK = true;
  console.log("[marcas.js] Script cargado.");

  function $id(id) {
    return document.getElementById(id);
  }

  function getUrls() {
    if (window.CYS_URLS) return window.CYS_URLS;
    var page = document.querySelector(".cys-marcas-page");
    if (page && page.dataset.urlCrear) {
      return {
        crear: page.dataset.urlCrear,
        editarBase: page.dataset.urlEditarBase,
      };
    }
    console.error("[marcas.js] No se encontraron las URLs de crear/editar.");
    return null;
  }

  /* ---------------- Modal ---------------- */

  function mostrarOverlay(overlay) {
    if (!overlay) return;
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

  function abrirModalNueva() {
    var overlay = $id("cysModalOverlay");
    var form = $id("cysMarcaForm");
    if (!overlay || !form) {
      console.error("[marcas.js] Falta #cysModalOverlay o #cysMarcaForm en el HTML.");
      return;
    }
    var urls = getUrls();
    var titulo = $id("cysModalTitle");
    var sub = $id("cysModalSubtitle");
    if (titulo) titulo.textContent = "Nueva marca";
    if (sub) sub.textContent = "Registra una nueva marca de productos";
    form.reset();
    if (urls) form.action = urls.crear;
    setEstado(true);
    actualizarContador();
    mostrarOverlay(overlay);
    var nombre = $id("fieldNombre");
    if (nombre) nombre.focus();
  }

  function abrirModalEditar(datos) {
    var overlay = $id("cysModalOverlay");
    var form = $id("cysMarcaForm");
    if (!overlay || !form) return;
    var urls = getUrls();
    var titulo = $id("cysModalTitle");
    var sub = $id("cysModalSubtitle");
    var nombre = $id("fieldNombre");
    var desc = $id("fieldDescripcion");
    if (titulo) titulo.textContent = "Editar marca";
    if (sub) sub.textContent = "Actualiza los datos de la marca";
    if (nombre) nombre.value = datos.nombre || "";
    if (desc) desc.value = datos.descripcion || "";
    setEstado(datos.estado === "activo");
    actualizarContador();
    if (urls) form.action = urls.editarBase + datos.id + "/";
    mostrarOverlay(overlay);
    if (nombre) nombre.focus();
  }

  function cerrarModal() {
    ocultarOverlay($id("cysModalOverlay"));
  }

  /* ---------------- Select de estado ---------------- */

  function cerrarSelect() {
    var sel = $id("cysEstadoSelect");
    if (sel) sel.classList.remove("cys-select--open");
  }

  /* ---------------- Exportar ---------------- */

  function cerrarExport() {
    var box = $id("cysExport");
    if (box) box.classList.remove("cys-export--open");
  }

  // Construye la URL de exportación con los filtros actuales
  // (búsqueda, estado, desde, hasta), aunque no se hayan aplicado aún.
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
    if (!url) {
      console.error("[marcas.js] No se encontró la URL de exportación:", tipo);
      return;
    }
    if (tipo === "imprimir") {
      window.open(url, "_blank");
    } else {
      window.location.href = url; // descarga directa (Content-Disposition: attachment)
    }
  }

  /* ---------------- Fechas ---------------- */

  // Evita rangos inválidos: "hasta" no puede ser menor que "desde".
  function validarRangoFechas(cambiado) {
    var desde = $id("fieldDesde");
    var hasta = $id("fieldHasta");
    if (!desde || !hasta) return true;

    hasta.min = desde.value || "";
    desde.max = hasta.value || "";

    if (desde.value && hasta.value && desde.value > hasta.value) {
      // Si el usuario cambió uno, el otro se ajusta para mantener coherencia.
      if (cambiado === desde) hasta.value = desde.value;
      else desde.value = hasta.value;
    }
    return true;
  }

  /* ---------------- Clicks (fase de captura) ---------------- */

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;

    if (t.closest("#btnNuevaMarca")) {
      abrirModalNueva();
      return;
    }

    var btnEditar = t.closest(".cys-action-btn--edit");
    if (btnEditar) {
      abrirModalEditar({
        id: btnEditar.dataset.id,
        nombre: btnEditar.dataset.nombre,
        descripcion: btnEditar.dataset.descripcion,
        estado: btnEditar.dataset.estado,
      });
      return;
    }

    if (t.closest("#cysModalClose") || t.closest("#cysCancelBtn")) {
      cerrarModal();
      return;
    }

    if (t.id === "cysModalOverlay") { cerrarModal(); return; }

    /* --- Exportar --- */
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

    /* --- Select de estado --- */
    if (t.closest("#cysEstadoTrigger")) {
      var sel = $id("cysEstadoSelect");
      if (sel) sel.classList.toggle("cys-select--open");
      cerrarExport();
      return;
    }

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

    if (!t.closest("#cysEstadoSelect")) cerrarSelect();
    if (!t.closest("#cysExport")) cerrarExport();
  }, true);

  /* ---------------- Change / Input / Submit / Keydown ---------------- */

  var debounceTimer = null;

  document.addEventListener("change", function (e) {
    var t = e.target;
    if (!t) return;

    if (t.name === "estado_radio") {
      actualizarEstadoSeleccionado();
    }

    // Al cambiar una fecha, se valida el rango y se filtra la tabla.
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
      }, 500);
    }
  });

  document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "cysMarcaForm") {
      actualizarEstadoSeleccionado();
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
    var ov = $id("cysModalOverlay");
    if (ov && ov.parentElement !== document.body) {
      document.body.appendChild(ov);
    }

    validarRangoFechas(null);

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