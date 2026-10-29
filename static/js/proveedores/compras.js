// ════════════════════════════════════════════════════════════════
// COMPRAS: modal de nueva compra, modal de pago, búsqueda de proveedores y gráficos
// ════════════════════════════════════════════════════════════════

(function () {
'use strict';

// La página se carga por htmx (hx-boost): el DOMContentLoaded no se repite al navegar,
// así que el HTML de compras llama a ComprasPage.init() cuando su contenido ya está en el DOM.
const fmtCOP = (n) => '$' + Math.round(Number(n) || 0).toLocaleString('es-CO');
const byId = (id) => document.getElementById(id);

function init() {
  if (!byId('formNuevaCompra') && !byId('chartComprasMes')) return;
  initNuevaCompra();
  initModalPago();
  initBusquedaProveedores();
  initAccesibilidad();
  initTabla();
  initializeCharts();

  const params = new URLSearchParams(window.location.search);
  const modalProv = byId('modalProveedores');
  if (params.get('modal') === 'proveedores' && modalProv && window.bootstrap) {
    new bootstrap.Modal(modalProv).show();
  }

  const modalNuevaCompra = byId('modalNuevaCompra');
  if (modalNuevaCompra && window.bootstrap) {
    if (modalNuevaCompra.dataset.autoOpen === 'true' ||
        modalNuevaCompra.querySelector('.alert-danger-dev') ||
        modalNuevaCompra.querySelector('.cmp-inline-error') ||
        modalNuevaCompra.querySelector('.is-invalid')) {
      const bsModal = bootstrap.Modal.getInstance(modalNuevaCompra) || new bootstrap.Modal(modalNuevaCompra);
      bsModal.show();
    }
  }

  document.querySelectorAll('.form-confirm-action').forEach(form => {
    if (!form.dataset.confirmBound) {
      form.dataset.confirmBound = 'true';
      form.addEventListener('submit', function(e) {
        const msg = form.dataset.confirm || '¿Estás seguro de realizar esta acción?';
        if (!window.confirm(msg)) {
          e.preventDefault();
        }
      });
    }
  });
}

function leerDatos() {
  const el = byId('compras-datos');
  if (!el) return {};
  if (el.tagName === 'SCRIPT') {
    try { return JSON.parse(el.textContent); } catch (e) { return {}; }
  }
  try {
    return {
      meses_labels: JSON.parse(el.dataset.mesesLabels || '[]'),
      meses_data: JSON.parse(el.dataset.mesesData || '[]'),
      productos_labels: JSON.parse(el.dataset.productosLabels || '[]'),
      productos_data: JSON.parse(el.dataset.productosData || '[]')
    };
  } catch (e) {
    return {};
  }
}

// Asegurar disponibilidad del helper de exportación unificado
if (typeof window.cysCrearDropdownExportar !== 'function') {
  window.cysCrearDropdownExportar = function(dt, containerOrId) {
    if (!dt) return;
    var container = typeof containerOrId === 'string' ? document.getElementById(containerOrId) : containerOrId;
    if (!container) return;

    var api = (typeof dt.button === 'function') ? dt : (window.jQuery && jQuery.fn && jQuery.fn.dataTable ? jQuery(dt).DataTable() : null);
    if (!api || typeof api.button !== 'function') return;

    if (!api._buttons || (typeof api.buttons === 'function' && api.buttons().count() === 0)) {
      var initOptions = (typeof api.init === 'function') ? api.init() : null;
      if (initOptions && initOptions.buttons && window.DataTable && window.DataTable.Buttons) {
        try { new window.DataTable.Buttons(api, initOptions.buttons); } catch (e) {}
      }
    }

    try {
      if (typeof api.buttons === 'function') {
        var dtBtns = api.buttons().container();
        if (dtBtns && dtBtns.length) {
          dtBtns.remove();
        }
      }
      var extraBtns = container.querySelectorAll('.dt-buttons, .cys-dt-btn-excel, .cys-dt-btn-pdf');
      extraBtns.forEach(function(el) { el.remove(); });
    } catch (eBtns) {}

    var btnPdf = container.querySelector('[data-cys-export="pdf"]');
    var btnExcel = container.querySelector('[data-cys-export="excel"]');

    function dispararExport(tipo) {
      var isPdf = (tipo === 'pdf');
      var primaryClass = isPdf ? '.cys-dt-btn-pdf' : '.cys-dt-btn-excel';
      var fallbackClass = isPdf ? '.buttons-pdf' : '.buttons-excel';

      try {
        var b = api.button(primaryClass);
        if (b && b.length) { b.trigger(); return; }
      } catch (e1) {}

      try {
        var b2 = api.button(fallbackClass);
        if (b2 && b2.length) { b2.trigger(); return; }
      } catch (e2) {}

      try {
        if (typeof api.buttons === 'function') {
          var btns = api.buttons();
          var count = (typeof btns.count === 'function') ? btns.count() : (btns.length || 0);
          for (var i = 0; i < count; i++) {
            var singleBtn = api.button(i);
            var node = singleBtn.node();
            if (node) {
              var cls = (node.className || '').toLowerCase();
              var txt = (node.textContent || '').toLowerCase();
              if (isPdf && (cls.indexOf('pdf') !== -1 || txt.indexOf('pdf') !== -1)) {
                singleBtn.trigger(); return;
              }
              if (!isPdf && (cls.indexOf('excel') !== -1 || txt.indexOf('excel') !== -1)) {
                singleBtn.trigger(); return;
              }
            }
          }
          if (count >= 2) {
            api.button(isPdf ? 1 : 0).trigger();
            return;
          }
        }
      } catch (e3) {
        console.error('Error al exportar ' + tipo, e3);
      }
    }

    if (btnPdf && !btnPdf.dataset.cysExportBound) {
      btnPdf.dataset.cysExportBound = 'true';
      btnPdf.addEventListener('click', function(e) {
        e.preventDefault();
        dispararExport('pdf');
      });
    }

    if (btnExcel && !btnExcel.dataset.cysExportBound) {
      btnExcel.dataset.cysExportBound = 'true';
      btnExcel.addEventListener('click', function(e) {
        e.preventDefault();
        dispararExport('excel');
      });
    }
  };
}

// ── Tabla del historial (DataTables) ───────────────────────────
function initTabla() {
  const tabla = byId('tablaHistorialCompras');
  if (!tabla || !window.jQuery || !jQuery.fn.DataTable) return;
  if (jQuery.fn.DataTable.isDataTable(tabla)) jQuery(tabla).DataTable().destroy();
  const dt = jQuery(tabla).DataTable({
    paging: true,
    searching: false,
    info: true,
    lengthChange: false,
    pageLength: 10,
    ordering: true,
    order: [],
    columnDefs: [{ orderable: false, targets: [0, 8] }],
    language: {
      info: 'Mostrando _START_ a _END_ de _TOTAL_ compras',
      infoEmpty: 'Mostrando 0 a 0 de 0 compras',
      emptyTable: 'Sin compras registradas aún.',
      paginate: { first: '«', previous: '‹', next: '›', last: '»' }
    },
    layout: {
      topStart: null,
      topEnd: null,
      bottomStart: 'info',
      bottomEnd: 'paging'
    },
    buttons: [
      {
        extend: 'excelHtml5',
        text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
        className: 'cys-dt-btn-excel',
        title: 'Distribuciones CYS Ltda - Historial de Compras',
        filename: 'Compras_CYS',
        exportOptions: {
          columns: [0, 1, 2, 3, 4, 5, 6, 7]
        }
      },
      {
        extend: 'pdfHtml5',
        text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
        className: 'cys-dt-btn-pdf',
        title: 'Distribuciones CYS Ltda - Historial de Compras',
        filename: 'Compras_CYS',
        orientation: 'landscape',
        pageSize: 'A4',
        exportOptions: {
          columns: [0, 1, 2, 3, 4, 5, 6, 7]
        },
        customize: function (doc) {
          doc.defaultStyle.fontSize = 9;
          if (doc.styles && doc.styles.tableHeader) {
            doc.styles.tableHeader.fontSize = 10;
            doc.styles.tableHeader.bold = true;
            doc.styles.tableHeader.fillColor = '#011936';
            doc.styles.tableHeader.color = '#CF9C48';
            doc.styles.tableHeader.alignment = 'center';
          }
        }
      }
    ]
  });

  if (typeof window.cysCrearDropdownExportar === 'function') {
    window.cysCrearDropdownExportar(dt, 'cys-dt-export-compras-historial');
  }
}

// ── Modal "Nueva compra" ───────────────────────────────────────
function initNuevaCompra() {
  const hiddenProducto = byId('formCompraProducto');
  const sourceSelect = byId('formCompraProductoSource');
  const lote = byId('formCompraLote');
  const cantidad = byId('formCompraCantidad');
  const precio = byId('formCompraPrecio');
  const pago = byId('formCompraPago');
  if (!hiddenProducto || !cantidad || !precio) return;

  const btnTotal = byId('btnPagarTotalNueva');
  const btnCredito = byId('btnCreditoNueva');
  const searchWrap = byId('cmpSearchBoxWrap');
  const searchInput = byId('buscarProductoInput');
  const btnLimpiar = byId('limpiarBuscarProducto');
  const sugList = byId('cmpSugerenciasList');
  const contador = byId('cmpProdContador');
  const selectedCard = byId('cmpProductoSeleccionadoCard');
  const selectedNombre = byId('cmpSelectedNombre');
  const selectedCat = byId('cmpSelectedCat');
  const selectedStock = byId('cmpSelectedStock');
  const btnCambiar = byId('btnCambiarProducto');

  const normalizar = (str) =>
    (str || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  function escapeHtml(str) {
    return (str || '').replace(/[&<>"']/g, (m) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
  }

  // Cargar catálogo de productos en memoria para búsquedas instantáneas
  const productosData = sourceSelect
    ? Array.from(sourceSelect.options)
        .filter((opt) => opt.value)
        .map((opt) => ({
          id: String(opt.value),
          nombre: (opt.dataset.nombre || opt.text || '').trim(),
          precio: parseFloat(opt.dataset.precio) || 0,
          stock: parseInt(opt.dataset.stock, 10) || 0,
          categoria: (opt.dataset.categoria || 'General').trim(),
          textoNorm: normalizar(`${opt.dataset.nombre || opt.text} ${opt.dataset.categoria || ''}`)
        }))
    : [];

  const totalProds = productosData.length;

  // Modalidad de pago: 'credito' ($0) | 'total' (100% total automático) | 'manual'
  let modoPago = 'credito';

  const total = () => (parseInt(cantidad.value, 10) || 0) * (parseFloat(precio.value) || 0);

  function actualizarBotonesModoPago() {
    const t = total();
    const val = parseFloat(pago && pago.value) || 0;

    if (btnTotal && btnCredito) {
      if (t > 0 && val > t) {
        btnTotal.className = 'btn btn-sm btn-outline-info py-1 px-3 fw-bold btn-modo-pago';
        btnCredito.className = 'btn btn-sm btn-outline-secondary py-1 px-3 fw-bold btn-modo-pago';
        return;
      }

      if (modoPago === 'total' || (t > 0 && Math.abs(val - t) < 0.01)) {
        btnTotal.className = 'btn btn-sm py-1 px-3 fw-bold btn-modo-pago is-active-total';
        btnCredito.className = 'btn btn-sm btn-outline-secondary py-1 px-3 fw-bold btn-modo-pago';
      } else if (modoPago === 'credito' || val === 0) {
        btnCredito.className = 'btn btn-sm py-1 px-3 fw-bold btn-modo-pago is-active-credito';
        btnTotal.className = 'btn btn-sm btn-outline-info py-1 px-3 fw-bold btn-modo-pago';
      } else {
        btnTotal.className = 'btn btn-sm btn-outline-info py-1 px-3 fw-bold btn-modo-pago';
        btnCredito.className = 'btn btn-sm btn-outline-secondary py-1 px-3 fw-bold btn-modo-pago';
      }
    }
  }

  function recalcular() {
    const cant = parseInt(cantidad.value, 10) || 0;
    const p = parseFloat(precio.value) || 0;
    const t = total();
    const txt = byId('calculoDetalleTexto');
    const disp = byId('calculoTotalDisplay');
    if (txt) txt.textContent = `${cant} und. × ${fmtCOP(p)}`;
    if (disp) disp.textContent = fmtCOP(t);

    if (pago) {
      pago.max = t > 0 ? t : 0;
    }

    if (modoPago === 'total') {
      if (pago) pago.value = t > 0 ? (Number.isInteger(t) ? t : t.toFixed(2)) : 0;
    } else if (modoPago === 'credito') {
      if (pago) pago.value = 0;
    }

    recalcularSaldo();
    actualizarBotonesModoPago();
  }

  function recalcularSaldo() {
    const t = total();
    const val = parseFloat(pago && pago.value) || 0;
    const fb = byId('formCompraSaldoFeedback');
    if (!fb) return;

    if (pago) pago.classList.remove('is-invalid');

    if (t === 0) {
      fb.innerHTML = '<span class="text-muted"><i class="bi bi-info-circle me-1"></i>Ingresa producto, cantidad y precio.</span>';
      return;
    }

    if (val < 0) {
      if (pago) pago.classList.add('is-invalid');
      fb.innerHTML = '<span class="badge bg-danger me-1"><i class="bi bi-exclamation-triangle-fill me-1"></i>Monto inválido</span> El abono no puede ser negativo.';
      return;
    }

    if (val > t) {
      if (pago) pago.classList.add('is-invalid');
      const exceso = val - t;
      fb.innerHTML = `<span class="badge bg-danger me-1"><i class="bi bi-exclamation-triangle-fill me-1"></i>Supera el total</span> El abono de <strong>${fmtCOP(val)}</strong> supera el total de la compra (<strong>${fmtCOP(t)}</strong>). Exceso: <strong class="text-danger">${fmtCOP(exceso)}</strong>`;
      return;
    }

    if (Math.abs(val - t) < 0.01) {
      fb.innerHTML = '<span class="badge bg-success me-1"><i class="bi bi-check-circle-fill me-1"></i>Pagada completa</span> Saldo restante: <strong class="text-success">$0</strong>';
      return;
    }

    if (val === 0) {
      fb.innerHTML = `<span class="badge bg-secondary me-1"><i class="bi bi-hourglass-split me-1"></i>A crédito</span> Falta por pagar: <strong class="text-warning">${fmtCOP(t)}</strong>`;
      return;
    }

    fb.innerHTML = `<span class="badge bg-warning text-dark me-1"><i class="bi bi-dash-circle me-1"></i>Pago parcial</span> Falta por pagar: <strong class="text-danger">${fmtCOP(t - val)}</strong>`;
  }

  function aplicarModoTotal() {
    modoPago = 'total';
    const t = total();
    if (pago) pago.value = t > 0 ? (Number.isInteger(t) ? t : t.toFixed(2)) : 0;
    recalcularSaldo();
    actualizarBotonesModoPago();
  }

  function aplicarModoCredito() {
    modoPago = 'credito';
    if (pago) pago.value = 0;
    recalcularSaldo();
    actualizarBotonesModoPago();
  }

  if (btnTotal) {
    btnTotal.addEventListener('click', (e) => {
      e.preventDefault();
      aplicarModoTotal();
    });
  }

  if (btnCredito) {
    btnCredito.addEventListener('click', (e) => {
      e.preventDefault();
      aplicarModoCredito();
    });
  }

  [cantidad, precio].forEach((el) => el.addEventListener('input', recalcular));

  if (pago) {
    pago.addEventListener('focus', () => {
      if (pago.value === '0' || pago.value === '0.00' || parseFloat(pago.value) === 0) {
        pago.select();
      }
    });

    pago.addEventListener('input', () => {
      const val = parseFloat(pago.value) || 0;
      const t = total();

      if (val > t) {
        modoPago = 'invalido';
      } else if (t > 0 && Math.abs(val - t) < 0.01) {
        modoPago = 'total';
      } else if (val === 0) {
        modoPago = 'credito';
      } else {
        modoPago = 'manual';
      }

      recalcularSaldo();
      actualizarBotonesModoPago();
    });

    pago.addEventListener('blur', () => {
      if (pago.value.trim() === '') {
        pago.value = 0;
        modoPago = 'credito';
      } else {
        const num = parseFloat(pago.value);
        if (!isNaN(num)) {
          pago.value = Number.isInteger(num) ? num : num.toFixed(2);
        }
      }
      recalcularSaldo();
      actualizarBotonesModoPago();
    });
  }

  // ── Selección y Limpieza de Producto ──
  function seleccionarProducto(id) {
    const p = productosData.find((item) => item.id === String(id));
    if (!p) return;

    hiddenProducto.value = p.id;
    if (searchWrap) searchWrap.classList.remove('has-error');

    // Actualizar tarjeta visual de producto seleccionado
    if (selectedNombre) selectedNombre.textContent = p.nombre;
    if (selectedCat) selectedCat.innerHTML = `<i class="bi bi-tag me-1 text-info"></i>${escapeHtml(p.categoria)}`;
    if (selectedStock) {
      selectedStock.textContent = `Stock actual: ${p.stock} und.`;
      selectedStock.className = p.stock > 0 ? 'text-success fw-semibold' : 'text-warning';
    }
    if (selectedCard) selectedCard.classList.remove('d-none');

    // Sincronizar input de búsqueda con el producto seleccionado
    if (searchInput) searchInput.value = p.nombre;
    if (btnLimpiar) btnLimpiar.classList.remove('d-none');

    // Pre-cargar precio sugerido
    if (p.precio > 0) {
      precio.value = Math.round(p.precio);
    }

    // Filtrar lotes asociados a este producto
    if (lote) {
      Array.from(lote.options).forEach((o, i) => {
        if (i === 0) return;
        const visible = !o.dataset.producto || o.dataset.producto === p.id;
        o.hidden = !visible;
        o.disabled = !visible;
      });
      lote.value = '';
    }

    // Cerrar menú flotante
    if (sugList) {
      sugList.innerHTML = '';
      sugList.classList.add('d-none');
    }

    recalcular();
  }

  function limpiarSeleccion(enfocarInput = true) {
    hiddenProducto.value = '';
    if (selectedCard) selectedCard.classList.add('d-none');
    if (searchInput) {
      searchInput.value = '';
      if (enfocarInput) searchInput.focus();
    }
    if (btnLimpiar) btnLimpiar.classList.add('d-none');
    if (searchWrap) searchWrap.classList.remove('has-error');

    if (lote) {
      Array.from(lote.options).forEach((o, i) => {
        if (i === 0) return;
        o.hidden = false;
        o.disabled = false;
      });
      lote.value = '';
    }

    renderizarSugerencias('');
    recalcular();
  }

  // ── Renderizado del Menú de Sugerencias ──
  function renderizarSugerencias(q) {
    if (!sugList) return;
    const query = normalizar(q);

    if (!query) {
      sugList.innerHTML = '';
      sugList.classList.add('d-none');
      if (btnLimpiar && !hiddenProducto.value) btnLimpiar.classList.add('d-none');
      if (contador) {
        contador.textContent = `${totalProds} disponibles`;
        contador.className = 'badge';
        contador.style.background = 'rgba(77, 168, 218, 0.15)';
        contador.style.color = '#4DA8DA';
      }
      return;
    }

    if (btnLimpiar) btnLimpiar.classList.remove('d-none');

    const coincidencias = productosData.filter((p) => p.textoNorm.includes(query));
    const totalEncontrados = coincidencias.length;
    const itemsAMostrar = coincidencias.slice(0, 30);

    if (contador) {
      contador.textContent = `${totalEncontrados} encontrado${totalEncontrados === 1 ? '' : 's'}`;
      contador.className = totalEncontrados > 0 ? 'badge bg-info text-dark' : 'badge bg-danger';
      contador.style.background = '';
      contador.style.color = '';
    }

    if (totalEncontrados === 0) {
      sugList.innerHTML = `
        <div class="p-4 text-center text-muted">
          <i class="bi bi-search fs-3 d-block mb-2 text-warning opacity-75"></i>
          <div>No se encontraron productos para "<strong>${escapeHtml(q)}</strong>"</div>
          <small class="text-white-50">Intenta buscar por otra palabra o marca.</small>
        </div>
      `;
      sugList.classList.remove('d-none');
      return;
    }

    let html = '';
    itemsAMostrar.forEach((p) => {
      const esSeleccionado = hiddenProducto.value === p.id;
      const stockBadge = p.stock > 0
        ? `<span class="badge cmp-stock-badge cmp-stock-badge--ok">${p.stock} und.</span>`
        : `<span class="badge cmp-stock-badge cmp-stock-badge--cero">0 und.</span>`;
      const precioBadge = p.precio > 0
        ? `<div class="small fw-bold text-warning">${fmtCOP(p.precio)}</div>`
        : '';

      html += `
        <button type="button"
                class="cmp-dropdown-item ${esSeleccionado ? 'active' : ''}"
                data-val="${p.id}"
                tabindex="0">
          <div class="text-truncate pe-2">
            <div class="fw-bold text-white text-truncate">${escapeHtml(p.nombre)}</div>
            <small class="text-muted"><i class="bi bi-tag me-1 text-info"></i>${escapeHtml(p.categoria)}</small>
          </div>
          <div class="text-end text-nowrap ms-2">
            ${stockBadge}
            ${precioBadge}
          </div>
        </button>
      `;
    });

    if (totalEncontrados > itemsAMostrar.length) {
      html += `
        <div class="p-2 text-center text-muted small cmp-sug-mas">
          <i class="bi bi-info-circle me-1 text-info"></i>...y ${totalEncontrados - itemsAMostrar.length} productos más. Escribe más letras para afinar.
        </div>
      `;
    }

    sugList.innerHTML = html;
    sugList.classList.remove('d-none');
  }

  // Eventos del buscador
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      if (searchWrap) searchWrap.classList.remove('has-error');
      // Si el usuario edita el texto y ya no coincide con el producto seleccionado, deseleccionar
      if (hiddenProducto.value) {
        const prodActual = productosData.find((p) => p.id === hiddenProducto.value);
        if (prodActual && normalizar(searchInput.value) !== normalizar(prodActual.nombre)) {
          hiddenProducto.value = '';
          if (selectedCard) selectedCard.classList.add('d-none');
        }
      }
      renderizarSugerencias(searchInput.value);
    });

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (sugList) sugList.classList.add('d-none');
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        const primero = sugList ? sugList.querySelector('.cmp-dropdown-item') : null;
        if (primero) primero.focus();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const primero = sugList ? sugList.querySelector('.cmp-dropdown-item') : null;
        if (primero) {
          seleccionarProducto(primero.dataset.val);
        }
      }
    });

    searchInput.addEventListener('focus', () => {
      if (searchInput.value.trim() && sugList && sugList.children.length > 0) {
        sugList.classList.remove('d-none');
      }
    });
  }

  if (sugList) {
    sugList.addEventListener('click', (e) => {
      const btn = e.target.closest('.cmp-dropdown-item');
      if (btn && btn.dataset.val) {
        seleccionarProducto(btn.dataset.val);
      }
    });

    sugList.addEventListener('keydown', (e) => {
      const actual = document.activeElement;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const sig = actual.nextElementSibling;
        if (sig && sig.classList.contains('cmp-dropdown-item')) sig.focus();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prev = actual.previousElementSibling;
        if (prev && prev.classList.contains('cmp-dropdown-item')) {
          prev.focus();
        } else if (searchInput) {
          searchInput.focus();
        }
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (actual && actual.dataset.val) {
          seleccionarProducto(actual.dataset.val);
        }
      } else if (e.key === 'Escape') {
        sugList.classList.add('d-none');
        if (searchInput) searchInput.focus();
      }
    });
  }

  if (btnLimpiar) {
    btnLimpiar.addEventListener('click', (e) => {
      e.preventDefault();
      limpiarSeleccion(true);
    });
  }

  if (btnCambiar) {
    btnCambiar.addEventListener('click', (e) => {
      e.preventDefault();
      limpiarSeleccion(true);
    });
  }

  // Cerrar lista flotante al hacer clic fuera
  document.addEventListener('click', (e) => {
    const wrap = byId('cmpProductoWrapper');
    if (wrap && !wrap.contains(e.target)) {
      if (sugList) sugList.classList.add('d-none');
    }
  });

  const modal = byId('modalNuevaCompra');
  if (modal) {
    modal.addEventListener('show.bs.modal', () => {
      modoPago = 'credito';
      if (pago) pago.value = 0;
      limpiarSeleccion(false);
      actualizarBotonesModoPago();
    });
    modal.addEventListener('shown.bs.modal', () => {
      recalcular();
      if (searchInput) searchInput.focus();
    });
  }

  // Confirmación dentro del modal
  const form = byId('formNuevaCompra');
  const panel = byId('cmpConfirmPago');
  let confirmado = false;

  const ocultarConfirmacion = () => { if (panel) panel.classList.add('d-none'); confirmado = false; };

  function mostrarConfirmacion(abono, t) {
    const pagada = Math.abs(abono - t) < 0.01;
    panel.classList.toggle('is-pagada', pagada);
    byId('cmpConfirmIcono').className = pagada ? 'bi bi-cash-coin' : 'bi bi-question-circle-fill';
    byId('cmpConfirmTitulo').textContent = pagada ? '¿Ya le pagaste al proveedor?' : 'Confirma el abono inicial';
    byId('cmpConfirmTexto').innerHTML = pagada
      ? `El abono de <strong>${fmtCOP(abono)}</strong> cubre el total. La compra quedará marcada como <strong>PAGADA</strong>.`
      : `Se registrará un abono de <strong>${fmtCOP(abono)}</strong>. Quedará un saldo pendiente de <strong>${fmtCOP(t - abono)}</strong>.`;
    panel.classList.remove('d-none');
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    byId('cmpConfirmAceptar').focus();
  }

  if (form && pago && panel) {
    [cantidad, precio, pago].forEach((el) => el.addEventListener('input', ocultarConfirmacion));
    if (btnTotal) btnTotal.addEventListener('click', ocultarConfirmacion);
    if (btnCredito) btnCredito.addEventListener('click', ocultarConfirmacion);
    if (modal) modal.addEventListener('show.bs.modal', ocultarConfirmacion);

    byId('cmpConfirmRevisar').addEventListener('click', () => { ocultarConfirmacion(); pago.focus(); pago.select(); });
    byId('cmpConfirmAceptar').addEventListener('click', () => {
      confirmado = true;
      if (form.requestSubmit) form.requestSubmit(); else form.submit();
    });

    form.addEventListener('submit', (e) => {
      // 1. Validar selección de producto antes de enviar
      if (!hiddenProducto.value) {
        e.preventDefault();
        if (searchWrap) {
          searchWrap.classList.add('has-error');
          searchWrap.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (searchInput) {
          searchInput.focus();
          searchInput.placeholder = '¡Debes seleccionar un producto de la lista!';
        }
        return;
      }

      // 2. Validar cantidad y precio
      const cant = parseInt(cantidad.value, 10) || 0;
      const p = parseFloat(precio.value) || 0;
      const t = total();

      if (cant <= 0) {
        e.preventDefault();
        cantidad.focus();
        return;
      }
      if (p <= 0 || t <= 0) {
        e.preventDefault();
        precio.focus();
        return;
      }

      // 3. Validar abono inicial
      const rawAbono = pago ? pago.value.trim() : '0';
      const abono = parseFloat(rawAbono) || 0;

      if (abono < 0) {
        e.preventDefault();
        pago.classList.add('is-invalid');
        pago.focus();
        recalcularSaldo();
        return;
      }

      // Validación estricta: el abono no puede superar el total
      if (abono > t) {
        e.preventDefault();
        pago.classList.add('is-invalid');
        pago.focus();
        recalcularSaldo();
        return;
      }

      // 4. Si el abono es 0 (crédito) o cubre el total (100% Total), o ya confirmó: enviar directamente
      if (confirmado || abono <= 0 || modoPago === 'total' || Math.abs(abono - t) < 0.01) {
        return;
      }

      // 5. Abono parcial: solicitar confirmación amigable
      e.preventDefault();
      mostrarConfirmacion(abono, t);
    });
  }
  recalcular();
}

