/**
 * PRESENTACIONES.JS — DataTable (paginación, buscador y filtros),
 * dropdown de acciones y modal de creación
 */

let dtPres = null;

// Estado de los filtros desplegables (Categoría, Estado, Stock, Precio)
const filtrosPres = {
  categoria: '',
  estado: '',
  stock: '',
  precioMin: null,
  precioMax: null
};

const IDIOMA_PRES = {
  emptyTable:   'No hay presentaciones registradas.',
  zeroRecords:  'Sin resultados para tu búsqueda.',
  info:         'Mostrando _START_ a _END_ de _TOTAL_ presentaciones',
  infoEmpty:    'Mostrando 0 a 0 de 0 presentaciones',
  infoFiltered: '(filtrado de _MAX_ presentaciones)',
  lengthMenu:   'Mostrar _MENU_',
  paginate: { first: 'Primero', last: 'Último', next: 'Siguiente', previous: 'Anterior' }
};

document.addEventListener('DOMContentLoaded', function () {
  if (typeof bootstrap === 'undefined') {
    console.error('[Presentaciones] Bootstrap JS no está cargado: los modales no van a abrir. Revisa base.html.');
  }

  moverModalesAlBody();
  inicializarDataTablePresentaciones();
  inicializarModalCrearPresentacion();
  resaltarFilaNueva();

  document.addEventListener('click', function (e) {
    // Cierra cualquier dropdown abierto si se hace clic fuera
    if (!e.target.closest('.dd-wrap')) {
      cerrarDropdownsPres();
      return;
    }

    // Al elegir un enlace del menú (ej. Editar) se cierra el dropdown
    if (e.target.closest('a.dd-item')) {
      cerrarDropdownsPres();
    }
  });

  // El menú usa position: fixed, así que se cierra al hacer scroll
  window.addEventListener('scroll', cerrarDropdownsPres, true);
});

/**
 * Mueve los modales al <body> para que ningún contenedor con
 * transform / overflow / z-index los deje detrás del backdrop.
 */
function moverModalesAlBody() {
  document.querySelectorAll('.modal').forEach(function (modal) {
    if (modal.parentElement !== document.body) {
      document.body.appendChild(modal);
    }
  });
}

function cerrarDropdownsPres() {
  document.querySelectorAll('.dd-menu.open').forEach(m => m.classList.remove('open'));
}

// ═══════ DATATABLE: BUSCADOR + FILTROS + PAGINACIÓN ═══════
function inicializarDataTablePresentaciones() {
  const tabla = document.getElementById('tablaPresentaciones');
  if (!tabla) return;

  if (!window.jQuery || !$.fn.DataTable) {
    console.error('[Presentaciones] jQuery o DataTables no están cargados.');
    return;
  }

    dtPres = $(tabla).DataTable({
    paging: true,
    pageLength: 10,
    lengthMenu: [5, 10, 25, 50, 100],
    searching: true,
    info: true,
    ordering: true,
    order: [],                       // respeta el orden con el que llega desde Django
    autoWidth: false,
    responsive: true,
    columnDefs: [
      { targets: 6, orderable: false, searchable: false }   // columna Acciones
    ],
    language: IDIOMA_PRES,
    dom: '<"row align-items-center mb-2"<"col-sm-6"l><"col-sm-6 text-end">>rt<"row align-items-center mt-3"<"col-sm-6"i><"col-sm-6 text-end"p>>'
  });

  // Los menús "⋯" usan position: fixed: se cierran al cambiar de página u ordenar
  dtPres.on('draw.dt', cerrarDropdownsPres);

  // ── Filtros desplegables: leen los data-* de cada <tr> ──
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    if (settings.nTable.id !== 'tablaPresentaciones') return true;   // solo esta tabla

    const tr = dtPres.row(dataIndex).node();
    if (!tr) return true;
    const d = tr.dataset;

    if (filtrosPres.categoria && d.categoria !== filtrosPres.categoria) return false;
    if (filtrosPres.estado && d.activo !== filtrosPres.estado) return false;

    const stock = parseFloat(d.stock) || 0;
    if (filtrosPres.stock === 'con' && stock <= 0) return false;
    if (filtrosPres.stock === 'sin' && stock > 0) return false;

    const precio = parseFloat(d.precio) || 0;
    if (filtrosPres.precioMin !== null && precio < filtrosPres.precioMin) return false;
    if (filtrosPres.precioMax !== null && precio > filtrosPres.precioMax) return false;

    return true;
  });

  enlazarFiltrosPresentaciones();
}

