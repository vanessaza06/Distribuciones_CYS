// ════════════════════════════════════════════════════════════════
// COMPRAS: modal de nueva compra, modal de pago, búsqueda de proveedores,
// menú de acciones de la tabla, exportación (Excel / PDF / Imprimir) y gráficos
// ════════════════════════════════════════════════════════════════

(function () {
'use strict';

const fmtCOP = (n) => '$' + Math.round(Number(n) || 0).toLocaleString('es-CO');
const byId = (id) => document.getElementById(id);
const esc = (str) => String(str == null ? '' : str).replace(/[&<>"']/g, (m) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
}[m]));

function init() {
  const raiz = byId('formNuevaCompra') || byId('chartComprasMes');
  if (!raiz) return;
  if (raiz.dataset.cmpInit === 'true') return;
  raiz.dataset.cmpInit = 'true';

  // Si venimos de una navegación htmx con un modal abierto, libera el scroll bloqueado
  if (!document.querySelector('.modal.show')) {
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }

  const pasos = [
    initGlobales,
    initNuevaCompra,
    initModalPago,
    initBusquedaProveedores,
    initAccesibilidad,
    initAccionesTabla,
    initTabla,
    initExportar,
    initializeCharts
  ];
  pasos.forEach((fn) => {
    try { fn(); } catch (err) { console.error('[Compras] Error en ' + fn.name + ':', err); }
  });

  const params = new URLSearchParams(window.location.search);
  const modalProv = byId('modalProveedores');
  if (params.get('modal') === 'proveedores' && modalProv && window.bootstrap) {
    new bootstrap.Modal(modalProv).show();
  }

  const modalNuevaCompra = byId('modalNuevaCompra');
  if (modalNuevaCompra && window.bootstrap) {
    if (modalNuevaCompra.dataset.autoOpen === 'true' ||
        modalNuevaCompra.querySelector('.alert-danger-dev') ||
        modalNuevaCompra.querySelector('.cmp-inline-error:not(.d-none)') ||
        modalNuevaCompra.querySelector('.is-invalid')) {
      const bsModal = bootstrap.Modal.getInstance(modalNuevaCompra) || new bootstrap.Modal(modalNuevaCompra);
      bsModal.show();
    }
  }

  document.querySelectorAll('.form-confirm-action').forEach((form) => {
    if (!form.dataset.confirmBound) {
      form.dataset.confirmBound = 'true';
      form.addEventListener('submit', function (e) {
        const msg = form.dataset.confirm || '¿Estás seguro de realizar esta acción?';
        if (!window.confirm(msg)) e.preventDefault();
      });
    }
  });
}

// Listeners de document/window: se registran UNA sola vez aunque htmx recargue el script
function initGlobales() {
  if (window.__cmpGlobales) return;
  window.__cmpGlobales = true;

  document.addEventListener('click', (e) => {
    // Cerrar lista de sugerencias de producto al hacer clic fuera
    const wrap = byId('cmpProductoWrapper');
    const sug = byId('cmpSugerenciasList');
    if (wrap && sug && !wrap.contains(e.target)) sug.classList.add('d-none');

    // Cerrar menús de acciones (⋯) al hacer clic fuera o en una opción
    const t = e.target;
    if (t && t.closest && (t.closest('.dd-item') || !t.closest('.dd-wrap'))) cerrarMenusAcciones();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') cerrarMenusAcciones(); });
  window.addEventListener('resize', cerrarMenusAcciones);
  document.addEventListener('scroll', cerrarMenusAcciones, true);
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

// ── Menú de acciones (⋯) de cada fila ──────────────────────────
// Se posiciona con "fixed" para que no lo recorte el scroll de la tabla.
function cerrarMenusAcciones() {
  document.querySelectorAll('.dd-menu').forEach((m) => {
    if (m.dataset.abierto === 'true') {
      m.dataset.abierto = '';
      m.style.cssText = '';
      m.classList.remove('show', 'open', 'is-open');
      if (m.parentElement) m.parentElement.classList.remove('show', 'open', 'is-open');
    }
  });
  document.querySelectorAll('.dd-btn[aria-expanded="true"]').forEach((b) => b.setAttribute('aria-expanded', 'false'));
}

function abrirMenuAcciones(btn) {
  const wrap = btn.closest('.dd-wrap');
  const menu = wrap && wrap.querySelector('.dd-menu');
  if (!menu) return;
  const yaAbierto = menu.dataset.abierto === 'true';
  cerrarMenusAcciones();
  if (yaAbierto) return;

  menu.dataset.abierto = 'true';
  menu.classList.add('show', 'open', 'is-open');
  wrap.classList.add('show', 'open', 'is-open');
  btn.setAttribute('aria-expanded', 'true');
  menu.style.cssText = [
    'position:fixed', 'display:block', 'opacity:1', 'visibility:visible',
    'transform:none', 'pointer-events:auto', 'z-index:2100', 'margin:0',
    'right:auto', 'bottom:auto', 'top:0', 'left:0'
  ].join(';');

  const r = btn.getBoundingClientRect();
  const mw = menu.offsetWidth;
  const mh = menu.offsetHeight;
  let left = r.right - mw;
  let top = r.bottom + 4;
  if (left < 8) left = 8;
  if (left + mw > window.innerWidth - 8) left = window.innerWidth - mw - 8;
  if (top + mh > window.innerHeight - 8) top = Math.max(8, r.top - mh - 4);
  menu.style.left = left + 'px';
  menu.style.top = top + 'px';
}

function initAccionesTabla() {
  const cont = byId('collapseHistorial');
  if (!cont || cont.dataset.ddBound) return;
  cont.dataset.ddBound = 'true';
  // Fase de captura + stopPropagation: este es el único manejador de los ⋯
  // (evita que otro script lo abra y lo cierre en el mismo clic).
  cont.addEventListener('click', (e) => {
    const btn = e.target.closest('.dd-btn');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    abrirMenuAcciones(btn);
  }, true);
}

// ── Aviso flotante (toast) ─────────────────────────────────────
let toastTimer = null;
function mostrarToast(texto, tipo) {
  let t = byId('cmp-toast-descarga');
  if (!t) {
    t = document.createElement('div');
    t.id = 'cmp-toast-descarga';
    t.setAttribute('role', 'status');
    t.setAttribute('aria-live', 'polite');
    t.style.cssText = [
      'position:fixed', 'top:16px', 'right:16px', 'z-index:3000',
      'min-width:260px', 'max-width:380px', 'padding:12px 16px',
      'border-radius:12px', 'color:#fff', 'font-size:14px', 'font-weight:600',
      'box-shadow:0 8px 24px rgba(0,0,0,.45)', 'display:flex', 'gap:10px',
      'align-items:center', 'transition:opacity .25s ease, transform .25s ease',
      'opacity:0', 'transform:translateY(-8px)', 'background:#1f1f1f',
      'border:1px solid rgba(255,255,255,.12)'
    ].join(';');
    document.body.appendChild(t);
  }
  const colores = { info: '#4DA8DA', ok: '#00C9A7', error: '#E05C7A' };
  const iconos = { info: 'bi-arrow-repeat', ok: 'bi-check-circle-fill', error: 'bi-exclamation-triangle-fill' };
  const k = colores[tipo] ? tipo : 'info';
  t.style.borderLeft = '4px solid ' + colores[k];
  t.innerHTML = '<i class="bi ' + iconos[k] + '" style="color:' + colores[k] + ';font-size:18px"></i><span></span>';
  t.querySelector('span').textContent = texto;
  requestAnimationFrame(() => { t.style.opacity = '1'; t.style.transform = 'translateY(0)'; });
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateY(-8px)';
  }, k === 'info' ? 8000 : 4500);
}

function nombreDesdeHeader(resp, respaldo) {
  const cd = resp.headers.get('Content-Disposition') || '';
  let m = cd.match(/filename\*=UTF-8''([^;]+)/i);
  if (m) { try { return decodeURIComponent(m[1].trim()); } catch (e) { /* sigue */ } }
  m = cd.match(/filename="?([^";]+)"?/i);
  if (m) return m[1].trim();
  return respaldo;
}

function guardarBlob(blob, nombre) {
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = nombre;
  a.setAttribute('hx-boost', 'false');
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
}

const selloFecha = () => new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '');

