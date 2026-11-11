(function () {
'use strict';

// Si la página no es la de Configuración (o htmx aún no puso el contenido), no hace nada.
const cfgData = document.getElementById('cfg-data');
if (!cfgData) return;

const $ = (id) => document.getElementById(id);

// ══════════════════════════════════════════
// URLs de Django (pasadas desde el template vía data-attributes)
// ══════════════════════════════════════════
const URL_ACTIVIDAD            = cfgData.dataset.urlActividad;
const URL_GUARDAR_EMPRESA      = cfgData.dataset.urlGuardarEmpresa;
const URL_VERIFICAR_EMPRESA    = cfgData.dataset.urlVerificarEmpresa;
const URL_BLOQUEAR_EMPRESA     = cfgData.dataset.urlBloquearEmpresa;
const URL_GUARDAR_IMPUESTOS    = cfgData.dataset.urlGuardarImpuestos;
const URL_GUARDAR_TEMA_SISTEMA = cfgData.dataset.urlGuardarTemaSistema;
const URL_A11Y_EXTRA           = cfgData.dataset.urlA11yExtra;

// Django puede entregar "True"/"true"/"1": se acepta cualquier mayúscula.
const ES_ADMIN_EMPRESA = ['true', '1'].includes(String(cfgData.dataset.esAdmin || '').trim().toLowerCase());

const NOMBRES_TEMA = {
  'oscuro': 'Oscuro',
  'claro': 'Claro',
  'alto-contraste': 'Alto contraste',
  'basecys': 'Base CyS',
  'sepia': 'Sepia',
};

// Escapa texto antes de meterlo con innerHTML
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// El tema del sistema se lee primero de <html data-tema-sistema> (que base.js
// mantiene al día en cada navegación htmx) y luego del data-attribute de esta página.
function leerTemaSistema() {
  const deHtml = document.documentElement.dataset.temaSistema;
  if (deHtml && NOMBRES_TEMA[deHtml]) return deHtml;
  const deCfg = cfgData.dataset.temaSistema;
  if (deCfg && NOMBRES_TEMA[deCfg]) return deCfg;
  return 'oscuro';
}

// Tema predeterminado actual del sistema (viene del servidor)
let TEMA_SISTEMA = leerTemaSistema();

// ══════════════════════════════════════════
// CSRF helper
// ══════════════════════════════════════════
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}
const CSRF_TOKEN = getCookie('csrftoken') ||
  document.querySelector('input[name=csrfmiddlewaretoken]')?.value;

// ══════════════════════════════════════════
// ESTADO VISUAL (tema/pagina de inicio/brillo/fuente/zoom/toggles)
// localStorage.cys_config
//
// IMPORTANTE: el "tema" solo cuenta como propio si lleva la marca
// temaPersonal === true. Si no, el usuario sigue el tema del sistema.
// ══════════════════════════════════════════
const CFG_DEFAULT = {
  tema: TEMA_SISTEMA, paginaInicio: 'tablero', brillo: 100, fuente: 14, zoom: 100,
  sidebarAuto: false, resumenSidebar: true,
  alertaStock: true, widgetRotacion: true, silencioso: false,
};

let temaPersonal = false; // true si el usuario eligió un tema propio

function cargarCfg() {
  let cfg = { ...CFG_DEFAULT };
  try {
    const g = JSON.parse(localStorage.getItem('cys_config') || '{}');
    // Un "tema" viejo sin marca se ignora: ya no cuenta como elección personal
    temaPersonal = g.temaPersonal === true && !!g.tema;
    cfg = { ...cfg, ...g };
  } catch (e) {}
  if (!temaPersonal) cfg.tema = TEMA_SISTEMA;
  return cfg;
}
function guardarCfg(cfg) {
  const copia = { ...cfg };
  if (temaPersonal) {
    copia.temaPersonal = true;   // marca: este tema lo eligió el usuario
  } else {
    delete copia.tema;           // sigue el del sistema: no se persiste
    delete copia.temaPersonal;
  }
  localStorage.setItem('cys_config', JSON.stringify(copia));
}

let cfgActual = cargarCfg();
let perillaBrillo, perillaFuente, perillaZoom;
let logoEmpresaFile = null; // archivo seleccionado, pendiente de subir al guardar
let toastPrefTimeout = null;
let toastTimeout = null;
let temaPendiente = null;   // tema a confirmar como predeterminado del sistema

// ══════════════════════════════════════════
// PERILLAS (DIAL)
// btnResetId (opcional): id del botón "Restablecer" asociado a esta perilla.
// Si se pasa, la perilla se encarga de deshabilitarlo cuando el valor
// ya está en el default (evita clics inútiles).
// ══════════════════════════════════════════
function crearPerilla(container, btnResetId) {
  const min    = parseFloat(container.dataset.min);
  const max    = parseFloat(container.dataset.max);
  const step   = parseFloat(container.dataset.step) || 1;
  const unidad = container.dataset.unit || '';
  const valorDefault = container.dataset.default !== undefined
    ? parseFloat(container.dataset.default)
    : null;

  container.innerHTML = `
    <div class="cfg-knob__dial">
      <svg class="cfg-knob__ring" viewBox="0 0 100 100">
        <path class="cfg-knob__track" pathLength="100" d="M20,80 A38,38 0 1 1 80,80"></path>
        <path class="cfg-knob__progress" pathLength="100" d="M20,80 A38,38 0 1 1 80,80"></path>
      </svg>
      <div class="cfg-knob__handle"><span class="cfg-knob__dot"></span></div>
      <div class="cfg-knob__center">
        <span class="cfg-knob__value">0</span><span class="cfg-knob__unit">${unidad}</span>
      </div>
    </div>
    <div class="cfg-knob__minmax"><span>${min}${unidad}</span><span>${max}${unidad}</span></div>
  `;

  const dial     = container.querySelector('.cfg-knob__dial');
  const progress = container.querySelector('.cfg-knob__progress');
  const handle   = container.querySelector('.cfg-knob__handle');
  const valorEl  = container.querySelector('.cfg-knob__value');
  const btnReset = btnResetId ? document.getElementById(btnResetId) : null;

  const MIN_ANGLE = -135;
  const MAX_ANGLE = 135;

  function pintar(val) {
    val = Math.max(min, Math.min(max, val));
    const pct = (val - min) / (max - min);
    const angulo = MIN_ANGLE + pct * (MAX_ANGLE - MIN_ANGLE);
    progress.style.strokeDasharray = `${pct * 100} 100`;
    handle.style.transform = `rotate(${angulo}deg)`;
    valorEl.textContent = val;
    container.dataset.value = val;
    if (btnReset && valorDefault !== null) {
      btnReset.disabled = (val === valorDefault);
    }
  }

  function anguloDesdeEvento(e) {
    const rect = dial.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const x = e.touches ? e.touches[0].clientX : e.clientX;
    const y = e.touches ? e.touches[0].clientY : e.clientY;
    let deg = Math.atan2(x - cx, -(y - cy)) * 180 / Math.PI;
    if (deg > MAX_ANGLE + 45 || deg < MIN_ANGLE - 45) {
      deg = deg > 0 ? MAX_ANGLE : MIN_ANGLE;
    }
    return Math.max(MIN_ANGLE, Math.min(MAX_ANGLE, deg));
  }

  let arrastrando = false;

  function mover(e) {
    if (!arrastrando) return;
    e.preventDefault();
    const angulo = anguloDesdeEvento(e);
    const pct = (angulo - MIN_ANGLE) / (MAX_ANGLE - MIN_ANGLE);
    let val = min + pct * (max - min);
    val = Math.round(val / step) * step;
    pintar(val);
    container.dispatchEvent(new CustomEvent('cambio', { detail: val }));
  }

  dial.addEventListener('pointerdown', (e) => {
    arrastrando = true;
    dial.setPointerCapture(e.pointerId);
    mover(e);
  });
  dial.addEventListener('pointermove', mover);
  dial.addEventListener('pointerup', () => arrastrando = false);
  dial.addEventListener('pointercancel', () => arrastrando = false);

  // Botón "Restablecer": vuelve al valor por defecto y dispara el mismo
  // evento 'cambio' que el arrastre, para no duplicar la lógica de guardado.
  if (btnReset && valorDefault !== null) {
    btnReset.addEventListener('click', () => {
      pintar(valorDefault);
      container.dispatchEvent(new CustomEvent('cambio', { detail: valorDefault }));
    });
  }

  return { pintar, valorDefault };
}

// ══════════════════════════════════════════
// APLICAR EN VIVO
// El tema se reutiliza desde window.aplicarTemaCYS (base.js).
// ══════════════════════════════════════════
function aplicarBrillo(val) {
  document.documentElement.style.filter = val === 100 ? '' : `brightness(${val}%)`;
}
function aplicarFuente(val) {
  document.documentElement.style.fontSize = val + 'px';
}
function aplicarZoom(val) {
  document.body.style.zoom = val === 100 ? '' : (val / 100);
}
function aplicarTema(tema) {
  const root = document.documentElement;
  const vars = window.CYS_TEMAS && window.CYS_TEMAS[tema];

  if (vars) {
    Object.entries(vars).forEach(([k, v]) => root.style.setProperty(k, v));
    const esClaro = (tema === 'claro');
    root.dataset.cysTema = tema;
    root.setAttribute('data-tema', tema);
    root.classList.toggle('cys-modo-claro', esClaro);
    root.classList.toggle('cys-a11y-modo-claro', esClaro);
  } else if (window.aplicarTemaCYS) {
    window.aplicarTemaCYS(tema);
  } else {
    console.warn('[CYS] No existe window.CYS_TEMAS ni aplicarTemaCYS: base.js no está cargando bien.');
  }
}

// ══════════════════════════════════════════
// ACCESIBILIDAD — espejo del widget flotante (#cys-a11y-widget)
// Los controles de Configuración NO guardan nada por su cuenta:
// accionan el widget de base.html, así base.js sigue siendo la única
// fuente de verdad (localStorage.cys_a11y).
// (El tamaño de texto ya se maneja arriba, en Apariencia.)
// ══════════════════════════════════════════
const A11Y_SWITCHES = [
  ['cfgA11yContraste', 'cysA11yContraste'],
  ['cfgA11yEspaciado', 'cysA11yEspaciado'],
  ['cfgA11yEnlaces',   'cysA11yEnlaces'],
  ['cfgA11yFuente',    'cysA11yFuente'],
];

// Ayudas extra (movimiento y foco). Las guarda cys-a11y-extra.js
const A11Y_EXTRA = [
  ['cfgXAnimaciones', 'animaciones'],
  ['cfgXCursor',      'cursor'],
  ['cfgXFoco',        'foco'],
];

function modoActivoDelWidget() {
  let activo = null;
  document.querySelectorAll('.cys-a11y-colormode__btn').forEach(b => {
    const c = b.classList;
    if (c.contains('active') || c.contains('activo') || c.contains('is-active') ||
        b.getAttribute('aria-pressed') === 'true') {
      activo = b.dataset.modo;
    }
  });
  return activo;
}

// Se redefine en cada carga (htmx reemplaza el DOM de la página)
window.cfgSyncA11y = function () {
  A11Y_SWITCHES.forEach(([mioId, widgetId]) => {
    const mio = $(mioId);
    const widget = $(widgetId);
    if (mio && widget) mio.checked = widget.checked;
  });

  const modo = modoActivoDelWidget();
  document.querySelectorAll('#cfgA11yModos .cfg-chip').forEach(chip => {
    chip.classList.toggle('activo', !!modo && chip.dataset.modo === modo);
  });

  // Ayudas extra
  if (window.CYS_A11Y_EXTRA) {
    const ex = window.CYS_A11Y_EXTRA.get();
    A11Y_EXTRA.forEach(([id, clave]) => {
      const el = $(id);
      if (el) el.checked = !!ex[clave];
    });
  }
};

function sincronizarA11yLuego() {
  setTimeout(() => { if (window.cfgSyncA11y) window.cfgSyncA11y(); }, 80);
}

function clickWidgetA11y(id) {
  const el = $(id);
  if (el) el.click();
  sincronizarA11yLuego();
}

// Carga cys-a11y-extra.js si base.html todavía no lo incluye
function cargarExtraA11y(cb) {
  if (window.CYS_A11Y_EXTRA || !URL_A11Y_EXTRA) { cb(); return; }
  const s = document.createElement('script');
  s.src = URL_A11Y_EXTRA;
  s.onload = cb;
  s.onerror = cb;
  document.head.appendChild(s);
}

function initA11yExtra() {
  A11Y_EXTRA.forEach(([id, clave]) => {
    const el = $(id);
    if (!el) return;
    el.addEventListener('change', () => {
      if (window.CYS_A11Y_EXTRA) {
        window.CYS_A11Y_EXTRA.set(clave, el.checked);
        mostrarToastPreferencia();
      } else {
        el.checked = false;
        mostrarToast('No se pudo cargar cys-a11y-extra.js', 'error');
      }
    });
  });
  if (window.cfgSyncA11y) window.cfgSyncA11y();
}

function initA11y() {
  const widget = $('cys-a11y-widget');
  if (!widget) {
    const aviso = $('cfgA11yAviso');
    if (aviso) aviso.hidden = false;
  } else {
    // Modo de color
    document.querySelectorAll('#cfgA11yModos .cfg-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const destino = document.querySelector(
          '.cys-a11y-colormode__btn[data-modo="' + chip.dataset.modo + '"]'
        );
        if (destino) destino.click();
        sincronizarA11yLuego();
      });
    });

    // Interruptores
    A11Y_SWITCHES.forEach(([mioId, widgetId]) => {
      const mio = $(mioId);
      if (!mio) return;
      mio.addEventListener('change', () => {
        const w = $(widgetId);
        if (w && w.checked !== mio.checked) w.click();
        sincronizarA11yLuego();
      });
    });

    // El widget es persistente (hx-preserve): se enlaza UNA sola vez.
    // El callback usa window.cfgSyncA11y, que apunta siempre al DOM actual.
    if (!widget.dataset.cfgBound) {
      widget.dataset.cfgBound = '1';
      ['click', 'change'].forEach(ev => {
        widget.addEventListener(ev, () => {
          setTimeout(() => { if (window.cfgSyncA11y) window.cfgSyncA11y(); }, 80);
        });
      });
    }
  }

  // Restablecer: widget + ayudas extra
  const reset = $('cfgA11yReset');
  if (reset) {
    reset.addEventListener('click', () => {
      if (widget) clickWidgetA11y('cysA11yReset');
      if (window.CYS_A11Y_EXTRA) window.CYS_A11Y_EXTRA.reset();
      sincronizarA11yLuego();
    });
  }

  cargarExtraA11y(initA11yExtra);
}

