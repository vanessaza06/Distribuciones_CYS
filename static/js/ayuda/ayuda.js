// ══════════════════════════════════════════
// ayuda.js — CYS Ltda
// Búsqueda en vivo + Asistente Virtual (Chatbot CYS)
// ══════════════════════════════════════════

let aydCategoriaActiva = 'todas';

function aydFiltrarCategoria(btn) {
  document.querySelectorAll('.ayd-cat-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  aydCategoriaActiva = btn.dataset.cat;
  aydAplicarFiltros();
}

function aydAplicarFiltros() {
  const texto = (document.getElementById('ayd-buscador')?.value || '').trim().toLowerCase();
  const items = document.querySelectorAll('.ayd-item');
  let visibles = 0;

  items.forEach(item => {
    const coincideCat = aydCategoriaActiva === 'todas' || item.dataset.cat === aydCategoriaActiva;
    const coincideTexto = !texto || (item.dataset.texto || '').includes(texto);
    const mostrar = coincideCat && coincideTexto;
    item.classList.toggle('ayd-oculto', !mostrar);
    if (mostrar) visibles++;
  });

  const sinResultados = document.getElementById('ayd-sin-resultados');
  if (sinResultados) {
    sinResultados.classList.toggle('d-none', visibles !== 0);
  }
}

// ══════════════════════════════════════════
// CHATBOT ENGINE — CYS
// ══════════════════════════════════════════

const BOT_KNOWLEDGE = [
  {
    keys: ['venta', 'vender', 'pos', 'factura', 'caja registradora', 'descuento', 'cliente', 'despacho'],
    respuesta: `<strong>🛒 Módulo de Ventas / POS:</strong><br>
    1. Dirígete a <strong>Ventas</strong> desde el menú principal.<br>
    2. Selecciona un cliente registrado o déjalo en <em>Consumidor Final</em>.<br>
    3. Agrega los productos desde el buscador o el catálogo.<br>
    4. Ingresa el desglose de pago (Efectivo, Nequi, Daviplata, Tarjeta o Transferencia).<br>
    5. Haz clic en <strong>Confirmar Venta</strong> para registrar la transacción e imprimir el comprobante.`
  },
  {
    keys: ['devolucion', 'devolver', 'reembolso', 'devoluciones', 'motivo', 'cambio'],
    respuesta: `<strong>🔄 Módulo de Devoluciones:</strong><br>
    1. Ve al módulo <strong>Devoluciones</strong>.<br>
    2. Selecciona la venta original o busca el código de factura.<br>
    3. Selecciona el ítem y la cantidad a devolver, indicando el motivo.<br>
    4. Elige si deseas <strong>restaurar el stock</strong> al inventario y el método de reembolso.<br>
    5. Confirma la devolución. El saldo y el reporte del día se actualizarán automáticamente.`
  },
  {
    keys: ['caja', 'apertura', 'cierre', 'arqueo', 'billetes', 'monedas', 'franja', 'hora pico'],
    respuesta: `<strong>💰 Gestión de Caja y Arqueo:</strong><br>
    1. En el módulo <strong>Caja</strong>, puedes realizar la <strong>Apertura de Turno</strong> ingresando el desglose de billetes y monedas iniciales.<br>
    2. Puedes monitorear el flujo de ventas por franjas horarias y la hora pico de facturación.<br>
    3. Al finalizar la jornada, realiza el <strong>Cierre de Caja</strong> con el conteo final para comparar el efectivo real contra el sistema.`
  },
  {
    keys: ['metodo', 'metodos', 'transaccion', 'bancolombia', 'nequi', 'daviplata', 'efectivo', 'pago'],
    respuesta: `<strong>💳 Métodos de Pago:</strong><br>
    1. Ingresa a <strong>Métodos de Pago</strong> para consultar el consolidado diario.<br>
    2. Podrás visualizar el recaudo desglosado en efectivo y transferencias electrónicas.<br>
    3. Puedes registrar pagos independientes o vincular abonos directos a órdenes de compras.`
  },
  {
    keys: ['stock', 'inventario', 'producto', 'existencias', 'presentacion', 'lote'],
    respuesta: `<strong>📦 Inventario y Productos:</strong><br>
    1. Ingresa a <strong>Inventario</strong> para consultar el stock disponible por producto y presentación.<br>
    2. Podrás verificar los lotes activados y las alertas de stock mínimo.<br>
    3. Al registrar ventas o devoluciones, las existencias se recalculan inmediatamente.`
  },
  {
    keys: ['compra', 'proveedor', 'orden', 'mercancia', 'pedido'],
    respuesta: `<strong>🚚 Compras a Proveedores:</strong><br>
    1. Dirígete a <strong>Compras</strong>.<br>
    2. Elige el proveedor, agrega los artículos comprados e ingresa el valor o saldo.<br>
    3. Al confirmar la recepción, el inventario aumentará automáticamente con la nueva mercancía.`
  },
  {
    keys: ['anular', 'cancelar', 'eliminar'],
    respuesta: `<strong>⚠️ Anulación de Registros:</strong><br>
    Para anular una venta o registro de pago, debes contar con permisos administrativos o de supervisor. Puedes gestionarlo directamente en la tabla de detalle de la venta o pago correspondiente.`
  }
];

function aydAbrirChatbot() {
  const modalEl = document.getElementById('modalChatbotAyuda');
  if (modalEl && window.bootstrap) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}

function aydIniciarChatDuda(titulo, contenido) {
  aydAbrirChatbot();
  setTimeout(() => {
    const preg = `Tengo una duda sobre: ${titulo}`;
    aydAgregarMensaje(preg, 'user');
    aydSimularRespuestaBot(`Respondiendo a tu consulta sobre <strong>"${titulo}"</strong>:<br><br>${contenido}`);
  }, 300);
}

function aydAgregarMensaje(texto, sender = 'bot') {
  const container = document.getElementById('ayd-chat-messages');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `ayd-msg ayd-msg-${sender}`;

  const isBot = sender === 'bot';
  const avatarHtml = isBot ? `<div class="ayd-chat-avatar"><img src="/static/img/mascota_cerveza.png?v=2" alt="CYS Mascota"></div>` : '';

  msgDiv.innerHTML = `
    ${avatarHtml}
    <div class="ayd-msg-bubble">
      ${texto}
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function aydSimularRespuestaBot(textoHTML) {
  const container = document.getElementById('ayd-chat-messages');
  if (!container) return;

  // Typing Indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'ayd-msg ayd-msg-bot ayd-typing-ind';
  typingDiv.innerHTML = `
    <div class="ayd-chat-avatar"><img src="/static/img/mascota_cerveza.png?v=2" alt="CYS Mascota"></div>
    <div class="ayd-msg-bubble text-muted small" style="font-style:italic;">
      <i class="bi bi-three-dots"></i> Escribiendo respuesta...
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  setTimeout(() => {
    typingDiv.remove();
    aydAgregarMensaje(textoHTML, 'bot');
  }, 600);
}

function aydEnviarMensajeChat(evt) {
  if (evt) evt.preventDefault();
  const input = document.getElementById('ayd-chat-input-text');
  if (!input) return;

  const query = input.value.trim();
  if (!query) return;

  aydAgregarMensaje(query, 'user');
  input.value = '';

  // Buscar coincidencia en BOT_KNOWLEDGE
  const queryLower = query.toLowerCase();
  let encontrada = null;

  for (const item of BOT_KNOWLEDGE) {
    if (item.keys.some(k => queryLower.includes(k))) {
      encontrada = item.respuesta;
      break;
    }
  }

  if (encontrada) {
    aydSimularRespuestaBot(encontrada);
  } else {
    aydSimularRespuestaBot(`Entiendo tu consulta sobre <em>"${query}"</em>.<br><br>
    Te sugiero revisar las guías rápidas o escribirnos tu mensaje directamente en el formulario de <strong>Contacto y Soporte</strong> al final de esta página para que un asesor te asista personalmente.`);
  }
}

function aydLimpiarChat() {
  const container = document.getElementById('ayd-chat-messages');
  if (!container) return;
  container.innerHTML = `
    <div class="ayd-msg ayd-msg-bot">
      <div class="ayd-chat-avatar"><img src="/static/img/mascota_cerveza.png?v=2" alt="CYS Mascota"></div>
      <div class="ayd-msg-bubble">
        <strong>👋 Chat reiniciado.</strong> ¿En qué más te puedo colaborar hoy? Selecciona un tema sugerido o escribe tu pregunta abajo.
      </div>
    </div>
  `;
}

document.addEventListener('DOMContentLoaded', () => {
  const buscador = document.getElementById('ayd-buscador');
  if (buscador) {
    buscador.addEventListener('input', aydAplicarFiltros);
  }

  const chatForm = document.getElementById('ayd-chat-form');
  if (chatForm) {
    chatForm.addEventListener('submit', aydEnviarMensajeChat);
  }
});