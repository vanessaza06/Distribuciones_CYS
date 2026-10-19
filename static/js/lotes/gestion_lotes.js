/**
 * GESTION_LOTES.JS — Gestión de Lotes de Inventario
 * Funcionalidades: gráfico de stock, dropdown de presentación, validación
 */

document.addEventListener('DOMContentLoaded', function () {
  try {
    inicializarGraficoProveedores();
  } catch (e) {
    console.error('No se pudo inicializar el gráfico de proveedores:', e);
  }
  inicializarDropdownPresentacion();
  inicializarBuscadorPresentaciones(); 
  inicializarValidacionFormulario();
  aplicarPreseleccionPresentacion();

});

/**
 * Crea el gráfico de barras de stock por producto
 */
function inicializarGraficoProveedores() {
  const canvas = document.getElementById('chartProveedores');
  if (!canvas) return;

  if (typeof Chart === 'undefined') {
    console.warn('Chart.js no está disponible; se omite el gráfico de proveedores.');
    return;
  }

  const configElement = document.getElementById('lotes-config');
  let labels = [];
  let data = [];

  if (configElement) {
    const labelsData = configElement.getAttribute('data-labels');
    const chartData = configElement.getAttribute('data-data');

    if (labelsData && chartData) {
      try {
        labels = JSON.parse(labelsData);
        data = JSON.parse(chartData);
      } catch (e) {
        console.error('Error al parsear datos del gráfico:', e);
      }
    }
  }

  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Unidades en stock',
        data: data,
        backgroundColor: [
          'rgba(62, 181, 229, 0.85)',
          'rgb(190, 87, 231)',
          'rgb(10, 74, 169)',
          'rgba(108, 92, 231, 0.85)',
          'rgba(155, 254, 218, 0.85)'
        ],
        borderColor: ['#4195c9', '#d059ff', '#014ab0', '#6c5ce7', '#9bfebc'],
        borderWidth: 1,
        borderRadius: 5
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#dce8f2', font: { size: 10 } }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#dce8f2', font: { size: 11, weight: '600' } }
        }
      }
    }
  });
}

/**
 * Sincroniza el dropdown visual con el select oculto
 */
function inicializarDropdownPresentacion() {
  const selLote = document.getElementById('select-presentacion-lote');
  const inputProducto = document.getElementById('input-producto-lote');
  if (!selLote || !inputProducto) return;

  document.querySelectorAll('.presentacion-lote-item').forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      selLote.value = item.dataset.value;
      inputProducto.value = item.dataset.productoPk;
      document.getElementById('presentacion-lote-label').textContent = item.textContent.trim();
    });
  });
}

/**
 * Si llegamos desde Bodega con ?presentacion=<pk>, selecciona esa
 * presentación automáticamente y lleva al usuario directo al formulario.
 */
function aplicarPreseleccionPresentacion() {
  const contenedor = document.getElementById('lotes-preseleccion');
  if (!contenedor) return;

  const pk = contenedor.dataset.presentacion;
  if (!pk) return;

  const item = document.querySelector(`.presentacion-lote-item[data-value="${pk}"]`);
  if (!item) return;

  item.click();

  const formulario = document.getElementById('form-lote');
  if (formulario) {
    formulario.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/**
 * Validación del formulario antes de enviar
 */
function inicializarValidacionFormulario() {
  const formLote = document.getElementById('form-lote');
  const selLote = document.getElementById('select-presentacion-lote');

  if (!formLote || !selLote) return;

  formLote.addEventListener('submit', e => {
    if (!selLote.value) {
      e.preventDefault();
      const btn = document.getElementById('presentacion-lote-btn');
      if (btn) {
        btn.style.borderColor = '#e74c3c';
        btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  });

  document.querySelectorAll('.lote-spin-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const step = parseFloat(input.dataset.salto) || parseFloat(input.step) || 1;
      const min = input.min !== '' ? parseFloat(input.min) : -Infinity;
      let valor = parseFloat(input.value) || 0;
      valor = btn.classList.contains('lote-spin-up') ? valor + step : valor - step;
      if (valor < min) valor = min;
      input.value = valor;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    });
  });
}

/**
 * Buscador dentro del desplegable de presentaciones.
 * Filtra por nombre de producto o de presentación (sin tildes ni mayúsculas).
 */
function inicializarBuscadorPresentaciones() {
  const buscador = document.getElementById('buscador-presentacion-lote');
  const menu = document.querySelector('.lote-presentacion-menu');
  const btn = document.getElementById('presentacion-lote-btn');
  const sinResultados = document.getElementById('presentacion-sin-resultados');
  if (!buscador || !menu || !btn) return;

  const limpiar = t => (t || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().trim();

  // Agrupa cada producto (encabezado) con sus presentaciones
  const grupos = [];
  let actual = null;
  menu.querySelectorAll(':scope > li').forEach(li => {
    const encabezado = li.querySelector('.dropdown-header');
    const item = li.querySelector('.presentacion-lote-item');
    if (encabezado) {
      actual = { li, producto: limpiar(encabezado.textContent), items: [] };
      grupos.push(actual);
    } else if (item && actual) {
      actual.items.push({ li, texto: limpiar(item.textContent) });
    }
  });

  function filtrar() {
    const terminos = limpiar(buscador.value).split(/\s+/).filter(Boolean);
    let visibles = 0;

    grupos.forEach(g => {
      let hayVisible = false;
      g.items.forEach(it => {
        const texto = g.producto + ' ' + it.texto;
        const coincide = terminos.every(t => texto.includes(t));
        it.li.classList.toggle('d-none', !coincide);
        if (coincide) { hayVisible = true; visibles++; }
      });
      g.li.classList.toggle('d-none', !hayVisible);
    });

    if (sinResultados) {
      sinResultados.classList.toggle('d-none', visibles > 0 || terminos.length === 0);
    }
  }

  buscador.addEventListener('input', filtrar);

  // Hacer clic en el buscador no debe cerrar el desplegable
  buscador.closest('.lote-buscador-item').addEventListener('click', e => e.stopPropagation());

  buscador.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();      // evita enviar el formulario
      e.stopPropagation();
      const primero = menu.querySelector('li:not(.d-none) > .presentacion-lote-item');
      if (primero) primero.click();
      return;
    }
    // Escape y flechas siguen funcionando con Bootstrap; el resto se queda en el campo
    if (!['Escape', 'ArrowDown', 'ArrowUp'].includes(e.key)) e.stopPropagation();
  });

  // Al abrir: foco en el buscador. Al cerrar: se limpia el filtro.
  const dropdown = btn.closest('.dropdown');
  dropdown.addEventListener('shown.bs.dropdown', () => buscador.focus());
  dropdown.addEventListener('hidden.bs.dropdown', () => {
    buscador.value = '';
    filtrar();
  });
}