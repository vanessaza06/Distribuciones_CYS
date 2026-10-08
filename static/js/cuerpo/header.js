(function () {
  'use strict';

  const headerEl = document.querySelector('.cys-header');
  if (!headerEl) return;
  const URL_STOCK_STATUS = headerEl.dataset.urlStockStatus;
  if (!URL_STOCK_STATUS) return;

  const INTERVALO = 8000;
  let historialNotif = JSON.parse(localStorage.getItem('cys_notif_historial') || '[]');
  let vistosPrevios = new Set(JSON.parse(localStorage.getItem('cys_notif_vistos') || '[]'));

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
    if (fStock) fStock.classList.toggle('d-none', esCompras);
    if (fCompras) fCompras.classList.toggle('d-none', !esCompras);
  };

  const fmtCOP = (n) => '$' + Math.round(Number(n) || 0).toLocaleString('es-CO');

  function guardar() {
    localStorage.setItem('cys_notif_historial', JSON.stringify(historialNotif.slice(0, 50)));
    localStorage.setItem('cys_notif_vistos', JSON.stringify([...vistosPrevios]));
  }

  function itemHTML(nombre, cantidad, nivel, fecha) {
    const c = nivel === 'critico' ? '#9b5de5' : (nivel === 'compra' ? '#CF9C48' : '#4DA8DA');
    const label = nivel === 'critico' ? 'crítico' : (nivel === 'compra' ? 'compra' : 'bajo');
    return `<div class="px-3 py-2" style="border-top:1px solid rgba(255,255,255,.05); transition: background 0.2s;">
      <div class="d-flex align-items-start gap-2">
        <span style="width:8px; height:8px; border-radius:50%; background:${c}; flex-shrink:0; margin-top:5px;"></span>
        <div style="font-size:12px; line-height:1.4; color:#e2e8f0;">
          ${nombre}<br>
          <small style="color:rgba(226,232,240,.5);">${cantidad} — ${label}${fecha ? ' · ' + fecha : ''}</small>
        </div>
      </div>
    </div>`;
  }

  function compraItemHTML(compra) {
    const esConfirmada = compra.estado_raw === 'confirmada';
    const dotColor = esConfirmada ? '#4DA8DA' : '#CF9C48';
    const badgeBg = esConfirmada ? 'rgba(77,168,218,0.15)' : 'rgba(207,156,72,0.15)';
    const badgeColor = esConfirmada ? '#4DA8DA' : '#CF9C48';

    return `<a href="${compra.url}" class="d-block px-3 py-2 text-decoration-none notif-item" style="border-top:1px solid rgba(255,255,255,.05); transition: background 0.2s;">
      <div class="d-flex align-items-start justify-content-between gap-2">
        <div class="d-flex align-items-start gap-2">
          <span style="width:8px; height:8px; border-radius:50%; background:${dotColor}; flex-shrink:0; margin-top:5px;"></span>
          <div style="font-size:12px; line-height:1.3; color:#e2e8f0;">
            <strong style="color:#fff;">Compra #${compra.id}</strong> — <span style="color:#e2e8f0;">${compra.proveedor}</span><br>
            <small style="color:rgba(226,232,240,.6);">${fmtCOP(compra.valor)} · ${compra.fecha}</small>
          </div>
        </div>
        <span class="badge" style="background:${badgeBg}; color:${badgeColor}; font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">
          ${compra.estado}
        </span>
      </div>
    </a>`;
  }

  function renderAlertas(criticos, bajos) {
    const panel = document.getElementById('panel-alertas');
    if (!panel) return;
    const todos = [
      ...(criticos || []).map(p => ({ ...p, nivel: 'critico' })),
      ...(bajos || []).map(p => ({ ...p, nivel: 'bajo' })),
    ];
    panel.innerHTML = todos.length
      ? todos.map(p => itemHTML(p.nombre, `${p.total_stock ?? p.cantidad} uds`, p.nivel)).join('')
      : `<div class="text-center py-4" style="font-size:12px; color:rgba(226,232,240,.4);">
           <i class="bi bi-check-circle fs-5 d-block mb-1" style="color:#2ecc71;"></i> Sin alertas de stock
         </div>`;
  }

  function renderCompras(compras) {
    const panel = document.getElementById('panel-compras');
    const badgeTab = document.getElementById('badge-compras-tab');
    if (badgeTab) {
      if (compras && compras.length > 0) {
        badgeTab.textContent = compras.length;
        badgeTab.classList.remove('d-none');
      } else {
        badgeTab.classList.add('d-none');
      }
    }
    if (!panel) return;
    panel.innerHTML = (compras && compras.length)
      ? compras.map(c => compraItemHTML(c)).join('')
      : `<div class="text-center py-4" style="font-size:12px; color:rgba(226,232,240,.4);">
           <i class="bi bi-bag-check fs-5 d-block mb-1" style="color:#CF9C48;"></i> Sin compras pendientes
         </div>`;
  }

  function renderHistorial() {
    const panel = document.getElementById('panel-historial');
    if (!panel) return;
    panel.innerHTML = historialNotif.length
      ? historialNotif.map(n => itemHTML(n.nombre, n.cantidad, n.nivel, n.fecha)).join('')
      : `<div class="text-center py-4" style="font-size:12px; color:rgba(226,232,240,.4);">Sin notificaciones aún</div>`;
  }

  function actualizarBadgeYBounce(total, hayNuevos) {
    const badge = document.getElementById('notif-badge');
    const icono = document.getElementById('notif-bell-icon');
    if (!badge || !icono) return;
    if (total > 0) {
      badge.textContent = total > 99 ? '99+' : total;
      badge.classList.remove('d-none');
      icono.classList.add('notif-bell-active');
    } else {
      badge.classList.add('d-none');
      icono.classList.remove('notif-bell-active');
    }
  }

  function actualizar() {
    fetch(URL_STOCK_STATUS + "?_=" + Date.now(), {
      cache: 'no-store',
      headers: { 'Cache-Control': 'no-cache' }
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => {
        const criticos = data.criticos || [];
        const bajos = data.bajos || [];
        const compras = data.compras_pendientes || [];

        renderAlertas(criticos, bajos);
        renderCompras(compras);

        let hayNuevos = false;
        [...criticos.map(p => ({ ...p, nivel: 'critico' })), ...bajos.map(p => ({ ...p, nivel: 'bajo' }))]
          .forEach(p => {
            const key = p.nombre + '|' + p.nivel;
            if (!vistosPrevios.has(key)) {
              historialNotif.unshift({
                nombre: p.nombre, nivel: p.nivel, cantidad: `${p.total_stock ?? p.cantidad} uds`,
                fecha: new Date().toLocaleString('es-CO', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
              });
              vistosPrevios.add(key);
              hayNuevos = true;
            }
          });

        compras.forEach(c => {
          const key = 'compra-' + c.id + '|' + c.estado_raw;
          if (!vistosPrevios.has(key)) {
            historialNotif.unshift({
              nombre: `Compra #${c.id} (${c.proveedor})`,
              nivel: 'compra',
              cantidad: c.estado,
              fecha: new Date().toLocaleString('es-CO', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
            });
            vistosPrevios.add(key);
            hayNuevos = true;
          }
        });

        if (hayNuevos) { guardar(); renderHistorial(); }

        const totalTotal = data.total_alertas ?? (criticos.length + bajos.length + compras.length);
        actualizarBadgeYBounce(totalTotal, hayNuevos);
      })
      .catch(() => {});
  }

  renderHistorial();
  actualizar();
  setInterval(actualizar, INTERVALO);
})();