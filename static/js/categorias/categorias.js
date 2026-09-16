document.addEventListener('DOMContentLoaded', function () {
  const modalEl = document.getElementById('modalConfirmarAccion');
  if (!modalEl) {
    console.error('No se encontró #modalConfirmarAccion en el DOM');
    return;
  }

  if (typeof bootstrap === 'undefined') {
    console.error('Bootstrap JS no está cargado. Revisa que bootstrap.bundle.min.js esté incluido antes de categorias.js');
    return;
  }

  const modal = new bootstrap.Modal(modalEl);
  const mensaje = document.getElementById('confirmar-mensaje');
  const btnAceptar = document.getElementById('confirmar-btn-aceptar');
  let formPendiente = null;

  const botones = document.querySelectorAll('.cat-btn-confirmar-toggle');
  console.log('Botones de confirmar toggle encontrados:', botones.length);

  botones.forEach(function (btn) {
    btn.addEventListener('click', function () {
      formPendiente = btn.closest('form');
      console.log('Form pendiente:', formPendiente, 'action:', formPendiente ? formPendiente.action : null);

      const nombre = formPendiente.dataset.nombre || 'esta categoría';
      mensaje.textContent =
        'Las categorías no se eliminan, solo se desactivan para conservar el histórico. ' +
        '¿Deseas desactivar "' + nombre + '"?';
      modal.show();
    });
  });

  btnAceptar.addEventListener('click', function () {
    console.log('Click en aceptar, enviando form:', formPendiente);
    if (formPendiente) {
      formPendiente.submit();
    } else {
      console.warn('No hay formulario pendiente para enviar');
    }
    modal.hide();
  });
});