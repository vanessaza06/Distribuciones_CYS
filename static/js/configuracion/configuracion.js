(function () {
'use strict';

// Si la página no es la de Configuración (o htmx aún no puso el contenido), no hace nada.
const cfgData = document.getElementById('cfg-data');
if (!cfgData) return;

// ══════════════════════════════════════════
// URLs de Django (pasadas desde el template vía data-attributes)
// ══════════════════════════════════════════
const URL_ACTIVIDAD            = cfgData.dataset.urlActividad;
const URL_GUARDAR_EMPRESA      = cfgData.dataset.urlGuardarEmpresa;
const URL_VERIFICAR_EMPRESA    = cfgData.dataset.urlVerificarEmpresa;
const URL_BLOQUEAR_EMPRESA     = cfgData.dataset.urlBloquearEmpresa;
const URL_GUARDAR_IMPUESTOS    = cfgData.dataset.urlGuardarImpuestos;
const URL_CREAR_BACKUP         = cfgData.dataset.urlCrearBackup;
const URL_GUARDAR_TEMA_SISTEMA = cfgData.dataset.urlGuardarTemaSistema;

// FIX: antes era `=== 'true'` exacto. Django entrega "True" (con mayúscula)
// si el template no lo pasa por |lower, y entonces el modal de confirmación
// de tema del sistema NUNCA salía. Ahora se acepta cualquier mayúscula.
const ES_ADMIN_EMPRESA = ['true', '1'].includes(String(cfgData.dataset.esAdmin || '').trim().toLowerCase());

const NOMBRES_TEMA = {
  'oscuro': 'Oscuro',
  'claro': 'Claro',
  'alto-contraste': 'Alto contraste',
  'basecys': 'Base CyS',
  'sepia': 'Sepia',
};

// FIX: el tema del sistema se lee primero de <html data-tema-sistema> (que base.js
// mantiene al día en cada navegación htmx) y luego del data-attribute de esta página.
// Antes solo se leía una vez de cfg-data y quedaba desactualizado.
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

function seleccionarTema(tema, el) {
  try {
    if (!NOMBRES_TEMA[tema]) return;

    TEMA_SISTEMA = leerTemaSistema();

    document.querySelectorAll('#opcionesTema .cfg-opt').forEach(o =>
      o.classList.toggle('activo', o.dataset.tema === tema));

    cfgActual.tema = tema;
    temaPersonal = (tema !== TEMA_SISTEMA);

    window.CYS_TEMA_SITIO = tema;
    liberarModoA11y();
    guardarCfg(cfgActual);

    // Mismo disparador que usa htmx al navegar (el que ya sabemos que funciona)
    document.dispatchEvent(new CustomEvent('htmx:afterSettle'));
    // Respaldo por si el listener tarda un ciclo
    setTimeout(() => {
      document.dispatchEvent(new CustomEvent('htmx:afterSettle'));
      aplicarFuente(cfgActual.fuente);
    }, 0);

    mostrarToastPreferencia();

    if (ES_ADMIN_EMPRESA && tema !== TEMA_SISTEMA) {
      pedirConfirmacionTemaSistema(tema);
    }
  } catch (err) {
    console.error('[CYS] Error al cambiar el tema:', err);
  }
}

// ══════════════════════════════════════════
// INIT
// ══════════════════════════════════════════
function init() {
  perillaBrillo = crearPerilla(document.getElementById('knobBrillo'), 'btnResetBrillo');
  perillaFuente = crearPerilla(document.getElementById('knobFuente'), 'btnResetFuente');
  perillaZoom   = crearPerilla(document.getElementById('knobZoom'), 'btnResetZoom');

  document.getElementById('knobBrillo').addEventListener('cambio', e => {
    cfgActual.brillo = e.detail;
    aplicarBrillo(e.detail);
    guardarCfg(cfgActual);
    mostrarToastPreferencia();
  });
  document.getElementById('knobFuente').addEventListener('cambio', e => {
    cfgActual.fuente = e.detail;
    aplicarFuente(e.detail);
    guardarCfg(cfgActual);
    mostrarToastPreferencia();
  });
  document.getElementById('knobZoom').addEventListener('cambio', e => {
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

  document.getElementById('toggleSidebarAuto').checked    = cfgActual.sidebarAuto;
  document.getElementById('toggleResumenSidebar').checked = cfgActual.resumenSidebar;
  document.getElementById('toggleAlertaStock').checked    = cfgActual.alertaStock;
  document.getElementById('toggleWidgetRotacion').checked = cfgActual.widgetRotacion;
  document.getElementById('toggleSilencioso').checked     = cfgActual.silencioso;

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
    document.getElementById(id).addEventListener('change', function () {
      cfgActual[key] = this.checked;
      guardarCfg(cfgActual);
      window.dispatchEvent(new CustomEvent('cys-config-changed', { detail: cfgActual }));
      mostrarToastPreferencia();
    });
  });

  // ── Modal de actividad de usuarios ──
  document.getElementById('modalActividad').addEventListener('show.bs.modal', function () {
    const tbody = document.getElementById('tablaActividad');
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Cargando...</td></tr>';

    fetch(URL_ACTIVIDAD)
      .then(res => res.json())
      .then(data => {
        document.getElementById('tituloActividad').textContent =
          data.es_admin ? 'Actividad de todos los usuarios' : 'Mi actividad';
        document.getElementById('colUsuario').style.display = data.es_admin ? '' : 'none';

        tbody.innerHTML = '';
        if (data.registros.length === 0) {
          tbody.innerHTML = '<tr><td colspan="3" class="text-center">Sin registros</td></tr>';
          return;
        }
        data.registros.forEach(r => {
          const fila = document.createElement('tr');
          fila.innerHTML = `
            ${data.es_admin ? `<td>${r.usuario}</td>` : ''}
            <td>${r.fecha_hora}</td>
            <td>${r.ip}</td>
          `;
          tbody.appendChild(fila);
        });
      })
      .catch(() => {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">Error al cargar la actividad</td></tr>';
      });
  });

  // ── Enter en el input de clave del bloqueo de empresa ──
  const claveInput = document.getElementById('claveEmpresaInput');
  if (claveInput) {
    claveInput.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        verificarClaveEmpresa();
      }
    });
  }
}

