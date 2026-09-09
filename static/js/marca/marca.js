document.addEventListener('DOMContentLoaded', function () {

    // ── Confirmación de eliminar/desactivar marca ──
    const modalConfirmar = document.getElementById('modalConfirmarAccion');
    const modalConfirmarInstance = new bootstrap.Modal(modalConfirmar);
    const mensajeConfirmar = document.getElementById('confirmar-mensaje');
    const btnAceptar = document.getElementById('confirmar-btn-aceptar');

    let formAEnviar = null;

    document.querySelectorAll('.marca-btn-confirmar-borrado').forEach(function (boton) {
        boton.addEventListener('click', function () {
            formAEnviar = boton.closest('form.marca-form-eliminar');
            const nombreMarca = formAEnviar.dataset.nombre;

            mensajeConfirmar.textContent =
                `¿Seguro que quieres eliminar o desactivar la marca "${nombreMarca}"? ` +
                `Si tiene productos asociados se desactivará en su lugar.`;

            modalConfirmarInstance.show();
        });
    });

    btnAceptar.addEventListener('click', function () {
        if (formAEnviar) {
            formAEnviar.submit();
        }
        modalConfirmarInstance.hide();
    });

});