/**
 * REPORTES.JS — Reportes y Análisis
 * DataTable, filtrado, paginación, gráficas en tarjetas
 */

/* ══════════════════════════════════════════════
   DataTable — Historial de Ventas
══════════════════════════════════════════════ */
$(document).ready(function () {

    var $tabla = $('#reportes-table');
    var table = null;

    if ($tabla.length && $.fn.DataTable) {

        var msgVacio = $tabla.data('empty-msg') || 'No hay ventas registradas aún.';
        var htmlVacio =
            '<div class="cys-empty-box"><i class="bi bi-bar-chart"></i>' + msgVacio + '</div>';

        table = $tabla.DataTable({
            paging: true,
            searching: true,
            info: true,
            lengthChange: false,
            pageLength: 10,
            ordering: true,
            order: [],              // respeta el orden que envía el servidor
            autoWidth: false,
            dom: 'rt',              // solo tabla; info y paginación se pintan a mano
            language: {
                emptyTable: htmlVacio,
                zeroRecords: '<div class="cys-empty-box"><i class="bi bi-search"></i>No se encontraron resultados.</div>'
            }
        });

        /* ── Pie: info + paginación propia ── */
        var $info = $('#cys-dt-info');
        var $pag = $('#cys-dt-pagination');

        function renderFooter() {
            var i = table.page.info();

            if (i.recordsDisplay === 0) {
                $info.text('Mostrando 0 a 0 de 0 ventas');
                $pag.empty();
                return;
            }

            var txt = 'Mostrando ' + (i.start + 1) + ' a ' + i.end +
                ' de ' + i.recordsDisplay + ' ventas';
            if (i.recordsDisplay !== i.recordsTotal) {
                txt += ' (filtrado de ' + i.recordsTotal + ')';
            }
            $info.text(txt);

            if (i.pages <= 1) {
                $pag.empty();
                return;
            }

            var actual = i.page;                     // base 0
            var ini = Math.max(0, actual - 2);
            var fin = Math.min(i.pages - 1, actual + 2);
            var html = '';

            html += '<button type="button" class="cys-pag-btn" data-page="prev"' +
                (actual === 0 ? ' disabled' : '') + '>‹</button>';

            if (ini > 0) {
                html += '<button type="button" class="cys-pag-btn" data-page="0">1</button>';
                if (ini > 1) html += '<span class="cys-pag-dots">…</span>';
            }

            for (var p = ini; p <= fin; p++) {
                html += '<button type="button" class="cys-pag-btn' +
                    (p === actual ? ' active' : '') + '" data-page="' + p + '">' +
                    (p + 1) + '</button>';
            }

            if (fin < i.pages - 1) {
                if (fin < i.pages - 2) html += '<span class="cys-pag-dots">…</span>';
                html += '<button type="button" class="cys-pag-btn" data-page="' +
                    (i.pages - 1) + '">' + i.pages + '</button>';
            }

            html += '<button type="button" class="cys-pag-btn" data-page="next"' +
                (actual === i.pages - 1 ? ' disabled' : '') + '>›</button>';

            $pag.html(html);
        }

        $pag.on('click', 'button[data-page]', function () {
            var d = $(this).data('page');
            if (d === 'prev') table.page('previous');
            else if (d === 'next') table.page('next');
            else table.page(parseInt(d, 10));
            table.draw('page');
        });

        table.on('draw', renderFooter);
        renderFooter();

        /* ── Buscador ── */
        $('#buscar-historial').on('input', function () {
            table.search(this.value).draw();
        });
    }

    /* ── Filtros de fecha ── */
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
        const ff = $('#filtro-fecha-fin').val() || '';
        const p = `&fecha_inicio=${fi}&fecha_fin=${ff}`;
        $('#btn-export-excel').attr('href', `?export=excel&tipo=ventas${p}`);
        $('#btn-export-pdf').attr('href', `?export=pdf&tipo=ventas${p}`);
        $('#btn-export-print').attr('href', `?export=pdf&tipo=ventas&print=true${p}`);
    }

    $('#filtro-fecha-inicio').on('change', function () {
        enlazarFechasReportes('ini');
        syncExportLinks();
        aplicarFiltro('ini');
    });

    $('#filtro-fecha-fin').on('change', function () {
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

    const params = new URLSearchParams();
    if (fi) params.set('fecha_inicio', fi);
    if (ff) params.set('fecha_fin', ff);
    const qs = params.toString();
    window.location.href = window.location.pathname + (qs ? '?' + qs : '');
}

/* ══════════════════════════════════════════════
   INVENTARIO — búsqueda + paginación de 10 en 10
══════════════════════════════════════════════ */
var INV_POR_PAGINA = 10;
var invPagActual = 1;
var invQuery = '';

function invFilasCoincidentes() {
    var filas = document.querySelectorAll('#tabla-modal-stock .inv-row');
    var res = [];
    filas.forEach(function (row) {
        var txt = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        if (txt.includes(invQuery)) res.push(row);
    });
    return res;
}

function renderInvPag() {
    var todas = document.querySelectorAll('#tabla-modal-stock .inv-row');
    var coinciden = invFilasCoincidentes();
    var totalPags = Math.max(1, Math.ceil(coinciden.length / INV_POR_PAGINA));
    invPagActual = Math.max(1, Math.min(invPagActual, totalPags));

    var inicio = (invPagActual - 1) * INV_POR_PAGINA;
    var fin = inicio + INV_POR_PAGINA;

    todas.forEach(function (r) { r.style.display = 'none'; });
    coinciden.slice(inicio, fin).forEach(function (r) { r.style.display = ''; });

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
    document.getElementById('inv-pag-prev').disabled = invPagActual === 1;
    document.getElementById('inv-pag-next').disabled = invPagActual === totalPags;
    document.getElementById('inv-pag-last').disabled = invPagActual === totalPags;
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

    document.getElementById('inv-pag-first').addEventListener('click', function () { irPagInv('first'); });
    document.getElementById('inv-pag-prev').addEventListener('click', function () { pagInv(-1); });
    document.getElementById('inv-pag-next').addEventListener('click', function () { pagInv(1); });
    document.getElementById('inv-pag-last').addEventListener('click', function () { irPagInv('last'); });

    renderInvPag();
}

/* ── Búsqueda proveedores ── */
function filtrarTablaProv(q) {
    q = q.toLowerCase();
    document.querySelectorAll('#tabla-modal-proveedores .prov-row').forEach(function (row) {
        const nombre = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const empresa = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        row.style.display = (nombre.includes(q) || empresa.includes(q)) ? '' : 'none';
    });
}

/* ── Paginación simple proveedores ── */
var provPagActual = 1;
function pagProv(dir) {
    var rows = document.querySelectorAll('#tabla-modal-proveedores .prov-row');
    var perPage = 5;
    var total = Math.ceil(rows.length / perPage);
    provPagActual = Math.max(1, Math.min(provPagActual + dir, total));
    rows.forEach(function (r, i) {
        var page = Math.floor(i / perPage) + 1;
        r.style.display = page === provPagActual ? '' : 'none';
    });
    var ind = document.getElementById('prov-pag-indicator');
    if (ind) ind.textContent = provPagActual;
}

/* ── Análisis de ventas — sidebar nav ── */
function avSetTab(tab) {
    ['resumen', 'fecha', 'top'].forEach(function (t) {
        var panel = document.getElementById('avPanel-' + t);
        var btn = document.getElementById('avNav-' + t);
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

/* ── Helper genérico de filtrado de filas ── */
function filtrarFilas(selFilas, colsIdx, q, idNoResults) {
    q = (q || '').toLowerCase().trim();
    const filas = document.querySelectorAll(selFilas);
    let visibles = 0;
    filas.forEach(function (row) {
        const coincide = colsIdx.some(function (c) {
            const td = row.querySelector('td:nth-child(' + c + ')');
            return td && td.textContent.toLowerCase().includes(q);
        });
        row.style.display = coincide ? '' : 'none';
        if (coincide) visibles++;
    });
    if (idNoResults) {
        const noResults = document.getElementById(idNoResults);
        if (noResults) {
            noResults.classList.toggle('d-none', !(filas.length > 0 && visibles === 0));
        }
    }
}

/* ── Búsqueda: Análisis de Ventas → "Por fecha" ── */
function filtrarTablaAVFecha(q) {
    filtrarFilas('#tabla-modal-av-ventas .av-fecha-row', [2, 3], q, 'av-fecha-no-results');
}

/* ── Búsqueda: Análisis de Ventas → "Top productos" ── */
function filtrarTablaAVTop(q) {
    filtrarFilas('#tabla-modal-av-top .av-top-row', [2], q, 'av-top-no-results');
}

/* ── Búsqueda devoluciones ── */
function filtrarTablaDevoluciones(q) {
    filtrarFilas('#tabla-modal-devoluciones .dev-row', [2, 3], q, null);
}

/* ── Búsqueda: Resumen Diario ── */
function filtrarTablaRDEntradas(q) {
    filtrarFilas('#tabla-modal-rd-entradas .rd-entrada-row', [2], q, 'rd-entradas-no-results');
}

function filtrarTablaRDVentas(q) {
    filtrarFilas('#tabla-modal-rd-ventas .rd-venta-row', [2, 3], q, 'rd-ventas-no-results');
}

/* ══════════════════════════════════════════════
   GRÁFICAS EN TARJETAS
══════════════════════════════════════════════ */
const CYS_CHART_PALETTE = ['#A78BFA', '#3ECF8E'];

function toggleCardChart(btn) {
    const card = btn.closest('.cys-card');
    const wrap = card.querySelector('.cys-report-card__chart-wrap');
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
    if (!canvas || typeof Chart === 'undefined') return;

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

/* ══════════════════════════════════════════════
   INIT UI
══════════════════════════════════════════════ */
function initReportesUI() {
    pagProv(0);
    crearPaginacionInv();

    document.querySelectorAll('.cys-report-card__chart-toggle').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            toggleCardChart(this);
        });
    });

    document.querySelectorAll('.cys-card--interactive[data-cys-modal-target]').forEach(function (card) {
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