/* Interacciones y DataTables para Detalle de Compra */
(function() {
  function fmtCopDetalle(n) {
    return '$' + Math.round(n).toLocaleString('es-CO');
  }

  function initPagoModal() {
    const modal = document.getElementById('modalPagoDetalle');
    if (!modal) return;

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

  function initTablaDetalleCompra() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const tableEl = document.getElementById('tablaDetalleCompra');
    if (!tableEl) return;

    if (jQuery.fn.DataTable.isDataTable(tableEl)) {
      jQuery(tableEl).DataTable().destroy();
    }

    const modal = document.getElementById('modalPagoDetalle');
    const codigo = (tableEl && tableEl.dataset.codigo) || (modal ? modal.dataset.codigo : '');
    const fecha = (tableEl && tableEl.dataset.fecha) || (modal ? modal.dataset.fecha : '');

    const dtCompra = jQuery(tableEl).DataTable({
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
      },
      buttons: [
        {
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
          className: 'cys-dt-btn-excel',
          title: 'Detalle_Compra_' + codigo + '_CYS',
          filename: 'Compra_' + codigo + '_' + fecha
        },
        {
          extend: 'pdfHtml5',
          text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
          className: 'cys-dt-btn-pdf',
          title: 'Distribuciones CYS Ltda - Detalle de Compra #' + codigo,
          filename: 'Compra_' + codigo + '_' + fecha,
          pageSize: 'A4',
          customize: function(doc) {
            doc.defaultStyle.fontSize = 9;
            if (doc.styles && doc.styles.tableHeader) {
              doc.styles.tableHeader.fontSize = 10;
              doc.styles.tableHeader.bold = true;
              doc.styles.tableHeader.fillColor = '#011936';
              doc.styles.tableHeader.color = '#CF9C48';
              doc.styles.tableHeader.alignment = 'center';
            }
          }
        }
      ]
    });

    const exportContainer = document.getElementById('cys-dt-export-compra');
    if (exportContainer) {
      if (window.cysCrearDropdownExportar) {
        window.cysCrearDropdownExportar(dtCompra, exportContainer);
      } else {
        exportContainer.innerHTML = '';
        dtCompra.buttons().container().removeClass('d-none').appendTo(exportContainer);
      }
    }
  }

  function initProgressBar() {
    document.querySelectorAll('.dc-progress-bar-fill[data-progreso]').forEach(function(el) {
      el.style.width = (el.dataset.progreso || '0') + '%';
    });
  }

  function initPage() {
    initPagoModal();
    initTablaDetalleCompra();
    initProgressBar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
  } else {
    initPage();
  }

  if (document.body) {
    document.body.addEventListener('htmx:afterSettle', initPage);
  }
})();
