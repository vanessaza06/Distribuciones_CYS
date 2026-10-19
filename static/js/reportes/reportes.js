/**
 * REPORTES.JS — Reportes y Análisis
 * DataTable, filtrado, paginación, gráficas en tarjetas
 */

/* ── DataTable Historial de Ventas ── */
$(document).ready(function() {
    var table = $('#reportes-table').DataTable({
        paging: true,
        searching: true,
        info: true,
        lengthChange: false,
        pageLength: 10,
        ordering: true,
        responsive: true,
        language: {
            info: "Mostrando _START_ a _END_ de _TOTAL_ ventas",
            infoEmpty: "Mostrando 0 a 0 de 0 ventas",
            paginate: { first:'«', previous:'‹', next:'›', last:'»' }
        },
        dom: 'rt<"cys-hv-table-footer"ip>'
    });

    $('#buscar-historial').on('keyup', function() {
        table.search(this.value).draw();
    });

    function enlazarFechasReportes(origen) {
        const $fi = $('#filtro-fecha-inicio');
        const $ff = $('#filtro-fecha-fin');
        let vi = $fi.val();
        let vf = $ff.val();

        if (vi && vf && vi > vf) {
            if (origen === 'ini') {
                $ff.val(vi);
                vf = vi;
            } else if (origen === 'fin') {
                $fi.val(vf);
                vi = vf;
            } else {
                $ff.val(vi);
                vf = vi;
            }
        }

        if (vi) $ff.attr('min', vi);
        else $ff.removeAttr('min');

        if (vf) $fi.attr('max', vf);
        else $fi.removeAttr('max');
    }

    function syncExportLinks() {
        const fi = $('#filtro-fecha-inicio').val() || '';
        const ff = $('#filtro-fecha-fin').val()    || '';
        const p  = `&fecha_inicio=${fi}&fecha_fin=${ff}`;
        $('#btn-export-excel').attr('href', `?export=excel&tipo=ventas${p}`);
        $('#btn-export-pdf').attr('href',   `?export=pdf&tipo=ventas${p}`);
        $('#btn-export-print').attr('href', `?export=pdf&tipo=ventas&print=true${p}`);
    }

    $('#filtro-fecha-inicio').on('change input', function() {
        enlazarFechasReportes('ini');
        syncExportLinks();
        aplicarFiltro('ini');
    });

    $('#filtro-fecha-fin').on('change input', function() {
        enlazarFechasReportes('fin');
        syncExportLinks();
        aplicarFiltro('fin');
    });

    enlazarFechasReportes();
    syncExportLinks();
});

function aplicarFiltro(origen) {
    const elFi = document.getElementById('filtro-fecha-inicio');
    const elFf = document.getElementById('filtro-fecha-fin');
    let fi = elFi ? elFi.value : '';
    let ff = elFf ? elFf.value : '';

    if (fi && ff && fi > ff) {
        if (origen === 'fin') {
            fi = ff;
            if (elFi) elFi.value = ff;
        } else {
            ff = fi;
            if (elFf) elFf.value = fi;
        }
    }

    let url  = window.location.pathname + '?';
    if (fi) url += 'fecha_inicio=' + fi + '&';
    if (ff) url += 'fecha_fin='    + ff;
    window.location.href = url;
}

/* ══════════════════════════════════════════════
   INVENTARIO — búsqueda + paginación de 10 en 10
══════════════════════════════════════════════ */
var INV_POR_PAGINA = 10;
var invPagActual   = 1;
var invQuery       = '';

function invFilasCoincidentes() {
    var filas = document.querySelectorAll('#tabla-modal-stock .inv-row');
    var res = [];
    filas.forEach(function(row) {
        var txt = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        if (txt.includes(invQuery)) res.push(row);
    });
    return res;
}

