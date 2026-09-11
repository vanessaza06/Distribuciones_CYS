/* =========================================================
   CYS Licorera — Marcas
   Lógica de interfaz. Trabaja sobre un arreglo local `marcas`,
   pero AHORA se inicializa leyendo las filas que Django ya
   renderizó en el HTML, en vez de arrancar vacío y borrarlas.
   Cuando conectes al backend con fetch/AJAX, reemplaza
   `leerMarcasIniciales()` por la respuesta del servidor.
   ========================================================= */

(function () {
  "use strict";

  // ---------------------------------------------------------
  // Referencias al DOM
  // ---------------------------------------------------------
  const tableBody = document.getElementById("cysTableBody");
  const tableCard = tableBody.closest(".cys-table-card");
  const inputBuscar = document.getElementById("inputBuscar");
  const statTotal = document.getElementById("statTotal");
  const statActivas = document.getElementById("statActivas");
  const statInactivas = document.getElementById("statInactivas");
  const tableCount = document.getElementById("cysTableCount");
  const pageNumbers = document.getElementById("cysPageNumbers");
  const pagePrev = document.getElementById("cysPagePrev");
  const pageNext = document.getElementById("cysPageNext");

  // ---------------------------------------------------------
  // Estado inicial: se lee de las filas ya renderizadas por
  // Django (data-id, data-nombre, data-descripcion, data-productos,
  // data-activa en el botón de editar de cada fila), para no
  // perder los datos reales del backend al primer render().
  // ---------------------------------------------------------
  function leerMarcasIniciales() {
    const filas = tableBody.querySelectorAll("tr[data-id]");
    const datos = [];
    filas.forEach((fila) => {
      const btnEditar = fila.querySelector(".cys-row-action-btn--edit");
      if (!btnEditar) return;
      datos.push({
        id: btnEditar.dataset.id,
        nombre: btnEditar.dataset.nombre || "",
        descripcion: btnEditar.dataset.descripcion || "",
        productos: parseInt(btnEditar.dataset.productos, 10) || 0,
        estado: btnEditar.dataset.activa === "true" ? "activa" : "inactiva",
      });
    });
    return datos;
  }

  let marcas = leerMarcasIniciales();
  let filtro = { texto: "", estado: "todos" };
  let paginaActual = 1;
  const porPagina = 10;

  // ---------------------------------------------------------
  // Select personalizado "Todos los estados"
  // ---------------------------------------------------------
  const estadoSelect = document.getElementById("cysEstadoSelect");
  const estadoTrigger = document.getElementById("cysEstadoTrigger");
  const estadoLabel = document.getElementById("cysEstadoLabel");
  const estadoMenu = document.getElementById("cysEstadoMenu");

  estadoTrigger.addEventListener("click", function () {
    estadoSelect.classList.toggle("cys-select--open");
  });

  estadoMenu.addEventListener("click", function (e) {
    const item = e.target.closest("li");
    if (!item) return;
    filtro.estado = item.dataset.value;
    estadoLabel.textContent = item.textContent;
    estadoSelect.classList.remove("cys-select--open");
    paginaActual = 1;
    render();
  });

  document.addEventListener("click", function (e) {
    if (!estadoSelect.contains(e.target)) {
      estadoSelect.classList.remove("cys-select--open");
    }
  });

  // ---------------------------------------------------------
  // Búsqueda
  // ---------------------------------------------------------
  inputBuscar.addEventListener("input", function () {
    filtro.texto = this.value.trim().toLowerCase();
    paginaActual = 1;
    render();
  });

  // ---------------------------------------------------------
  // Modal: nueva / editar marca
  // ---------------------------------------------------------
  const modalOverlay = document.getElementById("cysModalOverlay");
  const modalTitle = document.getElementById("cysModalTitle");
  const modalForm = document.getElementById("cysMarcaForm");
  const fieldNombre = document.getElementById("fieldNombre");
  const fieldDescripcion = document.getElementById("fieldDescripcion");
  const fieldEstado = document.getElementById("fieldEstado");
  const fieldEstadoLabel = document.getElementById("fieldEstadoLabel");
  let editandoId = null;

  function abrirModalNueva() {
    editandoId = null;
    modalTitle.textContent = "Nueva marca";
    modalForm.reset();
    fieldEstado.checked = true;
    fieldEstadoLabel.textContent = "Activa";
    modalOverlay.classList.add("cys-modal-overlay--open");
    fieldNombre.focus();
  }

  function abrirModalEditar(marca) {
    editandoId = marca.id;
    modalTitle.textContent = "Editar marca";
    fieldNombre.value = marca.nombre;
    fieldDescripcion.value = marca.descripcion;
    fieldEstado.checked = marca.estado === "activa";
    fieldEstadoLabel.textContent = fieldEstado.checked ? "Activa" : "Inactiva";
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
    fieldEstadoLabel.textContent = this.checked ? "Activa" : "Inactiva";
  });

  modalForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const datos = {
      nombre: fieldNombre.value.trim(),
      descripcion: fieldDescripcion.value.trim(),
      estado: fieldEstado.checked ? "activa" : "inactiva",
    };

    if (!datos.nombre || !datos.descripcion) return;

    if (editandoId) {
      const marca = marcas.find((m) => m.id === editandoId);
      Object.assign(marca, datos);
    } else {
      marcas.push({
        id: String(Date.now()),
        productos: 0,
        ...datos,
      });
    }

    // NOTA: aquí es donde luego harás el fetch/POST real al backend
    // (crear o actualizar) antes o en vez de mutar el arreglo local.

    cerrarModal();
    render();
  });

  // ---------------------------------------------------------
  // Modal: confirmar eliminación
  // ---------------------------------------------------------
  const deleteOverlay = document.getElementById("cysDeleteOverlay");
  const deleteName = document.getElementById("cysDeleteName");
  let idAEliminar = null;

  function abrirModalEliminar(marca) {
    idAEliminar = marca.id;
    deleteName.textContent = marca.nombre;
    deleteOverlay.classList.add("cys-modal-overlay--open");
  }

  function cerrarModalEliminar() {
    deleteOverlay.classList.remove("cys-modal-overlay--open");
    idAEliminar = null;
  }

  document.getElementById("cysDeleteClose").addEventListener("click", cerrarModalEliminar);
  document.getElementById("cysDeleteCancel").addEventListener("click", cerrarModalEliminar);
  deleteOverlay.addEventListener("click", function (e) {
    if (e.target === deleteOverlay) cerrarModalEliminar();
  });

  document.getElementById("cysDeleteConfirm").addEventListener("click", function () {
    // NOTA: aquí es donde luego harás el fetch/POST real de eliminación.
    marcas = marcas.filter((m) => m.id !== idAEliminar);
    cerrarModalEliminar();
    render();
  });

  // ---------------------------------------------------------
  // Render de tabla, tarjetas y paginación
  // ---------------------------------------------------------
  function marcasFiltradas() {
    return marcas.filter((m) => {
      const coincideTexto =
        !filtro.texto ||
        m.nombre.toLowerCase().includes(filtro.texto) ||
        m.descripcion.toLowerCase().includes(filtro.texto);
      const coincideEstado = filtro.estado === "todos" || m.estado === filtro.estado;
      return coincideTexto && coincideEstado;
    });
  }

  function crearFila(marca, indice) {
    const tr = document.createElement("tr");
    tr.dataset.id = marca.id;
    tr.innerHTML = `
      <td class="cys-col-num">${indice}</td>
      <td class="cys-marca-name">${marca.nombre}</td>
      <td class="cys-marca-desc">${marca.descripcion}</td>
      <td class="cys-col-center">${marca.productos}</td>
      <td>
        <span class="cys-status ${marca.estado === "inactiva" ? "cys-status--inactiva" : ""}">
          ${marca.estado === "inactiva" ? "Inactiva" : "Activa"}
        </span>
      </td>
      <td>
        <div class="cys-row-actions">
          <button class="cys-row-action-btn cys-row-action-btn--edit" aria-label="Editar">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="cys-row-action-btn cys-row-action-btn--delete" aria-label="Eliminar">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </td>
    `;
    tr.querySelector(".cys-row-action-btn--edit").addEventListener("click", () => abrirModalEditar(marca));
    tr.querySelector(".cys-row-action-btn--delete").addEventListener("click", () => abrirModalEliminar(marca));
    return tr;
  }

  function render() {
    const filtradas = marcasFiltradas();
    const totalPaginas = Math.max(1, Math.ceil(filtradas.length / porPagina));
    paginaActual = Math.min(paginaActual, totalPaginas);

    const inicio = (paginaActual - 1) * porPagina;
    const pagina = filtradas.slice(inicio, inicio + porPagina);

    tableBody.innerHTML = "";
    pagina.forEach((marca, i) => tableBody.appendChild(crearFila(marca, inicio + i + 1)));

    tableCard.classList.toggle("cys-table-card--empty", filtradas.length === 0);

    // Tarjetas de resumen
    statTotal.textContent = marcas.length;
    statActivas.textContent = marcas.filter((m) => m.estado === "activa").length;
    statInactivas.textContent = marcas.filter((m) => m.estado === "inactiva").length;

    // Conteo
    if (filtradas.length === 0) {
      tableCount.textContent = "Mostrando 0 marcas";
    } else {
      const desde = inicio + 1;
      const hasta = Math.min(inicio + porPagina, filtradas.length);
      tableCount.textContent = `Mostrando ${desde} a ${hasta} de ${filtradas.length} marcas`;
    }

    renderPaginacion(totalPaginas);
  }

  function renderPaginacion(totalPaginas) {
    pageNumbers.innerHTML = "";
    for (let i = 1; i <= totalPaginas; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = i;
      if (i === paginaActual) btn.classList.add("cys-page-numbers__active");
      btn.addEventListener("click", () => {
        paginaActual = i;
        render();
      });
      pageNumbers.appendChild(btn);
    }
    pagePrev.disabled = paginaActual === 1;
    pageNext.disabled = paginaActual === totalPaginas;
  }

  pagePrev.addEventListener("click", () => {
    if (paginaActual > 1) {
      paginaActual -= 1;
      render();
    }
  });

  pageNext.addEventListener("click", () => {
    const totalPaginas = Math.max(1, Math.ceil(marcasFiltradas().length / porPagina));
    if (paginaActual < totalPaginas) {
      paginaActual += 1;
      render();
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

  // ---------------------------------------------------------
  // Primer render (usa los datos leídos del HTML del servidor)
  // ---------------------------------------------------------
  render();
})();