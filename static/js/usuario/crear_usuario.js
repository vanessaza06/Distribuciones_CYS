// ── TEMA: aplica el color guardado en Configuración (esta página no carga base.js) ──
(function () {
  var T = {
    oscuro: {'--fondo':'#011936','--fondo-card':'#0a2240','--fondo-card2':'#0d2a4d','--texto':'#e2e8f0','--texto-muted':'#7a9bbf','--azul-claro':'#4DA8DA','--azul-oscuro':'#05244a','--azul-medio':'#0F3B6C','--verde':'#2ecc71','--rojo':'#c0392b'},
    claro: {'--fondo':'#f0f4f8','--fondo-card':'#ffffff','--fondo-card2':'#e8eef5','--texto':'#1a2a3a','--texto-muted':'#4a6a8a','--azul-claro':'#B22A1A','--azul-oscuro':'#ddeaf5','--azul-medio':'#cfe0f0','--verde':'#1a8a4a','--rojo':'#B22A1A'},
    'alto-contraste': {'--fondo':'#000000','--fondo-card':'#0a0a0a','--fondo-card2':'#111111','--texto':'#ffffff','--texto-muted':'#cccccc','--azul-claro':'#00cfff','--azul-oscuro':'#001a22','--azul-medio':'#00262f','--verde':'#00ff88','--rojo':'#ff4444'},
    basecys: {'--fondo':'#241008','--fondo-card':'#34160D','--fondo-card2':'#421B10','--texto':'#F2DFB8','--texto-muted':'#C9A876','--azul-claro':'#D9A441','--azul-oscuro':'#1A0A06','--azul-medio':'#4A2216','--verde':'#8AB86F','--rojo':'#B0392E'},
    sepia: {'--fondo':'#1a0f05','--fondo-card':'#2c1f0e','--fondo-card2':'#3d2b14','--texto':'#f5e6c8','--texto-muted':'#a08060','--azul-claro':'#d4a060','--azul-oscuro':'#150c04','--azul-medio':'#4a3418','--verde':'#7ab870','--rojo':'#c05030'}
  };
  try {
    var cfg  = JSON.parse(localStorage.getItem('cys_config') || '{}');
    var vars = T[cfg.tema];
    if (!vars) return;
    var r = document.documentElement;
    for (var k in vars) r.style.setProperty(k, vars[k]);
  } catch (e) {}
})();

