/**
 * REPORTES.JS — Reportes y Análisis
 * DataTables (historial + tablas de modales) con buscador,
 * filtros de fecha del historial, gráficas en tarjetas
 */

/* ══════════════════════════════════════════════
   BUSCADORES DE LAS TABLAS DE MODALES
   Solo las tablas que NO tienen un buscador en el HTML
   (data-dt-search) reciben uno creado aquí, con el mismo
   estilo del buscador del Historial de Ventas.
   Valor = texto del placeholder.
══════════════════════════════════════════════ */
var CYS_DT_BUSCADORES = {
    'tabla-modal-entradas':       'Buscar producto, orden...',
    'tabla-modal-compras':        'Buscar proveedor, producto...',
    'tabla-modal-rd-top':         'Buscar producto...',
    'tabla-modal-av-recientes':   'Buscar producto, cliente...',
    'tabla-modal-av-top-resumen': 'Buscar producto...'
};

/* ── Estilo mínimo de la barra del buscador (inyectado una sola vez) ── */
(function inyectarEstilosBuscador() {
    if (document.getElementById('cys-dt-toolbar-css')) return;
    var st = document.createElement('style');
    st.id = 'cys-dt-toolbar-css';
    st.textContent = '.cys-dt-toolbar{padding:12px 20px;}';
    document.head.appendChild(st);
})();

/* ══════════════════════════════════════════════
   HELPER: buscador con el estilo del Historial de Ventas
══════════════════════════════════════════════ */
function cysBuildSearch($, $tabla, table, placeholder) {
    var $bar = $(
        '<div class="cys-hv-filters cys-dt-toolbar">' +
        '<div class="cys-hv-date-group">' +
        '<div class="cys-hv-search-wrap">' +
        '<i class="bi bi-search cys-hv-search-icon"></i>' +
        '<input type="text" class="cys-hv-search-input">' +
        '</div>' +
        '</div>' +
        '</div>'
    );

    var $input = $bar.find('input');
    $input.attr('placeholder', placeholder || 'Buscar...');
    $input.on('input', function () {
        table.search(this.value).draw();
    });

    var $wrap = $tabla.closest('.table-responsive');
    if (!$wrap.length) $wrap = $tabla;
    $wrap.before($bar);
}

