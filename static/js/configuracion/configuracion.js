(function () {
'use strict';

// Si la página no es la de Configuración (o htmx aún no puso el contenido), no hace nada.
const cfgData = document.getElementById('cfg-data');
if (!cfgData) return;

const $ = (id) => document.getElementById(id);

// ══════════════════════════════════════════
// Datos que vienen del template
// ══════════════════════════════════════════
const URL_GUARDAR_TEMA_SISTEMA = cfgData.dataset.urlGuardarTemaSistema;
const URL_A11Y_EXTRA           = cfgData.dataset.urlA11yExtra;
const ES_ADMIN_EMPRESA = ['true', '1'].includes(String(cfgData.dataset.esAdmin || '').trim().toLowerCase());

const NOMBRES_TEMA = {
  'oscuro': 'Oscuro',
  'claro': 'Claro',
  'alto-contraste': 'Alto contraste',
  'basecys': 'Base CyS',
  'sepia': 'Sepia',
};

const FONDOS_TEMA = {
  'oscuro': 'linear-gradient(135deg, #011936, #0a2240)',
  'claro': 'linear-gradient(135deg, #f0f4f8, #dde8f0)',
  'alto-contraste': '#000',
  'basecys': '#D9A441',
  'sepia': 'linear-gradient(135deg, #1a0f05, #3d2b14)',
};

// El dato del servidor (data-attribute) manda: viene del archivo config_sistema.json.
function leerTemaSistema() {
  const deCfg = cfgData.dataset.temaSistema;
  if (deCfg && NOMBRES_TEMA[deCfg]) return deCfg;
  const deHtml = document.documentElement.dataset.temaSistema;
  if (deHtml && NOMBRES_TEMA[deHtml]) return deHtml;
  return 'oscuro';
}

let TEMA_SISTEMA = leerTemaSistema();

// ══════════════════════════════════════════
// CSRF
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
// ESTADO VISUAL (localStorage.cys_config)
// El "tema" solo cuenta como propio si lleva temaPersonal === true.
// ══════════════════════════════════════════
const CFG_DEFAULT = {
  tema: TEMA_SISTEMA, paginaInicio: 'tablero', brillo: 100, fuente: 14, zoom: 100,
  sidebarAuto: false, resumenSidebar: true,
  alertaStock: true, widgetRotacion: true, silencioso: false,
};

let temaPersonal = false;

function cargarCfg() {
  let cfg = { ...CFG_DEFAULT };
  try {
    const g = JSON.parse(localStorage.getItem('cys_config') || '{}');
    temaPersonal = g.temaPersonal === true && !!g.tema;
    cfg = { ...cfg, ...g };
  } catch (e) {}
  if (!temaPersonal) cfg.tema = TEMA_SISTEMA;
  return cfg;
}
function guardarCfg(cfg) {
  const copia = { ...cfg };
  if (temaPersonal) {
    copia.temaPersonal = true;
  } else {
    delete copia.tema;
    delete copia.temaPersonal;
  }
  localStorage.setItem('cys_config', JSON.stringify(copia));
}

let cfgActual = cargarCfg();
let perillaBrillo, perillaFuente, perillaZoom;
let toastPrefTimeout = null;
let toastTimeout = null;
let temaPendiente = null;

// ══════════════════════════════════════════
// PERILLAS (DIAL)
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
// ══════════════════════════════════════════
const A11Y_SWITCHES = [
  ['cfgA11yContraste', 'cysA11yContraste'],
  ['cfgA11yEspaciado', 'cysA11yEspaciado'],
  ['cfgA11yEnlaces',   'cysA11yEnlaces'],
  ['cfgA11yFuente',    'cysA11yFuente'],
];

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
    document.querySelectorAll('#cfgA11yModos .cfg-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const destino = document.querySelector(
          '.cys-a11y-colormode__btn[data-modo="' + chip.dataset.modo + '"]'
        );
        if (destino) destino.click();
        sincronizarA11yLuego();
      });
    });

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
    if (!widget.dataset.cfgBound) {
      widget.dataset.cfgBound = '1';
      ['click', 'change'].forEach(ev => {
        widget.addEventListener(ev, () => {
          setTimeout(() => { if (window.cfgSyncA11y) window.cfgSyncA11y(); }, 80);
        });
      });
    }
  }

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
// MENÚ DE ACCESOS: scroll suave a cada grupo
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

  actualizarEstadoTema();

  $('toggleSidebarAuto').checked    = cfgActual.sidebarAuto;
  $('toggleResumenSidebar').checked = cfgActual.resumenSidebar;
  $('toggleAlertaStock').checked    = cfgActual.alertaStock;
  $('toggleWidgetRotacion').checked = cfgActual.widgetRotacion;
  $('toggleSilencioso').checked     = cfgActual.silencioso;

  perillaBrillo.pintar(cfgActual.brillo);
  perillaFuente.pintar(cfgActual.fuente);
  perillaZoom.pintar(cfgActual.zoom);

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

  initNavegacion();
  initA11y();
}

// ══════════════════════════════════════════
// TEMA — estado visible
// ══════════════════════════════════════════
function actualizarEstadoTema() {
  const sis = $('temaSistemaLabel');
  if (sis) sis.textContent = NOMBRES_TEMA[TEMA_SISTEMA] || TEMA_SISTEMA;

  const propio = $('temaPropioLabel');
  if (propio) {
    const t = cfgActual.tema;
    propio.textContent = (temaPersonal && t !== TEMA_SISTEMA)
      ? (NOMBRES_TEMA[t] || t)
      : 'igual al del sistema';
  }
}