// DOMContentLoaded: inmediato, sin overhead de Turbo
document.addEventListener('DOMContentLoaded', () => {

  // Aplica clases e placeholders a los campos del formulario Django
  document.querySelectorAll('#formNuevoUsuario input, #formNuevoUsuario select, #formNuevoUsuario textarea').forEach(el => {
    el.classList.add('cys-input');
    const n = el.name;
    const placeholders = {
      email:          'usuario@correo.com',
      telefono:       '300 000 0000',
      nombre:         'Nombres completos',
      apellidos:      'Apellidos completos',
      identificacion: 'Número de documento'
    };
    if (placeholders[n]) el.setAttribute('placeholder', placeholders[n]);
    if (el.id === 'id_clave') el.setAttribute('placeholder', '••••••••');
  });

  // ── Copiar usuario (N.º de documento) en pantalla de éxito ──
  const btnCopiarUsuario = document.getElementById('btnCopiarUsuario');
  const valorUsuario     = document.getElementById('valorUsuario');
  if (btnCopiarUsuario && valorUsuario) {
    btnCopiarUsuario.addEventListener('click', () => {
      const texto = valorUsuario.textContent.trim();
      navigator.clipboard.writeText(texto).then(() => {
        const icono = btnCopiarUsuario.querySelector('i');
        icono.classList.remove('bi-clipboard');
        icono.classList.add('bi-clipboard-check');
        btnCopiarUsuario.classList.add('cys-copy-btn-ok');
        setTimeout(() => {
          icono.classList.remove('bi-clipboard-check');
          icono.classList.add('bi-clipboard');
          btnCopiarUsuario.classList.remove('cys-copy-btn-ok');
        }, 1500);
      });
    });
  }

  // ── Modales ──
  const modalConfClaveEl = document.getElementById('modalConfClave');
  const modalTCEl        = document.getElementById('modalTC');
  if (!modalConfClaveEl || !modalTCEl) return;

  const modalConfClave = new bootstrap.Modal(modalConfClaveEl);
  const modalTC        = new bootstrap.Modal(modalTCEl);

  // Limpia el modal de confirmación al cerrarse
  modalConfClaveEl.addEventListener('hidden.bs.modal', () => {
    const inputConf = document.getElementById('confirmar_clave');
    if (inputConf) {
      inputConf.value = '';
      inputConf.classList.remove('cys-input-invalid');
    }
    const errDiv = document.getElementById('err-conf-clave');
    if (errDiv) errDiv.style.display = 'none';
  });

  // ── Botón Continuar: valida campos y abre modal ──
  document.getElementById('btnContinuar')?.addEventListener('click', () => {
    const campos = ['tipo_id','identificacion','nombre','apellidos','email','telefono','clave'];
    let valido = true;

    campos.forEach(nombre => {
      const el = document.querySelector(`[name="${nombre}"]`) || document.getElementById(`id_${nombre}`);
      if (el) {
        el.classList.remove('cys-input-invalid');
        const v = el.value?.trim() || '';

        if (!v) {
          // Permitir vacío temporalmente si es email o telefono y no son requeridos,
          // pero en tu formulario original todos parecen obligatorios visualmente,
          // excepto email y telefono que en Django dicen required=False,
          // pero mantendremos la validación estricta general.
          if (nombre !== 'email' && nombre !== 'telefono') {
            el.classList.add('cys-input-invalid');
            valido = false;
          }
        } else if (nombre === 'email') {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (!emailRegex.test(v)) {
            el.classList.add('cys-input-invalid');
            valido = false;
          }
        } else if (nombre === 'nombre' || nombre === 'apellidos') {
          if (/\d/.test(v)) { // No puede contener números
            el.classList.add('cys-input-invalid');
            valido = false;
          }
        } else if (nombre === 'telefono') {
          if (!/^\d+$/.test(v)) { // Solo números
            el.classList.add('cys-input-invalid');
            valido = false;
          }
        } else if (nombre === 'clave') {
          const numCount = (v.match(/\d/g) || []).length;
          if (v.length < 6 || numCount < 2 || !/[A-Z]/.test(v)) {
            el.classList.add('cys-input-invalid');
            valido = false;
          }
        }
      }
    });

    if (valido) {
      modalConfClave.show();
    } else {
      const card = document.querySelector('.cys-card');
      card?.classList.add('cys-shake');
      setTimeout(() => card?.classList.remove('cys-shake'), 500);
    }
  });

  // ── Botón Confirmar Clave ──
  document.getElementById('btnConfirmarClave')?.addEventListener('click', () => {
    const claveOriginal     = document.getElementById('id_clave')?.value;
    const claveConfirmacion = document.getElementById('confirmar_clave')?.value;
    const errorDiv          = document.getElementById('err-conf-clave');
    const errorTexto        = document.getElementById('err-conf-texto');
    const inputConf         = document.getElementById('confirmar_clave');

    if (claveOriginal !== claveConfirmacion) {
      inputConf?.classList.add('cys-input-invalid');
      if (errorTexto) errorTexto.innerText = 'Las contraseñas no coinciden.';
      if (errorDiv)   errorDiv.style.display = 'flex';
    } else {
      modalConfClave.hide();
      // Pequeño delay para que Bootstrap termine la animación de cierre
      modalConfClaveEl.addEventListener('hidden.bs.modal', () => modalTC.show(), { once: true });
    }
  });

  // ── Checkbox T&C habilita botón ──
  const checkTC     = document.getElementById('checkTC');
  const btnAceptarTC = document.getElementById('btnAceptarTC');
  checkTC?.addEventListener('change', function () {
    btnAceptarTC.disabled = !this.checked;
  });

  // ── Volver al paso 1 desde T&C ──
  document.getElementById('btnVolverConf')?.addEventListener('click', () => {
    modalTC.hide();
    modalTCEl.addEventListener('hidden.bs.modal', () => modalConfClave.show(), { once: true });
  });

  // ── Crear Cuenta ──
  btnAceptarTC?.addEventListener('click', () => {
    document.getElementById('formNuevoUsuario')?.submit();
  });

  // ── Toggle visibilidad contraseñas ──
  const handlerToggle = (inputId, btn) => {
    const field = document.getElementById(inputId);
    const icon  = btn.querySelector('i');
    if (!field || !icon) return;
    const isPassword = field.type === 'password';
    field.type = isPassword ? 'text' : 'password';
    icon.classList.toggle('bi-eye',       !isPassword);
    icon.classList.toggle('bi-eye-slash',  isPassword);
  };

  document.getElementById('btnToggleClave')?.addEventListener('click', function () { handlerToggle('id_clave',       this); });
  document.getElementById('btnToggleConf')?.addEventListener('click',  function () { handlerToggle('confirmar_clave', this); });

  // ── Validación de contraseña en tiempo real ──
  const claveInput = document.getElementById('id_clave');
  if (claveInput) {
    claveInput.addEventListener('input', function() {
      const val = this.value;

      const ruleLength = document.getElementById('rule-length');
      if (val.length >= 6) {
        ruleLength.classList.add('valid'); ruleLength.querySelector('i').className = 'bi bi-check-circle-fill';
      } else {
        ruleLength.classList.remove('valid'); ruleLength.querySelector('i').className = 'bi bi-x-circle-fill';
      }

      const ruleNumbers = document.getElementById('rule-numbers');
      const numCount = (val.match(/\d/g) || []).length;
      if (numCount >= 2) {
        ruleNumbers.classList.add('valid'); ruleNumbers.querySelector('i').className = 'bi bi-check-circle-fill';
      } else {
        ruleNumbers.classList.remove('valid'); ruleNumbers.querySelector('i').className = 'bi bi-x-circle-fill';
      }

      const ruleUppercase = document.getElementById('rule-uppercase');
      if (/[A-Z]/.test(val)) {
        ruleUppercase.classList.add('valid'); ruleUppercase.querySelector('i').className = 'bi bi-check-circle-fill';
      } else {
        ruleUppercase.classList.remove('valid'); ruleUppercase.querySelector('i').className = 'bi bi-x-circle-fill';
      }
    });
  }
});