// ── Exportación local (respaldo si el servidor no responde un archivo) ──
function datosTabla() {
  const tabla = byId('tablaHistorialCompras');
  if (!tabla) return null;
  let nodos;
  if (window.jQuery && jQuery.fn.DataTable && jQuery.fn.DataTable.isDataTable(tabla)) {
    nodos = jQuery(tabla).DataTable().rows({ search: 'applied', order: 'applied' }).nodes().toArray();
  } else {
    nodos = tabla.tBodies[0] ? Array.from(tabla.tBodies[0].rows) : [];
  }
  const txt = (tr, i) => (tr.cells[i] ? tr.cells[i].textContent.replace(/\s+/g, ' ').trim() : '');
  const filas = nodos.map((tr, i) => [i + 1, txt(tr, 1), txt(tr, 2), txt(tr, 3), txt(tr, 4), txt(tr, 5), txt(tr, 6), txt(tr, 7)]);
  const subtotalEl = byId('subtotal-formatted');
  return {
    cabecera: ['#', 'Producto', 'Cant.', 'Precio', 'Total', 'Pago', 'Estado', 'Fecha'],
    filas,
    subtotal: subtotalEl ? subtotalEl.textContent.trim() : ''
  };
}

function nombreProveedor() {
  const el = document.querySelector('.proveedor-nombre');
  return el ? el.textContent.trim() : 'Proveedor';
}

