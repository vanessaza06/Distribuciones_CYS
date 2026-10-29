(function () {
  'use strict';

  /* ══════════════════════════════════════════════
     UTILIDADES
  ══════════════════════════════════════════════ */
  const GRID = 'rgba(77,168,218,.08)';
  const fmtPeso = v => '$' + (v >= 1_000_000
    ? (v / 1_000_000).toFixed(1) + 'M'
    : (v / 1_000).toFixed(0) + 'k');
  const fmtPesoFull = v => '$' + Math.round(v || 0).toLocaleString('es-CO');
  const tooltipLabel = ctx => ctx.datasetIndex === 0
    ? ' Facturado: '     + fmtPesoFull(ctx.raw)
    : ' Transacciones: ' + Math.round(ctx.raw);

  /* Fecha LOCAL en formato YYYY-MM-DD (toISOString usa UTC y desfasa el día) */
  function fechaLocalISO(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }


  /* ══════════════════════════════════════════════
     ALTURA DINÁMICA DEL CARRUSEL DE CATEGORÍAS
  ══════════════════════════════════════════════ */
  (function () {
    const carousel = document.getElementById('inventarioCarousel');
    if (!carousel) return;

    const inner = carousel.querySelector('.carousel-inner');

    function medirAltura(item) {
      if (!item) return 0;
      const clone = item.cloneNode(true);
      clone.style.position      = 'absolute';
      clone.style.visibility    = 'hidden';
      clone.style.pointerEvents = 'none';
      clone.style.display       = 'block';
      clone.style.width         = inner.clientWidth + 'px';
      clone.classList.add('active');
      inner.appendChild(clone);
      const alto = clone.getBoundingClientRect().height;
      inner.removeChild(clone);
      return alto;
    }

    function ajustarAltura(item) {
      const alto = medirAltura(item);
      if (alto > 0) inner.style.height = alto + 'px';
    }

    function alturaActiva() {
      ajustarAltura(carousel.querySelector('.carousel-item.active'));
    }

    alturaActiva();
    requestAnimationFrame(alturaActiva);
    window.addEventListener('load', alturaActiva);

    carousel.addEventListener('slide.bs.carousel', (e) => {
      ajustarAltura(e.relatedTarget);
    });

    window.addEventListener('resize', alturaActiva);
  })();


  /* ══════════════════════════════════════════════
     GRÁFICA SEMANAL (datos reales de Venta)
  ══════════════════════════════════════════════ */
  const canvasSemanal = document.getElementById('tendenciaChart');

  if (canvasSemanal) {
    const inicialEl = document.getElementById('semana-inicial');
    const inicial   = inicialEl ? JSON.parse(inicialEl.textContent) : {};

    let offsetW   = inicial.offset     ?? 0;
    const labelsW = inicial.labels     ?? [];
    const dataW   = inicial.data       ?? [];
    const countsW = inicial.data_count ?? [];
    const hoyIdxW = inicial.hoy_idx    ?? -1;

    function buildDatasetsSemanal(labels, data, counts, hoyIdx) {
      return {
        labels,
        datasets: [
          {
            label          : 'Facturado ($)',
            data,
            // El día de hoy (en curso) se muestra más claro
            backgroundColor: data.map((_, i) =>
              i === hoyIdx ? 'rgba(77,168,218,0.45)' : 'rgba(77,168,218,0.85)'
            ),
            borderColor : '#4DA8DA',
            borderWidth : 1,
            borderRadius: 4,
            yAxisID     : 'y',
            order       : 2,
          },
          {
            label               : 'Transacciones',
            data                : counts,
            type                : 'line',
            borderColor         : '#1D9E75',
            backgroundColor     : 'rgba(29,158,117,0.07)',
            tension             : 0.4,
            fill                : true,
            pointBackgroundColor: '#1D9E75',
            pointRadius         : 4,
            pointHoverRadius    : 6,
            yAxisID             : 'y2',
            order               : 1,
          }
        ]
      };
    }

    const opcionesSemanal = {
      responsive         : true,
      maintainAspectRatio: false,
      interaction        : { mode: 'index', intersect: false },
      plugins: {
        legend : { display: false },
        tooltip: { callbacks: { label: tooltipLabel } }
      },
      scales: {
        x : {
          ticks: { color: '#ADB5BD', font: { size: 11 }, autoSkip: false, maxRotation: 0 },
          grid : { color: GRID }
        },
        y : {
          position   : 'left',
          beginAtZero: true,
          ticks      : { color: '#ADB5BD', callback: fmtPeso },
          grid       : { color: GRID }
        },
        y2: {
          position   : 'right',
          beginAtZero: true,
          ticks      : {
            color   : '#1D9E75',
            font    : { size: 11 },
            stepSize: 1,
            callback: v => Number.isInteger(v) ? v : null,
          },
          grid: { drawOnChartArea: false }
        }
      }
    };

    const chartSemanal = new Chart(canvasSemanal, {
      type   : 'bar',
      data   : buildDatasetsSemanal(labelsW, dataW, countsW, hoyIdxW),
      options: opcionesSemanal
    });

    function actualizarMetricasSemana(json) {
      const esActual = !!json.es_actual;
      const lbl1     = document.getElementById('lbl-col1');
      const val1     = document.getElementById('metric-col1');
      const sub1     = document.getElementById('metric-col1-sub');

      let total, ventas, pendiente;
      if (esActual) {
        lbl1.textContent = 'Total hoy';
        total     = json.total_hoy      ?? 0;
        ventas    = json.ventas_hoy_num ?? 0;
        pendiente = json.pendiente_hoy  ?? 0;
      } else {
        lbl1.textContent = 'Total semana';
        total     = json.total_semana     ?? 0;
        ventas    = json.ventas_semana    ?? 0;
        pendiente = json.pendiente_semana ?? 0;
      }

      val1.textContent = fmtPesoFull(total);
      sub1.textContent = ventas + ' ventas' +
        (pendiente > 0 ? ' · ' + fmtPesoFull(pendiente) + ' por cobrar' : '');

      document.getElementById('metric-prom').textContent          = fmtPesoFull(json.prom_diario ?? 0);
      document.getElementById('metric-mejor-dia').textContent     = json.mejor_dia || '—';
      document.getElementById('metric-mejor-dia-val').textContent = fmtPesoFull(json.mejor_dia_val ?? 0);
    }

    async function cargarSemana(offset) {
      const btnPrev = document.getElementById('btn-semana-prev');
      const btnNext = document.getElementById('btn-semana-next');

      btnPrev.disabled = btnNext.disabled = true;
      btnPrev.style.opacity = btnNext.style.opacity = '.4';

      try {
        const resp = await fetch(`/semana-json/?offset=${offset}`);
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const json = await resp.json();

        chartSemanal.data = buildDatasetsSemanal(
          json.labels     ?? [],
          json.data       ?? [],
          json.data_count ?? [],
          json.hoy_idx    ?? -1
        );
        chartSemanal.update();

        document.getElementById('semana-label').textContent = json.semana_label ?? '';
        actualizarMetricasSemana(json);
        offsetW = offset;

      } catch (e) {
        console.error('Error cargando semana:', e);
      } finally {
        btnPrev.disabled      = false;
        btnPrev.style.opacity = '1';
        btnNext.disabled      = (offsetW === 0);
        btnNext.style.opacity = (offsetW === 0) ? '.4' : '1';
      }
    }

    /* Helpers de fecha para el date picker (todo en hora local) */
    function lunesDe(dateStr) {
      const d   = new Date(dateStr + 'T12:00:00');
      const day = d.getDay();
      d.setDate(d.getDate() + ((day === 0) ? -6 : 1 - day));
      return d;
    }

    function offsetDesde(lunes) {
      const lunesHoy = lunesDe(fechaLocalISO(new Date()));
      return Math.max(0, Math.round((lunesHoy - lunes) / (7 * 86400000)));
    }

    const pickerSemana = document.getElementById('semana-picker');
    pickerSemana.max = fechaLocalISO(new Date());

    document.getElementById('btn-semana-prev')
      .addEventListener('click', () => cargarSemana(offsetW + 1));

    document.getElementById('btn-semana-next')
      .addEventListener('click', () => { if (offsetW > 0) cargarSemana(offsetW - 1); });

    /* Antes era un onclick inline en el HTML */
    document.getElementById('semana-picker-wrap')
      .addEventListener('click', () => pickerSemana.showPicker());

    pickerSemana.addEventListener('change', e => {
      if (!e.target.value) return;
      cargarSemana(offsetDesde(lunesDe(e.target.value)));
    });
  }


  /* ══════════════════════════════════════════════
     GRÁFICA MENSUAL
  ══════════════════════════════════════════════ */
  async function cargarMensual() {
    const canvasMensual = document.getElementById('mensualChart');
    if (!canvasMensual) return;

    try {
      const resp = await fetch('/meses-json/');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const json = await resp.json();

      const labels  = json.labels     ?? [];
      const data    = json.data       ?? [];
      const counts  = json.data_count ?? [];
      const colores = json.colores    ?? data.map(() => 'rgba(167,139,250,0.75)');
      const idxMejores = new Set(json.idx_mejores ?? []);
      const idxPeores  = new Set(json.idx_peores  ?? []);

      document.getElementById('mensual-skeleton').style.display = 'none';
      document.getElementById('mensual-wrap').style.display     = 'block';

      new Chart(canvasMensual, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label          : 'Facturado ($)',
              data,
              backgroundColor: colores,
              borderColor    : colores.map(c => c.replace(/[\d.]+\)$/, '1)')),
              borderWidth    : 1,
              borderRadius   : 5,
              yAxisID        : 'y',
              order          : 2,
            },
            {
              label               : 'Transacciones',
              data                : counts,
              type                : 'line',
              borderColor         : '#FB923C',
              backgroundColor     : 'rgba(251,146,60,0.07)',
              tension             : 0.4,
              fill                : true,
              pointBackgroundColor: '#FB923C',
              pointRadius         : 5,
              pointHoverRadius    : 7,
              yAxisID             : 'y2',
              order               : 1,
            }
          ]
        },
        options: {
          responsive         : true,
          maintainAspectRatio: false,
          interaction        : { mode: 'index', intersect: false },
          plugins: {
            legend : { display: false },
            tooltip: {
              callbacks: {
                label    : tooltipLabel,
                afterBody: items => {
                  const i = items[0]?.dataIndex;
                  if (idxMejores.has(i)) return ['', '🏆 Mejor mes'];
                  if (idxPeores.has(i))  return ['', '⚠️  Mes bajo'];
                  return [];
                }
              }
            }
          },
          scales: {
            x : {
              ticks: { color: '#ADB5BD', font: { size: 12 } },
              grid : { color: GRID }
            },
            y : {
              position   : 'left',
              beginAtZero: true,
              ticks      : { color: '#ADB5BD', callback: fmtPeso },
              grid       : { color: GRID }
            },
            y2: {
              position   : 'right',
              beginAtZero: true,
              ticks      : {
                color   : '#FB923C',
                font    : { size: 11 },
                stepSize: 1,
                callback: v => Number.isInteger(v) ? v : null,
              },
              grid: { drawOnChartArea: false }
            }
          }
        }
      });

    } catch (e) {
      console.error('Error cargando datos mensuales:', e);
      document.getElementById('mensual-skeleton').innerHTML =
        `<span style="color:#dc3545;font-size:.8rem;">
           No se pudieron cargar los datos mensuales.
         </span>`;
    }
  }

  cargarMensual();
})();