/**
 * PRODUCTOS.JS — Gestión de Productos
 * DataTable, filtrado por categoría, creación
 */

let ultimaCatPk = null;
let dtInstance = null;
let GESTION_URL, CREAR_URL, CSRF_TOKEN, NEXT_PATH, todoProductos;

document.addEventListener('DOMContentLoaded', function () {
  const configEl = document.getElementById('productos-config');
  if (!configEl) return;

  GESTION_URL = configEl.getAttribute('data-gestion-url') || '';
  CREAR_URL = configEl.getAttribute('data-crear-url') || '';
  CSRF_TOKEN = configEl.getAttribute('data-csrf-token') || '';
  NEXT_PATH = configEl.getAttribute('data-next-path') || '';

  try {
    todoProductos = JSON.parse(configEl.getAttribute('data-productos') || '[]');
  } catch (e) {
    console.error('Error parsing productos data:', e);
    todoProductos = [];
  }

  dtInstance = $('#tablaProductosCat').DataTable({
    paging: false,
    searching: false,
    info: false,
    ordering: true,
    responsive: true,
    language: {
      zeroRecords: "Sin resultados.",
      emptyTable: "No hay productos en esta categoría."
    }
  });

  // Protegido: si inicializarGraficos() no existe todavía en ningún archivo
  // cargado, esto ya NO detiene la ejecución del resto del script.
  if (typeof inicializarGraficos === 'function') {
    inicializarGraficos();
  } else {
    console.warn('inicializarGraficos() no está definida — se omite (revisar si falta cargar su <script>).');
  }
});

// ═══════ INICIALIZACIÓN INDEPENDIENTE DEL DROPDOWN DE CATEGORÍA ═══════
// En su propio listener para que NUNCA dependa de si otras funciones
// (como inicializarGraficos) existen o fallan.
document.addEventListener('DOMContentLoaded', function () {
  inicializarDropdownCategorias();
});

function filasHtmlDe(filtrados) {
  return filtrados.map((p, i) => {
    const pres = p.presentaciones.length
      ? p.presentaciones.map(pr =>
          `<span class="badge prod-pres-badge me-1">
            ${pr.nombre} · ${pr.cantidad} uds · $${parseInt(pr.precio_venta || 0).toLocaleString('es-CO')}
          </span>`).join('')
      : `<span class="prod-label prod-label-sm">Sin definir</span>`;

    return `<tr>
      <td class="px-4 prod-label text-center">${i + 1}</td>
      <td class="fw-semibold prod-cell-nombre">${p.nombre}</td>
      <td class="prod-cell-codigo text-center">${p.codigo || '—'}</td>
      <td>${pres}</td>
    </tr>`;
  }).join('');
}

