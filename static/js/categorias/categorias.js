/* ---------------- Validación: nombre (solo letras) y código (letras + al menos un número) ---------------- */
(function () {
  "use strict";

  var INV_NOMBRE = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g;
  var OK_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$/;
  var INV_CODIGO = /[^A-Za-z0-9]/g;
  var OK_CODIGO = /^[A-Za-z0-9]+$/;
  var TIENE_NUMERO = /[0-9]/;

  function esFormCategoria(input) {
    return !!(input && input.form &&
      input.form.querySelector('[name="nombre"]') &&
      input.form.querySelector('[name="codigo"]'));
  }

  function mostrarError(input, msg) {
    var cont = input.parentElement;
    var err = cont.querySelector(".cat-error");
    if (!err) {
      err = document.createElement("small");
      err.className = "cat-error";
      err.style.cssText = "color:#e5484d;display:block;margin-top:6px;font-size:12px;";
      cont.appendChild(err);
    }
    err.textContent = msg;
    err.style.display = msg ? "block" : "none";
    input.style.setProperty("border-color", msg ? "#e5484d" : "", msg ? "important" : "");
  }

  function validarNombre(input) {
    var v = input.value.replace(/\s+/g, " ").trim();
    if (!v) { mostrarError(input, "El nombre es obligatorio."); return false; }
    if (!OK_NOMBRE.test(v)) { mostrarError(input, "El nombre solo puede tener letras y espacios. Sin números ni símbolos."); return false; }
    mostrarError(input, "");
    input.value = v;
    return true;
  }

  function validarCodigo(input) {
    var v = input.value.trim().toUpperCase();
    if (!v) { mostrarError(input, "El código es obligatorio."); return false; }
    if (!OK_CODIGO.test(v)) { mostrarError(input, "El código solo puede tener letras y números, sin espacios ni símbolos."); return false; }
    if (!TIENE_NUMERO.test(v)) { mostrarError(input, "El código debe llevar al menos un número."); return false; }
    mostrarError(input, "");
    input.value = v;
    return true;
  }

  document.addEventListener("input", function (e) {
    var t = e.target;
    if (!t || !esFormCategoria(t)) return;

    if (t.name === "nombre") {
      var limpio = t.value.replace(INV_NOMBRE, "");
      if (limpio !== t.value) {
        t.value = limpio;
        mostrarError(t, "Solo se permiten letras y espacios.");
      } else {
        mostrarError(t, "");
      }
    }

    if (t.name === "codigo") {
      var cod = t.value.replace(INV_CODIGO, "").toUpperCase();
      if (cod !== t.value.toUpperCase()) {
        mostrarError(t, "El código solo puede tener letras y números.");
      } else {
        mostrarError(t, "");
      }
      t.value = cod;
    }
  });

  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (!f || !f.querySelector) return;
    var nombre = f.querySelector('[name="nombre"]');
    var codigo = f.querySelector('[name="codigo"]');
    if (!nombre || !codigo) return;

    var okN = validarNombre(nombre);
    var okC = validarCodigo(codigo);
    if (!okN || !okC) {
      e.preventDefault();
      e.stopImmediatePropagation();
      (okN ? codigo : nombre).focus();
    }
  }, true);
})();

/* ---------------- Modal de confirmación (desactivar) ---------------- */
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

  botones.forEach(function (btn) {
    btn.addEventListener('click', function () {
      formPendiente = btn.closest('form');

      const nombre = formPendiente.dataset.nombre || 'esta categoría';
      mensaje.textContent =
        'Las categorías no se eliminan, solo se desactivan para conservar el histórico. ' +
        '¿Deseas desactivar "' + nombre + '"?';
      modal.show();
    });
  });

  btnAceptar.addEventListener('click', function () {
    if (formPendiente) {
      formPendiente.submit();
    }
    modal.hide();
  });
});