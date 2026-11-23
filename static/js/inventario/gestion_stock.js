/**
 * GESTION_STOCK.JS — Gestión de Stock & Productos
 * DataTable con búsqueda, filtros desplegables y formateo de moneda
 */

function formatMiles(n) {
  var num = parseInt(String(n).replace(/\D/g, ''), 10);
  if (isNaN(num)) return n;
  return num.toLocaleString('es-CO');
}

// ── TOOLTIPS: inicialización simple ──
function inicializarTooltipsLotes() {
  document.querySelectorAll('#tablaLotes [title]').forEach(function (el) {
    var existente = bootstrap.Tooltip.getInstance(el);
    if (existente) existente.dispose();

    new bootstrap.Tooltip(el, {
      placement: 'top',
      trigger: 'hover',
      container: 'body'
    });
  });
}

$(document).ready(function() {
  if ($.fn.DataTable.isDataTable('#tablaLotes')) {
    $('#tablaLotes').DataTable().destroy();
  }

  var table = $('#tablaLotes').DataTable({
    paging: true,
    searching: true,
    info: true,
    lengthChange: false,
    pageLength: 10,
    ordering: true,
    order: [],                           // respeta el orden con el que llega desde Django
    autoWidth: false,
    responsive: true,
    columnDefs: [
      { responsivePriority: 1, targets: 0 },  // Producto / Presentación — siempre visible
      { responsivePriority: 2, targets: 2 },  // Stock
      { responsivePriority: 3, targets: 4 },  // Estado
      { responsivePriority: 4, targets: 7 },  // Acciones
      { responsivePriority: 5, targets: 3 },  // Vencimiento
      { responsivePriority: 6, targets: 1 },  // Nº Lote
      { responsivePriority: 7, targets: 5 },  // Costo unit.
      { responsivePriority: 8, targets: 6 },  // Valor total
      { targets: 7, orderable: false, searchable: false }  // Acciones
    ],
    language: {
      info: "Mostrando _START_ a _END_ de _TOTAL_ lotes",
      infoEmpty: "Mostrando 0 a 0 de 0 lotes",
      infoFiltered: "(filtrado de _MAX_ lotes)",
      emptyTable: "No hay lotes con stock activo.",
      zeroRecords: "Sin resultados para tu búsqueda.",
      paginate: { first: '«', previous: '‹', next: '›', last: '»' }
    },
    dom: 'rt<"d-flex justify-content-center align-items-center mt-3"ip>',
    drawCallback: function() {
      $('#tablaLotes tbody tr').each(function() {
        [5, 6].forEach(function(idx) {
          var $td = $(this).find('td').eq(idx);
          var $span = $td.find('span');
          if ($span.length) {
            var texto = $span.text().trim();
            var num = texto.replace('$', '').replace(/\./g, '').trim();
            if (num && !isNaN(num) && parseInt(num) > 0) {
              $span.text('$' + formatMiles(num));
            }
          }
        }.bind(this));
      });
      inicializarTooltipsLotes();
    }
  });

  inicializarTooltipsLotes();

  // ═══════ BUSCADOR ═══════
  $('#buscarLote').on('input', function() {
    table.search(this.value).draw();
  });

  // ═══════ FILTROS DESPLEGABLES ═══════
  // Estado actual de cada filtro (vacío / null = sin filtrar)
  var filtros = {
    producto: '',
    estado: '',
    stockMin: null,
    stockMax: null,
    venceDesde: '',
    venceHasta: ''
  };

  // Compara contra los data-* de cada <tr>, no contra el texto formateado
  $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    if (settings.nTable.id !== 'tablaLotes') return true;     // solo esta tabla

    var tr = settings.aoData[dataIndex].nTr;
    if (!tr) return true;
    var d = tr.dataset;

    if (filtros.producto && d.producto !== filtros.producto) return false;
    if (filtros.estado && d.estado !== filtros.estado) return false;

    var stock = parseFloat(d.stock) || 0;
    if (filtros.stockMin !== null && stock < filtros.stockMin) return false;
    if (filtros.stockMax !== null && stock > filtros.stockMax) return false;

    // Fechas ISO (AAAA-MM-DD): comparar como texto funciona igual que como fecha.
    // Un lote sin vencimiento no pasa cuando hay filtro de fecha activo.
    if (filtros.venceDesde || filtros.venceHasta) {
      if (!d.vence) return false;
      if (filtros.venceDesde && d.vence < filtros.venceDesde) return false;
      if (filtros.venceHasta && d.vence > filtros.venceHasta) return false;
    }

    return true;
  });

  // Contador de filtros activos en el botón "Filtros"
  function actualizarContador() {
    var n = 0;
    if (filtros.producto) n++;
    if (filtros.estado) n++;
    if (filtros.stockMin !== null || filtros.stockMax !== null) n++;
    if (filtros.venceDesde || filtros.venceHasta) n++;

    var badge = document.getElementById('filtrosLotesContador');
    if (!badge) return;
    badge.textContent = n;
    badge.classList.toggle('d-none', n === 0);
  }

  function aplicarFiltros() {
    actualizarContador();
    table.draw();
  }

  // Un input vacío significa "sin límite" (null), no cero
  function leerNumero(input) {
    return input.value === '' ? null : parseFloat(input.value);
  }

  var selProducto  = document.getElementById('filtroLoteProducto');
  var selEstado    = document.getElementById('filtroLoteEstado');
  var inStockMin   = document.getElementById('filtroLoteStockMin');
  var inStockMax   = document.getElementById('filtroLoteStockMax');
  var inVenceDesde = document.getElementById('filtroLoteVenceDesde');
  var inVenceHasta = document.getElementById('filtroLoteVenceHasta');
  var btnLimpiar   = document.getElementById('filtroLoteLimpiar');

  // Llenar el select de productos con los que existen en la tabla
  if (selProducto) {
    var nombres = [];
    table.rows().nodes().each(function (tr) {
      var nombre = tr.dataset.producto;
      if (nombre && nombres.indexOf(nombre) === -1) nombres.push(nombre);
    });
    nombres.sort(function (a, b) { return a.localeCompare(b, 'es'); });
    nombres.forEach(function (nombre) {
      var opt = document.createElement('option');
      opt.value = nombre;
      opt.textContent = nombre;
      selProducto.appendChild(opt);
    });

    selProducto.addEventListener('change', function () {
      filtros.producto = this.value;
      aplicarFiltros();
    });
  }

  if (selEstado) {
    selEstado.addEventListener('change', function () {
      filtros.estado = this.value;
      aplicarFiltros();
    });
  }

  if (inStockMin) {
    inStockMin.addEventListener('input', function () {
      filtros.stockMin = leerNumero(inStockMin);
      aplicarFiltros();
    });
  }
  if (inStockMax) {
    inStockMax.addEventListener('input', function () {
      filtros.stockMax = leerNumero(inStockMax);
      aplicarFiltros();
    });
  }

  if (inVenceDesde) {
    inVenceDesde.addEventListener('change', function () {
      filtros.venceDesde = this.value;
      aplicarFiltros();
    });
  }
  if (inVenceHasta) {
    inVenceHasta.addEventListener('change', function () {
      filtros.venceHasta = this.value;
      aplicarFiltros();
    });
  }

  if (btnLimpiar) {
    btnLimpiar.addEventListener('click', function () {
      filtros.producto = '';
      filtros.estado = '';
      filtros.stockMin = null;
      filtros.stockMax = null;
      filtros.venceDesde = '';
      filtros.venceHasta = '';

      if (selProducto) selProducto.value = '';
      if (selEstado) selEstado.value = '';
      if (inStockMin) inStockMin.value = '';
      if (inStockMax) inStockMax.value = '';
      if (inVenceDesde) inVenceDesde.value = '';
      if (inVenceHasta) inVenceHasta.value = '';
      $('#buscarLote').val('');

      table.search('');
      aplicarFiltros();
    });
  }

  // ═══════ ?buscar=… (viene de otras páginas): busca y resalta la primera fila ═══════
  const params = new URLSearchParams(window.location.search);
  const termino = params.get('buscar');
  if (termino) {
    $('#buscarLote').val(termino);
    table.search(termino).draw();

    setTimeout(() => {
      const row = table.row({search: 'applied'}).node();
      if (row) {
        $(row).css({transition: 'background-color 0.3s ease', backgroundColor: 'rgba(77,168,218,0.18)'});
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  }
});