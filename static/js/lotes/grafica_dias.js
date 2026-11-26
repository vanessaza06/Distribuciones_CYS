(function () {
  const cfg = document.getElementById('lotes-rot-config');
  const canvas = document.getElementById('chartRotacion');
  if (!cfg || !canvas || typeof Chart === 'undefined') return;

  let labels = [], inicial = [], actual = [];
  try {
    labels = JSON.parse(cfg.dataset.labels || '[]');
    inicial = JSON.parse(cfg.dataset.inicial || '[]');
    actual = JSON.parse(cfg.dataset.actual || '[]');
  } catch (e) { return; }

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Cantidad inicial',
          data: inicial,
          backgroundColor: 'rgba(77,168,218,0.65)',
          borderRadius: 6,
          maxBarThickness: 28
        },
        {
          label: 'Stock actual',
          data: actual,
          backgroundColor: 'rgba(207,156,72,0.9)',
          borderRadius: 6,
          maxBarThickness: 28
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: 'rgba(220,232,242,0.8)', boxWidth: 12 }
        },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y} uds` }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: 'rgba(220,232,242,0.7)' }
        },
        y: {
          beginAtZero: true,
          ticks: { color: 'rgba(220,232,242,0.7)', precision: 0 },
          grid: { color: 'rgba(77,168,218,0.12)' }
        }
      }
    }
  });
})();