// Si el "Modo de color" del widget de accesibilidad estaba en Claro / Alto
// contraste, base.js lo reaplicaba encima del tema elegido. Al elegir un
// tema aquí, ese modo vuelve a "Predeterminado".
function liberarModoA11y() {
  try {
    const a = JSON.parse(localStorage.getItem('cys_a11y') || '{}');
    if (a.modo && a.modo !== 'predeterminado') {
      a.modo = 'predeterminado';
      localStorage.setItem('cys_a11y', JSON.stringify(a));
      if (typeof window.reaplicarA11yCYS === 'function') {
        window.reaplicarA11yCYS();
        aplicarFuente(cfgActual.fuente);
      }
    }
  } catch (e) {}
}

function seleccionarTema(tema, el) {
  try {
    if (!NOMBRES_TEMA[tema]) return;

    document.querySelectorAll('#opcionesTema .cfg-opt').forEach(o =>
      o.classList.toggle('activo', o.dataset.tema === tema));

    cfgActual.tema = tema;
    // Si coincide con el del sistema no es una elección propia
    temaPersonal = (tema !== TEMA_SISTEMA);

    aplicarTema(tema);
    window.CYS_TEMA_SITIO = tema;
    liberarModoA11y();
    guardarCfg(cfgActual);
    sincronizarA11yLuego();
    actualizarEstadoTema();

    if (tema === TEMA_SISTEMA) {
      mostrarToast('Tema ' + NOMBRES_TEMA[tema] + ' aplicado (igual al del sistema)', 'info');
    } else if (ES_ADMIN_EMPRESA) {
      // El administrador decide dónde aplicarlo
      pedirConfirmacionTemaSistema(tema);
    } else {
      mostrarToast('Tema ' + NOMBRES_TEMA[tema] + ' aplicado solo en tu cuenta', 'info');
    }
  } catch (err) {
    console.error('[CYS] Error al cambiar el tema:', err);
  }
}

// ══════════════════════════════════════════
// TEMA — confirmación (solo administrador)
// ══════════════════════════════════════════
function pedirConfirmacionTemaSistema(tema) {
  temaPendiente = tema;
  const nombre  = NOMBRES_TEMA[tema] || tema;
  const modalEl = $('modalTemaSistema');

  if (modalEl && window.bootstrap && window.bootstrap.Modal) {
    const nombreEl  = $('temaConfirmNombre');
    const errorEl   = $('temaConfirmError');
    const previewEl = $('temaConfirmPreview');
    if (nombreEl)  nombreEl.textContent = nombre;
    if (errorEl)   errorEl.style.display = 'none';
    if (previewEl) previewEl.style.background = FONDOS_TEMA[tema] || '';
    try {
      window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
      return;
    } catch (err) {
      console.error('[CYS] No se pudo abrir el modal de tema:', err);
    }
  }

  // Respaldo si el modal no abre
  if (window.confirm('¿Establecer "' + nombre + '" como tema predeterminado de todo el sistema?')) {
    confirmarTemaSistema();
  } else {
    soloParaMi();
  }
}

function soloParaMi() {
  const nombre = NOMBRES_TEMA[temaPendiente || cfgActual.tema] || '';
  temaPendiente = null;
  mostrarToast('Tema ' + nombre + ' aplicado solo en tu cuenta', 'info');
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
      // El administrador conserva también su elección en este navegador,
      // para que el color no se revierta al navegar.
      temaPersonal = true;
      cfgActual.tema = TEMA_SISTEMA;
      guardarCfg(cfgActual);
      window.CYS_TEMA_SISTEMA = TEMA_SISTEMA;
      window.CYS_TEMA_SITIO   = TEMA_SISTEMA;
      cfgData.dataset.temaSistema = TEMA_SISTEMA;
      document.documentElement.dataset.temaSistema = TEMA_SISTEMA;
      actualizarEstadoTema();

      const modalEl = $('modalTemaSistema');
      if (modalEl && window.bootstrap && window.bootstrap.Modal) {
        window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
      }
      mostrarToast('Tema predeterminado de todo el sistema actualizado');
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

// ══════════════════════════════════════════
// PÁGINA DE INICIO
// ══════════════════════════════════════════
function seleccionarInicio(valor, el) {
  document.querySelectorAll('#opcionesInicio .cfg-opt').forEach(o =>
    o.classList.toggle('activo', o.dataset.inicio === valor));
  cfgActual.paginaInicio = valor;
  guardarCfg(cfgActual);
  document.cookie = `cys_pagina_inicio=${valor}; path=/; max-age=31536000; SameSite=Lax`;
  mostrarToastPreferencia();
}

// ══════════════════════════════════════════
// TOAST
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

function mostrarToastPreferencia() {
  clearTimeout(toastPrefTimeout);
  toastPrefTimeout = setTimeout(() => {
    mostrarToast('Preferencia guardada', 'info');
  }, 250);
}

// Funciones usadas por onclick="..." en el HTML
Object.assign(window, {
  seleccionarTema,
  seleccionarInicio,
  confirmarTemaSistema,
  soloParaMi,
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

})();