// ── Modal "Registrar pago" ─────────────────────────────────────
function initModalPago() {
  const form = byId('formPago');
  const monto = byId('montoPagado');
  if (!form || !monto) return;

  const saldoActual = () => parseFloat(byId('saldoActual').value) || 0;

  function actualizar() {
    const saldo = saldoActual();
    const abono = parseFloat(monto.value) || 0;
    const saldoInput = byId('saldoPendiente');
    if (saldoInput) saldoInput.value = fmtCOP(Math.max(0, saldo - abono));

    const badge = byId('badgeNuevoEstado');
    if (!badge) return;

    if (abono > saldo) {
      monto.classList.add('is-invalid');
      badge.className = 'badge bg-danger px-3 py-2 w-100 text-center';
      badge.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-1"></i>Supera el saldo pendiente (${fmtCOP(saldo)})`;
    } else if (abono > 0 && Math.abs(abono - saldo) < 0.01) {
      monto.classList.remove('is-invalid');
      badge.className = 'badge badge-success-custom px-3 py-2 w-100 text-center';
      badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Quedará PAGADA';
    } else if (abono > 0) {
      monto.classList.remove('is-invalid');
      badge.className = 'badge badge-warning-custom px-3 py-2 w-100 text-center';
      badge.innerHTML = `<i class="bi bi-dash-circle me-1"></i>Abono parcial (aún debe ${fmtCOP(saldo - abono)})`;
    } else {
      monto.classList.remove('is-invalid');
      badge.className = 'badge badge-pending-custom px-3 py-2 w-100 text-center';
      badge.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Sin abono nuevo';
    }
  }

  document.querySelectorAll('.btn-abrir-pago').forEach((btn) => {
    btn.addEventListener('click', function () {
      const total = parseFloat(this.dataset.compraTotal) || 0;
      const pagado = parseFloat(this.dataset.compraPagado) || 0;
      const saldo = parseFloat(this.dataset.compraSaldo);
      const saldoFinal = isNaN(saldo) ? Math.max(0, total - pagado) : saldo;

      byId('compraId').value = this.dataset.compraId;
      byId('saldoActual').value = saldoFinal;
      byId('resumenMontoTotal').textContent = fmtCOP(total);
      byId('resumenMontoPagado').textContent = fmtCOP(pagado);
      byId('resumenSaldoPendiente').textContent = fmtCOP(saldoFinal);

      monto.value = '';
      monto.max = saldoFinal;
      byId('btnPagarTodoSaldo').innerHTML = `<i class="bi bi-check2-all me-1"></i>Pagar todo (${fmtCOP(saldoFinal)})`;

      const pagada = saldoFinal <= 0;
      byId('alertaPagada').classList.toggle('d-none', !pagada);
      form.querySelector('button[type="submit"]').disabled = pagada;
      actualizar();
    });
  });

  byId('btnPagarTodoSaldo').addEventListener('click', () => {
    monto.value = saldoActual().toFixed(2);
    actualizar();
  });
  monto.addEventListener('input', () => { mostrarError(''); actualizar(); });

  function mostrarError(texto) {
    const box = byId('montoPagadoError');
    if (!box) return;
    box.querySelector('span').textContent = texto;
    box.classList.toggle('d-none', !texto);
  }

  form.addEventListener('submit', function (e) {
    const valor = parseFloat(monto.value);
    if (!valor || valor <= 0) {
      e.preventDefault();
      mostrarError('Debes ingresar un monto válido.');
      monto.focus();
    } else if (valor > saldoActual()) {
      e.preventDefault();
      mostrarError(`El monto supera el saldo pendiente (${fmtCOP(saldoActual())}).`);
      monto.focus();
    }
  });
}