// ══════════════════════════════════════════
// TEMA / PÁGINA DE INICIO — se aplican y guardan al instante
// ══════════════════════════════════════════
function actualizarEtiquetaTemaSistema() {
  const el = document.getElementById('temaSistemaLabel');
  if (el) el.textContent = NOMBRES_TEMA[TEMA_SISTEMA] || TEMA_SISTEMA;
}

// FIX: si el usuario había dejado un "Modo de color" del widget de accesibilidad
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

// FIX: ya no depende de que se pase `el` (si llegaba null, lanzaba un error
// en la primera línea y no se hacía NADA: ni color, ni guardado, ni aviso).
// Se marca la opción activa por su data-tema.
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
  const modalEl = document.getElementById('modalTemaSistema');

  if (modalEl && window.bootstrap && window.bootstrap.Modal) {
    const nombreEl = document.getElementById('temaConfirmNombre');
    const errorEl  = document.getElementById('temaConfirmError');
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

  const btn     = document.getElementById('btnConfirmarTemaSistema');
  const errorEl = document.getElementById('temaConfirmError');
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
      // FIX: el administrador CONSERVA también su elección en este navegador.
      // Antes se borraba y dependía 100% de que el servidor devolviera el tema
      // nuevo en la siguiente página; si lo devolvía viejo, el color se revertía.
      temaPersonal = true;
      cfgActual.tema = TEMA_SISTEMA;
      guardarCfg(cfgActual);
      window.CYS_TEMA_SISTEMA = TEMA_SISTEMA;
      window.CYS_TEMA_SITIO   = TEMA_SISTEMA;
      // Mantiene <html data-tema-sistema> al día aunque htmx no recargue el <html>
      document.documentElement.dataset.temaSistema = TEMA_SISTEMA;
      actualizarEtiquetaTemaSistema();
      const modalEl = document.getElementById('modalTemaSistema');
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
function previewLogoEmpresa(input) {
  if (!input.files || !input.files[0]) return;
  logoEmpresaFile = input.files[0];
  const reader = new FileReader();
  reader.onload = function (e) {
    document.getElementById('logoEmpresaPreview').innerHTML =
      `<img src="${e.target.result}" alt="Logo empresa">`;
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

  const input   = document.getElementById('claveEmpresaInput');
  const clave   = input.value;
  const errorEl = document.getElementById('claveEmpresaError');
  const btn     = document.getElementById('btnVerificarClaveEmpresa');
  const icono   = document.getElementById('empresaLockIcon');

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
      document.getElementById('empresaLockIconGlyph').className = 'bi bi-unlock-fill';
      icono.classList.add('cfg-lockscreen__icon--open');

      // Rellenar campos con los datos reales
      document.getElementById('empresaNombre').value    = data.empresa.nombre_empresa;
      document.getElementById('empresaNit').value       = data.empresa.nit;
      document.getElementById('empresaDireccion').value = data.empresa.direccion;
      document.getElementById('empresaTelefono').value  = data.empresa.telefono;
      document.getElementById('empresaEmail').value     = data.empresa.email;

      setTimeout(() => {
        document.getElementById('empresaLockScreen').style.display = 'none';
        document.getElementById('empresaCampos').style.display = 'block';
        document.getElementById('btnGuardarEmpresa').style.display = 'inline-flex';
        const btnBloquear = document.getElementById('btnBloquearEmpresa');
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
  document.getElementById('empresaNombre').value    = '';
  document.getElementById('empresaNit').value       = '';
  document.getElementById('empresaDireccion').value = '';
  document.getElementById('empresaTelefono').value  = '';
  document.getElementById('empresaEmail').value     = '';

  document.getElementById('empresaCampos').style.display = 'none';
  document.getElementById('btnGuardarEmpresa').style.display = 'none';
  const btnBloquear = document.getElementById('btnBloquearEmpresa');
  if (btnBloquear) btnBloquear.style.display = 'none';

  const icono = document.getElementById('empresaLockIcon');
  icono.classList.remove('cfg-lockscreen__icon--open');
  document.getElementById('empresaLockIconGlyph').className = 'bi bi-lock-fill';

  const input = document.getElementById('claveEmpresaInput');
  if (input) input.value = '';
  document.getElementById('claveEmpresaError').style.display = 'none';

  document.getElementById('empresaLockScreen').style.display = 'flex';

  mostrarToast('Sección bloqueada', 'info');
}

// ══════════════════════════════════════════
// EMPRESA — POST real a configuracion:guardar_empresa (incluye logo si se cambió)
// ══════════════════════════════════════════
async function guardarInfoEmpresa() {
  const btn = document.getElementById('btnGuardarEmpresa');
  btn.disabled = true;

  const fd = new FormData();
  fd.append('nombre_empresa', document.getElementById('empresaNombre').value.trim());
  fd.append('nit',            document.getElementById('empresaNit').value.trim());
  fd.append('telefono',       document.getElementById('empresaTelefono').value.trim());
  fd.append('email',          document.getElementById('empresaEmail').value.trim());
  fd.append('direccion',      document.getElementById('empresaDireccion').value.trim());
  if (logoEmpresaFile) {
    fd.append('logo', logoEmpresaFile);
  }

  try {
    const resp = await fetch(URL_GUARDAR_EMPRESA, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
      body: fd,
    });
    const data = await resp.json();
    if (data.ok) {
      mostrarToast('Información de la empresa guardada');
      logoEmpresaFile = null;
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
// IMPUESTOS — POST real a configuracion:guardar_impuestos
// ══════════════════════════════════════════
async function guardarImpuestos() {
  const btn = document.getElementById('btnGuardarImpuestos');
  btn.disabled = true;

  const fd = new FormData();
  fd.append('iva_porcentaje', document.getElementById('ivaPorcentaje').value);
  fd.append('moneda', document.getElementById('monedaSelect').value);

  const unidadesRaw = document.getElementById('unidadesMedida').value;
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
// BACKUP — POST real a configuracion:crear_backup
// ══════════════════════════════════════════
async function generarRespaldo() {
  const btn = document.getElementById('btnBackup');
  btn.disabled = true;
  btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Generando...';

  try {
    const resp = await fetch(URL_CREAR_BACKUP, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    });
    const data = await resp.json();

    if (data.ok) {
      document.getElementById('dbUltimoRespaldo').textContent = data.fecha;
      mostrarToast('Respaldo generado: ' + data.nombre);

      const lista = document.getElementById('listaBackups');
      const vacio = lista.querySelector('[data-backup-empty]');
      if (vacio) vacio.remove();

      const item = document.createElement('div');
      item.className = 'cfg-backup-item';
      item.innerHTML = `
        <div>
          <div class="cfg-backup-item__nombre">${data.nombre}</div>
          <div class="cfg-backup-item__meta">${data.fecha} · ${data.tamaño}</div>
        </div>
        <i class="bi bi-file-earmark-zip" style="color:var(--azul-claro);"></i>
      `;
      lista.prepend(item);
    } else {
      mostrarToast(data.error || 'No se pudo generar el respaldo', 'error');
    }
  } catch (e) {
    mostrarToast('Error de conexión con el servidor', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cloud-arrow-down me-1"></i> Generar respaldo';
  }
}

// ══════════════════════════════════════════
// TOAST
// ══════════════════════════════════════════
function mostrarToast(msg = 'Configuración guardada', tipo = 'ok') {
  const t = document.getElementById('cfg-toast');
  if (!t) return;
  t.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>${msg}`;
  if (tipo === 'error') {
    t.style.background  = 'rgba(192,57,43,.15)';
    t.style.borderColor = 'rgba(192,57,43,.4)';
    t.style.color       = '#e87070';
  } else if (tipo === 'info') {
    t.style.background  = 'rgba(77,168,218,.15)';
    t.style.borderColor = 'rgba(77,168,218,.4)';
    t.style.color       = '#4DA8DA';
  } else {
    t.style.background  = 'rgba(39,174,96,.15)';
    t.style.borderColor = 'rgba(39,174,96,.4)';
    t.style.color       = '#2ecc71';
  }
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2800);
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
  generarRespaldo,
});

// Inicializa aunque el script se cargue después de DOMContentLoaded (htmx)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

})();