function filtrarCategoria(btn) {
  const pk     = btn.dataset.catPk;
  const nombre = btn.dataset.catNombre;
  const empty  = document.getElementById('cat-empty-state');
  const tabla  = document.getElementById('cat-tabla-wrap');

  if (ultimaCatPk === pk) {
    ultimaCatPk = null;
    btn.classList.remove('active');
    document.getElementById('cat-titulo').textContent = 'Productos por categoría';
    empty.classList.add('cat-panel-visible');
    empty.classList.remove('cat-panel-oculto');
    tabla.classList.add('cat-panel-oculto');
    tabla.classList.remove('cat-panel-visible');
    return;
  }

  ultimaCatPk = pk;
  document.querySelectorAll('.prod-cat-chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const filtrados = pk === 'todos'
    ? todoProductos
    : todoProductos.filter(p => String(p.categoria_pk) === String(pk) || String(p.categoria_subcategoria_pk) === String(pk));

  document.getElementById('cat-titulo').textContent =
    nombre + ' — ' + filtrados.length + ' producto' + (filtrados.length !== 1 ? 's' : '');

  empty.classList.add('cat-panel-oculto');
  empty.classList.remove('cat-panel-visible');
  tabla.classList.add('cat-panel-visible');
  tabla.classList.remove('cat-panel-oculto');

  dtInstance.clear();
  if (filtrados.length) {
    dtInstance.rows.add($(filasHtmlDe(filtrados)));
  }
  dtInstance.draw();
}

// Modal de productos por categoría
document.addEventListener('DOMContentLoaded', function() {
  const modalEl = document.getElementById('modalProductosCategoria');
  if (modalEl) {
    modalEl.addEventListener('show.bs.modal', function(e) {
      const btn = e.relatedTarget;
      if (!btn) return;
      const pk     = btn.dataset.catPk;
      const nombre = btn.dataset.catNombre;
      document.getElementById('titulo-categoria').textContent = nombre;

      const filtrados = todoProductos.filter(p => String(p.categoria_pk) === String(pk));
      const tbody     = document.getElementById('cuerpo-categoria');

      if (!filtrados.length) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">
          <i class="bi bi-box-seam d-block mb-2 fs-3"></i>No hay productos en esta categoría.</td></tr>`;
        return;
      }

      tbody.innerHTML = filtrados.map((p, i) => {
        const pres = p.presentaciones.length
          ? p.presentaciones.map(pr =>
              `<span class="badge prod-badge-pres me-1">
                ${pr.nombre} (${pr.cantidad} uds) — Stock: ${pr.stock_actual} — $${parseInt(pr.precio_venta||0).toLocaleString('es-CO')}
              </span>`).join('')
          : `<span class="text-muted">Sin definir</span>`;

        return `<tr>
          <td class="text-center">${i + 1}</td>
          <td class="fw-semibold">${p.nombre}</td>
          <td class="text-center">${p.codigo || '—'}</td>
          <td>${pres}</td>
        </tr>`;
      }).join('');
    });
  }
});

// ═══════ DROPDOWN CATEGORÍA (modal Nuevo Producto) ═══════
function inicializarDropdownCategorias() {
  document.querySelectorAll('.crear-cat-item').forEach(item => {
    item.addEventListener('click', function (e) {
      e.preventDefault();
      const valor  = this.dataset.value;
      const texto  = this.textContent.trim();

      document.getElementById('crear-categoria').value = valor;
      document.getElementById('crear-categoria-label').textContent = texto;
    });
  });
}

// ═══════ ENVÍO DEL FORMULARIO NUEVO PRODUCTO ═══════
function enviarCrearProducto() {
  const nombre           = document.getElementById('crear-nombre').value.trim();
  const categoria        = document.getElementById('crear-categoria').value;
  const descripcion      = document.getElementById('crear-descripcion').value.trim();
  const fechaVencimiento = document.getElementById('crear-fecha-venc').value;
  const feedback         = document.getElementById('crear-feedback');

  feedback.classList.add('d-none');
  feedback.innerHTML = '';

  if (!nombre || !categoria || !fechaVencimiento) {
    feedback.classList.remove('d-none');
    feedback.innerHTML = `<div class="alert alert-danger py-2 mb-0">
      Completa nombre, categoría y fecha de vencimiento antes de guardar.</div>`;
    return;
  }

  const formData = new FormData();
  formData.append('nombre', nombre);
  formData.append('categoria', categoria);
  formData.append('descripcion', descripcion);
  formData.append('fecha_vencimiento', fechaVencimiento);
  formData.append('next', NEXT_PATH);

  fetch(CREAR_URL, {
    method: 'POST',
    headers: {
      'X-CSRFToken': CSRF_TOKEN,
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        location.reload();
      } else {
        feedback.classList.remove('d-none');
        const mensajes = Object.values(data.errores || {}).flat().join(' ');
        feedback.innerHTML = `<div class="alert alert-danger py-2 mb-0">${mensajes || 'Error al guardar.'}</div>`;
      }
    })
    .catch(err => {
      console.error('Error creando producto:', err);
      feedback.classList.remove('d-none');
      feedback.innerHTML = `<div class="alert alert-danger py-2 mb-0">Error de conexión.</div>`;
    });
}
window.addEventListener('load', function () {
  const btnNuevo = document.querySelector('.prod-btn-nuevo');
  if (btnNuevo) {
    new bootstrap.Tooltip(btnNuevo, {
      title: 'Crear producto',
      placement: 'top',
      customClass: 'cys-tooltip'
    });
  }
});