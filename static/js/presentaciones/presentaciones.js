/**
 * PRESENTACIONES.JS — Búsqueda simple sobre la tabla
 */

document.addEventListener('DOMContentLoaded', function () {
  const inputBuscar = document.getElementById('buscarPresentacion');
  if (!inputBuscar) return;

  const filas = document.querySelectorAll('#tablaPresentaciones tbody tr');
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
});
/**
 * PRESENTACIONES.JS — Búsqueda simple sobre la tabla + dropdown de acciones
 */

document.addEventListener('DOMContentLoaded', function () {
  const inputBuscar = document.getElementById('buscarPresentacion');
  if (inputBuscar) {
    const filas = document.querySelectorAll('#tablaPresentaciones tbody tr');
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

  // Cierra cualquier dropdown abierto si se hace clic fuera
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.dd-wrap')) {
      document.querySelectorAll('.dd-menu.open').forEach(menu => menu.classList.remove('open'));
    }
  });
});

function toggleDropdownPres(btn) {
  const wrap = btn.closest('.dd-wrap');
  const menu = wrap.querySelector('.dd-menu');
  const yaAbierto = menu.classList.contains('open');

  // Cierra todos los demás dropdowns abiertos antes de abrir este
  document.querySelectorAll('.dd-menu.open').forEach(m => m.classList.remove('open'));

  if (!yaAbierto) {
    // Posiciona el menú justo debajo del botón (porque .dd-menu usa position: fixed)
    const rect = btn.getBoundingClientRect();
    menu.style.top = rect.bottom + 4 + 'px';
    menu.style.right = (window.innerWidth - rect.right) + 'px';
    menu.classList.add('open');
  }
}