(function () {
  'use strict';

  const headerEl = document.querySelector('.cys-header');
  if (!headerEl) return;
  const URL_STOCK_STATUS = headerEl.dataset.urlStockStatus;
  if (!URL_STOCK_STATUS) return;

  const INTERVALO = 8000;

  // Claves de localStorage
  const KEY_HISTORIAL = 'cys_notif_historial';
  const KEY_VISTOS = 'cys_notif_vistos';
  const KEY_ARCHIVADAS = 'cys_notif_archivadas';
  const KEY_BORRADAS = 'cys_notif_borradas';

  let historialNotif = [];
  try {
    historialNotif = JSON.parse(localStorage.getItem(KEY_HISTORIAL) || '[]');
  } catch (e) {
    historialNotif = [];
  }

  let vistosPrevios = new Set();
  try {
    vistosPrevios = new Set(JSON.parse(localStorage.getItem(KEY_VISTOS) || '[]'));
  } catch (e) {
    vistosPrevios = new Set();
  }

  let archivadas = new Set();
  try {
    archivadas = new Set(JSON.parse(localStorage.getItem(KEY_ARCHIVADAS) || '[]'));
  } catch (e) {
    archivadas = new Set();
  }

  let borradas = new Set();
  try {
    borradas = new Set(JSON.parse(localStorage.getItem(KEY_BORRADAS) || '[]'));
  } catch (e) {
    borradas = new Set();
  }

  let ultimaData = null;
  let contadorPrevio = -1;

  const esc = (s) => String(s || '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  const fmtCOP = (n) => '$' + Math.round(Number(n) || 0).toLocaleString('es-CO');

  function guardarTodo() {
    try {
      localStorage.setItem(KEY_HISTORIAL, JSON.stringify(historialNotif.slice(0, 80)));
      localStorage.setItem(KEY_VISTOS, JSON.stringify([...vistosPrevios]));
      localStorage.setItem(KEY_ARCHIVADAS, JSON.stringify([...archivadas]));
      localStorage.setItem(KEY_BORRADAS, JSON.stringify([...borradas]));
    } catch (e) {
      console.warn('Error guardando en localStorage:', e);
    }
  }

  // ── PESTAÑAS ──
  window.notifTab = function (tab) {
    const esAlertas = tab === 'alertas';
    const esCompras = tab === 'compras';
    const esHistorial = tab === 'historial';

    const pAlertas = document.getElementById('panel-alertas');
    const pCompras = document.getElementById('panel-compras');
    const pHistorial = document.getElementById('panel-historial');

    if (pAlertas) pAlertas.classList.toggle('d-none', !esAlertas);
    if (pCompras) pCompras.classList.toggle('d-none', !esCompras);
    if (pHistorial) pHistorial.classList.toggle('d-none', !esHistorial);

    const tAlertas = document.getElementById('tab-alertas');
    const tCompras = document.getElementById('tab-compras');
    const tHistorial = document.getElementById('tab-historial');

    if (tAlertas) tAlertas.classList.toggle('active', esAlertas);
    if (tCompras) tCompras.classList.toggle('active', esCompras);
    if (tHistorial) tHistorial.classList.toggle('active', esHistorial);

    const fStock = document.getElementById('notif-footer-stock');
    const fCompras = document.getElementById('notif-footer-compras');
    const fHistorial = document.getElementById('notif-footer-historial');

    if (fStock) fStock.classList.toggle('d-none', !esAlertas);
    if (fCompras) fCompras.classList.toggle('d-none', !esCompras);
    if (fHistorial) fHistorial.classList.toggle('d-none', !esHistorial);
  };

  // ── ACTUALIZAR CONTADOR Y CAMPANA ──
  function actualizarBadgeYBounce(nuevoTotal) {
    const badge = document.getElementById('notif-badge');
    const icono = document.getElementById('notif-bell-icon');
    if (!badge || !icono) return;

    if (contadorPrevio !== -1 && nuevoTotal > contadorPrevio) {
      icono.classList.remove('notif-bell-bounce');
      void icono.offsetWidth; // Reflow
      icono.classList.add('notif-bell-bounce');
    }
    contadorPrevio = nuevoTotal;

    if (nuevoTotal > 0) {
      badge.textContent = nuevoTotal > 99 ? '99+' : nuevoTotal;
      badge.classList.remove('d-none');
      icono.classList.add('notif-bell-active');
    } else {
      badge.classList.add('d-none');
      icono.classList.remove('notif-bell-active');
    }
  }

  // ── RENDER ITEMS ──

  function stockItemHTML(p) {
    const c = p.nivel === 'critico' ? '#ec4899' : '#38bdf8';
    const label = p.nivel === 'critico' ? 'crítico' : 'bajo';
    const nombre = esc(p.nombre);
    const key = 'stock:' + p.nombre;

    return `
      <div class="px-3 py-2 notif-row d-flex align-items-center justify-content-between gap-2" style="border-top:1px solid rgba(255,255,255,.05);" data-key="${key}" data-tipo="stock" data-nombre="${nombre}">
        <div class="d-flex align-items-start gap-2 flex-grow-1 overflow-hidden" style="min-width:0;">
          <span style="width:8px; height:8px; border-radius:50%; background:${c}; flex-shrink:0; margin-top:5px;"></span>
          <div style="font-size:12px; line-height:1.3; min-width:0;" class="text-truncate">
            <div class="fw-semibold text-truncate text-white" title="${nombre}">${nombre}</div>
            <small style="color:rgba(226,232,240,.6);">${p.total_stock ?? p.cantidad} uds — ${label}</small>
          </div>
        </div>
        <div class="d-flex align-items-center gap-1 flex-shrink-0">
          <button type="button" class="notif-btn-action notif-btn-archivar" data-act="archivar" data-key="${key}" data-tipo="stock" data-nombre="${nombre}" data-cantidad="${p.total_stock ?? p.cantidad} uds" data-nivel="${p.nivel}" title="Archivar notificación">
            <i class="bi bi-archive"></i>
          </button>
          <button type="button" class="notif-btn-action notif-btn-borrar" data-act="borrar" data-key="${key}" data-tipo="stock" data-nombre="${nombre}" title="Borrar notificación">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    `;
  }

  function compraItemHTML(c) {
    const esConfirmada = c.estado_raw === 'confirmada';
    const dotColor = esConfirmada ? '#38bdf8' : '#CF9C48';
    const badgeBg = esConfirmada ? 'rgba(56,189,248,0.15)' : 'rgba(207,156,72,0.15)';
    const badgeColor = esConfirmada ? '#38bdf8' : '#CF9C48';
    const prov = esc(c.proveedor);
    const key = 'compra:' + c.id;

    return `
      <div class="px-3 py-2 notif-row d-flex align-items-center justify-content-between gap-2" style="border-top:1px solid rgba(255,255,255,.05);" data-key="${key}" data-tipo="compra" data-id="${c.id}">
        <a href="${c.url}" class="d-flex align-items-start gap-2 flex-grow-1 overflow-hidden text-decoration-none" style="min-width:0; color:inherit;">
          <span style="width:8px; height:8px; border-radius:50%; background:${dotColor}; flex-shrink:0; margin-top:5px;"></span>
          <div style="font-size:12px; line-height:1.3; min-width:0;" class="text-truncate">
            <strong style="color:#fff;">Compra #${c.id}</strong> — <span class="text-truncate" style="color:#e2e8f0;">${prov}</span><br>
            <small style="color:rgba(226,232,240,.6);">${fmtCOP(c.valor)} · ${c.fecha}</small>
          </div>
        </a>
        <div class="d-flex align-items-center gap-1 flex-shrink-0">
          <span class="badge me-1" style="background:${badgeBg}; color:${badgeColor}; font-size:9.5px; font-weight:700; text-transform:uppercase;">
            ${c.estado}
          </span>
          <button type="button" class="notif-btn-action notif-btn-archivar" data-act="archivar" data-key="${key}" data-tipo="compra" data-nombre="Compra #${c.id} (${prov})" data-cantidad="${c.estado}" data-nivel="compra" title="Archivar notificación">
            <i class="bi bi-archive"></i>
          </button>
          <button type="button" class="notif-btn-action notif-btn-borrar" data-act="borrar" data-key="${key}" data-tipo="compra" data-nombre="Compra #${c.id}" title="Borrar notificación">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    `;
  }

  function historialItemHTML(item, index) {
    const c = item.nivel === 'critico' ? '#ec4899' : (item.nivel === 'compra' ? '#CF9C48' : '#38bdf8');
    const nombre = esc(item.nombre);

    return `
      <div class="px-3 py-2 notif-row d-flex align-items-center justify-content-between gap-2" style="border-top:1px solid rgba(255,255,255,.05);" data-index="${index}">
        <div class="d-flex align-items-start gap-2 flex-grow-1 overflow-hidden" style="min-width:0;">
          <span style="width:8px; height:8px; border-radius:50%; background:${c}; flex-shrink:0; margin-top:5px;"></span>
          <div style="font-size:12px; line-height:1.3; min-width:0;" class="text-truncate">
            <div class="fw-semibold text-truncate text-white" title="${nombre}">${nombre}</div>
            <small style="color:rgba(226,232,240,.6);">${item.cantidad || ''}${item.fecha ? ' · ' + item.fecha : ''}</small>
            ${item.archivada ? '<span class="badge bg-secondary ms-1" style="font-size:8.5px; padding:1px 4px;">Archivada</span>' : ''}
          </div>
        </div>
        <div class="d-flex align-items-center gap-1 flex-shrink-0">
          <button type="button" class="notif-btn-action notif-btn-restaurar" data-act="restaurar-item" data-index="${index}" data-key="${item.key || ''}" title="Restaurar a activas (incrementa contador)">
            <i class="bi bi-arrow-counterclockwise"></i>
          </button>
          <button type="button" class="notif-btn-action notif-btn-borrar" data-act="borrar-historial-item" data-index="${index}" title="Eliminar del historial">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    `;
  }

  // ── RENDER PANELES ──

  function renderStock(visibles) {
    const panel = document.getElementById('panel-alertas');
    const badgeTab = document.getElementById('badge-stock-tab');
    if (badgeTab) {
      if (visibles.length > 0) {
        badgeTab.textContent = visibles.length;
        badgeTab.classList.remove('d-none');
      } else {
        badgeTab.classList.add('d-none');
      }
    }
    if (!panel) return;

    if (visibles.length === 0) {
      panel.innerHTML = `
        <div class="text-center py-4" style="font-size:12px; color:rgba(226,232,240,.4);">
          <i class="bi bi-check-circle fs-5 d-block mb-1 text-success"></i> Sin alertas activas de stock
        </div>`;
    } else {
      panel.innerHTML = visibles.map(p => stockItemHTML(p)).join('');
    }
  }

  function renderCompras(visibles) {
    const panel = document.getElementById('panel-compras');
    const badgeTab = document.getElementById('badge-compras-tab');
    if (badgeTab) {
      if (visibles.length > 0) {
        badgeTab.textContent = visibles.length;
        badgeTab.classList.remove('d-none');
      } else {
        badgeTab.classList.add('d-none');
      }
    }
    if (!panel) return;

    if (visibles.length === 0) {
      panel.innerHTML = `
        <div class="text-center py-4" style="font-size:12px; color:rgba(226,232,240,.4);">
          <i class="bi bi-bag-check fs-5 d-block mb-1" style="color:#CF9C48;"></i> Sin compras pendientes
        </div>`;
    } else {
      panel.innerHTML = visibles.map(c => compraItemHTML(c)).join('');
    }
  }

  function renderHistorial() {
    const panel = document.getElementById('panel-historial');
    const badgeTab = document.getElementById('badge-historial-tab');
    if (badgeTab) {
      if (historialNotif.length > 0) {
        badgeTab.textContent = historialNotif.length;
        badgeTab.classList.remove('d-none');
      } else {
        badgeTab.classList.add('d-none');
      }
    }
    if (!panel) return;

    if (historialNotif.length === 0) {
      panel.innerHTML = `
        <div class="text-center py-4 notif-empty-text">
          <i class="bi bi-archive fs-5 d-block mb-1" style="color:#64748b;"></i> Historial vacío
        </div>`;
    } else {
      panel.innerHTML = historialNotif.map((item, idx) => historialItemHTML(item, idx)).join('');
    }
  }

  // ── PINTAR TODO ──
  function pintar() {
    if (!ultimaData) return;

    const todosStock = [
      ...(ultimaData.criticos || []).map(p => ({ ...p, nivel: 'critico' })),
      ...(ultimaData.bajos || []).map(p => ({ ...p, nivel: 'bajo' }))
    ];
    const stockVisibles = todosStock.filter(p => {
      const key = 'stock:' + p.nombre;
      return !archivadas.has(key) && !borradas.has(key);
    });

    const todasCompras = ultimaData.compras_pendientes || [];
    const comprasVisibles = todasCompras.filter(c => {
      const key = 'compra:' + c.id;
      return !archivadas.has(key) && !borradas.has(key);
    });

    renderStock(stockVisibles);
    renderCompras(comprasVisibles);
    renderHistorial();

    const totalActivas = stockVisibles.length + comprasVisibles.length;
    actualizarBadgeYBounce(totalActivas);
  }

  // ── MANEJADORES DE ACCIONES (ARCHIVAR / BORRAR / RESTAURAR) ──

  function archivarNotif(key, tipo, nombre, cantidad, nivel) {
    if (!key) return;
    archivadas.add(key);
    borradas.delete(key);

    // Agregar al historial como archivada si no está
    const existe = historialNotif.find(h => h.key === key);
    if (existe) {
      existe.archivada = true;
    } else {
      historialNotif.unshift({
        key: key,
        tipo: tipo,
        nombre: nombre,
        cantidad: cantidad,
        nivel: nivel,
        archivada: true,
        fecha: new Date().toLocaleString('es-CO', {
          hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
        })
      });
    }

    guardarTodo();
    pintar();
  }

  function borrarNotif(key) {
    if (!key) return;
    borradas.add(key);
    archivadas.delete(key);

    guardarTodo();
    pintar();
  }

  function restaurarItem(index, key) {
    if (key) {
      archivadas.delete(key);
      borradas.delete(key);
    }
    if (index >= 0 && index < historialNotif.length) {
      const item = historialNotif[index];
      if (item && item.key) {
        archivadas.delete(item.key);
        borradas.delete(item.key);
      }
      item.archivada = false;
    }

    guardarTodo();
    pintar();
  }

  function borrarHistorialItem(index) {
    if (index >= 0 && index < historialNotif.length) {
      historialNotif.splice(index, 1);
      guardarTodo();
      renderHistorial();
    }
  }

  function vaciarHistorial() {
    historialNotif = [];
    guardarTodo();
    renderHistorial();
  }

  // ── EVENT DELEGATION: ACCIONES EN PANELES ──

  const dropdownMenu = document.getElementById('notif-dropdown-menu');
  if (dropdownMenu) {
    dropdownMenu.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-act]');
      if (!btn) return;

      const act = btn.dataset.act;

      if (act === 'archivar') {
        e.stopPropagation();
        archivarNotif(
          btn.dataset.key,
          btn.dataset.tipo,
          btn.dataset.nombre,
          btn.dataset.cantidad,
          btn.dataset.nivel
        );
      } else if (act === 'borrar') {
        e.stopPropagation();
        borrarNotif(btn.dataset.key);
      } else if (act === 'restaurar-item') {
        e.stopPropagation();
        restaurarItem(Number(btn.dataset.index), btn.dataset.key);
      } else if (act === 'borrar-historial-item') {
        e.stopPropagation();
        borrarHistorialItem(Number(btn.dataset.index));
      }
    });
  }

  // Acciones en Lote: Archivar todas / Borrar todas
  const btnArchivarStock = document.getElementById('notif-archivar-todas-stock');
  if (btnArchivarStock) {
    btnArchivarStock.addEventListener('click', () => {
      if (!ultimaData) return;
      const todos = [
        ...(ultimaData.criticos || []).map(p => ({ ...p, nivel: 'critico' })),
        ...(ultimaData.bajos || []).map(p => ({ ...p, nivel: 'bajo' }))
      ];
      todos.forEach(p => {
        const key = 'stock:' + p.nombre;
        if (!archivadas.has(key) && !borradas.has(key)) {
          archivarNotif(key, 'stock', p.nombre, `${p.total_stock ?? p.cantidad} uds`, p.nivel);
        }
      });
    });
  }

  const btnBorrarStock = document.getElementById('notif-borrar-todas-stock');
  if (btnBorrarStock) {
    btnBorrarStock.addEventListener('click', () => {
      if (!ultimaData) return;
      const todos = [
        ...(ultimaData.criticos || []).map(p => ({ ...p, nivel: 'critico' })),
        ...(ultimaData.bajos || []).map(p => ({ ...p, nivel: 'bajo' }))
      ];
      todos.forEach(p => {
        const key = 'stock:' + p.nombre;
        borradas.add(key);
        archivadas.delete(key);
      });
      guardarTodo();
      pintar();
    });
  }

  const btnArchivarCompras = document.getElementById('notif-archivar-todas-compras');
  if (btnArchivarCompras) {
    btnArchivarCompras.addEventListener('click', () => {
      if (!ultimaData) return;
      (ultimaData.compras_pendientes || []).forEach(c => {
        const key = 'compra:' + c.id;
        if (!archivadas.has(key) && !borradas.has(key)) {
          archivarNotif(key, 'compra', `Compra #${c.id} (${c.proveedor})`, c.estado, 'compra');
        }
      });
    });
  }

  const btnBorrarCompras = document.getElementById('notif-borrar-todas-compras');
  if (btnBorrarCompras) {
    btnBorrarCompras.addEventListener('click', () => {
      if (!ultimaData) return;
      (ultimaData.compras_pendientes || []).forEach(c => {
        const key = 'compra:' + c.id;
        borradas.add(key);
        archivadas.delete(key);
      });
      guardarTodo();
      pintar();
    });
  }

  const btnVaciarHistorial = document.getElementById('notif-vaciar-historial');
  if (btnVaciarHistorial) {
    btnVaciarHistorial.addEventListener('click', () => {
      vaciarHistorial();
    });
  }

  // ── ACTUALIZACIÓN PERIÓDICA (POLLING) ──

  function actualizar() {
    fetch(URL_STOCK_STATUS + '?_=' + Date.now(), {
      cache: 'no-store',
      headers: { 'Cache-Control': 'no-cache' }
    })
      .then(r => {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(data => {
        ultimaData = data;
        const criticos = data.criticos || [];
        const bajos = data.bajos || [];
        const compras = data.compras_pendientes || [];

        let hayNuevos = false;

        // Registrar alertas de stock nuevas en historial de registro
        [...criticos.map(p => ({ ...p, nivel: 'critico' })), ...bajos.map(p => ({ ...p, nivel: 'bajo' }))]
          .forEach(p => {
            const key = 'stock:' + p.nombre;
            if (!vistosPrevios.has(key)) {
              vistosPrevios.add(key);
              historialNotif.unshift({
                key: key,
                tipo: 'stock',
                nombre: p.nombre,
                nivel: p.nivel,
                cantidad: `${p.total_stock ?? p.cantidad} uds`,
                archivada: false,
                fecha: new Date().toLocaleString('es-CO', {
                  hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
                })
              });
              hayNuevos = true;
            }
          });

        // Registrar compras pendientes nuevas en historial
        compras.forEach(c => {
          const key = 'compra:' + c.id;
          if (!vistosPrevios.has(key)) {
            vistosPrevios.add(key);
            historialNotif.unshift({
              key: key,
              tipo: 'compra',
              nombre: `Compra #${c.id} (${c.proveedor})`,
              nivel: 'compra',
              cantidad: c.estado,
              archivada: false,
              fecha: new Date().toLocaleString('es-CO', {
                hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
              })
            });
            hayNuevos = true;
          }
        });

        if (hayNuevos) {
          guardarTodo();
        }

        pintar();
      })
      .catch(() => {});
  }

  // Inicialización
  renderHistorial();
  actualizar();
  setInterval(actualizar, INTERVALO);
})();
