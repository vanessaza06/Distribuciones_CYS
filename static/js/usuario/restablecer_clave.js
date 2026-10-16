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

// ── Toggle ver/ocultar contraseña ──
function toggleEye(inputId, btn) {
  const field = document.getElementById(inputId);
  const icon  = btn.querySelector('i');
  if (!field || !icon) return;
  const isPassword = field.type === 'password';
  field.type = isPassword ? 'text' : 'password';
  icon.classList.toggle('bi-eye',       !isPassword);
  icon.classList.toggle('bi-eye-slash',  isPassword);
}

document.getElementById('btnToggleNueva')?.addEventListener('click', function () {
  toggleEye('nuevaClave', this);
});
document.getElementById('btnToggleConfirmar')?.addEventListener('click', function () {
  toggleEye('confirmarClave', this);
});

// ── Validación de formulario ──
const form = document.getElementById('formReset');
if (form) {
  form.addEventListener('submit', function(e) {
    const clave        = document.getElementById('nuevaClave').value;
    const confirmar    = document.getElementById('confirmarClave').value;
    const errClave     = document.getElementById('errClave');
    const errConfirmar = document.getElementById('errConfirmar');
    let ok = true;
    errClave.style.display = 'none';
    errConfirmar.style.display = 'none';

    if (clave.length < 6) {
      errClave.textContent = 'Mínimo 6 caracteres.';
      errClave.style.display = 'block'; ok = false;
    } else if ((clave.match(/\d/g) || []).length < 2) {
      errClave.textContent = 'Debe contener al menos 2 números.';
      errClave.style.display = 'block'; ok = false;
    } else if (!/[A-Z]/.test(clave)) {
      errClave.textContent = 'Debe contener al menos 1 mayúscula.';
      errClave.style.display = 'block'; ok = false;
    }
    if (clave !== confirmar) {
      errConfirmar.textContent = 'Las contraseñas no coinciden.';
      errConfirmar.style.display = 'block'; ok = false;
    }
    if (!ok) e.preventDefault();
  });
}