/* ══════════════════════════════════════════════
   HELPER: inicializar un DataTable con pie propio
   (info + paginación estilo píldoras) y buscador
══════════════════════════════════════════════ */
function cysInitDataTable($, $tabla, cfg) {
    cfg = cfg || {};

    var label = cfg.label || 'registros';
    var icon = cfg.icon || 'bi-inbox';
    var msgVacio = cfg.emptyMsg || 'No hay datos registrados.';
    var pageLength = parseInt(cfg.pageLength, 10) || 10;

    var table = $tabla.DataTable({
        paging: true,
        searching: true,
        info: true,
        lengthChange: false,
        pageLength: pageLength,
        ordering: true,          // clic en el encabezado = ordenar asc/desc
        order: [],               // respeta el orden que envía el servidor
        autoWidth: false,
        dom: 'rt',               // solo tabla; info y paginación se pintan a mano
        language: {
            emptyTable: '<div class="cys-empty-box"><i class="bi ' + icon + '"></i>' + msgVacio + '</div>',
            zeroRecords: '<div class="cys-empty-box"><i class="bi bi-search"></i>No se encontraron resultados.</div>'
        }
    });

    /* ── Contenedores del pie ── */
    var $info = cfg.$info;
    var $pag = cfg.$pag;

    if (!$info || !$info.length || !$pag || !$pag.length) {
        var $wrap = $tabla.closest('.table-responsive');
        if (!$wrap.length) $wrap = $tabla;

        var $footer = $(
            '<div class="cys-hv-table-footer">' +
            '<span class="cys-hv-showing-info"></span>' +
            '<div class="cys-hv-pagination-wrap"></div>' +
            '</div>'
        );
        $wrap.after($footer);
        $info = $footer.find('.cys-hv-showing-info');
        $pag = $footer.find('.cys-hv-pagination-wrap');
    }

    function renderFooter() {
        var i = table.page.info();

        if (i.recordsDisplay === 0) {
            $info.text('Mostrando 0 a 0 de 0 ' + label);
            $pag.empty();
            return;
        }

        var txt = 'Mostrando ' + (i.start + 1) + ' a ' + i.end +
            ' de ' + i.recordsDisplay + ' ' + label;
        if (i.recordsDisplay !== i.recordsTotal) {
            txt += ' (filtrado de ' + i.recordsTotal + ')';
        }
        $info.text(txt);

        if (i.pages <= 1) {
            $pag.empty();
            return;
        }

        var actual = i.page;                     // base 0
        var ini = Math.max(0, actual - 1);
        var fin = Math.min(i.pages - 1, actual + 1);

        // Mantener siempre 3 botones numéricos visibles cuando se pueda
        if (actual === 0) fin = Math.min(i.pages - 1, 2);
        if (actual === i.pages - 1) ini = Math.max(0, i.pages - 3);

        var html = '';

        // Anterior
        html += '<button type="button" class="cys-pag-btn" data-page="prev" aria-label="Anterior"' +
            (actual === 0 ? ' disabled' : '') + '><i class="bi bi-chevron-left"></i></button>';

        // Primera página + puntos
        if (ini > 0) {
            html += '<button type="button" class="cys-pag-btn" data-page="0">1</button>';
            if (ini > 1) html += '<span class="cys-pag-dots">...</span>';
        }

        // Páginas centrales
        for (var p = ini; p <= fin; p++) {
            html += '<button type="button" class="cys-pag-btn' +
                (p === actual ? ' active' : '') + '" data-page="' + p + '">' +
                (p + 1) + '</button>';
        }

        // Puntos + última página
        if (fin < i.pages - 1) {
            if (fin < i.pages - 2) html += '<span class="cys-pag-dots">...</span>';
            html += '<button type="button" class="cys-pag-btn" data-page="' +
                (i.pages - 1) + '">' + i.pages + '</button>';
        }

        // Siguiente
        html += '<button type="button" class="cys-pag-btn" data-page="next" aria-label="Siguiente"' +
            (actual === i.pages - 1 ? ' disabled' : '') + '><i class="bi bi-chevron-right"></i></button>';

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

    /* ── Buscador del HTML (si la tabla tiene data-dt-search / historial) ── */
    var tieneBuscadorExterno = false;
    if (cfg.searchId) {
        var $input = $('#' + cfg.searchId);
        if ($input.length) {
            tieneBuscadorExterno = true;
            $input.on('input', function () {
                table.search(this.value).draw();
            });
        }
    }

    /* ── Buscador propio (solo si la tabla no tiene uno en el HTML) ── */
    var idTabla = $tabla.attr('id');
    var placeholder = cfg.buscador || CYS_DT_BUSCADORES[idTabla];
    if (placeholder && !tieneBuscadorExterno) {
        cysBuildSearch($, $tabla, table, placeholder);
    }

    return table;
}

/* ══════════════════════════════════════════════
   DataTable — Historial de Ventas + tablas de modales
   (protegido: si jQuery/DataTables no cargan, el resto del script sigue funcionando)
══════════════════════════════════════════════ */
(function initDataTables() {
    if (!window.jQuery) {
        console.warn('[reportes.js] jQuery no está cargado; se omiten los DataTables.');
        return;
    }

    var $ = window.jQuery;

    $(document).ready(function () {

        if (!$.fn.DataTable) {
            console.warn('[reportes.js] DataTables no está cargado.');
        } else {

            /* ── 1) Historial de Ventas (ya tiene su propia barra de filtros) ── */
            var $tabla = $('#reportes-table');
            if ($tabla.length) {
                var msgVacio = $tabla.data('empty-msg') || 'No hay ventas registradas aún.';
                cysInitDataTable($, $tabla, {
                    label: 'ventas',
                    icon: 'bi-bar-chart',
                    emptyMsg: msgVacio,
                    pageLength: 10,
                    searchId: 'buscar-historial',
                    $info: $('#cys-dt-info'),
                    $pag: $('#cys-dt-pagination')
                });
            }

            /* ── 2) Tablas de los modales (clase .cys-dt) ── */
            $('table.cys-dt').each(function () {
                var $t = $(this);
                if ($.fn.DataTable.isDataTable(this)) return;

                $t.css('width', '100%');

                cysInitDataTable($, $t, {
                    label: $t.data('dt-label') || 'registros',
                    icon: $t.data('dt-icon') || 'bi-inbox',
                    emptyMsg: $t.data('dt-empty') || 'No hay datos registrados.',
                    pageLength: $t.data('dt-page') || 10,
                    searchId: $t.data('dt-search') || null
                });
            });
        }

        /* ── Filtros de fecha (historial, recarga con el servidor) ── */
        function enlazarFechasReportes(origen) {
            var $fi = $('#filtro-fecha-inicio');
            var $ff = $('#filtro-fecha-fin');
            var vi = $fi.val();
            var vf = $ff.val();

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
            var fi = $('#filtro-fecha-inicio').val() || '';
            var ff = $('#filtro-fecha-fin').val() || '';
            var p = '&fecha_inicio=' + fi + '&fecha_fin=' + ff;
            $('#btn-export-excel').attr('href', '?export=excel&tipo=ventas' + p);
            $('#btn-export-pdf').attr('href', '?export=pdf&tipo=ventas' + p);
            $('#btn-export-print').attr('href', '?export=pdf&tipo=ventas&print=true' + p);
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
})();

function aplicarFiltro(origen) {
    var elFi = document.getElementById('filtro-fecha-inicio');
    var elFf = document.getElementById('filtro-fecha-fin');
    var fi = elFi ? elFi.value : '';
    var ff = elFf ? elFf.value : '';

    if (fi && ff && fi > ff) {
        if (origen === 'fin') {
            fi = ff;
            if (elFi) elFi.value = ff;
        } else {
            ff = fi;
            if (elFf) elFf.value = fi;
        }
    }

    var params = new URLSearchParams();
    if (fi) params.set('fecha_inicio', fi);
    if (ff) params.set('fecha_fin', ff);
    var qs = params.toString();
    window.location.href = window.location.pathname + (qs ? '?' + qs : '');
}

/* ══════════════════════════════════════════════
   Reajustar columnas de DataTables visibles
   (las tablas dentro de modales/pestañas ocultas calculan mal el ancho)
══════════════════════════════════════════════ */
function ajustarDataTablesVisibles(contexto) {
    if (!window.jQuery || !window.jQuery.fn.DataTable) return;
    var $ = window.jQuery;
    var $root = contexto ? $(contexto) : $(document);
    $root.find('table.cys-dt').each(function () {
        if ($.fn.DataTable.isDataTable(this)) {
            $(this).DataTable().columns.adjust();
        }
    });
}

// Al abrir un modal
document.addEventListener('shown.bs.modal', function (e) {
    ajustarDataTablesVisibles(e.target);
});

// Al cambiar de pestaña (Resumen Diario: Entradas / Ventas)
document.addEventListener('shown.bs.tab', function (e) {
    var modal = e.target.closest ? e.target.closest('.modal') : null;
    ajustarDataTablesVisibles(modal || document);
});

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

    // Las tablas del panel recién mostrado necesitan recalcular el ancho
    var panelActivo = document.getElementById('avPanel-' + tab);
    if (panelActivo) ajustarDataTablesVisibles(panelActivo);
}

/* ══════════════════════════════════════════════
   GRÁFICAS EN TARJETAS
══════════════════════════════════════════════ */
var CYS_CHART_PALETTE = ['#A78BFA', '#3ECF8E']; // se reemplaza abajo por el color del tema

function cysColorAcento() {
    var c = getComputedStyle(document.documentElement)
        .getPropertyValue('--azul-claro').trim();
    return c || '#B3271C';
}

/**
 * Convierte el texto de una estadística ("$1.234.567", "1,234", "12.5%", "+8")
 * en número. Maneja separadores de miles con punto o coma.
 */
function parseNumeroStat(raw) {
    var t = String(raw).trim();
    var esPorcentaje = t.indexOf('%') !== -1;

    // Quedarse solo con dígitos, signo menos, punto y coma
    t = t.replace(/[^0-9.,\-]/g, '');

    if (esPorcentaje) {
        // En porcentajes el separador es decimal (12,5% o 12.5%)
        return parseFloat(t.replace(',', '.')) || 0;
    }

    // Valores enteros (floatformat:0): cualquier punto/coma es separador de miles
    return parseFloat(t.replace(/[.,]/g, '')) || 0;
}

function toggleCardChart(btn) {
    var card = btn.closest('.cys-card');
    if (!card) return;
    var wrap = card.querySelector('.cys-report-card__chart-wrap');
    var layout = card.querySelector('.cys-report-card-layout');
    if (!wrap || !layout) return;

    var yaEnModoGrafica = card.classList.contains('cys-card--chart-mode');

    // Si Chart.js no está disponible, no cambiamos de modo (evita tarjeta vacía)
    if (!yaEnModoGrafica && typeof Chart === 'undefined') {
        console.error('[reportes.js] Chart.js no está cargado (revisa vendor/chartjs/chart.umd.min.js).');
        return;
    }

    var mostrandoGrafica = card.classList.toggle('cys-card--chart-mode');
    btn.classList.toggle('is-active', mostrandoGrafica);

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
    var icon = btn.querySelector('i');
    if (!icon) return;

    if (mostrandoGrafica) {
        if (!icon.dataset.originalClass) {
            icon.dataset.originalClass = icon.className;
        }
        var cardIcon = card.querySelector('.cys-report-card-icon--large i');
        if (cardIcon) {
            icon.className = cardIcon.className;
        }
    } else if (icon.dataset.originalClass) {
        icon.className = icon.dataset.originalClass;
    }
}

function renderReportCardChart(wrap, card) {
    var statItems = card.querySelectorAll('.cys-report-card__stat-item');

    var labels = [];
    var data = [];
    var colors = [];

    var colorIndex = 0;
        CYS_CHART_PALETTE = ['#A78BFA', cysColorAcento()];
    statItems.forEach(function (item) {
        var numEl = item.querySelector('.cys-report-card__stat-num');
        var labelEl = item.querySelector('.cys-report-card__stat-label');
        if (!numEl || !labelEl) return;

        var rawText = numEl.textContent.trim();
        if (!/\d/.test(rawText)) return;

        var valorNumerico = parseNumeroStat(rawText);
        var color = CYS_CHART_PALETTE[colorIndex % CYS_CHART_PALETTE.length];
        colorIndex++;

        labels.push(labelEl.textContent.trim());
        data.push(valorNumerico);
        colors.push(color);
    });

    if (data.length === 0) {
        wrap.innerHTML = '<div class="cys-empty-box cys-empty-box--mini">Sin datos suficientes para graficar.</div>';
        return;
    }

    var canvas = wrap.querySelector('canvas');
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
   MODALES — mover a <body>
   Los modales están dentro del contenido de la página; si algún contenedor
   padre crea su propio contexto de apilamiento (transform, overflow, z-index,
   scroll-snap...), el modal queda debajo del backdrop y "no abre" o no se
   puede clicar. Moverlos a <body> lo resuelve.
══════════════════════════════════════════════ */
function moverModalesABody() {
    document.querySelectorAll('.modal').forEach(function (el) {
        if (el.parentElement !== document.body) {
            document.body.appendChild(el);
        }
    });
}

/* ══════════════════════════════════════════════
   INIT UI
══════════════════════════════════════════════ */
function abrirModalDeTarjeta(card) {
    var targetSel = card.getAttribute('data-cys-modal-target');
    var modalEl = targetSel ? document.querySelector(targetSel) : null;

    if (!modalEl) {
        console.error('[reportes.js] No se encontró el modal:', targetSel);
        return;
    }
    if (!window.bootstrap || !bootstrap.Modal) {
        console.error('[reportes.js] Bootstrap JS no está cargado; no se puede abrir el modal.');
        return;
    }
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

function initReportesUI() {
    moverModalesABody();

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
            abrirModalDeTarjeta(card);
        }

        card.addEventListener('click', intentarAbrirModal);

        card.setAttribute('tabindex', card.getAttribute('tabindex') || '0');
        card.setAttribute('role', card.getAttribute('role') || 'button');
        card.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' && e.key !== ' ') return;
            // Si el foco está en el botón de gráfica, dejar que el botón haga lo suyo
            if (e.target.closest('.cys-report-card__chart-toggle')) return;
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