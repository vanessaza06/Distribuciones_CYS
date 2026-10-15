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
}

function leerDatos() {
  const el = byId('compras-datos');
  try { return el ? JSON.parse(el.textContent) : {}; } catch (e) { return {}; }
}

// ── Tabla del historial (DataTables) ───────────────────────────
function initTabla() {
  const tabla = byId('tablaHistorialCompras');
  if (!tabla || !window.jQuery || !jQuery.fn.DataTable) return;
  if (jQuery.fn.DataTable.isDataTable(tabla)) jQuery(tabla).DataTable().destroy();
  jQuery(tabla).DataTable({
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
    dom: 'rt<"d-flex justify-content-center align-items-center mt-3"ip>'
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
    const t = cant * p;
    const txt = byId('calculoDetalleTexto');
    const disp = byId('calculoTotalDisplay');
    if (txt) txt.textContent = `${cant} und. × ${fmtCOP(p)}`;
    if (disp) disp.textContent = fmtCOP(t);

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
    const abono = parseFloat(pago && pago.value) || 0;
    const fb = byId('formCompraSaldoFeedback');
    if (!fb) return;
    if (t === 0) {
      fb.innerHTML = '<span class="text-muted">Selecciona producto, cantidad y precio.</span>';
    } else if (abono >= t) {
      fb.innerHTML = '<span class="badge bg-success me-1"><i class="bi bi-check-circle-fill me-1"></i>Pagada completa</span> Saldo restante: <strong class="text-success">$0</strong>';
    } else if (abono > 0) {
      fb.innerHTML = `<span class="badge bg-warning text-dark me-1"><i class="bi bi-dash-circle me-1"></i>Pago parcial</span> Falta por pagar: <strong class="text-danger">${fmtCOP(t - abono)}</strong>`;
    } else {
      fb.innerHTML = `<span class="badge bg-secondary me-1"><i class="bi bi-hourglass-split me-1"></i>A crédito</span> Falta por pagar: <strong class="text-warning">${fmtCOP(t)}</strong>`;
    }
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
    pago.addEventListener('input', () => {
      const val = parseFloat(pago.value) || 0;
      const t = total();
      if (t > 0 && Math.abs(val - t) < 0.01) {
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
      const t = total();
      if (t > 0 && parseFloat(pago.value) > t) {
        pago.value = t;
        modoPago = 'total';
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
      precio.value = p.precio;
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
        ? `<span class="badge" style="background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.4);">${p.stock} und.</span>`
        : `<span class="badge" style="background: rgba(255, 255, 255, 0.08); color: #adb5bd;">0 und.</span>`;
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
        <div class="p-2 text-center text-muted small" style="background: rgba(0,0,0,0.3); font-size: 0.8rem;">
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
    const pagada = abono >= t;
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
      // Validar selección de producto antes de enviar
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

      const t = total();
      let abono = parseFloat(pago.value) || 0;
      if (abono < 0) abono = 0;
      if (t > 0 && abono > t) abono = t;
      pago.value = abono;
      // Si el usuario ya confirmó, o es a crédito (abono <= 0), o eligió explícitamente "100% Total": se envía directamente sin bloquear
      if (confirmado || abono <= 0 || t <= 0 || modoPago === 'total') return;
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
    if (abono > 0 && abono >= saldo) {
      badge.className = 'badge badge-success-custom px-3 py-2 w-100 text-center';
      badge.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Quedará PAGADA';
    } else if (abono > 0) {
      badge.className = 'badge badge-warning-custom px-3 py-2 w-100 text-center';
      badge.innerHTML = `<i class="bi bi-dash-circle me-1"></i>Abono parcial (aún debe ${fmtCOP(saldo - abono)})`;
    } else {
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

})();
