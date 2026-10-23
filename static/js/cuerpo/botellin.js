// botellin.js — Botellín (mascota + chat con IA) · CYS Ltda
(function () {
  'use strict';

  const wrap = document.getElementById('botellin');
  if (!wrap) return;

  const mascota   = document.getElementById('bot-mascota');
  const burbuja   = document.getElementById('bot-burbuja');
  const chat      = document.getElementById('bot-chat');
  const cuerpo    = document.getElementById('bot-body');
  const form      = document.getElementById('bot-form');
  const input     = document.getElementById('bot-input');
  const btnEnv    = document.getElementById('bot-enviar');
  const btnCerrar = document.getElementById('bot-cerrar');

  const URL_CHAT = wrap.dataset.url;
  const CSRF     = wrap.dataset.csrf;
  const IMG_CARA = wrap.dataset.imgCara;

  const SUGERENCIAS = [
    '¿Cómo creo un usuario?',
    '¿Cómo creo un producto?',
    '¿Cómo hago una venta?',
    '¿Cómo registro una devolución?'
  ];

  let abierto = false, enviando = false, saludoInicial = false, timerBurbuja = null;
  let historial = [];        // [{role:'user'|'assistant', content:'...'}]
  let contextoExtra = '';    // guía/FAQ desde la que se abrió el chat

  function esc(t) {
    return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function formatear(t) {
    return esc(t)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }
  function bajar() { cuerpo.scrollTop = cuerpo.scrollHeight; }

  function agregarMensaje(rol, texto) {
    const div = document.createElement('div');
    div.className = 'bot-msg ' + (rol === 'user' ? 'bot-msg-user' : 'bot-msg-bot');
    if (rol !== 'user') {
      const av = document.createElement('img');
      av.className = 'bot-msg-avatar'; av.src = IMG_CARA; av.alt = '';
      div.appendChild(av);
    }
    const b = document.createElement('div');
    b.className = 'bot-msg-burbuja';
    b.innerHTML = rol === 'user' ? esc(texto) : formatear(texto);
    div.appendChild(b);
    cuerpo.appendChild(div);
    // las respuestas del bot se leen desde el inicio; tus mensajes bajan al final
    div.scrollIntoView({ block: rol === 'user' ? 'end' : 'start', behavior: 'smooth' });
  }

  function mostrarSugerencias() {
    const box = document.createElement('div');
    box.className = 'bot-sugerencias';
    SUGERENCIAS.forEach(function (s) {
      const c = document.createElement('button');
      c.type = 'button'; c.className = 'bot-chip'; c.textContent = s;
      c.addEventListener('click', function () { box.remove(); enviar(s); });
      box.appendChild(c);
    });
    cuerpo.appendChild(box);
    bajar();
  }

  function indicadorEscribiendo() {
    const div = document.createElement('div');
    div.className = 'bot-msg bot-msg-bot bot-escribiendo';
    div.innerHTML = '<img class="bot-msg-avatar" src="' + IMG_CARA + '" alt="">' +
                    '<div class="bot-msg-burbuja"><span></span><span></span><span></span></div>';
    cuerpo.appendChild(div);
    bajar();
    return div;
  }

  /* ── animación de la mascota ── */
  function setEstado(clase) {
    wrap.classList.remove('bot-intro', 'bot-regreso');
    if (clase) wrap.classList.add(clase);
  }
  function mostrarBurbuja(ms) {
    clearTimeout(timerBurbuja);
    burbuja.classList.add('visible');
    timerBurbuja = setTimeout(function () { burbuja.classList.remove('visible'); }, ms);
  }
    /* ── tapa de la cerveza: sale volando al abrir el chat ── */
  const imgReposo  = mascota.querySelector('.bot-img-reposo');
  const reducirMov = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const IMG_W = 481, IMG_H = 640;   // tamaño real de botellin_reposo.png
  // borde inferior de la tapa (coordenadas de la imagen original)
  const LINEA = [[-20, 62], [120, 59], [167, 44], [232, 37], [500, 37]];
  // bolitas de espuma: [x, y, radio]
  const ESPUMA = [[140, 54, 12], [155, 48, 13], [170, 43, 14], [186, 41, 14], [202, 39, 13],
                  [217, 38, 12], [150, 40, 11], [165, 32, 12], [182, 26, 13], [198, 28, 12],
                  [212, 30, 11], [172, 16, 9], [190, 14, 8]];
  let fx = null, timerTapa = null;

  function geometria() {
    const w = imgReposo.offsetWidth, h = imgReposo.offsetHeight;
    const s = Math.min(w / IMG_W, h / IMG_H);
    return { w: w, h: h, s: s, left: imgReposo.offsetLeft, top: imgReposo.offsetTop,
             lx: (w - IMG_W * s) / 2, ly: (h - IMG_H * s) / 2 };
  }
  function poligono(g, arriba) {
    const cierre = arriba ? [[500, -20], [-20, -20]] : [[500, 700], [-20, 700]];
    return 'polygon(' + LINEA.concat(cierre).map(function (p) {
      return (g.lx + p[0] * g.s).toFixed(1) + 'px ' + (g.ly + p[1] * g.s).toFixed(1) + 'px';
    }).join(',') + ')';
  }
  function aBoton(g, x, y) {          // punto de la imagen -> px dentro del botón
    return [g.left + g.lx + x * g.s, g.top + g.ly + y * g.s];
  }

  function ponerTapa() {              // deja todo como al inicio (tapa puesta)
    clearTimeout(timerTapa);
    if (fx) { fx.remove(); fx = null; }
    if (imgReposo) imgReposo.style.clipPath = '';
  }

  function quitarTapa() {
    if (!imgReposo) return;
    clearTimeout(timerTapa);
    timerTapa = setTimeout(function () {       // espera a que aparezca la pose del guiño
      if (!abierto || !imgReposo.offsetWidth) return;
      ponerTapa();
      if (getComputedStyle(mascota).position === 'static') mascota.style.position = 'relative';
      const g = geometria();
      fx = document.createElement('span');
      fx.className = 'bot-tapa-fx';
      mascota.appendChild(fx);

      // 1) la botella pierde la tapa
      imgReposo.style.clipPath = poligono(g, false);

      // 2) corona de espuma
      ESPUMA.forEach(function (e, i) {
        const c = aBoton(g, e[0], e[1]);
        const r = Math.max(2.5, e[2] * g.s * 1.5);
        const d = document.createElement('i');
        d.className = 'bot-espuma';
        d.style.cssText = 'left:' + (c[0] - r) + 'px;top:' + (c[1] - r) + 'px;width:' + (2 * r) +
                          'px;height:' + (2 * r) + 'px;animation-delay:' + (i * 25) + 'ms';
        fx.appendChild(d);
      });

      if (reducirMov) return;

      // 3) gotitas que salen disparadas
      const boca = aBoton(g, 178, 36);
      for (let i = 0; i < 10; i++) {
        const t = 2 + Math.random() * 3;
        const gota = document.createElement('i');
        gota.className = 'bot-gota';
        gota.style.cssText = 'left:' + (boca[0] - t / 2) + 'px;top:' + (boca[1] - t / 2) +
                             'px;width:' + t + 'px;height:' + t + 'px';
        fx.appendChild(gota);
        const dx = (Math.random() - 0.5) * g.h * 0.7;
        const dy = -(0.2 + Math.random() * 0.5) * g.h;
        gota.animate([
          { transform: 'translate(0,0) scale(1)', opacity: 1 },
          { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(1)', opacity: 1, offset: 0.55 },
          { transform: 'translate(' + dx * 1.25 + 'px,' + (dy + g.h * 0.35) + 'px) scale(.6)', opacity: 0 }
        ], { duration: 700 + Math.random() * 500, easing: 'ease-out', fill: 'forwards' })
          .onfinish = function () { gota.remove(); };
      }

      // 4) la tapa sale volando
      const tapa = new Image();
      tapa.src = imgReposo.currentSrc || imgReposo.src;
      tapa.alt = ''; tapa.draggable = false; tapa.className = 'bot-tapa';
      tapa.style.cssText = 'left:' + g.left + 'px;top:' + g.top + 'px;width:' + g.w + 'px;height:' +
                           g.h + 'px;clip-path:' + poligono(g, true) + ';transform-origin:' +
                           (g.lx + 178 * g.s) + 'px ' + (g.ly + 28 * g.s) + 'px';
      fx.appendChild(tapa);
      tapa.animate([
        { transform: 'translate(0,0) rotate(0deg)', opacity: 1, easing: 'cubic-bezier(.2,.8,.3,1)' },
        { transform: 'translate(' + g.h * 0.1 + 'px,' + (-g.h * 0.7) + 'px) rotate(260deg)',
          opacity: 1, offset: 0.45, easing: 'cubic-bezier(.5,0,.9,.5)' },
        { transform: 'translate(' + g.h * 0.28 + 'px,' + g.h * 0.15 + 'px) rotate(560deg)', opacity: 0 }
      ], { duration: 1100, fill: 'forwards' }).onfinish = function () { tapa.remove(); };
    }, 250);
  }
    /* ── que el chat nunca se salga por arriba de la pantalla ── */
  function ajustarAlto() {
    chat.style.maxHeight = '';                 // mide con su alto natural
    const pa = chat.offsetParent;
    if (!pa) return;
    // borde inferior del chat en pantalla (el chat crece hacia arriba desde ahí)
    const borde = pa.getBoundingClientRect().top + chat.offsetTop + chat.offsetHeight;
    chat.style.maxHeight = Math.max(240, borde - 12) + 'px';
  }
    /* ── que Botellín se corra según el aside (normal / compacto / cerrado) ── */
  const aside = document.getElementById('sidebarRight');

  function ajustarPosicion() {
    let ancho = 0;
    if (aside) {
      const r = aside.getBoundingClientRect();
      ancho = Math.max(0, window.innerWidth - r.left);   // 0 si el aside está cerrado
    }
    wrap.style.right = (ancho + 24) + 'px';
  }

  if (aside) {
    if (window.ResizeObserver) new ResizeObserver(ajustarPosicion).observe(aside);  // modo compacto
    ['show.bs.offcanvas', 'shown.bs.offcanvas', 'hidden.bs.offcanvas'].forEach(function (ev) {
      aside.addEventListener(ev, function () {            // abrir / cerrar el aside
        ajustarPosicion();
        setTimeout(ajustarPosicion, 350);
      });
    });
  }
  window.addEventListener('resize', ajustarPosicion);
  document.body.addEventListener('htmx:afterSettle', ajustarPosicion);

  const btnMini = document.getElementById('btnMiniSidebar');
  if (btnMini) btnMini.addEventListener('click', function () {
    setTimeout(ajustarPosicion, 60);
    setTimeout(ajustarPosicion, 450);
  });
    /* ── flecha: ocultar / mostrar a Botellín (se recuerda entre páginas) ── */
  const flecha = document.getElementById('bot-flecha');
  let oculto = false;
  try { oculto = localStorage.getItem('botellin_oculto') === '1'; } catch (e) {}

  function aplicarOculto(valor, animar) {
    oculto = valor;
    if (valor && abierto) cerrar();
    wrap.classList.toggle('bot-oculto', valor);
    if (flecha) {
      flecha.setAttribute('aria-expanded', String(!valor));
      flecha.setAttribute('aria-label', valor ? 'Mostrar a Botellín' : 'Ocultar a Botellín');
    }
    try { localStorage.setItem('botellin_oculto', valor ? '1' : '0'); } catch (e) {}
    if (!valor && animar) {              // al mostrarlo vuelve saludando
      setEstado(null);
      void wrap.offsetWidth;
      setEstado('bot-regreso');
    }
  }
  if (flecha) flecha.addEventListener('click', function () { aplicarOculto(!oculto, true); });
  aplicarOculto(oculto, false);

  /* ── abrir / cerrar ── */
    function abrir() {
    if (abierto) return;
    if (oculto) aplicarOculto(false, false);   // NUEVO: si estaba oculta, la muestra
    abierto = true;
    clearTimeout(timerBurbuja);
    burbuja.classList.remove('visible');
    setEstado(null);
    wrap.classList.add('bot-abierto');          // pose 2 (guiño)
    quitarTapa();                               // NUEVO: la tapa sale volando
    chat.hidden = false;
    ajustarAlto();                              // NUEVO: que el chat no se corte arriba
    mascota.setAttribute('aria-expanded', 'true');
    mascota.setAttribute('aria-label', 'Cerrar chat con Botellín');
    if (!saludoInicial) {
      saludoInicial = true;
      agregarMensaje('bot',
        '¡Hola! Soy **Botellín** 🍺 Te ayudo con cualquier duda del sistema de CYS: ' +
        'usuarios, productos, ventas, devoluciones, caja, compras…\n¿Qué necesitas?');
      mostrarSugerencias();
    }
    setTimeout(function () { input.focus(); }, 150);
  }

  function cerrar() {
    if (!abierto) return;
    abierto = false;
    chat.hidden = true;
    wrap.classList.remove('bot-abierto');       // vuelve a pose 1 (saludando)
    ponerTapa();                                // NUEVO: la tapa vuelve a su lugar
    setEstado('bot-regreso');
    mascota.setAttribute('aria-expanded', 'false');
    mascota.setAttribute('aria-label', 'Abrir chat con Botellín');
  }

  mascota.addEventListener('click', function () { abierto ? cerrar() : abrir(); });
  btnCerrar.addEventListener('click', cerrar);
  mascota.addEventListener('mouseenter', function () { if (!abierto) mostrarBurbuja(3500); });
  window.addEventListener('resize', function () { if (abierto) ajustarAlto(); });

  /* ── envío a la IA ── */
  async function enviar(texto) {
    texto = (texto || '').trim();
    if (!texto || enviando) return;
    enviando = true; btnEnv.disabled = true; input.value = '';

    agregarMensaje('user', texto);
    const typing = indicadorEscribiendo();
    const payload = { mensaje: texto, historial: historial.slice(-10), contexto: contextoExtra };
    contextoExtra = '';

    try {
      const resp = await fetch(URL_CHAT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });
      const data = await resp.json().catch(function () { return {}; });
      typing.remove();
      agregarMensaje('bot', data.respuesta ||
        'Uy, no pude responderte en este momento. Intenta de nuevo en un ratico 🙏');
      if (resp.ok && data.respuesta) {
        historial.push({ role: 'user', content: texto });
        historial.push({ role: 'assistant', content: data.respuesta });
      }
    } catch (err) {
      typing.remove();
      agregarMensaje('bot', 'No tengo conexión con el servidor ahora mismo. Revisa tu internet e intenta otra vez.');
    } finally {
      enviando = false; btnEnv.disabled = false; input.focus();
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault(); e.stopPropagation();
    enviar(input.value);
  });

  /* ── funciones globales que usan los botones de guías y FAQs de Ayuda ── */
  window.aydAbrirChatbot = abrir;
  window.aydIniciarChatDuda = function (titulo, contenido) {
    abrir();
    contextoExtra = 'Guía/FAQ que el usuario está leyendo — Título: ' + titulo +
                    '\nContenido: ' + String(contenido || '').slice(0, 1500);
    enviar('Tengo una duda sobre: "' + titulo + '". ¿Me lo explicas paso a paso?');
  };

  /* ── al cargar la página: aparece saludando ── */
  ajustarPosicion();                                                       
  requestAnimationFrame(function () { wrap.classList.add('bot-anim'); });   
    if (!oculto) {                                 // si la ocultaste, no saluda
    setEstado('bot-intro');
    setTimeout(function () { mostrarBurbuja(6000); }, 1000);
  }

  /* ── al entrar al módulo de Ayuda (navegación htmx): saluda de nuevo ── */
  document.body.addEventListener('htmx:afterSettle', function () {
      if (!abierto && !oculto && document.getElementById('ayd-buscador')) {
      setEstado(null);
      void wrap.offsetWidth;          // reinicia la animación
      setEstado('bot-regreso');
      mostrarBurbuja(5000);
    }
  });
})();