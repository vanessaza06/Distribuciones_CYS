/* ============================================================
   aside.js — Barra lateral CYS
   ------------------------------------------------------------
   - Modo compacto (solo íconos) con flyouts de submenú estables
   - Tooltips de Bootstrap SOLO en modo compacto (en modo normal
     las etiquetas ya están visibles)
   - El grupo del submenú de la página actual queda abierto, también
     cuando se navega con htmx (el aside usa hx-preserve y el script
     no se vuelve a ejecutar en cada navegación)
   ============================================================ */
(function () {
  'use strict';

  const KEY_MINI   = 'cys_sidebar_mini';
  const ANCHO_FULL = '290px';
  const ANCHO_MINI = '84px';

  // Prefijos de URL extra por submenú, para subpáginas cuya URL no cuelga
  // exactamente del href de un link (ej. /compra/detalle/5/).
  // Ajústalos a tus rutas reales.
  const RUTAS_SUBMENU = {
    submenuVentas:       ['/ventas', '/caja', '/metodos-pago'],
    submenuDevoluciones: ['/devolucion'],
    submenuInventario:   ['/producto', '/presentacion', '/stock', '/categoria', '/marca', '/bodega', '/lote'],
    submenuCompras:      ['/compra']
  };

  let sidebar      = null;
  let miniActivo   = false;
  let tipsNav      = [];     // tooltips de la navegación (solo activos en modo compacto)
  let tipMini      = null;   // tooltip del botón compacto/expandido
  let rutaAnterior = null;   // última ruta procesada (evita reabrir grupos cerrados a mano)
  let grupoAuto    = null;   // id del submenú abierto automáticamente por la URL
  let wrapHover    = null;   // grupo bajo el mouse en modo compacto

  const normalizar = p => (p || '').replace(/\/+$/, '') || '/';

  function seguro(nombre, fn) {
    try { fn(); } catch (err) { console.error('[CYS] aside — error en "' + nombre + '":', err); }
  }

  // ══════════════════════════════════════════
  // PREFERENCIAS
  // ══════════════════════════════════════════
  function leerCfg() {
    try { return JSON.parse(localStorage.getItem('cys_config') || '{}') || {}; }
    catch (e) { return {}; }
  }

  function leerPrefMini() {
    try {
      const dedicado = localStorage.getItem(KEY_MINI);
      if (dedicado !== null) return dedicado === '1';
    } catch (e) {}
    return !!leerCfg().sidebarMini;
  }

  function guardarPrefMini(activo) {
    try {
      localStorage.setItem(KEY_MINI, activo ? '1' : '0');
      const cfg = leerCfg();
      cfg.sidebarMini = activo;
      localStorage.setItem('cys_config', JSON.stringify(cfg));
    } catch (e) {}
  }

  function actualizarResumenWrap(visible) {
    const wrap = document.getElementById('cys-sb-resumen-wrap');
    if (wrap) wrap.classList.toggle('cys-sb-resumen-oculto', visible === false);
  }

  // ══════════════════════════════════════════
  // SUBMENÚS (toggle manual con el chevron)
  // ══════════════════════════════════════════
  window.toggleSubmenu = function (e, parent, id) {
    if (e) e.stopPropagation();
    const sub = document.getElementById(id);
    if (!sub) return;
    const abrir = !sub.classList.contains('abierto');
    sub.classList.toggle('abierto', abrir);
    if (parent) parent.classList.toggle('abierto', abrir);
    // Decisión manual: ya no lo cierra la navegación automática
    delete sub.dataset.cysAuto;
  };

  // Título del flyout en modo compacto (sale de la etiqueta del link padre)
  function prepararFlyouts() {
    sidebar.querySelectorAll('.cys-sb-inventario-wrap').forEach(function (wrap) {
      const sub   = wrap.querySelector('.cys-sb-submenu');
      const label = wrap.querySelector('.sb-link-flex-grow > span');
      if (sub && label) sub.setAttribute('data-titulo', label.textContent.trim());
    });
  }

  // El flyout es "position: fixed" (así el scroll del aside no lo recorta).
  // Aquí se calcula dónde va: a la izquierda del ícono, alineado con su fila,
  // y subido lo justo si no cabe hacia abajo.
  function posicionarFlyout(wrap) {
    const sub = wrap.querySelector('.cys-sb-submenu');
    if (!sub) return;

    const margen = 8;
    const gap    = 10;
    const r      = wrap.getBoundingClientRect();
    const w      = sub.offsetWidth;
    const h      = sub.offsetHeight;

    let top = r.top;
    if (top + h + margen > window.innerHeight) {
      top = Math.max(margen, window.innerHeight - h - margen);
    }
    const left = Math.max(margen, r.left - gap - w);

    // Calibración: si algún ancestro (transform/filter/backdrop-filter) cambia
    // el bloque contenedor del fixed, se corrige con la diferencia real.
    // Se descuenta el translate de la animación de entrada (si no, el flyout
    // queda corrido y el puente de hover no llega hasta el ícono).
    sub.style.setProperty('--fly-left', '0px');
    sub.style.setProperty('--fly-top', '0px');
    const o  = sub.getBoundingClientRect();
    const tr = getComputedStyle(sub).transform;
    let dx = 0, dy = 0;
    if (tr && tr !== 'none') {
      try { const m = new DOMMatrixReadOnly(tr); dx = m.m41; dy = m.m42; } catch (err) {}
    }

    sub.style.setProperty('--fly-left', (left - (o.left - dx)) + 'px');
    sub.style.setProperty('--fly-top', (top - (o.top - dy)) + 'px');
  }

  // ══════════════════════════════════════════
  // TOOLTIPS
  // ══════════════════════════════════════════
  function crearTipMini(texto) {
    const btn = document.getElementById('btnMiniSidebar');
    if (!btn || !window.bootstrap || !bootstrap.Tooltip) return;
    const previo = bootstrap.Tooltip.getInstance(btn);
    if (previo) previo.dispose();
    btn.setAttribute('data-bs-title', texto);
    tipMini = new bootstrap.Tooltip(btn, {
      trigger: 'hover',
      placement: 'bottom',
      container: 'body',
      title: texto
    });
  }

  function inicializarTooltips() {
    tipsNav = [];
    tipMini = null;
    if (!window.bootstrap || !bootstrap.Tooltip) return;

    sidebar.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
      try {
        // Evita tooltips duplicados si otro script ya los inicializó
        const previo = bootstrap.Tooltip.getInstance(el);
        if (previo) previo.dispose();

        const enNav = !!el.closest('.cys-sb-body');

        // Botones del header (compacto / cerrar): siempre activos
        if (!enNav) {
          if (el.id === 'btnMiniSidebar') {
            crearTipMini('Modo compacto');
          } else {
            new bootstrap.Tooltip(el, {
              trigger: 'hover',
              placement: el.getAttribute('data-bs-placement') || 'bottom',
              container: 'body'
            });
          }
          return;
        }

        // Sin tooltip: sublinks (ya muestran su texto) y padres con submenú
        // (en modo compacto el flyout lleva el título).
        if (el.classList.contains('cys-sb-sublink') || el.closest('.cys-sb-link--parent')) {
          el.removeAttribute('data-bs-toggle');
          return;
        }

        let customClass = '';
        if (el.classList.contains('cys-sb-link--ayuda'))  customClass = 'cys-tip-ayuda';
        if (el.classList.contains('cys-sb-link--config')) customClass = 'cys-tip-config';
        if (el.classList.contains('cys-sb-link--logout')) customClass = 'cys-tip-logout';

        // El aside está pegado a la derecha: el tooltip va a la izquierda
        const tip = new bootstrap.Tooltip(el, {
          trigger: 'hover',
          placement: 'left',
          fallbackPlacements: ['left', 'top', 'bottom'],
          container: 'body',
          customClass: customClass,
          delay: { show: 200, hide: 0 }
        });
        tipsNav.push(tip);
      } catch (err) {
        console.error('[CYS] aside — no se pudo inicializar un tooltip:', err);
      }
    });
  }

  // ══════════════════════════════════════════
  // MODO COMPACTO
  // ══════════════════════════════════════════
  function aplicarModoMini(activo) {
    miniActivo = activo;
    sidebar.classList.toggle('cys-sb-mini', activo);

    if (activo) sidebar.style.setProperty('width', ANCHO_MINI, 'important');
    else        sidebar.style.removeProperty('width');

    document.documentElement.style.setProperty('--sidebar-offset', activo ? ANCHO_MINI : ANCHO_FULL);

    const btn   = sidebar.querySelector('#btnMiniSidebar');
    const icono = btn ? btn.querySelector('i') : null;
    if (icono) {
      icono.classList.toggle('bi-chevron-double-left', !activo);
      icono.classList.toggle('bi-chevron-double-right', activo);
    }

    const texto = activo ? 'Modo expandido' : 'Modo compacto';
    if (btn) {
      btn.setAttribute('aria-label', texto);
      if (tipMini) crearTipMini(texto);
    }

    // Tooltips de navegación: solo en modo compacto
    tipsNav.forEach(function (t) {
      if (activo) { t.enable(); }
      else        { t.hide(); t.disable(); }
    });

    // Limpia ajustes de posición de flyouts anteriores
    wrapHover = null;
    sidebar.querySelectorAll('.cys-sb-submenu').forEach(function (s) {
      s.style.removeProperty('--fly-left');
      s.style.removeProperty('--fly-top');
    });
  }

  function configurarModoMini() {
    aplicarModoMini(leerPrefMini());

    const btn = sidebar.querySelector('#btnMiniSidebar');
    if (btn) {
      btn.addEventListener('click', function () {
        aplicarModoMini(!miniActivo);
        guardarPrefMini(miniActivo);
      });
    }

    // Posiciona el flyout al entrar a un grupo (una sola vez por hover)
    sidebar.addEventListener('mouseover', function (e) {
      if (!miniActivo) return;
      const wrap = e.target.closest('.cys-sb-inventario-wrap');
      if (wrap && wrap !== wrapHover) {
        wrapHover = wrap;
        posicionarFlyout(wrap);
      }
    });
    sidebar.addEventListener('mouseout', function (e) {
      const wrap = e.target.closest('.cys-sb-inventario-wrap');
      if (wrap && wrap === wrapHover && !wrap.contains(e.relatedTarget)) wrapHover = null;
    });
    // Si se hace scroll en el aside con el flyout abierto, seguirlo
    sidebar.addEventListener('scroll', function () {
      if (miniActivo && wrapHover) posicionarFlyout(wrapHover);
    }, true);
  }

  // ══════════════════════════════════════════
  // LINKS "#" (Inventario, Ayuda)
  // ══════════════════════════════════════════
  function configurarLinks() {
    sidebar.addEventListener('click', function (e) {
      const a = e.target.closest('a[href="#"]');
      if (!a) return;
      e.preventDefault();
      // En modo normal, clic en la etiqueta = abrir/cerrar su submenú
      if (!miniActivo) {
        const wrap = a.closest('.cys-sb-inventario-wrap');
        const toggle = wrap ? wrap.querySelector('.sb-submenu-toggle') : null;
        if (toggle) toggle.click();
      }
    });
  }

  // ══════════════════════════════════════════
  // LINK ACTIVO + SUBMENÚ ABIERTO SEGÚN LA URL
  // ══════════════════════════════════════════
  // 'active'      = la página actual ES este link (caja resaltada)
  // 'activo-hijo'  = la página actual es un hijo de este padre (solo cambia el color)
  function marcar(el, clase) {
    if (!el) return;
    el.classList.add(clase || 'active');
    el.dataset.cysActivo = '1';
  }

  function abrirGrupo(id) {
    const sub = sidebar.querySelector('#' + id);
    if (!sub) return;
    const wrap   = sub.closest('.cys-sb-inventario-wrap');
    const parent = wrap ? wrap.querySelector('.cys-sb-link--parent') : null;
    if (!sub.classList.contains('abierto')) {
      sub.classList.add('abierto');
      if (parent) parent.classList.add('abierto');
      sub.dataset.cysAuto = '1';   // lo abrió la URL, no el usuario
    }
  }

  function cerrarGrupoAuto(id) {
    const sub = sidebar.querySelector('#' + id);
    if (!sub || sub.dataset.cysAuto !== '1') return;   // si el usuario lo tocó, se respeta
    const wrap   = sub.closest('.cys-sb-inventario-wrap');
    const parent = wrap ? wrap.querySelector('.cys-sb-link--parent') : null;
    sub.classList.remove('abierto');
    if (parent) parent.classList.remove('abierto');
    delete sub.dataset.cysAuto;
  }

  function actualizarActivo(forzar) {
    const actual = normalizar(window.location.pathname);
    if (!forzar && actual === rutaAnterior) return;   // misma ruta: no tocar nada
    rutaAnterior = actual;

    // 1) Limpiar marcas previas de este script
    sidebar.querySelectorAll('[data-cys-activo]').forEach(function (el) {
      el.classList.remove('active', 'activo-hijo');
      delete el.dataset.cysActivo;
    });

    // 2) Mejor coincidencia por href (gana el href más largo)
    let mejor = null, mejorLen = -1;
    sidebar.querySelectorAll('a.cys-sb-link[href], a.cys-sb-sublink[href], a.sb-link-flex-grow[href]').forEach(function (a) {
      const href = a.getAttribute('href');
      if (!href || href.charAt(0) === '#') return;
      let ruta;
      try { ruta = normalizar(new URL(href, window.location.origin).pathname); }
      catch (err) { return; }
      const coincide = ruta === '/'
        ? actual === '/'
        : (actual === ruta || actual.indexOf(ruta) === 0);
      if (coincide && ruta.length > mejorLen) { mejor = a; mejorLen = ruta.length; }
    });

    // 3) Marcar y averiguar a qué grupo (submenú) pertenece
    let idGrupo = null;
    if (mejor) {
      const wrap = mejor.closest('.cys-sb-inventario-wrap');
      if (wrap) {
        const sub    = wrap.querySelector('.cys-sb-submenu');
        const parent = wrap.querySelector('.cys-sb-link--parent');
        idGrupo = sub ? sub.id : null;
        if (mejor.classList.contains('cys-sb-sublink')) {
          marcar(mejor, 'active');          // el sublink actual
          marcar(parent, 'activo-hijo');    // el padre solo cambia de color
        } else {
          marcar(parent, 'active');         // estamos en la página del padre
        }
      } else {
        marcar(mejor, 'active');
      }
    }

    // Si por href no se encontró grupo, probar con los prefijos manuales
    if (!idGrupo) {
      const ids = Object.keys(RUTAS_SUBMENU);
      for (let i = 0; i < ids.length; i++) {
        const hit = RUTAS_SUBMENU[ids[i]].some(function (p) { return actual.indexOf(p) === 0; });
        if (hit) { idGrupo = ids[i]; break; }
      }
      if (idGrupo) {
        const sub  = sidebar.querySelector('#' + idGrupo);
        const wrap = sub ? sub.closest('.cys-sb-inventario-wrap') : null;
        marcar(wrap ? wrap.querySelector('.cys-sb-link--parent') : null, 'activo-hijo');
      }
    }

    // 4) Cerrar el grupo que abrió la URL anterior y abrir el actual
    if (grupoAuto && grupoAuto !== idGrupo) cerrarGrupoAuto(grupoAuto);
    if (idGrupo) abrirGrupo(idGrupo);
    grupoAuto = idGrupo;
  }

  // ══════════════════════════════════════════
  // OFFCANVAS + LOGOUT
  // ══════════════════════════════════════════
  function configurarOffcanvas() {
    sidebar.addEventListener('show.bs.offcanvas', function () { document.body.classList.add('sidebar-open'); });
    sidebar.addEventListener('hide.bs.offcanvas', function () { document.body.classList.remove('sidebar-open'); });
    if (sidebar.classList.contains('show')) document.body.classList.add('sidebar-open');
  }

  function configurarLogout() {
    const logoutLink = sidebar.querySelector('.cys-sb-link--logout');
    const overlay    = document.getElementById('cysLogoutOverlay');
    if (!logoutLink || !overlay) return;
    logoutLink.addEventListener('click', function (e) {
      e.preventDefault();
      const destino = logoutLink.getAttribute('href');
      overlay.classList.add('activo');
      setTimeout(function () { window.location.href = destino; }, 600);
    });
  }

  // ══════════════════════════════════════════
  // INICIALIZACIÓN
  // ══════════════════════════════════════════
  function init() {
    const el = document.getElementById('sidebarRight');
    if (!el) return;

    // Ya inicializado (navegación htmx con hx-preserve): solo refrescar el estado activo
    if (el.dataset.cysAsideInit === '1') {
      sidebar = el;
      seguro('activo', function () { actualizarActivo(false); });
      return;
    }

    sidebar = el;
    el.dataset.cysAsideInit = '1';
    rutaAnterior = null;
    grupoAuto = null;

    seguro('resumen',    function () { actualizarResumenWrap(leerCfg().resumenSidebar); });
    seguro('flyouts',    prepararFlyouts);
    seguro('tooltips',   inicializarTooltips);
    seguro('modo mini',  configurarModoMini);
    seguro('links',      configurarLinks);
    seguro('activo',     function () { actualizarActivo(true); });
    seguro('offcanvas',  configurarOffcanvas);
    seguro('logout',     configurarLogout);
  }

  // Listeners globales (una sola vez): navegación htmx / historial / configuración
  function registrarGlobales() {
    if (window.__cysAsideGlobales) return;
    window.__cysAsideGlobales = true;

    const refrescar = function () { setTimeout(init, 0); };
    ['htmx:afterSettle', 'htmx:pushedIntoHistory', 'htmx:replacedInHistory', 'htmx:historyRestore'].forEach(function (ev) {
      document.addEventListener(ev, refrescar);
    });
    window.addEventListener('popstate', refrescar);

    // Si el servidor responde 4xx/5xx a un link del aside, htmx NO cambia la página
    // y el clic parece "no hacer nada". Se repite como navegación normal para que
    // Django muestre su página de error (con el traceback si DEBUG está activo).
    document.addEventListener('htmx:responseError', function (e) {
      const d   = e.detail || {};
      const xhr = d.xhr || {};
      const cfg = d.requestConfig || {};
      const url = xhr.responseURL || (d.pathInfo && (d.pathInfo.finalRequestPath || d.pathInfo.requestPath));
      console.error('[CYS] El servidor respondió ' + xhr.status + ' al cargar ' + url);
      const desdeAside = !!(sidebar && d.elt && sidebar.contains(d.elt));
      const esGet = !cfg.verb || String(cfg.verb).toLowerCase() === 'get';
      if (url && esGet && (cfg.boosted || desdeAside)) window.location.assign(url);
    });

    // Cubre cualquier navegación que cambie la URL sin recargar (pushState / replaceState)
    ['pushState', 'replaceState'].forEach(function (fn) {
      const original = history[fn];
      history[fn] = function () {
        const r = original.apply(this, arguments);
        refrescar();
        return r;
      };
    });

    // Cambios desde la página de Configuración (sin recargar)
    window.addEventListener('cys-config-changed', function (e) {
      if (!sidebar) return;
      const d = e.detail || {};
      actualizarResumenWrap(d.resumenSidebar);
      if (typeof d.sidebarMini === 'boolean' && d.sidebarMini !== miniActivo) {
        aplicarModoMini(d.sidebarMini);
      }
    });
  }

  function arrancar() {
    registrarGlobales();
    init();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', arrancar);
  } else {
    arrancar();
  }
})();