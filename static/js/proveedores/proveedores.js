// Inicializar gráficas
function initializeCharts() {
  const colores = {
    principal: '#4DA8DA',
    secundario: '#00C9A7',
    terciario: '#CF9C48',
    cuartario: '#9B59B6',
    quinto: '#22D3EE'
  };

  const gastosLabels = window.gastosLabels || [];
  const gastosData = window.gastosData || [];
  const gastosPorcentajes = window.gastosPorcentajes || [];

  const coloresGraficos = [
    colores.principal,
    colores.secundario,
    colores.terciario,
    colores.cuartario,
    colores.quinto
  ];

  // Gráfico de pastel: Gastos por proveedor
  const ctxGastosProveedor = document.getElementById('chartGastosProveedor');
  if (ctxGastosProveedor && gastosLabels.length > 0) {
    const gastosLabelsConPorcentaje = gastosLabels.map((label, idx) =>
      `${label} - ${gastosPorcentajes[idx]}%`
    );

    new Chart(ctxGastosProveedor, {
      type: 'doughnut',
      data: {
        labels: gastosLabelsConPorcentaje,
        datasets: [{
          data: gastosData,
          backgroundColor: coloresGraficos.slice(0, gastosLabels.length),
          borderColor: '#011936',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#FFFFFF',
              padding: 15,
              font: {
                size: 12,
                weight: 'bold'
              }
            }
          }
        }
      }
    });
  }
}

// Asegurar disponibilidad del helper de exportación unificado
if (typeof window.cysCrearDropdownExportar !== 'function') {
  window.cysCrearDropdownExportar = function(dt, containerOrId) {
    if (!dt) return;
    var container = typeof containerOrId === 'string' ? document.getElementById(containerOrId) : containerOrId;
    if (!container) return;

    var api = (typeof dt.button === 'function') ? dt : (window.jQuery && jQuery.fn && jQuery.fn.dataTable ? jQuery(dt).DataTable() : null);
    if (!api || typeof api.button !== 'function') return;

    if (!api._buttons || (typeof api.buttons === 'function' && api.buttons().count() === 0)) {
      var initOptions = (typeof api.init === 'function') ? api.init() : null;
      if (initOptions && initOptions.buttons && window.DataTable && window.DataTable.Buttons) {
        try { new window.DataTable.Buttons(api, initOptions.buttons); } catch (e) {}
      }
    }

    try {
      if (typeof api.buttons === 'function') {
        var dtBtns = api.buttons().container();
        if (dtBtns && dtBtns.length) {
          dtBtns.remove();
        }
      }
      var extraBtns = container.querySelectorAll('.dt-buttons, .cys-dt-btn-excel, .cys-dt-btn-pdf');
      extraBtns.forEach(function(el) { el.remove(); });
    } catch (eBtns) {}

    var btnPdf = container.querySelector('[data-cys-export="pdf"]');
    var btnExcel = container.querySelector('[data-cys-export="excel"]');

    function dispararExport(tipo) {
      var isPdf = (tipo === 'pdf');
      var primaryClass = isPdf ? '.cys-dt-btn-pdf' : '.cys-dt-btn-excel';
      var fallbackClass = isPdf ? '.buttons-pdf' : '.buttons-excel';

      try {
        var b = api.button(primaryClass);
        if (b && b.length) { b.trigger(); return; }
      } catch (e1) {}

      try {
        var b2 = api.button(fallbackClass);
        if (b2 && b2.length) { b2.trigger(); return; }
      } catch (e2) {}

      try {
        if (typeof api.buttons === 'function') {
          var btns = api.buttons();
          var count = (typeof btns.count === 'function') ? btns.count() : (btns.length || 0);
          for (var i = 0; i < count; i++) {
            var singleBtn = api.button(i);
            var node = singleBtn.node();
            if (node) {
              var cls = (node.className || '').toLowerCase();
              var txt = (node.textContent || '').toLowerCase();
              if (isPdf && (cls.indexOf('pdf') !== -1 || txt.indexOf('pdf') !== -1)) {
                singleBtn.trigger(); return;
              }
              if (!isPdf && (cls.indexOf('excel') !== -1 || txt.indexOf('excel') !== -1)) {
                singleBtn.trigger(); return;
              }
            }
          }
          if (count >= 2) {
            api.button(isPdf ? 1 : 0).trigger();
            return;
          }
        }
      } catch (e3) {
        console.error('Error al exportar ' + tipo, e3);
      }
    }

    if (btnPdf && !btnPdf.dataset.cysExportBound) {
      btnPdf.dataset.cysExportBound = 'true';
      btnPdf.addEventListener('click', function(e) {
        e.preventDefault();
        dispararExport('pdf');
      });
    }

    if (btnExcel && !btnExcel.dataset.cysExportBound) {
      btnExcel.dataset.cysExportBound = 'true';
      btnExcel.addEventListener('click', function(e) {
        e.preventDefault();
        dispararExport('excel');
      });
    }
  };
}

