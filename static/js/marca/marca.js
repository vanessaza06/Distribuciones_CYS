/* =========================================================
   CYS Licorera — Marcas
   Ya no simula backend en memoria: cada acción (crear, editar,
   eliminar, buscar, filtrar) dispara una petición real al
   servidor (form submit / GET con querystring). Django repinta
   la tabla en cada respuesta.
   ========================================================= */

(function () {
  "use strict";

  const tableBody = document.getElementById("cysTableBody");
  const deleteOverlay = document.getElementById("cysDeleteOverlay");
  const modalOverlay = document.getElementById("cysModalOverlay");

  // ---------------------------------------------------------
  // Filtro de estado (select personalizado) — dispara GET real
  // ---------------------------------------------------------
  const estadoSelect = document.getElementById("cysEstadoSelect");
  const estadoTrigger = document.getElementById("cysEstadoTrigger");
  const estadoLabel = document.getElementById("cysEstadoLabel");
  const estadoMenu = document.getElementById("cysEstadoMenu");
  const fieldEstadoFiltro = document.getElementById("fieldEstadoFiltro");
  const filtroForm = document.getElementById("cysFiltroForm");

  estadoTrigger.addEventListener("click", function () {
    estadoSelect.classList.toggle("cys-select--open");
  });

  estadoMenu.addEventListener("click", function (e) {
    const item = e.target.closest("li");
    if (!item) return;
    fieldEstadoFiltro.value = item.dataset.value;
    estadoLabel.textContent = item.textContent.trim();
    estadoSelect.classList.remove("cys-select--open");
    filtroForm.submit();
  });

  document.addEventListener("click", function (e) {
    if (!estadoSelect.contains(e.target)) {
      estadoSelect.classList.remove("cys-select--open");
    }
  });

  // ---------------------------------------------------------
  // Búsqueda — GET real, con pequeño debounce
  // ---------------------------------------------------------
  const inputBuscar = document.getElementById("inputBuscar");
  let debounceTimer = null;

  inputBuscar.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(function () {
      filtroForm.submit();
    }, 500);
  });

  // ---------------------------------------------------------
  // Modal: nueva / editar marca
  // ---------------------------------------------------------
  const modalTitle = document.getElementById("cysModalTitle");
  const modalForm = document.getElementById("cysMarcaForm");
  const fieldNombre = document.getElementById("fieldNombre");
  const fieldDescripcion = document.getElementById("fieldDescripcion");
  const fieldEstado = document.getElementById("fieldEstado");
  const fieldEstadoValue = document.getElementById("fieldEstadoValue");
  const fieldEstadoLabel = document.getElementById("fieldEstadoLabel");

  function abrirModalNueva() {
    modalTitle.textContent = "Nueva marca";
    modalForm.reset();
    modalForm.action = window.CYS_URLS.crear;
    fieldEstado.checked = true;
    fieldEstadoValue.value = "activo";
    fieldEstadoLabel.textContent = "Activa";
    modalOverlay.classList.add("cys-modal-overlay--open");
    fieldNombre.focus();
  }

  function abrirModalEditar(datos) {
    modalTitle.textContent = "Editar marca";
    fieldNombre.value = datos.nombre;
    fieldDescripcion.value = datos.descripcion;
    const activa = datos.estado === "activo";
    fieldEstado.checked = activa;
    fieldEstadoValue.value = activa ? "activo" : "inactivo";
    fieldEstadoLabel.textContent = activa ? "Activa" : "Inactiva";
    modalForm.action = window.CYS_URLS.editarBase + datos.id + "/";
    modalOverlay.classList.add("cys-modal-overlay--open");
    fieldNombre.focus();
  }

  function cerrarModal() {
    modalOverlay.classList.remove("cys-modal-overlay--open");
  }

  document.getElementById("btnNuevaMarca").addEventListener("click", abrirModalNueva);
  document.getElementById("cysModalClose").addEventListener("click", cerrarModal);
  document.getElementById("cysCancelBtn").addEventListener("click", cerrarModal);
  modalOverlay.addEventListener("click", function (e) {
    if (e.target === modalOverlay) cerrarModal();
  });

  fieldEstado.addEventListener("change", function () {
    fieldEstadoValue.value = this.checked ? "activo" : "inactivo";
    fieldEstadoLabel.textContent = this.checked ? "Activa" : "Inactiva";
  });

  // ---------------------------------------------------------
  // Modal: confirmar eliminación
  // ---------------------------------------------------------
  const deleteForm = document.getElementById("cysDeleteForm");
  const deleteName = document.getElementById("cysDeleteName");

  function abrirModalEliminar(id, nombre) {
    deleteForm.action = window.CYS_URLS.eliminarBase + id + "/";
    deleteName.textContent = nombre;
    deleteOverlay.classList.add("cys-modal-overlay--open");
  }

  function cerrarModalEliminar() {
    deleteOverlay.classList.remove("cys-modal-overlay--open");
  }

  document.getElementById("cysDeleteClose").addEventListener("click", cerrarModalEliminar);
  document.getElementById("cysDeleteCancel").addEventListener("click", cerrarModalEliminar);
  deleteOverlay.addEventListener("click", function (e) {
    if (e.target === deleteOverlay) cerrarModalEliminar();
  });

  // ---------------------------------------------------------
  // Delegación de eventos en la tabla (filas vienen de Django)
  // ---------------------------------------------------------
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

  // ---------------------------------------------------------
  // Cierre de modales con tecla Escape
  // ---------------------------------------------------------
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    cerrarModal();
    cerrarModalEliminar();
  });
})();