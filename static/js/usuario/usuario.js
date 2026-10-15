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

// ── Sacudir tarjeta si hay errores ──
function sacudir() {
  const t = document.getElementById('tarjeta');
  if (t) { t.classList.remove('shake'); void t.offsetWidth; t.classList.add('shake'); }
}

// ── Overlay Acceso Denegado ──
const overlayDenegado = document.getElementById('overlayDenegado');
if (overlayDenegado) {
  sacudir();
  const btnCerrar = document.getElementById('btnCerrarDenegado');
  if (btnCerrar) {
    btnCerrar.addEventListener('click', () => {
      overlayDenegado.style.opacity = '0';
      setTimeout(() => overlayDenegado.remove(), 200);
    });
  }
}

// ── Overlay Acceso Concedido (redirige automáticamente a inicio) ──
const overlayConcedido = document.getElementById('overlayConcedido');
if (overlayConcedido) {
  const destino = overlayConcedido.dataset.redirect || '/';
  setTimeout(() => {
    window.location.href = destino;
  }, 1600);
}

// ── Toggle password login ──
const btnToggleLogin = document.getElementById('btnToggleLogin');
if (btnToggleLogin) {
  btnToggleLogin.addEventListener('click', function () {
    const field = document.getElementById('loginPass');
    const icon  = this.querySelector('i');
    if (field && icon) {
      const isPass = field.type === 'password';
      field.type = isPass ? 'text' : 'password';
      icon.classList.toggle('bi-eye',      !isPass);
      icon.classList.toggle('bi-eye-slash', isPass);
    }
  });
}

// ── Hint dinámico campo usuario ──
const loginUser = document.getElementById('loginUser');
if (loginUser) {
  loginUser.addEventListener('input', function () {
    const val  = this.value.trim();
    const hint = document.getElementById('loginHint');
    if (!hint) return;
    if (!val) { hint.style.display = 'none'; hint.innerHTML = ''; return; }
    const soloNumeros = /^\d+$/.test(val);
    if (soloNumeros) {
      hint.className = 'cys-login-hint cys-login-hint--doc';
      hint.innerHTML = `<i class="bi bi-card-text"></i>
        <span>Estás ingresando tu <strong>número de documento</strong>.</span>`;
    } else {
      hint.className = 'cys-login-hint cys-login-hint--user';
      hint.innerHTML = `<i class="bi bi-person-badge"></i>
        <span>Estás ingresando tu <strong>nombre de usuario personalizado</strong>.</span>`;
    }
    hint.style.display = 'flex';
  });
}

// ── Solo números en OTP ──
const inputOtp = document.getElementById('inputOtp');
if (inputOtp) {
  inputOtp.addEventListener('input', function () {
    this.value = this.value.replace(/\D/g, '').slice(0, 6);
  });
}

// ── Cuenta regresiva 10 min (persistente con sessionStorage) ──
const spanTimer  = document.getElementById('cuentaRegresiva');
const badgeTimer = document.getElementById('badgeTimer');
const btnVerif   = document.getElementById('btnVerificar');

if (spanTimer) {
  const STORAGE_KEY = 'cys_otp_expira';
  const DURACION    = 10 * 60 * 1000; // 10 min en ms

  // Si no hay timestamp guardado o ya expiró más de 10 min, crear uno nuevo
  let expiraEn = parseInt(sessionStorage.getItem(STORAGE_KEY) || '0');
  if (!expiraEn || Date.now() > expiraEn + 1000) {
    expiraEn = Date.now() + DURACION;
    sessionStorage.setItem(STORAGE_KEY, expiraEn);
  }

  function mostrarExpirado() {
    spanTimer.textContent   = '00:00';
    spanTimer.style.color   = 'var(--rojo)';
    if (badgeTimer) {
      badgeTimer.innerHTML  = '<i class="bi bi-x-circle me-1"></i> Código expirado';
      badgeTimer.style.color       = 'var(--rojo)';
      badgeTimer.style.background  = 'color-mix(in srgb, var(--rojo) 10%, transparent)';
      badgeTimer.style.borderColor = 'color-mix(in srgb, var(--rojo) 35%, transparent)';
    }
    if (btnVerif) {
      btnVerif.disabled    = true;
      btnVerif.style.opacity    = '.45';
      btnVerif.style.cursor     = 'not-allowed';
      btnVerif.innerHTML   = '<i class="bi bi-x-circle me-1"></i> Código expirado';
    }
    // Mostrar enlace de reenvío
    const reenviar = document.getElementById('enlaceReenviar');
    if (reenviar) reenviar.style.display = 'inline-flex';
    sessionStorage.removeItem(STORAGE_KEY);
  }

  function actualizarTimer() {
    const restante = expiraEn - Date.now();
    if (restante <= 0) {
      clearInterval(intervalo);
      mostrarExpirado();
      return;
    }
    const m = String(Math.floor(restante / 60000)).padStart(2, '0');
    const s = String(Math.floor((restante % 60000) / 1000)).padStart(2, '0');
    spanTimer.textContent = `${m}:${s}`;
    if (restante <= 60000) spanTimer.style.color = 'var(--rojo)';
  }

  actualizarTimer();
  const intervalo = setInterval(actualizarTimer, 1000);
}

// ── Limpiar timer al reenviar ──
const enlaceReenviar = document.getElementById('enlaceReenviar');
if (enlaceReenviar) {
  enlaceReenviar.addEventListener('click', () => {
    sessionStorage.removeItem('cys_otp_expira');
  });
}