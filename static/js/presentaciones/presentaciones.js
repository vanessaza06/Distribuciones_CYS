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