function enlazarFiltrosPresentaciones() {
  const inputBuscar = document.getElementById('buscarPresentacion');
  const selCategoria = document.getElementById('filtroPresCategoria');
  const selEstado = document.getElementById('filtroPresEstado');
  const selStock = document.getElementById('filtroPresStock');
  const inputMin = document.getElementById('filtroPresPrecioMin');
  const inputMax = document.getElementById('filtroPresPrecioMax');
  const btnLimpiar = document.getElementById('filtroPresLimpiar');

  // Buscador de la barra → búsqueda global de DataTables
  if (inputBuscar) {
    inputBuscar.addEventListener('input', function () {
      dtPres.search(this.value.trim()).draw();
    });
  }

  // Llenar el select de categorías con las que existen en la tabla
  if (selCategoria) {
    const nombres = [];
    dtPres.rows().nodes().each(function (tr) {
      const nombre = tr.dataset.categoria;
      if (nombre && nombres.indexOf(nombre) === -1) nombres.push(nombre);
    });
    nombres.sort(function (a, b) { return a.localeCompare(b, 'es'); });
    nombres.forEach(function (nombre) {
      const opt = document.createElement('option');
      opt.value = nombre;
      opt.textContent = nombre;
      selCategoria.appendChild(opt);
    });

    selCategoria.addEventListener('change', function () {
      filtrosPres.categoria = this.value;
      dtPres.draw();
    });
  }

  if (selEstado) {
    selEstado.addEventListener('change', function () {
      filtrosPres.estado = this.value;
      dtPres.draw();
    });
  }

  if (selStock) {
    selStock.addEventListener('change', function () {
      filtrosPres.stock = this.value;
      dtPres.draw();
    });
  }

  // Un input vacío significa "sin límite" (null), no cero
  function leerNumero(input) {
    return input.value === '' ? null : parseFloat(input.value);
  }
  if (inputMin) {
    inputMin.addEventListener('input', function () {
      filtrosPres.precioMin = leerNumero(inputMin);
      dtPres.draw();
    });
  }
  if (inputMax) {
    inputMax.addEventListener('input', function () {
      filtrosPres.precioMax = leerNumero(inputMax);
      dtPres.draw();
    });
  }

  if (btnLimpiar) {
    btnLimpiar.addEventListener('click', function () {
      filtrosPres.categoria = '';
      filtrosPres.estado = '';
      filtrosPres.stock = '';
      filtrosPres.precioMin = null;
      filtrosPres.precioMax = null;

      if (selCategoria) selCategoria.value = '';
      if (selEstado) selEstado.value = '';
      if (selStock) selStock.value = '';
      if (inputMin) inputMin.value = '';
      if (inputMax) inputMax.value = '';
      if (inputBuscar) inputBuscar.value = '';

      dtPres.search('').draw();
    });
  }
}

/**
 * Arma el action del formulario "Nueva Presentación" según el producto elegido.
 * La URL base viene de {% url 'presentacion_crear' 0 %} (data-url-template).
 */
function inicializarModalCrearPresentacion() {
  const form = document.getElementById('form-crear-presentacion');
  const selectProducto = document.getElementById('crear-pres-producto');
  if (!form || !selectProducto) return;

  const plantilla = form.dataset.urlTemplate || '';

  function actualizarAction() {
    if (!selectProducto.value) {
      form.setAttribute('action', '');
      return;
    }
    // Reemplaza el segmento "/0" (con o sin barra final) por el id del producto
    form.setAttribute(
      'action',
      plantilla.replace(/\/0(?=\/|$)/, '/' + selectProducto.value)
    );
  }

  selectProducto.addEventListener('change', actualizarAction);

  form.addEventListener('submit', function (e) {
    if (!selectProducto.value) {
      e.preventDefault();
      selectProducto.focus();
      return;
    }
    actualizarAction();
  });
}

function toggleDropdownPres(btn) {
  const wrap = btn.closest('.dd-wrap');
  const menu = wrap.querySelector('.dd-menu');
  const yaAbierto = menu.classList.contains('open');

  // Cierra todos los demás dropdowns abiertos antes de abrir este
  cerrarDropdownsPres();

  if (!yaAbierto) {
    // Posiciona el menú justo debajo del botón (porque .dd-menu usa position: fixed)
    const rect = btn.getBoundingClientRect();
    menu.style.top = rect.bottom + 4 + 'px';
    menu.style.right = (window.innerWidth - rect.right) + 'px';
    menu.classList.add('open');
  }
}

/**
 * Si la URL trae ?resaltar=<pk>, salta a la página donde está esa fila,
 * la lleva a la vista y limpia el parámetro para que al recargar no se vuelva a marcar.
 * Con paginación la fila puede estar en otra página, por eso se usa la API de DataTables.
 */
function resaltarFilaNueva() {
  if (!dtPres) return;

  const nodos = dtPres.rows({ order: 'current', search: 'applied' }).nodes().toArray();
  const fila = nodos.find(function (n) { return n.classList.contains('fila-resaltada'); });
  if (!fila) return;

  fila.scrollIntoView({ behavior: 'smooth', block: 'center' });

  const url = new URL(window.location.href);
  url.searchParams.delete('resaltar');
  window.history.replaceState({}, '', url.pathname + url.search + url.hash);
}