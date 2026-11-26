/* ============================================================
   aside.js — Barra lateral CYS
   ------------------------------------------------------------
   - Modo compacto (solo íconos) con flyouts de submenú estables
   - Lado del aside (izquierda / derecha) configurable desde
     Configuración: cambia la clase del offcanvas, el lado del flyout,
     el lado de los tooltips y las variables de espacio del contenido
   - Tooltips de Bootstrap SOLO en modo compacto (en modo normal
     las etiquetas ya están visibles)
   - Al cerrar el aside se ocultan sus tooltips (si no, el de la
     equis se queda "volando" porque el botón desaparece antes de
     que el mouse lo "abandone")
   - El grupo del submenú de la página actual queda abierto, también
     cuando se navega con htmx (el aside usa hx-preserve y el script
     no se vuelve a ejecutar en cada navegación)
   ============================================================ */
(function () {
  'use strict';

  const KEY_MINI   = 'cys_sidebar_mini';
  const KEY_LADO   = 'cys_aside_lado';
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
  let ladoActual   = 'derecha';  // 'derecha' | 'izquierda'
  let tipsNav      = [];     // tooltips de la navegación (solo activos en modo compacto)
  let tipMini      = null;   // tooltip del botón compacto/expandido
  let rutaAnterior = null;   // última ruta procesada (evita reabrir grupos cerrados a mano)
  let grupoAuto    = null;   // id del submenú abierto automáticamente por la URL
  let wrapHover    = null;   // grupo bajo el mouse en modo compacto
  let flipTimer    = null;

  const normalizar = p => (p || '').replace(/\/+$/, '') || '/';
  const ladoValido = v => v === 'izquierda' || v === 'derecha';

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

  function leerLado() {
    try {
      const dedicado = localStorage.getItem(KEY_LADO);
      if (ladoValido(dedicado)) return dedicado;
    } catch (e) {}
    return leerCfg().asideLado === 'izquierda' ? 'izquierda' : 'derecha';
  }

  function actualizarResumenWrap(visible) {
    const wrap = document.getElementById('cys-sb-resumen-wrap');
    if (wrap) wrap.classList.toggle('cys-sb-resumen-oculto', visible === false);
  }

  // ══════════════════════════════════════════
  // LADO DEL ASIDE
  // ══════════════════════════════════════════
  // Variables que usa el CSS del contenido para dejar el hueco del aside
  function actualizarOffsets() {
    const root = document.documentElement;
    const off  = miniActivo ? ANCHO_MINI : ANCHO_FULL;
    root.style.setProperty('--sidebar-offset', off);
    root.style.setProperty('--sidebar-offset-izq', ladoActual === 'izquierda' ? off : '0px');
    root.style.setProperty('--sidebar-offset-der', ladoActual === 'derecha' ? off : '0px');
  }

  // Solo DOM: atributo en <html> + clase de Bootstrap del offcanvas
  function pintarLado(lado) {
    document.documentElement.setAttribute('data-aside-lado', lado);
    if (!sidebar) return;
    sidebar.classList.toggle('offcanvas-end', lado === 'derecha');
    sidebar.classList.toggle('offcanvas-start', lado === 'izquierda');
  }

  // El chevron del botón compacto se espeja según el lado
  function actualizarIconoMini() {
    if (!sidebar) return;
    const btn   = sidebar.querySelector('#btnMiniSidebar');
    const icono = btn ? btn.querySelector('i') : null;
    if (!icono) return;
    // Derecha: expandido «, compacto ».  Izquierda: expandido », compacto «.
    const apuntaIzq = (ladoActual === 'derecha') ? !miniActivo : miniActivo;
    icono.classList.toggle('bi-chevron-double-left', apuntaIzq);
    icono.classList.toggle('bi-chevron-double-right', !apuntaIzq);
  }

  function limpiarFlyouts() {
    wrapHover = null;
    if (!sidebar) return;
    sidebar.querySelectorAll('.cys-sb-submenu').forEach(function (s) {
      s.style.removeProperty('--fly-left');
      s.style.removeProperty('--fly-top');
    });
  }

  // Cambio de lado en caliente (desde Configuración u otra pestaña)
  function aplicarLado(lado) {
    if (!ladoValido(lado)) return;
    const cambio = lado !== ladoActual;
    ladoActual = lado;
    pintarLado(lado);
    if (!sidebar) return;

    actualizarOffsets();
    if (!cambio) return;

    // Tooltips: cambian de lado (izquierda ↔ derecha)
    inicializarTooltips();
    crearTipMini(miniActivo ? 'Modo expandido' : 'Modo compacto');
    aplicarEstadoTooltips();
    actualizarIconoMini();
    limpiarFlyouts();

    // Animación de entrada por el nuevo borde (solo si está visible)
    if (sidebar.classList.contains('show')) {
      sidebar.classList.remove('cys-sb-flip');
      void sidebar.offsetWidth;   // reinicia la animación
      sidebar.classList.add('cys-sb-flip');
      clearTimeout(flipTimer);
      flipTimer = setTimeout(function () { sidebar.classList.remove('cys-sb-flip'); }, 350);
    }
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
  // Aquí se calcula dónde va: hacia el lado libre del ícono (izquierda si el
  // aside está a la derecha, derecha si está a la izquierda), alineado con su
  // fila, y subido lo justo si no cabe hacia abajo.
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

    let left;
    if (ladoActual === 'izquierda') {
      left = Math.min(window.innerWidth - w - margen, r.right + gap);
    } else {
      left = Math.max(margen, r.left - gap - w);
    }

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
    tipsNav.forEach(function (t) { try { t.dispose(); } catch (err) {} });
    tipsNav = [];
    tipMini = null;
    if (!window.bootstrap || !bootstrap.Tooltip) return;

    // Los tooltips de navegación salen hacia el lado libre del aside
    const ladoTip   = ladoActual === 'izquierda' ? 'right' : 'left';
    const fallbacks = ladoActual === 'izquierda'
      ? ['right', 'top', 'bottom']
      : ['left', 'top', 'bottom'];

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

        const tip = new bootstrap.Tooltip(el, {
          trigger: 'hover',
          placement: ladoTip,
          fallbackPlacements: fallbacks,
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

  // Tooltips de navegación: solo en modo compacto
  function aplicarEstadoTooltips() {
    tipsNav.forEach(function (t) {
      if (miniActivo) { t.enable(); }
      else            { t.hide(); t.disable(); }
    });
  }

  // Oculta TODOS los tooltips del aside y limpia los que quedaron en <body>.
  // Se usa al cerrar el aside: el botón (equis) desaparece bajo el mouse y
  // nunca recibe "mouseleave", así que su tooltip se quedaba flotando.
  function ocultarTooltipsAside() {
    if (sidebar && window.bootstrap && bootstrap.Tooltip) {
      sidebar.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        const t = bootstrap.Tooltip.getInstance(el);
        if (t) { try { t.hide(); } catch (err) {} }
      });
    }
    document.querySelectorAll('.tooltip').forEach(function (t) { t.remove(); });
  }

  // ══════════════════════════════════════════
  // MODO COMPACTO
  // ══════════════════════════════════════════
  function aplicarModoMini(activo) {
    miniActivo = activo;
    sidebar.classList.toggle('cys-sb-mini', activo);

    if (activo) sidebar.style.setProperty('width', ANCHO_MINI, 'important');
    else        sidebar.style.removeProperty('width');

    actualizarOffsets();
    actualizarIconoMini();

    const btn   = sidebar.querySelector('#btnMiniSidebar');
    const texto = activo ? 'Modo expandido' : 'Modo compacto';
    if (btn) {
      btn.setAttribute('aria-label', texto);
      if (tipMini) crearTipMini(texto);
    }

    aplicarEstadoTooltips();

    // Limpia ajustes de posición de flyouts anteriores
    limpiarFlyouts();
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
    sidebar.addEventListener('hide.bs.offcanvas', function () {
      document.body.classList.remove('sidebar-open');
      // Al cerrar con la equis, su tooltip no debe quedarse flotando
      ocultarTooltipsAside();
    });
    // Por si el mouse vuelve a quedar sobre el botón durante la animación de cierre
    sidebar.addEventListener('hidden.bs.offcanvas', ocultarTooltipsAside);
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

    // Ya inicializado (navegación htmx con hx-preserve): refrescar activo y lado
    if (el.dataset.cysAsideInit === '1') {
      sidebar = el;
      seguro('lado',   function () { const l = leerLado(); if (l !== ladoActual) aplicarLado(l); else pintarLado(l); });
      seguro('activo', function () { actualizarActivo(false); });
      return;
    }

    sidebar = el;
    el.dataset.cysAsideInit = '1';
    rutaAnterior = null;
    grupoAuto = null;

    // El lado se fija ANTES de crear tooltips y calcular offsets
    seguro('lado',       function () { ladoActual = leerLado(); pintarLado(ladoActual); });
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
      if (ladoValido(d.asideLado) && d.asideLado !== ladoActual) {
        aplicarLado(d.asideLado);
      }
    });

    // Cambio de lado hecho en otra pestaña
    window.addEventListener('storage', function (e) {
      if (!sidebar || e.key !== KEY_LADO) return;
      if (ladoValido(e.newValue) && e.newValue !== ladoActual) aplicarLado(e.newValue);
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