/* Interacciones y DataTables para Devoluciones (Clientes y Proveedores) */
(function() {
  if (window.jQuery && jQuery.fn.dataTable) {
    jQuery.fn.dataTable.ext.errMode = 'none';
  }

  function initDevolucionesPage() {
    // 1. Lógica del formulario de pasos (si existe)
    const form = document.getElementById('formDevoluciones');
    if (form) {
      const productChecks = [...form.querySelectorAll('.dev-product-check')];
      productChecks.forEach((check) => {
        const quantity = form.querySelector(`[name="cantidad_devolucion_${check.value}"]`);
        if (!quantity) return;

        quantity.disabled = !check.checked;
        check.addEventListener('change', () => {
          quantity.disabled = !check.checked;
          if (check.checked && Number(quantity.value) < 1) quantity.value = 1;
        });
      });

      form.addEventListener('submit', (event) => {
        const nextAction = event.submitter?.value !== 'atras';
        if (!nextAction) return;

        if (productChecks.length && !productChecks.some((check) => check.checked)) {
          event.preventDefault();
          window.alert('Selecciona al menos un producto para continuar.');
        }
      });
    }

    // 1b. Lógica del formulario de devoluciones a proveedores
    const formProv = document.getElementById('formDevolucionProveedor');
    if (formProv) {
      const prodSelect = document.getElementById('id_devprov_presentacion');
      const precioInput = document.getElementById('id_devprov_precio');
      const cantInput = document.getElementById('id_devprov_cantidad');

      if (prodSelect && precioInput) {
        prodSelect.addEventListener('change', function() {
          const opt = this.options[this.selectedIndex];
          const precio = opt ? opt.getAttribute('data-precio') : null;
          if (precio && (!precioInput.value || parseFloat(precioInput.value) <= 0)) {
            precioInput.value = parseFloat(precio) || '';
          }
        });
      }

      formProv.addEventListener('submit', function(e) {
        const provSelect = document.getElementById('id_devprov_proveedor');
        let valid = true;

        if (provSelect && !provSelect.value) {
          provSelect.classList.add('is-invalid');
          valid = false;
        } else if (provSelect) {
          provSelect.classList.remove('is-invalid');
        }

        if (prodSelect && !prodSelect.value) {
          prodSelect.classList.add('is-invalid');
          valid = false;
        } else if (prodSelect) {
          prodSelect.classList.remove('is-invalid');
        }

        const cant = cantInput ? parseInt(cantInput.value, 10) : 0;
        if (cant <= 0) {
          if (cantInput) cantInput.classList.add('is-invalid');
          valid = false;
        } else if (cantInput) {
          cantInput.classList.remove('is-invalid');
        }

        const p = precioInput ? parseFloat(precioInput.value) : 0;
        if (p <= 0) {
          if (precioInput) precioInput.classList.add('is-invalid');
          valid = false;
        } else if (precioInput) {
          precioInput.classList.remove('is-invalid');
        }

        if (!valid) {
          e.preventDefault();
        }
      });
    }

    // 2. Acordeón de Historial de Clientes
    const historyToggle = document.getElementById('devHistoryToggle');
    const historyBody = document.getElementById('devHistoryBody');

    if (historyToggle && historyBody) {
      // Remover listener previo clonando o limpiando
      historyToggle.onclick = function() {
        const isOpen = !historyBody.classList.contains('d-none');
        historyBody.classList.toggle('d-none', isOpen);
        historyToggle.setAttribute('aria-expanded', String(!isOpen));
        if (!isOpen) {
          initTablaDevolucionesClientes();
        }
      };
    }

    // Botones de impresión (para comprobantes y detalles)
    document.querySelectorAll('.btn-print, .btn-print-action, #btnImprimirComprobante').forEach(function(btn) {
      btn.onclick = function(e) {
        e.preventDefault();
        window.print();
      };
    });

    // Inicializar ambas tablas
    initTablaDevolucionesClientes();
    initTablaDevolucionesProveedor();
  }

  // 3. Tabla Devoluciones Clientes (#tablaDevoluciones)
  function initTablaDevolucionesClientes() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const $table = jQuery('#tablaDevoluciones');
    if (!$table.length) return;

    if (jQuery.fn.DataTable.isDataTable($table)) {
      $table.DataTable().destroy();
    }

    const dt = $table.DataTable({
      responsive: true,
      paging: false,
      searching: false,
      lengthChange: false,
      info: false,
      order: [[5, 'desc']],
      columnDefs: [{ targets: [6], orderable: false, searchable: false }],
      language: {
        emptyTable: 'No hay devoluciones registradas.',
        zeroRecords: 'No encontramos coincidencias.'
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: null,
        bottomEnd: null
      },
      buttons: [
        {
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
          className: 'cys-dt-btn-excel',
          title: 'Devoluciones_Clientes_CYS',
          filename: 'Devoluciones_Clientes_CYS',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] }
        },
        {
          extend: 'pdfHtml5',
          text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
          className: 'cys-dt-btn-pdf',
          title: 'Distribuciones CYS Ltda - Historial de Devoluciones (Clientes)',
          filename: 'Devoluciones_Clientes_CYS',
          orientation: 'landscape',
          pageSize: 'A4',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] },
          customize: function (doc) {
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

    const exportContainer = document.getElementById('cys-dt-export-devoluciones');
    if (exportContainer) {
      exportContainer.innerHTML = '';
      dt.buttons().container().removeClass('d-none').appendTo(exportContainer);
    }
  }

  // 4. Tabla Devoluciones Proveedor (#tablaDevolucionesProveedor)
  function initTablaDevolucionesProveedor() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const $tableProv = jQuery('#tablaDevolucionesProveedor');
    if (!$tableProv.length) return;

    if (jQuery.fn.DataTable.isDataTable($tableProv)) {
      $tableProv.DataTable().destroy();
    }

    const dtProv = $tableProv.DataTable({
      responsive: true,
      paging: false,
      searching: false,
      lengthChange: false,
      info: false,
      order: [[0, 'desc']],
      columnDefs: [{ targets: [6], orderable: false, searchable: false }],
      language: {
        emptyTable: 'No hay devoluciones a proveedores registradas.',
        zeroRecords: 'No se encontraron registros.'
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: null,
        bottomEnd: null
      },
      buttons: [
        {
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
          className: 'cys-dt-btn-excel',
          title: 'Devoluciones_Proveedores_CYS',
          filename: 'Devoluciones_Proveedores_CYS',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] }
        },
        {
          extend: 'pdfHtml5',
          text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
          className: 'cys-dt-btn-pdf',
          title: 'Distribuciones CYS Ltda - Devoluciones a Proveedores',
          filename: 'Devoluciones_Proveedores_CYS',
          orientation: 'landscape',
          pageSize: 'A4',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] },
          customize: function (doc) {
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

    const contProv = document.getElementById('cys-dt-export-dev-proveedor');
    if (contProv) {
      contProv.innerHTML = '';
      dtProv.buttons().container().removeClass('d-none').appendTo(contProv);
    }
  }

  // Exponer globalmente
  window.initDevolucionesTables = initDevolucionesPage;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDevolucionesPage);
  } else {
    initDevolucionesPage();
  }

  if (document.body) {
    document.body.addEventListener('htmx:afterSettle', initDevolucionesPage);
  }
})();