function htmlTabla(d, conEstilos) {
  const estilos = conEstilos
    ? '<style>body{font-family:Arial,sans-serif;padding:16px}h2{margin:0 0 4px}p{margin:0 0 12px;color:#555;font-size:12px}' +
      'table{border-collapse:collapse;width:100%;font-size:12px}th,td{border:1px solid #999;padding:5px 7px;text-align:left}' +
      'th{background:#eee}tfoot td{font-weight:bold}</style>'
    : '';
  let h = '<table><thead><tr>' + d.cabecera.map((c) => '<th>' + esc(c) + '</th>').join('') + '</tr></thead><tbody>';
  d.filas.forEach((f) => { h += '<tr>' + f.map((c) => '<td>' + esc(c) + '</td>').join('') + '</tr>'; });
  h += '</tbody><tfoot><tr><td colspan="4">Subtotal</td><td colspan="4">' + esc(d.subtotal) + '</td></tr></tfoot></table>';
  return estilos + h;
}

function exportarExcelLocal() {
  const d = datosTabla();
  if (!d || !d.filas.length) { mostrarToast('No hay compras para exportar.', 'error'); return false; }
  const html = '<html><head><meta charset="utf-8"></head><body><h3>Compras - ' + esc(nombreProveedor()) + '</h3>' +
    htmlTabla(d, false) + '</body></html>';
  const blob = new Blob(['\ufeff' + html], { type: 'application/vnd.ms-excel;charset=utf-8' });
  guardarBlob(blob, 'compras_' + selloFecha() + '.xls');
  return true;
}

function imprimirLocal() {
  const d = datosTabla();
  if (!d || !d.filas.length) { mostrarToast('No hay compras para imprimir.', 'error'); return false; }
  const html = '<!doctype html><html><head><meta charset="utf-8"><title>Compras</title></head><body>' +
    '<h2>Compras - ' + esc(nombreProveedor()) + '</h2><p>Generado: ' + esc(new Date().toLocaleString('es-CO')) + '</p>' +
    htmlTabla(d, true) + '</body></html>';
  const f = document.createElement('iframe');
  f.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0';
  document.body.appendChild(f);
  const doc = f.contentWindow.document;
  doc.open(); doc.write(html); doc.close();
  setTimeout(() => {
    try { f.contentWindow.focus(); f.contentWindow.print(); }
    catch (err) { mostrarToast('No se pudo abrir la impresión.', 'error'); }
    setTimeout(() => f.remove(), 60000);
  }, 300);
  return true;
}

