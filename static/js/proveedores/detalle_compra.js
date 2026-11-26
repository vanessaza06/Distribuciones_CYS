/* Interacciones y DataTables para Detalle de Compra */
(function() {
  'use strict';

  function fmtCopDetalle(n) {
    return '$' + Math.round(n).toLocaleString('es-CO');
  }

  /* ── Aviso flotante ────────────────────────────────────────────
     Solo se muestran los errores. Las descargas correctas se ven
     directamente en el panel de descargas del navegador. */
  var _avisoTimer = null;
  function mostrarAviso(mensaje, tipo) {
    if (tipo !== 'error') return;

    var el = document.getElementById('cys-aviso-descarga');
    if (!el) {
      el = document.createElement('div');
      el.id = 'cys-aviso-descarga';
      el.setAttribute('role', 'status');
      el.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2000;color:#fff;' +
        'padding:12px 18px;border-radius:10px;font-size:14px;font-weight:600;' +
        'box-shadow:0 6px 20px rgba(0,0,0,.25);display:flex;align-items:center;gap:10px;' +
        'max-width:360px;transition:opacity .25s ease;';
      document.body.appendChild(el);
    }
    el.style.background = '#dc3545';
    el.style.opacity = '1';
    el.innerHTML = '<i class="bi bi-x-circle-fill"></i><span></span>';
    el.querySelector('span').textContent = mensaje;

    clearTimeout(_avisoTimer);
    _avisoTimer = setTimeout(function() {
      el.style.opacity = '0';
      setTimeout(function() { if (el.parentNode && el.style.opacity === '0') el.remove(); }, 300);
    }, 4000);
  }

  /* ── Modal de pago ─────────────────────────────────────────── */
  function initPagoModal() {
    const modal = document.getElementById('modalPagoDetalle');
    if (!modal) return;

    if (modal.dataset.pagoBound === 'true') return;
    modal.dataset.pagoBound = 'true';

    const saldo = parseFloat(modal.dataset.saldo) || 0;
    const inputMonto = document.getElementById('inputMontoDetalle');
    const inputRaw = document.getElementById('inputMontoDetalleRaw');
    const btnTodo = document.getElementById('btnPagarTodoDetalle');
    const btnConfirmar = document.getElementById('btnConfirmarPagoDetalle');
    const errorDiv = document.getElementById('errorMontoDetalle');
    const saldoTexto = document.getElementById('saldoRestanteDetalleTexto');
    const badgeEl = document.getElementById('badgeEstadoDetalle');
    const form = document.getElementById('formPagoDetalle');

    function recalcularPago() {
      const abono = parseFloat(inputRaw ? inputRaw.value : '0') || 0;
      const excede = abono > saldo;
      const nuevoSaldo = Math.max(0, saldo - abono);

      if (errorDiv) {
        const span = errorDiv.querySelector('span');
        if (span) {
          span.textContent = excede
            ? 'El monto (' + fmtCopDetalle(abono) + ') supera el saldo pendiente (' + fmtCopDetalle(saldo) + ').'
            : '';
        }
        errorDiv.classList.toggle('d-none', !excede);
      }

      if (inputMonto) inputMonto.classList.toggle('is-invalid', excede);
      if (btnConfirmar) btnConfirmar.disabled = excede || abono <= 0;

      if (saldoTexto) {
        saldoTexto.textContent = excede ? '—' : fmtCopDetalle(nuevoSaldo);
        saldoTexto.className = nuevoSaldo === 0 && !excede ? 'fw-bold text-success fs-6' : 'fw-bold text-danger fs-6';
      }

      if (badgeEl) {
        if (excede) {
          badgeEl.className = 'badge bg-danger px-2 py-1';
          badgeEl.innerHTML = '<i class="bi bi-x-circle-fill me-1"></i>Monto no válido';
        } else if (abono > 0 && nuevoSaldo === 0) {
          badgeEl.className = 'badge badge-success-custom px-2 py-1';
          badgeEl.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>Quedará PAGADA';
        } else if (abono > 0) {
          badgeEl.className = 'badge badge-warning-custom px-2 py-1';
          badgeEl.innerHTML = '<i class="bi bi-dash-circle me-1"></i>Abono parcial (aún debe ' + fmtCopDetalle(nuevoSaldo) + ')';
        } else {
          badgeEl.className = 'badge badge-pending-custom px-2 py-1';
          badgeEl.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Sin abono';
        }
      }
    }

    if (inputMonto && inputRaw) {
      inputMonto.addEventListener('input', function() {
        const digitos = this.value.replace(/\D/g, '').replace(/^0+/, '');
        this.value = digitos ? Number(digitos).toLocaleString('es-CO') : '';
        inputRaw.value = digitos;
        recalcularPago();
      });
    }

    if (btnTodo && inputMonto && inputRaw) {
      btnTodo.addEventListener('click', function() {
        inputMonto.value = Math.round(saldo).toLocaleString('es-CO');
        inputRaw.value = saldo.toFixed(2);
        recalcularPago();
      });
    }

    if (form && inputRaw) {
      form.addEventListener('submit', function(e) {
        const abono = parseFloat(inputRaw.value) || 0;
        recalcularPago();
        if (abono <= 0 || abono > saldo) {
          e.preventDefault();
        }
      });
    }

    modal.addEventListener('shown.bs.modal', function() {
      recalcularPago();
      if (inputMonto) inputMonto.focus();
    });
  }

  /* ── Exportación (Excel / PDF / Imprimir) ─────────────────────
     1) Pide el archivo al servidor (?export=excel|pdf) y lo guarda
        como descarga real → el navegador abre su panel de Descargas.
     2) Si el servidor falla, genera el archivo en el navegador.
     No se muestran avisos cuando todo sale bien. */

  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function txt(selector) {
    var el = document.querySelector(selector);
    return el ? el.textContent.replace(/\s+/g, ' ').trim() : '';
  }

  function aNumero(s) {
    var limpio = String(s || '').replace(/[^\d-]/g, '');
    return limpio === '' || limpio === '-' ? null : Number(limpio);
  }

  function obtenerFilas() {
    var tabla = document.getElementById('tablaDetalleCompra');
    if (!tabla) return [];

    var nodos = [];
    if (window.jQuery && jQuery.fn.DataTable && jQuery.fn.DataTable.isDataTable(tabla)) {
      nodos = jQuery(tabla).DataTable().rows().nodes().toArray();
    } else {
      nodos = Array.prototype.slice.call(tabla.querySelectorAll('tbody tr'));
    }

    return nodos
      .map(function(tr) {
        return Array.prototype.map.call(tr.cells, function(td) {
          return td.textContent.replace(/\s+/g, ' ').trim();
        });
      })
      .filter(function(celdas) { return celdas.length >= 7; });
  }

  function obtenerDatos() {
    var tabla = document.getElementById('tablaDetalleCompra');
    var codigo = tabla ? tabla.dataset.codigo : 'compra';
    var fecha = tabla ? tabla.dataset.fecha : '';

    var metricas = {};
    document.querySelectorAll('.dc-metric-card').forEach(function(card) {
      var l = card.querySelector('.dc-metric-card__label');
      var v = card.querySelector('.dc-metric-card__value');
      if (l && v) metricas[l.textContent.trim()] = v.textContent.replace(/\s+/g, ' ').trim();
    });

    var metaEl = document.querySelector('.dc-hero__meta');
    var spans = metaEl ? Array.prototype.map.call(metaEl.querySelectorAll('span'), function(s) {
      return s.textContent.trim();
    }).filter(function(t) { return t && t !== '·'; }) : [];

    var pagos = [];
    document.querySelectorAll('.dc-pago-row').forEach(function(row) {
      var ref = row.querySelector('.fw-semibold');
      var det = row.querySelector('small');
      var val = row.querySelector('.fw-bold');
      pagos.push([
        ref ? ref.textContent.trim() : 'Pago',
        det ? det.textContent.replace(/\s+/g, ' ').trim() : '',
        val ? val.textContent.trim() : ''
      ]);
    });

    return {
      codigo: codigo,
      fecha: fecha,
      titulo: txt('.dc-hero__title') || ('Compra #' + codigo),
      estado: txt('.dc-status-badge'),
      meta: spans,
      total: txt('.dc-hero__total strong'),
      estadoPago: metricas['Estado de pago'] || '',
      montoPagado: metricas['Monto pagado'] || '',
      saldo: metricas['Saldo pendiente'] || '',
      filas: obtenerFilas(),
      pagos: pagos
    };
  }

  function nombreArchivo(d, ext) {
    return 'Compra_' + d.codigo + '_' + d.fecha + '.' + ext;
  }

  // Guarda un blob como descarga real (el navegador la muestra en su panel de Descargas)
  function descargarBlob(blob, nombre) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = nombre;
    a.setAttribute('hx-boost', 'false');
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(function() { a.remove(); URL.revokeObjectURL(url); }, 30000);
  }

  function urlExportacion(tipo) {
    var params = new URLSearchParams(window.location.search);
    params.set('export', tipo);
    return window.location.pathname + '?' + params.toString();
  }

  // Pide el archivo al servidor. Devuelve {blob, nombre} o null si falla.
  async function pedirAlServidor(tipo) {
    try {
      var resp = await fetch(urlExportacion(tipo), {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!resp.ok) return null;
      var ct = (resp.headers.get('Content-Type') || '').toLowerCase();
      if (ct.indexOf('text/html') !== -1) return null;

      var blob = await resp.blob();
      var cd = resp.headers.get('Content-Disposition') || '';
      var nombre = null;
      var m = /filename\*=UTF-8''([^;]+)/i.exec(cd) || /filename="?([^";]+)"?/i.exec(cd);
      if (m) {
        try { nombre = decodeURIComponent(m[1].trim()); } catch (e) { nombre = m[1].trim(); }
      }
      return { blob: blob, nombre: nombre };
    } catch (err) {
      console.warn('[DetalleCompra] Servidor no disponible, uso respaldo:', err);
      return null;
    }
  }

  /* ── Respaldo Excel (en el navegador) ── */
  function generarExcelLocal() {
    var d = obtenerDatos();
    var h = '';

    h += '<table>';
    h += '<tr><td colspan="7" style="font-size:16pt;font-weight:bold">' + escHtml(d.titulo) + '</td></tr>';
    h += '<tr><td><b>Estado</b></td><td colspan="6">' + escHtml(d.estado) + '</td></tr>';
    d.meta.forEach(function(m) {
      h += '<tr><td colspan="7">' + escHtml(m) + '</td></tr>';
    });
    h += '<tr><td colspan="7"></td></tr>';

    h += '<tr>';
    ['#', 'Producto', 'Categoría', 'Lote', 'Cantidad', 'Precio Unit.', 'Subtotal'].forEach(function(t) {
      h += '<th style="background:#1F3A5F;color:#ffffff;border:1px solid #999">' + t + '</th>';
    });
    h += '</tr>';

    d.filas.forEach(function(f) {
      h += '<tr>';
      for (var i = 0; i < 7; i++) {
        var v = f[i];
        if (i === 5 || i === 6) {
          var n = aNumero(v);
          h += '<td style="border:1px solid #ccc;mso-number-format:\'\\$\\#\\,\\#\\#0\'">' + (n === null ? escHtml(v) : n) + '</td>';
        } else if (i === 0 || i === 4) {
          var q = aNumero(v);
          h += '<td style="border:1px solid #ccc">' + (q === null ? escHtml(v) : q) + '</td>';
        } else {
          h += '<td style="border:1px solid #ccc">' + escHtml(v) + '</td>';
        }
      }
      h += '</tr>';
    });

    h += '<tr><td colspan="7"></td></tr>';
    [['Total', d.total], ['Monto pagado', d.montoPagado], ['Saldo pendiente', d.saldo]].forEach(function(p) {
      var n = aNumero(p[1]);
      h += '<tr><td colspan="5"></td><td><b>' + p[0] + '</b></td><td style="mso-number-format:\'\\$\\#\\,\\#\\#0\'"><b>' +
           (n === null ? escHtml(p[1]) : n) + '</b></td></tr>';
    });

    if (d.pagos.length) {
      h += '<tr><td colspan="7"></td></tr>';
      h += '<tr><td colspan="7" style="font-size:12pt;font-weight:bold">Pagos registrados</td></tr>';
      d.pagos.forEach(function(p) {
        var n = aNumero(p[2]);
        h += '<tr><td colspan="2">' + escHtml(p[0]) + '</td><td colspan="4">' + escHtml(p[1]) +
             '</td><td style="mso-number-format:\'\\$\\#\\,\\#\\#0\'">' + (n === null ? escHtml(p[2]) : n) + '</td></tr>';
      });
    }
    h += '</table>';

    var doc = '<html xmlns:o="urn:schemas-microsoft-com:office:office" ' +
              'xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">' +
              '<head><meta charset="UTF-8"><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets>' +
              '<x:ExcelWorksheet><x:Name>Compra</x:Name><x:WorksheetOptions><x:DisplayGridlines/>' +
              '</x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->' +
              '</head><body>' + h + '</body></html>';

    return {
      blob: new Blob(['\ufeff' + doc], { type: 'application/vnd.ms-excel;charset=utf-8' }),
      nombre: nombreArchivo(d, 'xls')
    };
  }

  /* ── Vista de impresión (PDF de respaldo / Imprimir) ── */
  function htmlImpresion(d) {
    var filas = d.filas.map(function(f) {
      return '<tr>' +
        '<td class="c">' + escHtml(f[0]) + '</td>' +
        '<td>' + escHtml(f[1]) + '</td>' +
        '<td>' + escHtml(f[2]) + '</td>' +
        '<td>' + escHtml(f[3]) + '</td>' +
        '<td class="c">' + escHtml(f[4]) + '</td>' +
        '<td class="r">' + escHtml(f[5]) + '</td>' +
        '<td class="r"><b>' + escHtml(f[6]) + '</b></td></tr>';
    }).join('');

    var pagos = d.pagos.length
      ? '<h3>Pagos registrados</h3><table><thead><tr><th>Referencia</th><th>Detalle</th><th class="r">Valor</th></tr></thead><tbody>' +
        d.pagos.map(function(p) {
          return '<tr><td>' + escHtml(p[0]) + '</td><td>' + escHtml(p[1]) + '</td><td class="r">' + escHtml(p[2]) + '</td></tr>';
        }).join('') + '</tbody></table>'
      : '';

    return '<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">' +
      '<title>' + escHtml(nombreArchivo(d, 'pdf').replace(/\.pdf$/, '')) + '</title>' +
      '<style>' +
      '@page{size:A4;margin:14mm}' +
      'body{font-family:Arial,Helvetica,sans-serif;color:#222;font-size:12px;margin:0}' +
      'h1{font-size:20px;margin:0 0 4px}h3{margin:22px 0 6px;font-size:14px}' +
      '.meta{color:#555;margin-bottom:14px}.meta span{margin-right:14px}' +
      'table{width:100%;border-collapse:collapse;margin-top:6px}' +
      'th{background:#1F3A5F;color:#fff;text-align:left;padding:6px 8px;font-size:11px;-webkit-print-color-adjust:exact;print-color-adjust:exact}' +
      'td{padding:6px 8px;border-bottom:1px solid #ddd}' +
      '.c{text-align:center}.r{text-align:right}th.r{text-align:right}' +
      '.tot{margin-top:16px;margin-left:auto;width:260px}' +
      '.tot div{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #eee}' +
      '.tot .g{font-weight:bold;font-size:14px;border-bottom:2px solid #1F3A5F}' +
      '</style></head><body>' +
      '<h1>' + escHtml(d.titulo) + '</h1>' +
      '<div class="meta"><span><b>Estado:</b> ' + escHtml(d.estado) + '</span>' +
      d.meta.map(function(m) { return '<span>' + escHtml(m) + '</span>'; }).join('') + '</div>' +
      '<table><thead><tr><th class="c">#</th><th>Producto</th><th>Categoría</th><th>Lote</th>' +
      '<th class="c">Cant.</th><th class="r">Precio Unit.</th><th class="r">Subtotal</th></tr></thead><tbody>' +
      filas + '</tbody></table>' +
      '<div class="tot">' +
      '<div class="g"><span>Total</span><span>' + escHtml(d.total) + '</span></div>' +
      '<div><span>Monto pagado</span><span>' + escHtml(d.montoPagado) + '</span></div>' +
      '<div><span>Saldo pendiente</span><span>' + escHtml(d.saldo) + '</span></div>' +
      '<div><span>Estado de pago</span><span>' + escHtml(d.estadoPago) + '</span></div>' +
      '</div>' + pagos +
      '<script>window.onload=function(){setTimeout(function(){window.focus();window.print();},300);};<\/script>' +
      '</body></html>';
  }

  function abrirVistaImpresion() {
    var ventana = window.open('', '_blank');
    if (!ventana) {
      mostrarAviso('El navegador bloqueó la ventana. Permite las ventanas emergentes.', 'error');
      return false;
    }
    ventana.document.open();
    ventana.document.write(htmlImpresion(obtenerDatos()));
    ventana.document.close();
    return true;
  }

  /* ── Flujo de cada botón ── */
  async function exportarArchivo(tipo, btn) {
    var ext = tipo === 'excel' ? 'xlsx' : 'pdf';
    var d = obtenerDatos();

    if (btn) btn.disabled = true;
    try {
      // 1) Archivo real del servidor → descarga normal del navegador
      var res = await pedirAlServidor(tipo);
      if (res) {
        descargarBlob(res.blob, res.nombre || nombreArchivo(d, ext));
        return;
      }

      // 2) Respaldo en el navegador si el servidor no respondió con un archivo
      if (tipo === 'excel') {
        var local = generarExcelLocal();
        descargarBlob(local.blob, local.nombre);
      } else {
        // Sin PDF del servidor: se abre la vista lista para "Guardar como PDF"
        abrirVistaImpresion();
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function manejarClickExportar(e) {
    var btn = e.target && e.target.closest ? e.target.closest('[data-cys-export]') : null;
    if (!btn) return;
    var contenedor = btn.closest('#cys-dt-export-compra');
    if (!contenedor) return;

    e.preventDefault();
    e.stopImmediatePropagation();

    var tipo = btn.getAttribute('data-cys-export');
    try {
      if (tipo === 'excel' || tipo === 'pdf') {
        exportarArchivo(tipo, btn).catch(function(err) {
          console.error('[DetalleCompra] Falló la exportación:', err);
          mostrarAviso('No se pudo generar el archivo: ' + err.message, 'error');
        });
      } else if (tipo === 'imprimir') {
        abrirVistaImpresion();
      }
    } catch (err) {
      console.error('[DetalleCompra] Falló la exportación:', err);
      mostrarAviso('No se pudo generar el archivo: ' + err.message, 'error');
    }

    var toggle = contenedor.querySelector('[data-bs-toggle="dropdown"]');
    if (toggle && window.bootstrap && bootstrap.Dropdown) {
      var inst = bootstrap.Dropdown.getInstance(toggle);
      if (inst) inst.hide();
    }
  }

  // Quita el listener de una carga anterior y registra el actual.
  if (window._cysDetalleExportHandler) {
    window.removeEventListener('click', window._cysDetalleExportHandler, true);
    document.removeEventListener('click', window._cysDetalleExportHandler, true);
  }
  window._cysDetalleExportHandler = manejarClickExportar;
  window.addEventListener('click', manejarClickExportar, true);

  function initExportacionServidor() {
    var contenedor = document.getElementById('cys-dt-export-compra');
    if (!contenedor) return;
    contenedor.querySelectorAll('[data-cys-export]').forEach(function(btn) {
      btn.dataset.cysExportBound = 'true';
    });
  }

  /* ── DataTable de ítems ────────────────────────────────────── */
  function initTablaDetalleCompra() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const tableEl = document.getElementById('tablaDetalleCompra');
    if (!tableEl) return;

    if (jQuery.fn.DataTable.isDataTable(tableEl)) {
      jQuery(tableEl).DataTable().destroy();
    }

    jQuery(tableEl).DataTable({
      paging: true,
      pageLength: 5,
      searching: false,
      info: true,
      lengthChange: false,
      ordering: true,
      language: {
        info: "Mostrando _START_ a _END_ de _TOTAL_ ítems",
        infoEmpty: "Mostrando 0 a 0 de 0 ítems",
        emptyTable: "No hay productos registrados.",
        paginate: { first: '«', previous: '‹', next: '›', last: '»' }
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: 'info',
        bottomEnd: 'paging'
      }
    });
  }

  function initProgressBar() {
    document.querySelectorAll('.dc-progress-bar-fill[data-progreso]').forEach(function(el) {
      el.style.width = (el.dataset.progreso || '0') + '%';
    });
  }

  function initPage() {
    [initProgressBar, initPagoModal, initExportacionServidor, initTablaDetalleCompra].forEach(function(fn) {
      try {
        fn();
      } catch (err) {
        console.error('[DetalleCompra] Error en ' + fn.name + ':', err);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }

  if (document.body && !window._cysDetalleHtmxBound) {
    window._cysDetalleHtmxBound = true;
    document.body.addEventListener('htmx:afterSettle', initPage);
  }
})();