$(document).ready(function() {
  // Inicializar gráficas
  initializeCharts();

  if ($.fn.DataTable.isDataTable('#tablaProveedores')) {
    $('#tablaProveedores').DataTable().destroy();
  }

  var table = $('#tablaProveedores').DataTable({
    responsive: true,
    paging: true,
    searching: true,
    info: true,
    lengthChange: false,
    pageLength: 10,
    ordering: true,
    columnDefs: [
      { orderable: false, targets: 8, searchable: false }
    ],
    language: {
      info: "Mostrando _START_ a _END_ de _TOTAL_ proveedores",
      infoEmpty: "Mostrando 0 a 0 de 0 proveedores",
      emptyTable: "No hay proveedores registrados.",
      zeroRecords: "Sin resultados para tu búsqueda.",
      paginate: { first:'«', previous:'‹', next:'›', last:'»' }
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
        title: 'Distribuciones CYS Ltda - Reporte de Proveedores',
        filename: 'Proveedores_CYS',
        exportOptions: {
          columns: [0, 1, 2, 3, 4, 5, 6, 7]
        }
      },
      {
        extend: 'pdfHtml5',
        text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
        className: 'cys-dt-btn-pdf',
        title: 'Distribuciones CYS Ltda - Reporte de Proveedores',
        filename: 'Proveedores_CYS',
        orientation: 'landscape',
        pageSize: 'A4',
        exportOptions: {
          columns: [0, 1, 2, 3, 4, 5, 6, 7]
        },
        customize: function (doc) {
          doc.defaultStyle.fontSize = 9;
          if (doc.styles && doc.styles.tableHeader) {
            doc.styles.tableHeader.fontSize = 10;
            doc.styles.tableHeader.bold = true;
            doc.styles.tableHeader.fillColor = '#011936';
            doc.styles.tableHeader.color = '#CF9C48';
            doc.styles.tableHeader.alignment = 'center';
          }
          if (doc.content && doc.content[1] && doc.content[1].table) {
            doc.content[1].table.widths = ['5%', '24%', '12%', '14%', '12%', '10%', '13%', '10%'];
          }
        }
      }
    ]
  });

  // Colocar el dropdown de exportación (PDF y Excel) en la barra de herramientas
  if (typeof window.cysCrearDropdownExportar === 'function') {
    window.cysCrearDropdownExportar(table, 'cys-dt-export-proveedores');
  }

  // Conectar input principal de búsqueda y botón lupa
  $('#buscar-proveedores').on('input', function() {
    table.search(this.value.trim()).draw();
  });

  $('#buscar-proveedores').on('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      table.search(this.value.trim()).draw();
    }
  });

  $('#prov-btn-buscar').on('click', function() {
    table.search($('#buscar-proveedores').val().trim()).draw();
  });

  // Filtro por NIT (columna 2)
  $('#prov-f-nit').on('input', function() {
    table.column(2).search(this.value.trim()).draw();
  });

  // Filtro por estado y tipo (solo se registra una vez en DataTables)
  if (!window._cysProvExtSearchBound) {
    window._cysProvExtSearchBound = true;
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
      if (settings.sTableId !== 'tablaProveedores') return true;
      var estadoSel = $('#prov-f-estado').val() || 'todos';
      var tipoSel = $('#prov-f-tipo').val() || 'todos';
      var rowNode = settings.aoData[dataIndex] && settings.aoData[dataIndex].nTr;
      if (!rowNode) return true;
      if (estadoSel !== 'todos' && $(rowNode).attr('data-estado') !== estadoSel) return false;
      if (tipoSel !== 'todos' && $(rowNode).attr('data-tipo') !== tipoSel) return false;
      return true;
    });
  }

  $('#prov-f-estado, #prov-f-tipo').on('change', function() {
    table.draw();
  });

  // Botón Limpiar filtros
  $('#prov-btn-limpiar').on('click', function() {
    $('#buscar-proveedores').val('');
    $('#prov-f-nit').val('');
    $('#prov-f-tipo').val('todos');
    $('#prov-f-estado').val('todos');
    table.search('').columns().search('').draw();
    syncExportProv();
  });

  // Sincronizar export (si se usan filtros)
  function syncExportProv() {
    var q = $('#buscar-proveedores').val() || '';
    var p = q ? ('&q=' + encodeURIComponent(q)) : '';
    if (typeof $('#btn-export-excel-prov') !== 'undefined') {
      $('#btn-export-excel-prov').attr('href', '?export=excel&tipo=proveedores' + p);
      $('#btn-export-pdf-prov').attr('href',   '?export=pdf&tipo=proveedores' + p);
    }
  }
  $('#buscar-proveedores').on('keyup change', syncExportProv);
  syncExportProv();

  // Aplicar ancho dinámico a las barras desde data-width
  document.querySelectorAll('.bar-visual').forEach(bar => {
    const width = bar.getAttribute('data-width');
    if (width) {
      bar.style.width = width + '%';
    }
  });

  // ============================================
  // VALIDACIÓN DE NUEVO PROVEEDOR
  // ============================================
  const formNuevoProveedor = document.getElementById('formNuevoProveedor');
  const modalNuevoProveedor = document.getElementById('modalNuevoProveedor');

  if (formNuevoProveedor && modalNuevoProveedor) {
    const limpiarErroresProveedor = () => {
      document.querySelectorAll('#formNuevoProveedor .invalid-feedback').forEach(el => {
        el.innerHTML = '';
        el.classList.remove('d-block');
      });
      document.querySelectorAll('#formNuevoProveedor .prod-input').forEach(el => {
        el.classList.remove('is-invalid');
      });
    };

    // Limpiar errores cuando se cierre el modal
    modalNuevoProveedor.addEventListener('hidden.bs.modal', function() {
      limpiarErroresProveedor();
      formNuevoProveedor.reset();
    });

    // Limpiar error de un campo individual al escribir
    formNuevoProveedor.querySelectorAll('.prod-input').forEach(input => {
      input.addEventListener('input', function() {
        this.classList.remove('is-invalid');
        const errDiv = this.parentElement.querySelector('.invalid-feedback');
        if (errDiv) {
          errDiv.innerHTML = '';
          errDiv.classList.remove('d-block');
        }
      });
    });

    // Manejar el envío del formulario
    formNuevoProveedor.addEventListener('submit', function(e) {
      e.preventDefault();
      limpiarErroresProveedor();

      // Enviar formulario via AJAX
      const formData = new FormData(this);
      fetch(this.action, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Mostrar toast de éxito
          showToast('Proveedor registrado exitosamente', 'success');

          // Cerrar modal y recargar tabla después de 2 segundos
          const modal = bootstrap.Modal.getInstance(modalNuevoProveedor);
          modal.hide();
          setTimeout(() => location.reload(), 1500);
        } else {
          // Mostrar errores debajo de cada campo
          if (data.errors) {
            for (const [field, messages] of Object.entries(data.errors)) {
              const errorDiv = document.getElementById(`error-${field}`);
              const input = document.getElementById(`id_${field}`);
              if (errorDiv && input) {
                const errorMsg = Array.isArray(messages) ? messages[0] : messages;
                errorDiv.textContent = '';
                const small = document.createElement('small');
                small.className = 'text-danger fw-bold';
                const icon = document.createElement('i');
                icon.className = 'bi bi-exclamation-circle me-1';
                small.append(icon, document.createTextNode(String(errorMsg)));
                errorDiv.appendChild(small);
                errorDiv.classList.add('d-block');
                input.classList.add('is-invalid');
              }
            }
          }
        }
      })
      .catch(error => console.error('Error:', error));
    });
  }

  // Función para mostrar notificaciones estilo Bootstrap Alert
  function showToast(message, type = 'success') {
    const mainContent = document.querySelector('main') || document.body;

    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-circle';

    const alertHTML = `
      <div class="alert ${alertClass} alert-dismissible fade show d-flex align-items-center" role="alert" style="margin: 0; border-radius: 0; position: sticky; top: 0; z-index: 1050;">
        <i class="bi ${icon} me-2"></i>
        <div>${message}</div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
      </div>
    `;

    mainContent.insertAdjacentHTML('afterbegin', alertHTML);
  }

  // ============================================
  // MENÚ DE ACCIONES (⋯) CON POSICIONAMIENTO FIJO
  // ============================================
  function cerrarDropdownsProv() {
    document.querySelectorAll('#tablaProveedores .dd-menu.open').forEach(m => m.classList.remove('open'));
    document.querySelectorAll('#tablaProveedores .dd-btn[aria-expanded="true"]').forEach(b => b.setAttribute('aria-expanded', 'false'));
  }

  table.on('draw.dt', cerrarDropdownsProv);

  if (!window._cysProvDdBound) {
    window._cysProvDdBound = true;

    document.addEventListener('click', function(e) {
      const btn = e.target.closest('#tablaProveedores .dd-btn');
      if (btn) {
        e.stopPropagation();
        const wrap = btn.closest('.dd-wrap');
        const menu = wrap && wrap.querySelector('.dd-menu');
        if (!menu) return;
        const yaAbierto = menu.classList.contains('open');
        cerrarDropdownsProv();
        if (!yaAbierto) {
          menu.classList.add('open');
          btn.setAttribute('aria-expanded', 'true');
          const rect = btn.getBoundingClientRect();
          const menuH = menu.offsetHeight || 160;
          let top = rect.bottom + 4;
          if (top + menuH > window.innerHeight - 8 && rect.top - menuH - 4 > 8) {
            top = rect.top - menuH - 4;
          }
          menu.style.top = top + 'px';
          menu.style.right = Math.max(8, window.innerWidth - rect.right) + 'px';
        }
        return;
      }

      if (e.target.closest('#tablaProveedores .dd-item')) {
        setTimeout(cerrarDropdownsProv, 0);
        return;
      }

      if (!e.target.closest('#tablaProveedores .dd-wrap')) {
        cerrarDropdownsProv();
      }
    });

    window.addEventListener('scroll', cerrarDropdownsProv, true);
    window.addEventListener('resize', cerrarDropdownsProv);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') cerrarDropdownsProv();
    });
  }

  // ============================================
  // MANEJO DE ACCIONES CON MODALES (delegado para paginación DataTables)
  // ============================================

  if (!window._cysProvActionsBound) {
    window._cysProvActionsBound = true;

    document.addEventListener('click', function(e) {
      // Desactivar proveedor
      const btnDesactivar = e.target.closest('.btn-desactivar');
      if (btnDesactivar) {
        const providerId = btnDesactivar.dataset.providerId;
        const providerName = btnDesactivar.dataset.providerName;

        document.getElementById('proveedorDesactivarNombre').textContent = providerName;
        const modalElement = document.getElementById('modalDesactivarGeneral');
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();

        const form = document.getElementById('formDesactivarProveedor');
        form.onsubmit = function(ev) {
          ev.preventDefault();
          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          fetch(`/proveedores/modal/desactivar/${providerId}/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                modal.hide();
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
              } else {
                showToast(data.error || 'Error al desactivar', 'error');
              }
            })
            .catch(error => {
              console.error('Error:', error);
              showToast('Error en la solicitud', 'error');
            });
        };
        return;
      }

      // Reactivar proveedor
      const btnReactivar = e.target.closest('.btn-reactivar');
      if (btnReactivar) {
        const providerId = btnReactivar.dataset.providerId;
        const providerName = btnReactivar.dataset.providerName;

        if (confirm(`¿Deseas reactivar a ${providerName}?`)) {
          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          fetch(`/proveedores/modal/reactivar/${providerId}/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
              } else {
                showToast(data.error || 'Error al reactivar', 'error');
              }
            })
            .catch(error => console.error('Error:', error));
        }
        return;
      }

      // Sancionar proveedor
      const btnSancionar = e.target.closest('.btn-sancionar');
      if (btnSancionar) {
        const providerId = btnSancionar.dataset.providerId;
        const providerName = btnSancionar.dataset.providerName;

        document.getElementById('proveedorSancionarNombre').textContent = providerName;
        document.getElementById('motivoSancion').value = '';

        const modalElement = document.getElementById('modalSancionarGeneral');
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();

        const form = document.getElementById('formSancionar');
        form.onsubmit = function(ev) {
          ev.preventDefault();
          const observacion = document.getElementById('motivoSancion').value;
          if (!observacion.trim()) {
            showToast('Debes indicar el motivo de la sanción', 'error');
            return;
          }

          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          const formData = new FormData();
          formData.append('observacion', observacion);
          formData.append('csrfmiddlewaretoken', csrfToken);

          fetch(`/proveedores/modal/sancionar/${providerId}/`, {
            method: 'POST',
            body: formData,
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                modal.hide();
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
              } else {
                showToast(data.error || 'Error al sancionar', 'error');
              }
            })
            .catch(error => {
              console.error('Error:', error);
              showToast('Error en la solicitud', 'error');
            });
        };
        return;
      }

      // Levantar sanción
      const btnLevantar = e.target.closest('.btn-levantar-sancion');
      if (btnLevantar) {
        const providerId = btnLevantar.dataset.providerId;
        const providerName = btnLevantar.dataset.providerName;

        if (confirm(`¿Deseas levantar la sanción a ${providerName}?`)) {
          const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
          fetch(`/proveedores/modal/levantar-sancion/${providerId}/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 1500);
              } else {
                showToast(data.error || 'Error al levantar sanción', 'error');
              }
            })
            .catch(error => console.error('Error:', error));
        }
      }
    });
  }
});
