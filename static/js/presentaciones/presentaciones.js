/**
 * PRESENTACIONES.JS — Búsqueda, dropdown de acciones y modal de creación
 */

document.addEventListener('DOMContentLoaded', function () {
  if (typeof bootstrap === 'undefined') {
    console.error('[Presentaciones] Bootstrap JS no está cargado: los modales no van a abrir. Revisa base.html.');
  }

  moverModalesAlBody();
  inicializarBusquedaPresentaciones();
  inicializarModalCrearPresentacion();

  document.addEventListener('click', function (e) {
    // Cierra cualquier dropdown abierto si se hace clic fuera
    if (!e.target.closest('.dd-wrap')) {
      cerrarDropdownsPres();
      return;
    }

    // Al elegir un enlace del menú (ej. Editar) se cierra el dropdown
    if (e.target.closest('a.dd-item')) {
      cerrarDropdownsPres();
    }
  });

  // El menú usa position: fixed, así que se cierra al hacer scroll
  window.addEventListener('scroll', cerrarDropdownsPres, true);
});

/**
 * Mueve los modales al <body> para que ningún contenedor con
 * transform / overflow / z-index los deje detrás del backdrop.
 */
function moverModalesAlBody() {
  document.querySelectorAll('.modal').forEach(function (modal) {
    if (modal.parentElement !== document.body) {
      document.body.appendChild(modal);
    }
  });
}

function cerrarDropdownsPres() {
  document.querySelectorAll('.dd-menu.open').forEach(m => m.classList.remove('open'));
}

function inicializarBusquedaPresentaciones() {
  const inputBuscar = document.getElementById('buscarPresentacion');
  if (!inputBuscar) return;

  const filas = document.querySelectorAll('#tablaPresentaciones tbody tr[data-producto]');
  const sinResultados = document.getElementById('sinResultadosPresentaciones');

  inputBuscar.addEventListener('input', function () {
    const q = this.value.trim().toLowerCase();
    let visibles = 0;

    filas.forEach(fila => {
      const producto = (fila.dataset.producto || '').toLowerCase();
      const presentacion = (fila.dataset.presentacion || '').toLowerCase();
      const coincide = producto.includes(q) || presentacion.includes(q);

      fila.classList.toggle('d-none', !coincide);
      if (coincide) visibles++;
    });

    if (sinResultados) {
      sinResultados.classList.toggle('d-none', visibles > 0);
    }
  });
}

/**
 * Arma el action del formulario "Nueva Presentación" según el producto elegido.
 * La URL base viene de {% url 'presentacion_crear' 0 %} (data-url-template).
 */
function inicializarModalCrearPresentacion() {
  const form = document.getElementById('form-crear-presentacion');
  const selectProducto = document.getElementById('crear-pres-producto');
  if (!form || !selectProducto) return;

  const plantilla = form.dataset.urlTemplate || '';

  function actualizarAction() {
    if (!selectProducto.value) {
      form.setAttribute('action', '');
      return;
    }
    // Reemplaza el segmento "/0" (con o sin barra final) por el id del producto
    form.setAttribute(
      'action',
      plantilla.replace(/\/0(?=\/|$)/, '/' + selectProducto.value)
    );
  }

  selectProducto.addEventListener('change', actualizarAction);

  form.addEventListener('submit', function (e) {
    if (!selectProducto.value) {
      e.preventDefault();
      selectProducto.focus();
      return;
    }
    actualizarAction();
  });
}

function toggleDropdownPres(btn) {
  const wrap = btn.closest('.dd-wrap');
  const menu = wrap.querySelector('.dd-menu');
  const yaAbierto = menu.classList.contains('open');

  // Cierra todos los demás dropdowns abiertos antes de abrir este
  cerrarDropdownsPres();

  if (!yaAbierto) {
    // Posiciona el menú justo debajo del botón (porque .dd-menu usa position: fixed)
    const rect = btn.getBoundingClientRect();
    menu.style.top = rect.bottom + 4 + 'px';
    menu.style.right = (window.innerWidth - rect.right) + 'px';
    menu.classList.add('open');
  }
}