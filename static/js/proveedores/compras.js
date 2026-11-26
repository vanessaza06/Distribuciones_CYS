// ── Exportar: Excel / PDF / Imprimir ───────────────────────────
// Llama a la misma URL con ?export=excel|pdf|imprimir.
// El servidor aplica los mismos filtros (proveedor, q, estado, pago, desde, hasta).
function initExportar() {
  if (window._cysComprasExportDelegado) return;
  window._cysComprasExportDelegado = true;

  function construirUrl(tipo) {
    const params = new URLSearchParams(window.location.search);
    params.delete('modal');
    params.delete('page');

    // Filtros escritos en el formulario aunque no se haya pulsado "buscar"
    const formFiltros = document.getElementById('filtrosCompras');
    if (formFiltros) {
      ['q', 'desde', 'hasta', 'estado', 'pago'].forEach((nombre) => {
        const campo = formFiltros.elements[nombre];
        if (!campo) return;
        const valor = (campo.value || '').trim();
        const esTodos = (nombre === 'estado' || nombre === 'pago') && valor === 'todos';
        if (valor && !esTodos) params.set(nombre, valor);
        else params.delete(nombre);
      });
    }

    // Proveedor: URL → hidden del formulario → selector del modal
    if (!params.get('proveedor')) {
      const hidden = formFiltros && formFiltros.elements['proveedor'];
      const sel = document.getElementById('proveedorSeleccionado');
      const prov = (hidden && hidden.value) || (sel && sel.value);
      if (prov) params.set('proveedor', prov);
    }

    params.set('export', tipo);
    return window.location.pathname + '?' + params.toString();
  }

  async function descargar(url, nombreSugerido) {
    try {
      const resp = await fetch(url, {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!resp.ok) throw new Error('Error HTTP ' + resp.status);

      const ct = resp.headers.get('Content-Type') || '';
      if (ct.indexOf('text/html') !== -1) {
        throw new Error('El servidor devolvió HTML en lugar del archivo (¿sesión vencida o falta implementar ?export en la vista?).');
      }

      const blob = await resp.blob();
      const cd = resp.headers.get('Content-Disposition') || '';
      const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
      const nombre = m ? decodeURIComponent(m[1]) : nombreSugerido;

      const objUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objUrl;
      a.download = nombre;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { a.remove(); URL.revokeObjectURL(objUrl); }, 1000);
    } catch (err) {
      console.error('[Compras] Falló la exportación:', err);
      alert('No se pudo generar el archivo.\n' + err.message);
    }
  }

  document.addEventListener('click', function (e) {
    const btn = e.target && e.target.closest ? e.target.closest('#cys-export-compras [data-export]') : null;
    if (!btn) return;

    e.preventDefault();
    e.stopImmediatePropagation();

    const tipo = btn.dataset.export;
    const url = construirUrl(tipo);
    const hoy = new Date().toISOString().slice(0, 10).replace(/-/g, '');

    if (tipo === 'imprimir') {
      const w = window.open(url, '_blank');
      if (!w) alert('El navegador bloqueó la ventana de impresión. Permite las ventanas emergentes para este sitio.');
    } else if (tipo === 'excel') {
      descargar(url, 'Compras_' + hoy + '.xlsx');
    } else if (tipo === 'pdf') {
      descargar(url, 'Compras_' + hoy + '.pdf');
    }

    const contenedor = document.getElementById('cys-export-compras');
    const toggle = contenedor && contenedor.querySelector('[data-bs-toggle="dropdown"]');
    if (toggle && window.bootstrap && bootstrap.Dropdown) {
      const inst = bootstrap.Dropdown.getInstance(toggle);
      if (inst) inst.hide();
    }
  }, true);
}