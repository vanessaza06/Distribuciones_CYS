/* =========================================================
   CYS Licorera — Marcas
   Todos los botones usan delegación de eventos sobre `document`:
   funcionan aunque los elementos se muevan de lugar o se
   repinten, y no dependen de que cada #id exista al cargar.
   ========================================================= */

(function () {
  "use strict";

  // Señal para que marcas.html sepa que este archivo sí cargó.
  window.CYS_MARCAS_OK = true;
  console.log("[marcas.js] Script cargado.");

  function $id(id) {
    return document.getElementById(id);
  }

  // ---------------------------------------------------------
  // URLs (crear / editar / eliminar)
  // Primero window.CYS_URLS; si no existe, data-* de la página.
  // ---------------------------------------------------------
  function getUrls() {
    if (window.CYS_URLS) return window.CYS_URLS;
    var page = document.querySelector(".cys-marcas-page");
    if (page && page.dataset.urlCrear) {
      return {
        crear: page.dataset.urlCrear,
        editarBase: page.dataset.urlEditarBase,
        eliminarBase: page.dataset.urlEliminarBase,
      };
    }
    console.error("[marcas.js] No se encontraron las URLs de crear/editar/eliminar.");
    return null;
  }

  // ---------------------------------------------------------
  // Abrir / cerrar overlays (con fallback inline por si base.css
  // pisa el display de la clase)
  // ---------------------------------------------------------
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

  // ---------------------------------------------------------
  // Modal nueva / editar marca
  // ---------------------------------------------------------
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

  // ---------------------------------------------------------
  // Modal eliminar
  // ---------------------------------------------------------
  function abrirModalEliminar(id, nombre) {
    var overlay = $id("cysDeleteOverlay");
    var form = $id("cysDeleteForm");
    if (!overlay || !form) return;
    var urls = getUrls();
    var lbl = $id("cysDeleteName");
    if (urls) form.action = urls.eliminarBase + id + "/";
    if (lbl) lbl.textContent = nombre;
    mostrarOverlay(overlay);
  }

  function cerrarModalEliminar() {
    ocultarOverlay($id("cysDeleteOverlay"));
  }

  // ---------------------------------------------------------
  // Filtro de estado (select personalizado)
  // ---------------------------------------------------------
  function cerrarSelect() {
    var sel = $id("cysEstadoSelect");
    if (sel) sel.classList.remove("cys-select--open");
  }

  // ---------------------------------------------------------
  // CLICS (un solo listener para todos los botones)
  // ---------------------------------------------------------
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;

    // Botón "Nueva marca"
    if (t.closest("#btnNuevaMarca")) {
      abrirModalNueva();
      return;
    }

    // Editar / Eliminar (botones de la tabla)
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

    var btnEliminar = t.closest(".cys-action-btn--delete");
    if (btnEliminar) {
      abrirModalEliminar(btnEliminar.dataset.id, btnEliminar.dataset.nombre);
      return;
    }

    // Cerrar / cancelar modal de marca
    if (t.closest("#cysModalClose") || t.closest("#cysCancelBtn")) {
      cerrarModal();
      return;
    }

    // Cerrar / cancelar modal de eliminación
    if (t.closest("#cysDeleteClose") || t.closest("#cysDeleteCancel")) {
      cerrarModalEliminar();
      return;
    }

    // Clic en el fondo oscuro
    if (t.id === "cysModalOverlay") { cerrarModal(); return; }
    if (t.id === "cysDeleteOverlay") { cerrarModalEliminar(); return; }

    // Select de estado: abrir/cerrar
    if (t.closest("#cysEstadoTrigger")) {
      var sel = $id("cysEstadoSelect");
      if (sel) sel.classList.toggle("cys-select--open");
      return;
    }

    // Select de estado: elegir una opción y filtrar (GET real)
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

    // Clic en cualquier otro lado: cerrar el select
    if (!t.closest("#cysEstadoSelect")) cerrarSelect();
  });

  // ---------------------------------------------------------
  // CAMBIOS E INPUTS
  // ---------------------------------------------------------
  var debounceTimer = null;

  document.addEventListener("change", function (e) {
    if (e.target && e.target.name === "estado_radio") {
      actualizarEstadoSeleccionado();
    }
  });

  document.addEventListener("input", function (e) {
    var t = e.target;
    if (!t) return;

    if (t.id === "fieldDescripcion") actualizarContador();

    // Búsqueda: GET real con pequeño debounce
    if (t.id === "inputBuscar") {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        var form = $id("cysFiltroForm");
        if (form) form.submit();
      }, 500);
    }
  });

  // Antes de guardar, asegurar que el estado oculto está sincronizado
  document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "cysMarcaForm") {
      actualizarEstadoSeleccionado();
    }
  });

  // Cerrar modales con Escape
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    cerrarModal();
    cerrarModalEliminar();
    cerrarSelect();
  });

  // ---------------------------------------------------------
  // Al cargar el DOM: mover modales al <body> y devolver el foco
  // al buscador (la búsqueda recarga la página)
  // ---------------------------------------------------------
  function alListo() {
    ["cysModalOverlay", "cysDeleteOverlay"].forEach(function (id) {
      var ov = $id(id);
      if (ov && ov.parentElement !== document.body) {
        document.body.appendChild(ov);
      }
    });

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