function renderInvPag() {
    var todas       = document.querySelectorAll('#tabla-modal-stock .inv-row');
    var coinciden   = invFilasCoincidentes();
    var totalPags   = Math.max(1, Math.ceil(coinciden.length / INV_POR_PAGINA));
    invPagActual    = Math.max(1, Math.min(invPagActual, totalPags));

    var inicio = (invPagActual - 1) * INV_POR_PAGINA;
    var fin    = inicio + INV_POR_PAGINA;

    todas.forEach(function(r) { r.style.display = 'none'; });
    coinciden.slice(inicio, fin).forEach(function(r) { r.style.display = ''; });

    var bar = document.getElementById('inv-pag-bar');
    if (!bar) return;

    bar.style.display = todas.length === 0 ? 'none' : 'flex';

    var desde = coinciden.length === 0 ? 0 : inicio + 1;
    var hasta = Math.min(fin, coinciden.length);

    document.getElementById('inv-pag-info').textContent =
        'Mostrando ' + desde + '–' + hasta + ' de ' + coinciden.length;
    document.getElementById('inv-pag-indicator').textContent =
        invPagActual + ' / ' + totalPags;

    document.getElementById('inv-pag-first').disabled = invPagActual === 1;
    document.getElementById('inv-pag-prev').disabled  = invPagActual === 1;
    document.getElementById('inv-pag-next').disabled  = invPagActual === totalPags;
    document.getElementById('inv-pag-last').disabled  = invPagActual === totalPags;
}

function pagInv(dir) {
    invPagActual += dir;
    renderInvPag();
}

function irPagInv(destino) {
    var total = Math.max(1, Math.ceil(invFilasCoincidentes().length / INV_POR_PAGINA));
    invPagActual = destino === 'last' ? total : 1;
    renderInvPag();
}

/* Búsqueda inventario (la llama el oninput del HTML) */
function filtrarTablaInv(q) {
    invQuery = (q || '').toLowerCase().trim();
    invPagActual = 1;
    renderInvPag();
}

function crearPaginacionInv() {
    var tabla = document.getElementById('tabla-modal-stock');
    if (!tabla || document.getElementById('inv-pag-bar')) return;

    var wrap = tabla.closest('.table-responsive') || tabla.parentElement;

    var bar = document.createElement('div');
    bar.id = 'inv-pag-bar';
    bar.className = 'cys-prov-pagination';
    bar.style.flexWrap = 'wrap';
    bar.innerHTML =
        '<span id="inv-pag-info" style="margin-right:auto;padding-left:20px;font-size:.8rem;color:var(--texto-muted);"></span>' +
        '<button type="button" class="cys-pag-btn" id="inv-pag-first" title="Primera"><i class="bi bi-chevron-double-left"></i></button>' +
        '<button type="button" class="cys-pag-btn" id="inv-pag-prev" title="Anterior"><i class="bi bi-chevron-left"></i></button>' +
        '<span id="inv-pag-indicator" class="cys-prov-pagination__indicator" style="width:auto;min-width:36px;padding:0 12px;">1</span>' +
        '<button type="button" class="cys-pag-btn" id="inv-pag-next" title="Siguiente"><i class="bi bi-chevron-right"></i></button>' +
        '<button type="button" class="cys-pag-btn" id="inv-pag-last" title="Última"><i class="bi bi-chevron-double-right"></i></button>' +
        '<span style="margin-left:auto;padding-right:20px;"></span>';

    wrap.insertAdjacentElement('afterend', bar);

    document.getElementById('inv-pag-first').addEventListener('click', function() { irPagInv('first'); });
    document.getElementById('inv-pag-prev').addEventListener('click',  function() { pagInv(-1); });
    document.getElementById('inv-pag-next').addEventListener('click',  function() { pagInv(1); });
    document.getElementById('inv-pag-last').addEventListener('click',  function() { irPagInv('last'); });

    renderInvPag();
}

