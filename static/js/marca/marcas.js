/* =========================================================
   CYS Licorera — Marcas
   Cada acción (crear, editar, eliminar, buscar, filtrar) dispara
   una petición real al servidor (form submit / GET con querystring).
   Django repinta la tabla en cada respuesta.
   ========================================================= */

(function () {
  "use strict";

  function init() {
    console.log("[marcas.js] Script cargado y DOM listo.");

    function $id(id) {
      const el = document.getElementById(id);
      if (!el) console.warn("[marcas.js] No se encontró el elemento #" + id);
      return el;
    }

    const tableBody = $id("cysTableBody");
    const deleteOverlay = $id("cysDeleteOverlay");
    const modalOverlay = $id("cysModalOverlay");

    // ---------------------------------------------------------
    // Filtro de estado (select personalizado) — dispara GET real
    // ---------------------------------------------------------
    const estadoSelect = $id("cysEstadoSelect");
    const estadoTrigger = $id("cysEstadoTrigger");
    const estadoLabel = $id("cysEstadoLabel");
    const estadoMenu = $id("cysEstadoMenu");
    const fieldEstadoFiltro = $id("fieldEstadoFiltro");
    const filtroForm = $id("cysFiltroForm");

    if (estadoTrigger && estadoSelect) {
      estadoTrigger.addEventListener("click", function () {
        estadoSelect.classList.toggle("cys-select--open");
      });
    }

    if (estadoMenu && fieldEstadoFiltro && estadoLabel && estadoSelect && filtroForm) {
      estadoMenu.addEventListener("click", function (e) {
        const item = e.target.closest("li");
        if (!item) return;
        fieldEstadoFiltro.value = item.dataset.value;
        estadoLabel.textContent = item.textContent.trim();
        estadoSelect.classList.remove("cys-select--open");
        filtroForm.submit();
      });
    }

    document.addEventListener("click", function (e) {
      if (estadoSelect && !estadoSelect.contains(e.target)) {
        estadoSelect.classList.remove("cys-select--open");
      }
    });

    // ---------------------------------------------------------
    // Búsqueda — GET real, con pequeño debounce
    // ---------------------------------------------------------
    const inputBuscar = $id("inputBuscar");
    let debounceTimer = null;

    if (inputBuscar && filtroForm) {
      inputBuscar.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function () {
          filtroForm.submit();
        }, 500);
      });

      // Como la búsqueda recarga la página, devolvemos el foco al input
      // (con el cursor al final) para poder seguir escribiendo.
      if (new URLSearchParams(window.location.search).has("q") && inputBuscar.value) {
        inputBuscar.focus();
        const len = inputBuscar.value.length;
        try { inputBuscar.setSelectionRange(len, len); } catch (err) { /* noop */ }
      }
    }

    // ---------------------------------------------------------
    // Modal: nueva / editar marca
    // ---------------------------------------------------------
    const modalTitle = $id("cysModalTitle");
    const modalSubtitle = $id("cysModalSubtitle");
    const modalForm = $id("cysMarcaForm");
    const fieldNombre = $id("fieldNombre");
    const fieldDescripcion = $id("fieldDescripcion");
    const fieldEstadoActivo = $id("fieldEstadoActivo");
    const fieldEstadoInactivo = $id("fieldEstadoInactivo");
    const fieldEstadoValue = $id("fieldEstadoValue");
    const cysEstadoActivaCard = $id("cysEstadoActivaCard");
    const cysEstadoInactivaCard = $id("cysEstadoInactivaCard");
    const cysCharCount = $id("cysCharCount");

    function getUrls() {
      if (!window.CYS_URLS) {
        console.error("[marcas.js] window.CYS_URLS no está definido. Revisa el <script> inline antes de marcas.js.");
        return null;
      }
      return window.CYS_URLS;
    }

    function actualizarEstadoSeleccionado() {
      if (!fieldEstadoActivo || !fieldEstadoValue) return;
      const activa = fieldEstadoActivo.checked;
      fieldEstadoValue.value = activa ? "activo" : "inactivo";
      if (cysEstadoActivaCard) cysEstadoActivaCard.classList.toggle("cys-estado-card--selected", activa);
      if (cysEstadoInactivaCard) cysEstadoInactivaCard.classList.toggle("cys-estado-card--selected", !activa);
    }

    function setEstado(esActivo) {
      if (fieldEstadoActivo) fieldEstadoActivo.checked = esActivo;
      if (fieldEstadoInactivo) fieldEstadoInactivo.checked = !esActivo;
      actualizarEstadoSeleccionado();
    }

    if (fieldEstadoActivo) fieldEstadoActivo.addEventListener("change", actualizarEstadoSeleccionado);
    if (fieldEstadoInactivo) fieldEstadoInactivo.addEventListener("change", actualizarEstadoSeleccionado);

    function actualizarContador() {
      if (fieldDescripcion && cysCharCount) {
        cysCharCount.textContent = fieldDescripcion.value.length + "/200";
      }
    }
    if (fieldDescripcion) fieldDescripcion.addEventListener("input", actualizarContador);

    // --- Helpers de apertura/cierre con FALLBACK inline ---------------
    // Si algún CSS externo (p. ej. base.css) pisa el "display:flex" de
    // .cys-modal-overlay--open, forzamos el estilo inline como respaldo.
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

    function abrirModalNueva() {
      const urls = getUrls();
      if (!modalForm) { console.error("[marcas.js] Falta #cysMarcaForm en el HTML."); return; }
      if (!modalOverlay) { console.error("[marcas.js] Falta #cysModalOverlay en el HTML."); return; }
      if (modalTitle) modalTitle.textContent = "Nueva marca";
      if (modalSubtitle) modalSubtitle.textContent = "Registra una nueva marca de productos";
      modalForm.reset();
      if (urls) modalForm.action = urls.crear;
      setEstado(true);
      actualizarContador();
      mostrarOverlay(modalOverlay);
      if (fieldNombre) fieldNombre.focus();
    }

    function abrirModalEditar(datos) {
      const urls = getUrls();
      if (!modalForm || !modalOverlay) return;
      if (modalTitle) modalTitle.textContent = "Editar marca";
      if (modalSubtitle) modalSubtitle.textContent = "Actualiza los datos de la marca";
      if (fieldNombre) fieldNombre.value = datos.nombre || "";
      if (fieldDescripcion) fieldDescripcion.value = datos.descripcion || "";
      setEstado(datos.estado === "activo");
      actualizarContador();
      if (urls) modalForm.action = urls.editarBase + datos.id + "/";
      mostrarOverlay(modalOverlay);
      if (fieldNombre) fieldNombre.focus();
    }

    function cerrarModal() {
      ocultarOverlay(modalOverlay);
    }

    const btnNuevaMarca = $id("btnNuevaMarca");
    const cysModalClose = $id("cysModalClose");
    const cysCancelBtn = $id("cysCancelBtn");

    if (btnNuevaMarca) {
      btnNuevaMarca.addEventListener("click", abrirModalNueva);
    } else {
      console.error("[marcas.js] NO se encontró #btnNuevaMarca. Revisa que el botón tenga exactamente ese id.");
    }

    if (cysModalClose) cysModalClose.addEventListener("click", cerrarModal);
    if (cysCancelBtn) cysCancelBtn.addEventListener("click", cerrarModal);

    if (modalOverlay) {
      modalOverlay.addEventListener("click", function (e) {
        if (e.target === modalOverlay) cerrarModal();
      });
    }

    // ---------------------------------------------------------
    // Modal: confirmar eliminación
    // ---------------------------------------------------------
    const deleteForm = $id("cysDeleteForm");
    const deleteName = $id("cysDeleteName");

    function abrirModalEliminar(id, nombre) {
      const urls = getUrls();
      if (!deleteForm || !deleteOverlay) return;
      if (urls) deleteForm.action = urls.eliminarBase + id + "/";
      if (deleteName) deleteName.textContent = nombre;
      mostrarOverlay(deleteOverlay);
    }

    function cerrarModalEliminar() {
      ocultarOverlay(deleteOverlay);
    }

    const cysDeleteClose = $id("cysDeleteClose");
    const cysDeleteCancel = $id("cysDeleteCancel");

    if (cysDeleteClose) cysDeleteClose.addEventListener("click", cerrarModalEliminar);
    if (cysDeleteCancel) cysDeleteCancel.addEventListener("click", cerrarModalEliminar);

    if (deleteOverlay) {
      deleteOverlay.addEventListener("click", function (e) {
        if (e.target === deleteOverlay) cerrarModalEliminar();
      });
    }

    // ---------------------------------------------------------
    // Delegación de eventos en la tabla (filas vienen de Django)
    // ---------------------------------------------------------
    if (tableBody) {
      tableBody.addEventListener("click", function (e) {
        const btnEditar = e.target.closest(".cys-action-btn--edit");
        const btnEliminar = e.target.closest(".cys-action-btn--delete");

        if (btnEditar) {
          abrirModalEditar({
            id: btnEditar.dataset.id,
            nombre: btnEditar.dataset.nombre,
            descripcion: btnEditar.dataset.descripcion,
            estado: btnEditar.dataset.estado,
          });
        }

        if (btnEliminar) {
          abrirModalEliminar(btnEliminar.dataset.id, btnEliminar.dataset.nombre);
        }
      });
    }

    // ---------------------------------------------------------
    // Cierre de modales con tecla Escape
    // ---------------------------------------------------------
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      cerrarModal();
      cerrarModalEliminar();
    });
  }

  // El script ahora se carga al final del contenido: el DOM puede estar
  // ya listo o no, así que cubrimos ambos casos.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();