// ── Búsqueda de proveedores en el directorio ───────────────────
function initBusquedaProveedores() {
  const input = byId('buscarProveedor');
  if (!input) return;
  const sinResultados = byId('sinResultados');
  input.addEventListener('input', function () {
    const q = this.value.toLowerCase().trim();
    let visibles = 0;
    document.querySelectorAll('.fila-proveedor').forEach((fila) => {
      const d = fila.dataset;
      const coincide = [d.nombre, d.nit, d.telefono].some((v) => (v || '').includes(q));
      fila.style.display = coincide ? '' : 'none';
      if (coincide) visibles++;
    });
    if (sinResultados) sinResultados.style.display = visibles === 0 && q !== '' ? 'block' : 'none';
  });
}

// ── Accesibilidad: Enter/Espacio activan elementos role="button" ─
function initAccesibilidad() {
  document.querySelectorAll('[role="button"][data-bs-toggle]').forEach((el) => {
    el.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        el.click();
      }
    });
  });
}

// ════════════════════════════════════════════════════════════════
// GRÁFICOS CON CHART.JS
// ════════════════════════════════════════════════════════════════

function initializeCharts() {
  const colores = {
    principal: '#4DA8DA',
    secundario: '#00C9A7',
    terciario: '#9B59B6',
    cuartario: '#f0d080',
    quinto: '#E05C7A'
  };

  if (!window.Chart) return;
  const datos = leerDatos();
  const meseslabels = datos.meses_labels || [];
  const mesesa = datos.meses_data || [];
  const productosLabels = datos.productos_labels || [];
  const productosData = datos.productos_data || [];

  const coloresGraficos = [
    colores.principal,
    colores.secundario,
    colores.terciario,
    colores.cuartario,
    colores.quinto
  ];

  // Gráfico de línea: Compras por mes
  const ctxComprasMes = document.getElementById('chartComprasMes');
  if (ctxComprasMes && meseslabels.length > 0) {
    Chart.getChart(ctxComprasMes)?.destroy();
    new Chart(ctxComprasMes, {
      type: 'line',
      data: {
        labels: meseslabels,
        datasets: [{
          label: 'Compras',
          data: mesesa,
          borderColor: colores.principal,
          backgroundColor: 'rgba(77, 168, 218, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: colores.principal,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(77, 168, 218, 0.1)',
              drawBorder: false
            },
            ticks: {
              color: '#FFFFFF',
              font: {
                size: 12,
                weight: 'bold'
              }
            }
          },
          x: {
            grid: {
              display: false,
              drawBorder: false
            },
            ticks: {
              color: '#FFFFFF',
              font: {
                size: 12,
                weight: 'bold'
              }
            }
          }
        }
      }
    });
  }

  // Gráfico de barras: Productos más comprados
  const ctxProductosTop = document.getElementById('chartProductosTop');
  if (ctxProductosTop && productosLabels.length > 0) {
    Chart.getChart(ctxProductosTop)?.destroy();
    new Chart(ctxProductosTop, {
      type: 'bar',
      data: {
        labels: productosLabels,
        datasets: [{
          label: 'Cantidad',
          data: productosData,
          backgroundColor: coloresGraficos.slice(0, productosLabels.length),
          borderRadius: 6,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: {
              color: 'rgba(77, 168, 218, 0.1)',
              drawBorder: false
            },
            ticks: {
              color: '#FFFFFF',
              font: {
                size: 12,
                weight: 'bold'
              }
            }
          },
          y: {
            grid: {
              display: false,
              drawBorder: false
            },
            ticks: {
              color: '#FFFFFF',
              font: {
                size: 13,
                weight: 'bold'
              },
              padding: 10
            }
          }
        }
      }
    });
  }
}

window.ComprasPage = { init };

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

if (document.body) {
  document.body.addEventListener('htmx:afterSettle', init);
}

})();