/* ── Búsqueda proveedores ── */
function filtrarTablaProv(q) {
    q = q.toLowerCase();
    document.querySelectorAll('#tabla-modal-proveedores .prov-row').forEach(function(row) {
        const nombre  = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const empresa = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        row.style.display = (nombre.includes(q) || empresa.includes(q)) ? '' : 'none';
    });
}

/* ── Paginación simple proveedores ── */
var provPagActual = 1;
function pagProv(dir) {
    var rows = document.querySelectorAll('#tabla-modal-proveedores .prov-row');
    var perPage = 5;
    var total   = Math.ceil(rows.length / perPage);
    provPagActual = Math.max(1, Math.min(provPagActual + dir, total));
    rows.forEach(function(r, i) {
        var page = Math.floor(i / perPage) + 1;
        r.style.display = page === provPagActual ? '' : 'none';
    });
    document.getElementById('prov-pag-indicator').textContent = provPagActual;
}

/* ── Análisis de ventas — sidebar nav ── */
function avSetTab(tab) {
    ['resumen','fecha','top'].forEach(function(t) {
        var panel = document.getElementById('avPanel-'  + t);
        var btn   = document.getElementById('avNav-'    + t);
        if (!panel || !btn) return;
        if (t === tab) {
            panel.classList.remove('cys-av-panel--hidden');
            btn.classList.add('active');
        } else {
            panel.classList.add('cys-av-panel--hidden');
            btn.classList.remove('active');
        }
    });
}

