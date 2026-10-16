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

  /* ── abrir / cerrar ── */
  function abrir() {
    if (abierto) return;
    abierto = true;
    clearTimeout(timerBurbuja);
    burbuja.classList.remove('visible');
    setEstado(null);
    wrap.classList.add('bot-abierto');          // pose 2 (guiño)
    chat.hidden = false;
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
    setEstado('bot-regreso');
    mascota.setAttribute('aria-expanded', 'false');
    mascota.setAttribute('aria-label', 'Abrir chat con Botellín');
  }

  mascota.addEventListener('click', function () { abierto ? cerrar() : abrir(); });
  btnCerrar.addEventListener('click', cerrar);
  mascota.addEventListener('mouseenter', function () { if (!abierto) mostrarBurbuja(3500); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && abierto) cerrar(); });

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
  setEstado('bot-intro');
  setTimeout(function () { mostrarBurbuja(6000); }, 1000);

  /* ── al entrar al módulo de Ayuda (navegación htmx): saluda de nuevo ── */
  document.body.addEventListener('htmx:afterSettle', function () {
    if (!abierto && document.getElementById('ayd-buscador')) {
      setEstado(null);
      void wrap.offsetWidth;          // reinicia la animación
      setEstado('bot-regreso');
      mostrarBurbuja(5000);
    }
  });
})();