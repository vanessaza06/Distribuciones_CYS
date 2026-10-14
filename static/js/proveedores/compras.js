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
  const producto = byId('formCompraProducto');
  const lote = byId('formCompraLote');
  const cantidad = byId('formCompraCantidad');
  const precio = byId('formCompraPrecio');
  const pago = byId('formCompraPago');
  if (!producto || !cantidad || !precio) return;

  const total = () => (parseInt(cantidad.value, 10) || 0) * (parseFloat(precio.value) || 0);

  function recalcular() {
    const cant = parseInt(cantidad.value, 10) || 0;
    const txt = byId('calculoDetalleTexto');
    const disp = byId('calculoTotalDisplay');
    if (txt) txt.textContent = `${cant} und. × ${fmtCOP(precio.value)}`;
    if (disp) disp.textContent = fmtCOP(total());
    recalcularSaldo();
  }

  function recalcularSaldo() {
    const t = total();
    const abono = parseFloat(pago && pago.value) || 0;
    const fb = byId('formCompraSaldoFeedback');
    if (!fb) return;
    if (t === 0) {
      fb.innerHTML = '<span class="text-muted">Ingresa producto, cantidad y precio.</span>';
    } else if (abono >= t) {
      fb.innerHTML = '<span class="badge bg-success me-1"><i class="bi bi-check-circle-fill me-1"></i>Pagada completa</span> Saldo restante: <strong class="text-success">$0</strong>';
    } else if (abono > 0) {
      fb.innerHTML = `<span class="badge bg-warning text-dark me-1"><i class="bi bi-dash-circle me-1"></i>Pago parcial</span> Falta por pagar: <strong class="text-danger">${fmtCOP(t - abono)}</strong>`;
    } else {
      fb.innerHTML = `<span class="badge bg-secondary me-1"><i class="bi bi-hourglass-split me-1"></i>A crédito</span> Falta por pagar: <strong class="text-warning">${fmtCOP(t)}</strong>`;
    }
  }

  producto.addEventListener('change', function () {
    const opt = this.options[this.selectedIndex];
    const sugerido = parseFloat(opt && opt.dataset.precio) || 0;
    precio.value = sugerido > 0 ? sugerido : '';
    if (lote) {
      Array.from(lote.options).forEach((o, i) => {
        if (i === 0) return;
        const visible = !o.dataset.producto || o.dataset.producto === this.value;
        o.hidden = !visible;
        o.disabled = !visible;
      });
      lote.value = '';
    }
    recalcular();
  });

  [cantidad, precio].forEach((el) => el.addEventListener('input', recalcular));
  if (pago) {
    pago.addEventListener('input', recalcularSaldo);
    // El abono no puede superar el total
    pago.addEventListener('blur', () => {
      const t = total();
      if (t > 0 && parseFloat(pago.value) > t) pago.value = t;
      recalcularSaldo();
    });
  }

  const btnTotal = byId('btnPagarTotalNueva');
  const btnCredito = byId('btnCreditoNueva');
  if (btnTotal) btnTotal.addEventListener('click', () => { pago.value = total(); recalcularSaldo(); });
  if (btnCredito) btnCredito.addEventListener('click', () => { pago.value = 0; recalcularSaldo(); });

  const modal = byId('modalNuevaCompra');
  if (modal) {
    // Cada compra nueva arranca SIN pago (a crédito); el abono se escribe a propósito
    modal.addEventListener('show.bs.modal', () => { if (pago) pago.value = 0; });
    modal.addEventListener('shown.bs.modal', recalcular);
  }

  // Confirmación dentro del modal: evita marcar como PAGADA una compra que aún no se ha pagado
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
    [producto, cantidad, precio, pago].forEach((el) => el.addEventListener('input', ocultarConfirmacion));
    if (btnTotal) btnTotal.addEventListener('click', ocultarConfirmacion);
    if (btnCredito) btnCredito.addEventListener('click', ocultarConfirmacion);
    if (modal) modal.addEventListener('show.bs.modal', ocultarConfirmacion);

    byId('cmpConfirmRevisar').addEventListener('click', () => { ocultarConfirmacion(); pago.focus(); pago.select(); });
    byId('cmpConfirmAceptar').addEventListener('click', () => {
      confirmado = true;
      if (form.requestSubmit) form.requestSubmit(); else form.submit();
    });

    form.addEventListener('submit', (e) => {
      const t = total();
      let abono = parseFloat(pago.value) || 0;
      if (abono < 0) abono = 0;
      if (t > 0 && abono > t) abono = t;
      pago.value = abono;
      if (confirmado || abono <= 0 || t <= 0) return;   // a crédito o ya confirmado: se guarda
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
      badge.innerHTML = '<i class="bi bi-dash-circle me-1"></i>Quedará PARCIAL';
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