// ══════════════════════════════════════════
// MENÚ DE ACCESOS (chips de arriba): scroll suave a cada grupo
// ══════════════════════════════════════════
function initNavegacion() {
  const botones = document.querySelectorAll('.cfg-nav__btn');
  botones.forEach(btn => {
    btn.addEventListener('click', () => {
      const destino = $(btn.dataset.target);
      if (!destino) return;
      destino.scrollIntoView({ behavior: 'smooth', block: 'start' });
      botones.forEach(b => b.classList.toggle('activo', b === btn));
    });
  });
}

// ══════════════════════════════════════════
// ACTIVIDAD DE USUARIOS (modal)
// ══════════════════════════════════════════
async function cargarActividad() {
  const tbody = $('tablaActividad');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="3" class="text-center">Cargando...</td></tr>';

  try {
    const res = await fetch(URL_ACTIVIDAD, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();

    const esAdmin = !!data.es_admin;
    const cols = esAdmin ? 3 : 2;

    $('tituloActividad').textContent = esAdmin ? 'Actividad de todos los usuarios' : 'Mi actividad';
    $('colUsuario').style.display = esAdmin ? '' : 'none';

    const registros = Array.isArray(data.registros) ? data.registros : [];
    if (registros.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${cols}" class="text-center">Sin registros</td></tr>`;
      return;
    }

    tbody.innerHTML = registros.map(r => `
      <tr>
        ${esAdmin ? `<td>${esc(r.usuario)}</td>` : ''}
        <td>${esc(r.fecha_hora)}</td>
        <td>${esc(r.ip)}</td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Error al cargar la actividad</td></tr>';
  }
}

// ══════════════════════════════════════════
// INIT
// ══════════════════════════════════════════
function init() {
  perillaBrillo = crearPerilla($('knobBrillo'), 'btnResetBrillo');
  perillaFuente = crearPerilla($('knobFuente'), 'btnResetFuente');
  perillaZoom   = crearPerilla($('knobZoom'), 'btnResetZoom');

  $('knobBrillo').addEventListener('cambio', e => {
    cfgActual.brillo = e.detail;
    aplicarBrillo(e.detail);
    guardarCfg(cfgActual);
    mostrarToastPreferencia();
  });
  $('knobFuente').addEventListener('cambio', e => {
    cfgActual.fuente = e.detail;
    aplicarFuente(e.detail);
    guardarCfg(cfgActual);
    mostrarToastPreferencia();
  });
  $('knobZoom').addEventListener('cambio', e => {
    cfgActual.zoom = e.detail;
    aplicarZoom(e.detail);
    guardarCfg(cfgActual);
    mostrarToastPreferencia();
  });

  document.querySelectorAll('#opcionesTema .cfg-opt').forEach(el =>
    el.classList.toggle('activo', el.dataset.tema === cfgActual.tema));
  document.querySelectorAll('#opcionesInicio .cfg-opt').forEach(el =>
    el.classList.toggle('activo', el.dataset.inicio === cfgActual.paginaInicio));

  actualizarEtiquetaTemaSistema();

  $('toggleSidebarAuto').checked    = cfgActual.sidebarAuto;
  $('toggleResumenSidebar').checked = cfgActual.resumenSidebar;
  $('toggleAlertaStock').checked    = cfgActual.alertaStock;
  $('toggleWidgetRotacion').checked = cfgActual.widgetRotacion;
  $('toggleSilencioso').checked     = cfgActual.silencioso;

  perillaBrillo.pintar(cfgActual.brillo);
  perillaFuente.pintar(cfgActual.fuente);
  perillaZoom.pintar(cfgActual.zoom);

  // ── Autoguardado de toggles (barra lateral, alertas) ──
  const togglesMap = {
    toggleSidebarAuto:    'sidebarAuto',
    toggleResumenSidebar: 'resumenSidebar',
    toggleAlertaStock:    'alertaStock',
    toggleWidgetRotacion: 'widgetRotacion',
    toggleSilencioso:     'silencioso',
  };
  Object.entries(togglesMap).forEach(([id, key]) => {
    $(id).addEventListener('change', function () {
      cfgActual[key] = this.checked;
      guardarCfg(cfgActual);
      window.dispatchEvent(new CustomEvent('cys-config-changed', { detail: cfgActual }));
      mostrarToastPreferencia();
    });
  });

  // ── Usuarios y perfiles: texto del acceso + modal de actividad ──
  const hint = $('actividadHint');
  if (hint) {
    hint.textContent = ES_ADMIN_EMPRESA
      ? 'Consulta los inicios de sesión de todos los usuarios.'
      : 'Consulta tus últimos inicios de sesión.';
  }
  const modalAct = $('modalActividad');
  if (modalAct) modalAct.addEventListener('show.bs.modal', cargarActividad);

  // ── Enter en el input de clave del bloqueo de empresa ──
  const claveInput = $('claveEmpresaInput');
  if (claveInput) {
    claveInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        verificarClaveEmpresa();
      }
    });
  }

  initNavegacion();
  initA11y();
}

// ══════════════════════════════════════════
// TEMA / PÁGINA DE INICIO — se aplican y guardan al instante
// ══════════════════════════════════════════
function actualizarEtiquetaTemaSistema() {
  const el = $('temaSistemaLabel');
  if (el) el.textContent = NOMBRES_TEMA[TEMA_SISTEMA] || TEMA_SISTEMA;
}

// Si el usuario había dejado un "Modo de color" del widget de accesibilidad
// distinto de "Predeterminado" (Claro / Alto contraste), base.js lo reaplicaba
// ENCIMA del tema elegido en cada navegación y por eso el color "no se quedaba".
// Al elegir un tema aquí, ese modo vuelve a "Predeterminado".
function liberarModoA11y() {
  try {
    const a = JSON.parse(localStorage.getItem('cys_a11y') || '{}');
    if (a.modo && a.modo !== 'predeterminado') {
      a.modo = 'predeterminado';
      localStorage.setItem('cys_a11y', JSON.stringify(a));
      if (typeof window.reaplicarA11yCYS === 'function') {
        window.reaplicarA11yCYS();       // relee cys_a11y y reaplica con el tema elegido
        aplicarFuente(cfgActual.fuente); // reaplicarA11yCYS pisa el tamaño de fuente
      }
    }
  } catch (e) {}
}

// No depende de que se pase `el`: se marca la opción activa por su data-tema.
function seleccionarTema(tema, el) {
  try {
    if (!NOMBRES_TEMA[tema]) return;

    TEMA_SISTEMA = leerTemaSistema();

    document.querySelectorAll('#opcionesTema .cfg-opt').forEach(o =>
      o.classList.toggle('activo', o.dataset.tema === tema));

    cfgActual.tema = tema;
    // Si coincide con el del sistema no es una elección propia: sigue al sistema
    temaPersonal = (tema !== TEMA_SISTEMA);

    aplicarTema(tema);
    window.CYS_TEMA_SITIO = tema;
    liberarModoA11y();
    guardarCfg(cfgActual);
    sincronizarA11yLuego(); // los chips de "Modo de color" reflejan el reset
    mostrarToastPreferencia();

    if (ES_ADMIN_EMPRESA && tema !== TEMA_SISTEMA) {
      pedirConfirmacionTemaSistema(tema);
    }
  } catch (err) {
    console.error('[CYS] Error al cambiar el tema:', err);
  }
}

function pedirConfirmacionTemaSistema(tema) {
  temaPendiente = tema;
  const nombre  = NOMBRES_TEMA[tema] || tema;
  const modalEl = $('modalTemaSistema');

  if (modalEl && window.bootstrap && window.bootstrap.Modal) {
    const nombreEl = $('temaConfirmNombre');
    const errorEl  = $('temaConfirmError');
    if (nombreEl) nombreEl.textContent = nombre;
    if (errorEl)  errorEl.style.display = 'none';
    try {
      window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
      return;
    } catch (err) {
      console.error('[CYS] No se pudo abrir el modal de tema del sistema:', err);
    }
  } else {
    console.warn('[CYS] Falta #modalTemaSistema en el HTML o Bootstrap no está cargado.');
  }

  // Respaldo: si el modal no existe o falla, igual se pregunta al administrador
  if (window.confirm(`¿Establecer "${nombre}" como tema predeterminado de todo el sistema?`)) {
    confirmarTemaSistema();
  } else {
    temaPendiente = null;
  }
}

async function confirmarTemaSistema() {
  if (!temaPendiente) return;

  const btn     = $('btnConfirmarTemaSistema');
  const errorEl = $('temaConfirmError');
  if (errorEl) errorEl.style.display = 'none';
  if (btn) btn.disabled = true;

  const fd = new FormData();
  fd.append('tema', temaPendiente);

  try {
    const resp = await fetch(URL_GUARDAR_TEMA_SISTEMA, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: fd,
    });
    const data = await resp.json();

    if (data.ok) {
      TEMA_SISTEMA = temaPendiente;
      // El administrador CONSERVA también su elección en este navegador, para que
      // el color no se revierta si el servidor devuelve el tema viejo en la siguiente página.
      temaPersonal = true;
      cfgActual.tema = TEMA_SISTEMA;
      guardarCfg(cfgActual);
      window.CYS_TEMA_SISTEMA = TEMA_SISTEMA;
      window.CYS_TEMA_SITIO   = TEMA_SISTEMA;
      // Mantiene <html data-tema-sistema> al día aunque htmx no recargue el <html>
      document.documentElement.dataset.temaSistema = TEMA_SISTEMA;
      actualizarEtiquetaTemaSistema();
      const modalEl = $('modalTemaSistema');
      if (modalEl && window.bootstrap && window.bootstrap.Modal) {
        window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
      }
      mostrarToast('Tema predeterminado del sistema actualizado');
      temaPendiente = null;
    } else {
      const msg = data.error || 'No se pudo establecer el tema del sistema.';
      if (errorEl) { errorEl.textContent = msg; errorEl.style.display = 'block'; }
      else mostrarToast(msg, 'error');
    }
  } catch (e) {
    const msg = 'Error de conexión con el servidor.';
    if (errorEl) { errorEl.textContent = msg; errorEl.style.display = 'block'; }
    else mostrarToast(msg, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

function seleccionarInicio(valor, el) {
  document.querySelectorAll('#opcionesInicio .cfg-opt').forEach(o =>
    o.classList.toggle('activo', o.dataset.inicio === valor));
  cfgActual.paginaInicio = valor;
  guardarCfg(cfgActual);
  document.cookie = `cys_pagina_inicio=${valor}; path=/; max-age=31536000; SameSite=Lax`;
  mostrarToastPreferencia();
}

// ══════════════════════════════════════════
// LOGO EMPRESA — preview local, se sube junto con "Guardar"
// ══════════════════════════════════════════
function pintarLogo(url) {
  const cont = $('logoEmpresaPreview');
  if (!cont) return;
  cont.innerHTML = url
    ? `<img src="${esc(url)}" alt="Logo empresa">`
    : '<i class="bi bi-image"></i>';
}

// Evita que el navegador muestre el logo viejo desde caché
function conCacheBust(url) {
  if (!url) return '';
  return url + (url.includes('?') ? '&' : '?') + 't=' + Date.now();
}

function previewLogoEmpresa(input) {
  if (!input.files || !input.files[0]) return;
  logoEmpresaFile = input.files[0];
  const reader = new FileReader();
  reader.onload = function (e) {
    pintarLogo(e.target.result);
  };
  reader.readAsDataURL(logoEmpresaFile);
}

// ══════════════════════════════════════════
// BLOQUEO — Información de la Empresa (estilo "desbloquear celular")
// ══════════════════════════════════════════
function sacudirElemento(el) {
  const clase = el.id === 'claveEmpresaInput'
    ? 'cfg-lockscreen__input--shake'
    : 'cfg-lockscreen__icon--shake';
  el.classList.remove(clase);
  // Forzar reflow para poder repetir la animación seguidas veces
  void el.offsetWidth;
  el.classList.add(clase);
  setTimeout(() => el.classList.remove(clase), 400);
}

async function verificarClaveEmpresa() {
  if (!ES_ADMIN_EMPRESA) return;

  const input   = $('claveEmpresaInput');
  const clave   = input.value;
  const errorEl = $('claveEmpresaError');
  const btn     = $('btnVerificarClaveEmpresa');
  const icono   = $('empresaLockIcon');

  errorEl.style.display = 'none';

  if (!clave) {
    errorEl.textContent = 'Ingresa tu contraseña.';
    errorEl.style.display = 'block';
    sacudirElemento(input);
    return;
  }

  btn.disabled = true;
  const fd = new FormData();
  fd.append('clave', clave);

  try {
    const resp = await fetch(URL_VERIFICAR_EMPRESA, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: fd,
    });
    const data = await resp.json();

    if (data.ok) {
      // Animación de candado abriéndose
      $('empresaLockIconGlyph').className = 'bi bi-unlock-fill';
      icono.classList.add('cfg-lockscreen__icon--open');

      // Rellenar campos con los datos reales (sin mostrar "null")
      const emp = data.empresa || {};
      $('empresaNombre').value    = emp.nombre_empresa ?? '';
      $('empresaNit').value       = emp.nit ?? '';
      $('empresaDireccion').value = emp.direccion ?? '';
      $('empresaTelefono').value  = emp.telefono ?? '';
      $('empresaEmail').value     = emp.email ?? '';

      // Logo guardado (si la vista devuelve emp.logo_url)
      if (emp.logo_url) pintarLogo(conCacheBust(emp.logo_url));

      setTimeout(() => {
        $('empresaLockScreen').style.display = 'none';
        $('empresaCampos').style.display = 'block';
        $('btnGuardarEmpresa').style.display = 'inline-flex';
        const btnBloquear = $('btnBloquearEmpresa');
        if (btnBloquear) btnBloquear.style.display = 'inline-flex';
      }, 300);

      mostrarToast('Acceso concedido');
    } else {
      errorEl.textContent = data.error || 'No se pudo verificar.';
      errorEl.style.display = 'block';
      sacudirElemento(input);
      input.value = '';
      input.focus();
    }
  } catch (e) {
    errorEl.textContent = 'Error de conexión con el servidor.';
    errorEl.style.display = 'block';
  } finally {
    btn.disabled = false;
  }
}

async function bloquearEmpresa() {
  try {
    await fetch(URL_BLOQUEAR_EMPRESA, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    });
  } catch (e) {
    // aunque falle la llamada, igual bloqueamos visualmente
  }

  // Limpiar del DOM los datos sensibles
  $('empresaNombre').value    = '';
  $('empresaNit').value       = '';
  $('empresaDireccion').value = '';
  $('empresaTelefono').value  = '';
  $('empresaEmail').value     = '';
  logoEmpresaFile = null;
  const inputLogo = $('inputLogoEmpresa');
  if (inputLogo) inputLogo.value = '';

  $('empresaCampos').style.display = 'none';
  $('btnGuardarEmpresa').style.display = 'none';
  const btnBloquear = $('btnBloquearEmpresa');
  if (btnBloquear) btnBloquear.style.display = 'none';

  const icono = $('empresaLockIcon');
  icono.classList.remove('cfg-lockscreen__icon--open');
  $('empresaLockIconGlyph').className = 'bi bi-lock-fill';

  const input = $('claveEmpresaInput');
  if (input) input.value = '';
  const errorEl = $('claveEmpresaError');
  if (errorEl) errorEl.style.display = 'none';

  $('empresaLockScreen').style.display = 'flex';

  mostrarToast('Sección bloqueada', 'info');
}

// ══════════════════════════════════════════
// EMPRESA — POST real a configuracion:guardar_empresa (incluye logo si se cambió)
// ══════════════════════════════════════════
async function guardarInfoEmpresa() {
  const btn = $('btnGuardarEmpresa');
  btn.disabled = true;

  const fd = new FormData();
  fd.append('nombre_empresa', $('empresaNombre').value.trim());
  fd.append('nit',            $('empresaNit').value.trim());
  fd.append('telefono',       $('empresaTelefono').value.trim());
  fd.append('email',          $('empresaEmail').value.trim());
  fd.append('direccion',      $('empresaDireccion').value.trim());

  // Respaldo: si por algo logoEmpresaFile se perdió, se toma directo del input
  const inputLogo = $('inputLogoEmpresa');
  const archivoLogo = logoEmpresaFile || (inputLogo && inputLogo.files && inputLogo.files[0]) || null;
  if (archivoLogo) {
    fd.append('logo', archivoLogo, archivoLogo.name);
  }

  try {
    const resp = await fetch(URL_GUARDAR_EMPRESA, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: fd,
    });

    let data = null;
    try {
      data = await resp.json();
    } catch (e) {
      throw new Error('El servidor no devolvió JSON (HTTP ' + resp.status + ')');
    }

    if (data.ok) {
      logoEmpresaFile = null;
      if (inputLogo) inputLogo.value = '';

      // Si el servidor devuelve la URL del logo guardado, se muestra esa (prueba de que sí se guardó)
      if (data.logo_url) {
        pintarLogo(conCacheBust(data.logo_url));
      } else if (archivoLogo) {
        // Se envió un logo pero el servidor no confirmó URL: se avisa
        console.warn('[CYS] Se envió el logo pero guardar_empresa no devolvió logo_url.');
      }
      mostrarToast('Información de la empresa guardada');
    } else {
      mostrarToast(data.error || 'No se pudo guardar', 'error');
    }
  } catch (e) {
    console.error('[CYS] guardarInfoEmpresa:', e);
    mostrarToast('Error de conexión con el servidor', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ══════════════════════════════════════════
// IMPUESTOS — POST real a configuracion:guardar_impuestos
// ══════════════════════════════════════════
async function guardarImpuestos() {
  const btn = $('btnGuardarImpuestos');

  const iva = parseFloat($('ivaPorcentaje').value);
  if (isNaN(iva) || iva < 0 || iva > 100) {
    mostrarToast('El IVA debe estar entre 0 y 100', 'error');
    return;
  }

  btn.disabled = true;

  const fd = new FormData();
  fd.append('iva_porcentaje', $('ivaPorcentaje').value);
  fd.append('moneda', $('monedaSelect').value);

  const unidadesRaw = $('unidadesMedida').value;
  unidadesRaw.split(',').map(u => u.trim()).filter(Boolean).forEach(u => {
    fd.append('unidades[]', u);
  });

  try {
    const resp = await fetch(URL_GUARDAR_IMPUESTOS, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: fd,
    });
    const data = await resp.json();
    if (data.ok) {
      mostrarToast('Impuestos guardados');
    } else {
      mostrarToast(data.error || 'No se pudo guardar', 'error');
    }
  } catch (e) {
    mostrarToast('Error de conexión con el servidor', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ══════════════════════════════════════════
// TOAST (colores desde variables de tema)
// ══════════════════════════════════════════
function mostrarToast(msg = 'Configuración guardada', tipo = 'ok') {
  const t = $('cfg-toast');
  if (!t) return;

  const estilos = {
    ok:    { color: 'var(--verde, #2ecc71)',  icono: 'bi-check-circle-fill' },
    error: { color: 'var(--rojo, #e87070)',   icono: 'bi-exclamation-triangle-fill' },
    info:  { color: 'var(--azul-claro)',      icono: 'bi-info-circle-fill' },
  };
  const e = estilos[tipo] || estilos.ok;

  t.innerHTML = `<i class="bi ${e.icono} me-2"></i>`;
  t.appendChild(document.createTextNode(msg));
  t.style.background  = `color-mix(in srgb, ${e.color} 15%, var(--fondo-card, #fff))`;
  t.style.borderColor = `color-mix(in srgb, ${e.color} 45%, transparent)`;
  t.style.color       = e.color;
  t.style.display     = 'block';

  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { t.style.display = 'none'; }, 2800);
}

// Toast corto y silencioso para autoguardado de preferencias (evita spam si se togglean varias seguidas)
function mostrarToastPreferencia() {
  clearTimeout(toastPrefTimeout);
  toastPrefTimeout = setTimeout(() => {
    mostrarToast('Preferencia guardada', 'info');
  }, 250);
}

// ══════════════════════════════════════════
// Funciones usadas por onclick="..." en el HTML
// ══════════════════════════════════════════
Object.assign(window, {
  seleccionarTema,
  seleccionarInicio,
  confirmarTemaSistema,
  previewLogoEmpresa,
  verificarClaveEmpresa,
  bloquearEmpresa,
  guardarInfoEmpresa,
  guardarImpuestos,
});

// Inicializa aunque el script se cargue después de DOMContentLoaded (htmx).
// Si la página se carga completa por primera vez, el widget de accesibilidad
// aún no existe cuando corre este script, así que se espera al DOM completo.
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

})();