// Intenta que el servidor genere el archivo; si falla, lo genera desde la tabla
async function descargarArchivo(url, tipo, btn) {
  const ext = tipo === 'excel' ? 'xlsx' : 'pdf';
  const respaldo = 'compras_' + selloFecha() + '.' + ext;
  if (btn) btn.disabled = true;

  try {
    const resp = await fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    if (!resp.ok) throw new Error('El servidor respondió ' + resp.status);
    const ct = (resp.headers.get('Content-Type') || '').toLowerCase();
    if (ct.includes('text/html')) throw new Error('El servidor no devolvió un archivo');

    const nombre = nombreDesdeHeader(resp, respaldo);
    const blob = await resp.blob();
    guardarBlob(blob, nombre);
  } catch (err) {
    console.warn('[Compras] Exportación del servidor falló, usando respaldo local:', err);
    if (tipo === 'excel') {
      if (exportarExcelLocal()) mostrarToast('Excel generado desde la tabla (formato .xls).', 'ok');
    } else {
      if (imprimirLocal()) mostrarToast('En la ventana de impresión elige "Guardar como PDF".', 'info');
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── Exportar: Excel / PDF / Imprimir ───────────────────────────
function initExportar() {
  const contenedor = byId('cys-export-compras');
  if (!contenedor) return;

  contenedor.querySelectorAll('[data-export]').forEach((btn) => {
    if (btn.dataset.exportBound) return;
    btn.dataset.exportBound = 'true';

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const tipo = btn.dataset.export;

      if (tipo === 'imprimir') {
        imprimirLocal();
        return;
      }

      const params = new URLSearchParams(window.location.search);
      params.delete('modal');
      params.delete('page');
      if (!params.get('proveedor')) {
        const sel = byId('proveedorSeleccionado');
        if (sel && sel.value) params.set('proveedor', sel.value);
      }
      params.set('export', tipo);
      descargarArchivo(window.location.pathname + '?' + params.toString(), tipo, btn);
    });
  });
}

// ── Tabla del historial (DataTables) ───────────────────────────
function initTabla() {
  const tabla = byId('tablaHistorialCompras');
  if (!tabla || !window.jQuery || !jQuery.fn.DataTable) return;
  if (jQuery.fn.DataTable.isDataTable(tabla)) jQuery(tabla).DataTable().destroy();
  jQuery(tabla).DataTable({
    responsive: true,
    paging: true,
    searching: true,
    info: true,
    lengthChange: false,
    pageLength: 10,
    ordering: true,
    order: [],
    columnDefs: [{ orderable: false, targets: [0, 8], searchable: false }],
    language: {
      info: 'Mostrando _START_ a _END_ de _TOTAL_ compras',
      infoEmpty: 'Mostrando 0 a 0 de 0 compras',
      infoFiltered: '(filtrado de _MAX_)',
      emptyTable: 'Sin compras registradas aún.',
      zeroRecords: 'Sin resultados para tu búsqueda.',
      paginate: { first: '«', previous: '‹', next: '›', last: '»' }
    },
    layout: {
      topStart: null,
      topEnd: null,
      bottomStart: 'info',
      bottomEnd: 'paging'
    }
  });
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

  // Permite abonos con decimales sin que el navegador bloquee el envío
  if (pago) pago.step = 'any';

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
  const valorInicialProducto = hiddenProducto.value;

  // Modalidad de pago: 'credito' ($0) | 'total' (100%) | 'manual' | 'invalido'
  let modoPago = 'credito';

  const total = () => (parseInt(cantidad.value, 10) || 0) * (parseFloat(precio.value) || 0);

  function inferirModo() {
    const t = total();
    const val = parseFloat(pago && pago.value) || 0;
    if (val > t) modoPago = 'invalido';
    else if (t > 0 && Math.abs(val - t) < 0.01) modoPago = 'total';
    else if (val === 0) modoPago = 'credito';
    else modoPago = 'manual';
  }

  function actualizarBotonesModoPago() {
    const t = total();
    const val = parseFloat(pago && pago.value) || 0;
    if (!btnTotal || !btnCredito) return;

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

  function recalcular() {
    const cant = parseInt(cantidad.value, 10) || 0;
    const p = parseFloat(precio.value) || 0;
    const t = total();
    const txt = byId('calculoDetalleTexto');
    const disp = byId('calculoTotalDisplay');
    if (txt) txt.textContent = `${cant} und. × ${fmtCOP(p)}`;
    if (disp) disp.textContent = fmtCOP(t);

    if (pago) pago.max = t > 0 ? t : 0;

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
      fb.innerHTML = `<span class="badge bg-danger me-1"><i class="bi bi-exclamation-triangle-fill me-1"></i>Supera el total</span> El abono de <strong>${fmtCOP(val)}</strong> supera el total de la compra (<strong>${fmtCOP(t)}</strong>). Exceso: <strong class="text-danger">${fmtCOP(val - t)}</strong>`;
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

  if (btnTotal) btnTotal.addEventListener('click', (e) => { e.preventDefault(); aplicarModoTotal(); });
  if (btnCredito) btnCredito.addEventListener('click', (e) => { e.preventDefault(); aplicarModoCredito(); });

  [cantidad, precio].forEach((el) => el.addEventListener('input', recalcular));

  if (pago) {
    pago.addEventListener('focus', () => {
      if (pago.value === '0' || pago.value === '0.00' || parseFloat(pago.value) === 0) pago.select();
    });

    pago.addEventListener('input', () => {
      inferirModo();
      recalcularSaldo();
      actualizarBotonesModoPago();
    });

    pago.addEventListener('blur', () => {
      if (pago.value.trim() === '') {
        pago.value = 0;
        modoPago = 'credito';
      } else {
        const num = parseFloat(pago.value);
        if (!isNaN(num)) pago.value = Number.isInteger(num) ? num : num.toFixed(2);
      }
      recalcularSaldo();
      actualizarBotonesModoPago();
    });
  }

  // ── Selección y limpieza de producto ──
  // conservar = true: no pisa el precio ni el lote (se usa al reabrir el modal con errores)
  function seleccionarProducto(id, conservar) {
    const p = productosData.find((item) => item.id === String(id));
    if (!p) return;

    hiddenProducto.value = p.id;
    if (searchWrap) searchWrap.classList.remove('has-error');

    if (selectedNombre) selectedNombre.textContent = p.nombre;
    if (selectedCat) selectedCat.innerHTML = `<i class="bi bi-tag me-1 text-info"></i>${esc(p.categoria)}`;
    if (selectedStock) {
      selectedStock.textContent = `Stock actual: ${p.stock} und.`;
      selectedStock.className = p.stock > 0 ? 'text-success fw-semibold' : 'text-warning';
    }
    if (selectedCard) selectedCard.classList.remove('d-none');

    if (searchInput) searchInput.value = p.nombre;
    if (btnLimpiar) btnLimpiar.classList.remove('d-none');

    if (!conservar && p.precio > 0) precio.value = Math.round(p.precio);

    if (lote) {
      const loteActual = lote.value;
      Array.from(lote.options).forEach((o, i) => {
        if (i === 0) return;
        const visible = !o.dataset.producto || o.dataset.producto === p.id;
        o.hidden = !visible;
        o.disabled = !visible;
      });
      lote.value = conservar ? loteActual : '';
    }

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

  // ── Menú de sugerencias ──
  function renderizarSugerencias(q) {
    if (!sugList) return;
    const query = normalizar(q);

    if (!query) {
      sugList.innerHTML = '';
      sugList.classList.add('d-none');
      if (btnLimpiar && !hiddenProducto.value) btnLimpiar.classList.add('d-none');
      if (contador) {
        contador.textContent = `${totalProds} disponibles`;
        contador.className = 'badge cmp-badge-contador';
        contador.style.background = '';
        contador.style.color = '';
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
          <div>No se encontraron productos para "<strong>${esc(q)}</strong>"</div>
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
                data-val="${esc(p.id)}"
                tabindex="0">
          <div class="text-truncate pe-2">
            <div class="fw-bold text-white text-truncate">${esc(p.nombre)}</div>
            <small class="text-muted"><i class="bi bi-tag me-1 text-info"></i>${esc(p.categoria)}</small>
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

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      if (searchWrap) searchWrap.classList.remove('has-error');
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
        if (primero) seleccionarProducto(primero.dataset.val);
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
      if (btn && btn.dataset.val) seleccionarProducto(btn.dataset.val);
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
        if (prev && prev.classList.contains('cmp-dropdown-item')) prev.focus();
        else if (searchInput) searchInput.focus();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (actual && actual.dataset.val) seleccionarProducto(actual.dataset.val);
      } else if (e.key === 'Escape') {
        sugList.classList.add('d-none');
        if (searchInput) searchInput.focus();
      }
    });
  }

  if (btnLimpiar) btnLimpiar.addEventListener('click', (e) => { e.preventDefault(); limpiarSeleccion(true); });
  if (btnCambiar) btnCambiar.addEventListener('click', (e) => { e.preventDefault(); limpiarSeleccion(true); });

  const modal = byId('modalNuevaCompra');
  if (modal) {
    modal.addEventListener('show.bs.modal', () => {
      // Si el modal se abre solo por errores del servidor, conserva lo que el usuario escribió
      if (modal.dataset.autoOpen === 'true' && !modal.dataset.restaurado) {
        modal.dataset.restaurado = 'true';
        if (valorInicialProducto) seleccionarProducto(valorInicialProducto, true);
        inferirModo();
        recalcular();
        return;
      }
      modoPago = 'credito';
      if (pago) pago.value = 0;
      limpiarSeleccion(false);
      actualizarBotonesModoPago();
    });
    modal.addEventListener('shown.bs.modal', () => {
      recalcular();
      if (searchInput && !hiddenProducto.value) searchInput.focus();
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
      // 1. Producto seleccionado
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

      // 2. Cantidad y precio
      const cant = parseInt(cantidad.value, 10) || 0;
      const p = parseFloat(precio.value) || 0;
      const t = total();

      if (cant <= 0) { e.preventDefault(); cantidad.focus(); return; }
      if (p <= 0 || t <= 0) { e.preventDefault(); precio.focus(); return; }

      // 3. Abono
      const abono = parseFloat(pago ? pago.value.trim() : '0') || 0;

      if (abono < 0 || abono > t) {
        e.preventDefault();
        pago.classList.add('is-invalid');
        pago.focus();
        recalcularSaldo();
        return;
      }

      // 4. Crédito, pago total o ya confirmado: enviar
      if (confirmado || abono <= 0 || modoPago === 'total' || Math.abs(abono - t) < 0.01) return;

      // 5. Abono parcial: pedir confirmación
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

  monto.step = 'any'; // el botón "Pagar todo" puede poner decimales

  const saldoActual = () => parseFloat(byId('saldoActual').value) || 0;

  function mostrarError(texto) {
    const box = byId('montoPagadoError');
    if (!box) return;
    box.querySelector('span').textContent = texto;
    box.classList.toggle('d-none', !texto);
  }

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

  // Delegado: funciona aunque DataTables cambie de página o redibuje las filas
  const cont = byId('collapseHistorial') || document;
  cont.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.btn-abrir-pago');
    if (!btn) return;
    const total = parseFloat(btn.dataset.compraTotal) || 0;
    const pagado = parseFloat(btn.dataset.compraPagado) || 0;
    const saldo = parseFloat(btn.dataset.compraSaldo);
    const saldoFinal = isNaN(saldo) ? Math.max(0, total - pagado) : saldo;

    byId('compraId').value = btn.dataset.compraId;
    byId('saldoActual').value = saldoFinal;
    byId('resumenMontoTotal').textContent = fmtCOP(total);
    byId('resumenMontoPagado').textContent = fmtCOP(pagado);
    byId('resumenSaldoPendiente').textContent = fmtCOP(saldoFinal);

    monto.value = '';
    monto.max = saldoFinal;
    mostrarError('');
    byId('btnPagarTodoSaldo').innerHTML = `<i class="bi bi-check2-all me-1"></i>Pagar todo (${fmtCOP(saldoFinal)})`;

    const pagada = saldoFinal <= 0;
    byId('alertaPagada').classList.toggle('d-none', !pagada);
    form.querySelector('button[type="submit"]').disabled = pagada;
    actualizar();
  });

  byId('btnPagarTodoSaldo').addEventListener('click', () => {
    monto.value = Number.isInteger(saldoActual()) ? saldoActual() : saldoActual().toFixed(2);
    mostrarError('');
    actualizar();
  });
  monto.addEventListener('input', () => { mostrarError(''); actualizar(); });

  form.addEventListener('submit', function (e) {
    const valor = parseFloat(monto.value);
    if (!valor || valor <= 0) {
      e.preventDefault();
      mostrarError('Debes ingresar un monto válido.');
      monto.focus();
    } else if (valor > saldoActual() + 0.01) {
      e.preventDefault();
      mostrarError(`El monto supera el saldo pendiente (${fmtCOP(saldoActual())}).`);
      monto.focus();
    }
  });
}

// ── Búsqueda de proveedores en el directorio ───────────────────
function initBusquedaProveedores() {
  const input = byId('buscarProveedor');
  const tabla = byId('tablaSeleccionProveedor');
  if (!input || !tabla || !window.jQuery || !jQuery.fn.DataTable) return;
  if (jQuery.fn.DataTable.isDataTable(tabla)) jQuery(tabla).DataTable().destroy();
  const dt = jQuery(tabla).DataTable({
    responsive: true,
    paging: true,
    pageLength: 5,
    lengthChange: false,
    searching: true,
    info: true,
    ordering: true,
    order: [[0, 'asc']],
    columnDefs: [{ orderable: false, targets: [5] }],
    language: {
      info: 'Mostrando _START_ a _END_ de _TOTAL_ proveedores',
      infoEmpty: 'Mostrando 0 a 0 de 0 proveedores',
      infoFiltered: '(filtrado de _MAX_)',
      emptyTable: 'No hay proveedores registrados.',
      zeroRecords: 'No se encontraron proveedores',
      paginate: { first: '«', previous: '‹', next: '›', last: '»' }
    },
    layout: { topStart: null, topEnd: null, bottomStart: 'info', bottomEnd: 'paging' }
  });
  input.addEventListener('input', function () {
    dt.search(this.value.trim()).draw();
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
  const mesesLabels = datos.meses_labels || [];
  const mesesData = datos.meses_data || [];
  const productosLabels = datos.productos_labels || [];
  const productosData = datos.productos_data || [];

  const coloresGraficos = [colores.principal, colores.secundario, colores.terciario, colores.cuartario, colores.quinto];

  const ejeTicks = (size) => ({ color: '#FFFFFF', font: { size, weight: 'bold' } });
  const rejilla = { color: 'rgba(77, 168, 218, 0.1)', drawBorder: false };

  const ctxComprasMes = byId('chartComprasMes');
  if (ctxComprasMes && mesesLabels.length > 0) {
    Chart.getChart(ctxComprasMes)?.destroy();
    new Chart(ctxComprasMes, {
      type: 'line',
      data: {
        labels: mesesLabels,
        datasets: [{
          label: 'Compras',
          data: mesesData,
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
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: rejilla, ticks: ejeTicks(12) },
          x: { grid: { display: false, drawBorder: false }, ticks: ejeTicks(12) }
        }
      }
    });
  }

  const ctxProductosTop = byId('chartProductosTop');
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
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, grid: rejilla, ticks: ejeTicks(12) },
          y: { grid: { display: false, drawBorder: false }, ticks: Object.assign(ejeTicks(13), { padding: 10 }) }
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