/* ── Búsqueda: Análisis de Ventas → panel "Por fecha" ── */
function filtrarTablaAVFecha(q) {
    q = q.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-modal-av-ventas .av-fecha-row');
    let visibles = 0;
    filas.forEach(function(row) {
        const cliente  = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const producto = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        const coincide = cliente.includes(q) || producto.includes(q);
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    const noResults = document.getElementById('av-fecha-no-results');
    if (noResults) {
        noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
    }
}

/* ── Búsqueda: Análisis de Ventas → panel "Top productos" ── */
function filtrarTablaAVTop(q) {
    q = q.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-modal-av-top .av-top-row');
    let visibles = 0;
    filas.forEach(function(row) {
        const producto = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const coincide = producto.includes(q);
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    const noResults = document.getElementById('av-top-no-results');
    if (noResults) {
        noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
    }
}

/* ── Búsqueda devoluciones ── */
function filtrarTablaDevoluciones(q) {
    q = q.toLowerCase();
    document.querySelectorAll('#tabla-modal-devoluciones .dev-row').forEach(function(row) {
        const cliente  = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const producto = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        row.style.display = (cliente.includes(q) || producto.includes(q)) ? '' : 'none';
    });
}

/* ── Búsqueda: Resumen Diario → tab "Entradas" ── */
function filtrarTablaRDEntradas(q) {
    q = q.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-modal-rd-entradas .rd-entrada-row');
    let visibles = 0;
    filas.forEach(function(row) {
        const producto = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const coincide = producto.includes(q);
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    const noResults = document.getElementById('rd-entradas-no-results');
    if (noResults) {
        noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
    }
}

function filtrarTablaRDSalidas(q) {
    q = q.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-modal-rd-salidas .rd-salida-row');
    let visibles = 0;
    filas.forEach(function(row) {
        const producto = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const coincide = producto.includes(q);
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    const noResults = document.getElementById('rd-salidas-no-results');
    if (noResults) {
        noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
    }
}

function filtrarTablaRDVentas(q) {
    q = q.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-modal-rd-ventas .rd-venta-row');
    let visibles = 0;
    filas.forEach(function(row) {
        const cliente  = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const producto = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        const coincide = cliente.includes(q) || producto.includes(q);
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    const noResults = document.getElementById('rd-ventas-no-results');
    if (noResults) {
        noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
    }
}

const CYS_CHART_PALETTE = ['#A78BFA', '#3ECF8E'];

function toggleCardChart(btn) {
    const card   = btn.closest('.cys-card');
    const wrap   = card.querySelector('.cys-report-card__chart-wrap');
    const layout = card.querySelector('.cys-report-card-layout');
    if (!wrap || !layout) return;

    const mostrandoGrafica = card.classList.toggle('cys-card--chart-mode');
    btn.classList.toggle('is-active');

    swapChartToggleIcon(btn, card, mostrandoGrafica);

    if (mostrandoGrafica) {
        layout.classList.add('d-none');
        wrap.classList.remove('d-none');

        if (!wrap.dataset.rendered) {
            renderReportCardChart(wrap, card);
            wrap.dataset.rendered = '1';
        }
    } else {
        layout.classList.remove('d-none');
        wrap.classList.add('d-none');
    }
}

function swapChartToggleIcon(btn, card, mostrandoGrafica) {
    const icon = btn.querySelector('i');
    if (!icon) return;

    if (mostrandoGrafica) {

        if (!icon.dataset.originalClass) {
            icon.dataset.originalClass = icon.className;
        }
        const cardIcon = card.querySelector('.cys-report-card-icon--large i');
        if (cardIcon) {
            icon.className = cardIcon.className;
        }
    } else if (icon.dataset.originalClass) {
        icon.className = icon.dataset.originalClass;
    }
}

function renderReportCardChart(wrap, card) {
    const statItems = card.querySelectorAll('.cys-report-card__stat-item');

    const labels = [];
    const data = [];
    const colors = [];

    let colorIndex = 0;
    statItems.forEach(function (item) {
        const numEl = item.querySelector('.cys-report-card__stat-num');
        const labelEl = item.querySelector('.cys-report-card__stat-label');
        if (!numEl || !labelEl) return;

        const rawText = numEl.textContent.trim();
        if (!/\d/.test(rawText)) return;

        const valorNumerico = parseFloat(rawText.replace(/[^0-9.\-]/g, '')) || 0;
        const color = CYS_CHART_PALETTE[colorIndex % CYS_CHART_PALETTE.length];
        colorIndex++;

        labels.push(labelEl.textContent.trim());
        data.push(valorNumerico);
        colors.push(color);
    });

    if (data.length === 0) {
        wrap.innerHTML = '<div class="cys-empty-box cys-empty-box--mini">Sin datos suficientes para graficar.</div>';
        return;
    }

    const canvas = wrap.querySelector('canvas');
    if (!canvas) return;

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderRadius: 6,
                maxBarThickness: 42
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 500 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#02224a',
                    borderColor: 'rgba(167,139,250,.35)',
                    borderWidth: 1,
                    titleColor: '#fff',
                    bodyColor: '#EAF3FA'
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8FA3B1', font: { size: 10 } },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: '#8FA3B1', font: { size: 10 }, precision: 0 },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        }
    });
}


function initReportesUI() {
    pagProv(0);
    crearPaginacionInv();

    const botonesGrafica = document.querySelectorAll('.cys-report-card__chart-toggle');
    botonesGrafica.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            toggleCardChart(this);
        });
    });


    const tarjetas = document.querySelectorAll('.cys-card--interactive[data-cys-modal-target]');
    tarjetas.forEach(function (card) {
        function intentarAbrirModal(e) {

            if (e.target.closest('.cys-report-card__chart-toggle')) return;

            if (card.classList.contains('cys-card--chart-mode')) return;

            const targetSel = card.getAttribute('data-cys-modal-target');
            const modalEl = targetSel ? document.querySelector(targetSel) : null;
            if (modalEl && window.bootstrap) {
                bootstrap.Modal.getOrCreateInstance(modalEl).show();
            }
        }

        card.addEventListener('click', intentarAbrirModal);

        card.setAttribute('tabindex', card.getAttribute('tabindex') || '0');
        card.setAttribute('role', card.getAttribute('role') || 'button');
        card.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            e.preventDefault();
            intentarAbrirModal(e);
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initReportesUI);
} else {
    initReportesUI();
}