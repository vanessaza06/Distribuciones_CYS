(function () {
  const SIMBOLOS = " .-*/&'()";
  const SIMBOLOS_LOTE = "-_./";
  const ES_ALNUM = /^[\p{L}\p{N}]$/u;
  const SELECTOR = 'input[data-validar-nombre], input[data-validar-lote]';

  const normalizar = v => (v || '').normalize('NFC').replace(/\s+/g, ' ').trim();

  // ── Nombres (producto, presentación, etc.) ──
  window.validarNombre = function (valor, opciones) {
    const o = Object.assign({ etiqueta: 'El nombre', min: 3, max: 150 }, opciones);
    const nombre = normalizar(valor);

    if (!nombre) return o.etiqueta + ' es obligatorio; no puede estar vacío ni tener solo espacios.';
    if (nombre.length < o.min) return o.etiqueta + ' debe tener al menos ' + o.min + ' caracteres.';
    if (nombre.length > o.max) return o.etiqueta + ' no puede superar ' + o.max + ' caracteres.';

    const chars = Array.from(nombre);
    if (!ES_ALNUM.test(chars[0])) return o.etiqueta + ' debe empezar con una letra o un número.';

    const invalidos = [...new Set(chars.filter(c => !ES_ALNUM.test(c) && !SIMBOLOS.includes(c)))];
    if (invalidos.length) return o.etiqueta + ' tiene caracteres no permitidos: ' + invalidos.join(' ');

    const letras = chars.filter(c => /\p{L}/u.test(c)).length;
    if (letras < 2) return o.etiqueta + ' debe tener al menos 2 letras.';
    if (/[.\-*\/&'()]{2,}/.test(nombre)) return o.etiqueta + ' no puede tener dos símbolos seguidos (por ejemplo "..").';

    return '';
  };

  // Alias para que productos.js siga funcionando sin cambios
  window.validarNombreProducto = function (valor) {
    return window.validarNombre(valor);
  };

  // ── Número de lote ──
  window.validarCodigoLote = function (valor, opciones) {
    const o = Object.assign({ etiqueta: 'El número de lote', min: 3, max: 100 }, opciones);
    const codigo = (valor || '').normalize('NFC').trim();

    if (!codigo) return o.etiqueta + ' es obligatorio; no puede estar vacío ni tener solo espacios.';
    if (/\s/.test(codigo)) return o.etiqueta + ' no puede contener espacios.';
    if (codigo.length < o.min) return o.etiqueta + ' debe tener al menos ' + o.min + ' caracteres.';
    if (codigo.length > o.max) return o.etiqueta + ' no puede superar ' + o.max + ' caracteres.';

    const chars = Array.from(codigo);
    if (!ES_ALNUM.test(chars[0])) return o.etiqueta + ' debe empezar con una letra o un número.';
    if (!ES_ALNUM.test(chars[chars.length - 1])) return o.etiqueta + ' debe terminar con una letra o un número.';

    const invalidos = [...new Set(chars.filter(c => !ES_ALNUM.test(c) && !SIMBOLOS_LOTE.includes(c)))];
    if (invalidos.length) return o.etiqueta + ' tiene caracteres no permitidos: ' + invalidos.join(' ');
    if (/[-_.\/]{2,}/.test(codigo)) return o.etiqueta + ' no puede tener dos símbolos seguidos (por ejemplo "..").';

    return '';
  };

  // ── Mostrar / quitar el error ──
  // Dentro de un modal: alerta roja arriba del formulario.
  // Fuera de un modal: texto rojo justo debajo del campo.
  function mostrarError(input, mensaje) {
    const cuerpo = input.closest('.modal-body');
    if (cuerpo) {
      let aviso = cuerpo.querySelector('.aviso-validacion');
      if (!aviso) {
        aviso = document.createElement('div');
        aviso.className = 'alert alert-danger py-2 mb-3 aviso-validacion';
        aviso.setAttribute('role', 'alert');
        cuerpo.prepend(aviso);
      }
      aviso.textContent = mensaje;
      return;
    }

    quitarAvisos(input.parentElement);
    const aviso = document.createElement('div');
    aviso.className = 'aviso-validacion aviso-validacion--inline';
    aviso.setAttribute('role', 'alert');
    aviso.innerHTML = '<i class="bi bi-exclamation-circle me-1"></i>';
    aviso.appendChild(document.createTextNode(mensaje));
    input.insertAdjacentElement('afterend', aviso);
  }

  function quitarAvisos(contenedor) {
    contenedor.querySelectorAll('.aviso-validacion').forEach(a => a.remove());
  }

  // ── Validación automática al enviar cualquier formulario ──
  document.addEventListener('submit', function (e) {
    const inputs = e.target.querySelectorAll(SELECTOR);
    for (const input of inputs) {
      // En edición, si el valor no cambió, no se valida (no bloquea registros viejos)
      if (input.defaultValue && normalizar(input.value) === normalizar(input.defaultValue)) continue;

      const opciones = {
        etiqueta: input.dataset.etiqueta || undefined,
        min: parseInt(input.dataset.min, 10) || 3,
        max: input.maxLength > 0 ? input.maxLength : undefined
      };
      const mensaje = input.hasAttribute('data-validar-lote')
        ? window.validarCodigoLote(input.value, opciones)
        : window.validarNombre(input.value, opciones);

      if (mensaje) {
        e.preventDefault();
        mostrarError(input, mensaje);
        input.focus();
        return;
      }
    }
  }, true);

  // El aviso desaparece al volver a escribir o al cerrar el modal
  document.addEventListener('input', function (e) {
    if (!e.target.matches(SELECTOR)) return;
    quitarAvisos(e.target.closest('.modal-body') || e.target.parentElement);
  });
  document.addEventListener('hidden.bs.modal', function (e) {
    quitarAvisos(e.target);
  });
})();