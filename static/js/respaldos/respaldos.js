/* ════════════════════════════════════════════════════════════════
   RESPALDOS.JS — DataTables, filtros desplegables, menú (⋯),
   modales y carga por arrastrar/soltar (compatible con htmx)
   ════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function byId(id) {
    return document.getElementById(id);
  }

  function formatBytes(bytes) {
    if (!bytes || bytes <= 0) return '0 KB';
    var mb = bytes / (1024 * 1024);
    if (mb < 1) return (bytes / 1024).toFixed(1) + ' KB';
    return mb.toFixed(2) + ' MB';
  }

  function cerrarMenusResp() {
    document.querySelectorAll('#tablaRespaldos .dd-menu.open').forEach(function (m) {
      m.classList.remove('open');
    });
    document.querySelectorAll('#tablaRespaldos .dd-btn[aria-expanded="true"]').forEach(function (b) {
      b.setAttribute('aria-expanded', 'false');
    });
  }

  // ── DataTable + Buscador + Filtros desplegables ──
  function initTablaRespaldos() {
    var tabla = byId('tablaRespaldos');
    if (!tabla || !window.jQuery || !jQuery.fn.DataTable) return;

    if (jQuery.fn.DataTable.isDataTable(tabla)) {
      jQuery(tabla).DataTable().destroy();
    }

    var dt = jQuery(tabla).DataTable({
      paging: true,
      pageLength: 10,
      searching: true,
      info: true,
      lengthChange: false,
      ordering: true,
      order: [[2, 'desc']],
      columnDefs: [
        { orderable: false, targets: [0, 5], searchable: false }
      ],
      language: {
        info: 'Mostrando _START_ a _END_ de _TOTAL_ copias',
        infoEmpty: 'Mostrando 0 a 0 de 0 copias',
        infoFiltered: '(filtrado de _MAX_)',
        emptyTable: 'Aún no hay copias de seguridad registradas.',
        zeroRecords: 'No se encontraron copias de seguridad que coincidan con la búsqueda.',
        paginate: { first: '«', previous: '‹', next: '›', last: '»' }
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: 'info',
        bottomEnd: 'paging'
      }
    });

    dt.on('draw.dt', cerrarMenusResp);

    if (!window._cysRespExtSearchBound) {
      window._cysRespExtSearchBound = true;
      jQuery.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        if (settings.sTableId !== 'tablaRespaldos') return true;
        var rowNode = settings.aoData[dataIndex] && settings.aoData[dataIndex].nTr;
        if (!rowNode) return true;

        var desdeEl = byId('respFiltroDesde');
        var hastaEl = byId('respFiltroHasta');
        var estEl = byId('respFiltroEstado');

        var desde = desdeEl ? desdeEl.value : '';
        var hasta = hastaEl ? hastaEl.value : '';
        var estado = estEl ? estEl.value : 'todos';

        var fechaRow = rowNode.getAttribute('data-fecha') || '';
        var estadoRow = rowNode.getAttribute('data-estado') || '';

        if (desde && fechaRow && fechaRow < desde) return false;
        if (hasta && fechaRow && fechaRow > hasta) return false;
        if (estado && estado !== 'todos' && estadoRow !== estado) return false;
        return true;
      });
    }

    var searchInput = byId('respSearchInput');
    var btnBuscar = byId('resp-btn-buscar');
    var desdeEl = byId('respFiltroDesde');
    var hastaEl = byId('respFiltroHasta');
    var estadoEl = byId('respFiltroEstado');
    var btnLimpiar = byId('respBtnLimpiar');

    if (searchInput) {
      searchInput.oninput = function () {
        dt.search(this.value.trim()).draw();
      };
      searchInput.onkeydown = function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          dt.search(this.value.trim()).draw();
        }
      };
    }

    if (btnBuscar) {
      btnBuscar.onclick = function () {
        dt.search(searchInput ? searchInput.value.trim() : '').draw();
      };
    }

    [desdeEl, hastaEl, estadoEl].forEach(function (el) {
      if (el) {
        el.onchange = function () {
          dt.draw();
        };
      }
    });

    if (btnLimpiar) {
      btnLimpiar.onclick = function () {
        if (searchInput) searchInput.value = '';
        if (desdeEl) desdeEl.value = '';
        if (hastaEl) hastaEl.value = '';
        if (estadoEl) estadoEl.value = 'todos';
        dt.search('').draw();
      };
    }
  }

  // ── Menú flotante (⋯) + Delegación de botones de acciones ──
  function initAccionesRespaldos() {
    if (window._cysRespActionsBound) return;
    window._cysRespActionsBound = true;

    document.addEventListener('click', function (e) {
      // 1. Botón de tres puntos
      var ddBtn = e.target.closest('#tablaRespaldos .dd-btn');
      if (ddBtn) {
        e.stopPropagation();
        var wrap = ddBtn.closest('.dd-wrap');
        var menu = wrap && wrap.querySelector('.dd-menu');
        if (!menu) return;
        var yaAbierto = menu.classList.contains('open');
        cerrarMenusResp();
        if (!yaAbierto) {
          menu.classList.add('open');
          ddBtn.setAttribute('aria-expanded', 'true');
          var rect = ddBtn.getBoundingClientRect();
          var menuH = menu.offsetHeight || 180;
          var top = rect.bottom + 4;
          if (top + menuH > window.innerHeight - 8 && rect.top - menuH - 4 > 8) {
            top = rect.top - menuH - 4;
          }
          menu.style.top = top + 'px';
          menu.style.right = Math.max(8, window.innerWidth - rect.right) + 'px';
        }
        return;
      }

      // 2. Acción Editar
      var btnEditar = e.target.closest('#tablaRespaldos .btn-resp-editar');
      if (btnEditar) {
        cerrarMenusResp();
        var formE = byId('formEditarRespaldo');
        var inNom = byId('editRespaldoNombre');
        var inDesc = byId('editRespaldoDesc');
        var modalE = byId('modalEditarRespaldo');
        if (formE) formE.action = btnEditar.dataset.url || '';
        if (inNom) inNom.value = btnEditar.dataset.nombre || '';
        if (inDesc) inDesc.value = btnEditar.dataset.desc || '';
        if (modalE && window.bootstrap) {
          bootstrap.Modal.getOrCreateInstance(modalE).show();
        }
        return;
      }

      // 3. Acción Restaurar
      var btnRestaurar = e.target.closest('#tablaRespaldos .btn-resp-restaurar');
      if (btnRestaurar) {
        cerrarMenusResp();
        var formR = byId('formRestaurarRespaldo');
        var lblNom = byId('restoreRespaldoNombre');
        var lblMeta = byId('restoreRespaldoMeta');
        var chkConfirm = byId('chkConfirmRestore');
        var chkPrevio = byId('chkCrearPrevio');
        var btnSubmitR = byId('btnSubmitRestore');
        var modalR = byId('modalRestaurarRespaldo');
        if (formR) formR.action = btnRestaurar.dataset.url || '';
        if (lblNom) lblNom.textContent = btnRestaurar.dataset.nombre || '';
        if (lblMeta) {
          var fecha = btnRestaurar.dataset.fecha || '';
          var tam = btnRestaurar.dataset.tamano || '';
          lblMeta.textContent = fecha + (tam ? ' · ' + tam : '');
        }
        if (chkConfirm) chkConfirm.checked = false;
        if (chkPrevio) chkPrevio.checked = true;
        if (btnSubmitR) {
          btnSubmitR.disabled = true;
          btnSubmitR.innerHTML = '<i class="bi bi-arrow-counterclockwise me-1"></i> Sí, Restaurar Ahora';
        }
        if (modalR && window.bootstrap) {
          bootstrap.Modal.getOrCreateInstance(modalR).show();
        }
        return;
      }

      // 4. Acción Eliminar
      var btnEliminar = e.target.closest('#tablaRespaldos .btn-resp-eliminar');
      if (btnEliminar) {
        cerrarMenusResp();
        var formD = byId('formEliminarRespaldo');
        var lblDel = byId('deleteRespaldoNombre');
        var modalD = byId('modalEliminarRespaldo');
        if (formD) formD.action = btnEliminar.dataset.url || '';
        if (lblDel) lblDel.textContent = btnEliminar.dataset.nombre || '';
        if (modalD && window.bootstrap) {
          bootstrap.Modal.getOrCreateInstance(modalD).show();
        }
        return;
      }

      if (e.target.closest('#tablaRespaldos .dd-item')) {
        setTimeout(cerrarMenusResp, 0);
        return;
      }

      if (!e.target.closest('#tablaRespaldos .dd-wrap')) {
        cerrarMenusResp();
      }
    });

    window.addEventListener('scroll', cerrarMenusResp, true);
    window.addEventListener('resize', cerrarMenusResp);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') cerrarMenusResp();
    });
  }

  // ── Formularios de modales y Dropzone .sql ──
  function initModalesYDropzone() {
    var chkConfirm = byId('chkConfirmRestore');
    var btnSubmitRestore = byId('btnSubmitRestore');
    if (chkConfirm && btnSubmitRestore && !chkConfirm.dataset.bound) {
      chkConfirm.dataset.bound = '1';
      chkConfirm.addEventListener('change', function () {
        btnSubmitRestore.disabled = !this.checked;
      });
    }

    var formRestaurar = byId('formRestaurarRespaldo');
    if (formRestaurar && !formRestaurar.dataset.bound) {
      formRestaurar.dataset.bound = '1';
      formRestaurar.addEventListener('submit', function () {
        var btn = byId('btnSubmitRestore');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Restaurando base de datos...';
        }
      });
    }

    var formCrear = byId('formCrearRespaldo');
    if (formCrear && !formCrear.dataset.bound) {
      formCrear.dataset.bound = '1';
      formCrear.addEventListener('submit', function () {
        var btn = byId('btnSubmitCrear');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando respaldo...';
        }
      });
    }

    // Drag & Drop para Subir .sql
    var dropzone = byId('respDropzone');
    var fileInput = byId('subirArchivoSql');
    var dzTitle = byId('respDropzoneTitle');
    var dzSub = byId('respDropzoneSub');
    var errBox = byId('respSubirError');
    var formSubir = byId('formSubirRespaldo');

    function mostrarErrorSubida(msg) {
      if (!errBox) return;
      errBox.textContent = msg || '';
      errBox.classList.toggle('d-none', !msg);
    }

    function actualizarVistaArchivo(file) {
      mostrarErrorSubida('');
      if (!file) {
        if (dropzone) dropzone.classList.remove('has-file');
        if (dzTitle) dzTitle.textContent = 'Haz clic o arrastra tu archivo .sql aquí';
        if (dzSub) dzSub.textContent = 'Solo archivos .sql · Máximo 500 MB';
        return true;
      }
      if (!file.name.toLowerCase().endsWith('.sql')) {
        mostrarErrorSubida('El archivo debe tener extensión .sql.');
        if (fileInput) fileInput.value = '';
        if (dropzone) dropzone.classList.remove('has-file');
        return false;
      }
      if (file.size === 0) {
        mostrarErrorSubida('El archivo seleccionado está vacío.');
        if (fileInput) fileInput.value = '';
        if (dropzone) dropzone.classList.remove('has-file');
        return false;
      }
      if (file.size > 500 * 1024 * 1024) {
        mostrarErrorSubida('El archivo supera el límite permitido de 500 MB.');
        if (fileInput) fileInput.value = '';
        if (dropzone) dropzone.classList.remove('has-file');
        return false;
      }
      if (dropzone) dropzone.classList.add('has-file');
      if (dzTitle) dzTitle.textContent = file.name;
      if (dzSub) dzSub.textContent = formatBytes(file.size) + ' · Listo para subir';
      return true;
    }

    if (fileInput && !fileInput.dataset.bound) {
      fileInput.dataset.bound = '1';
      fileInput.addEventListener('change', function () {
        actualizarVistaArchivo(this.files && this.files[0]);
      });
    }

    if (dropzone && !dropzone.dataset.bound) {
      dropzone.dataset.bound = '1';
      ['dragenter', 'dragover'].forEach(function (evName) {
        dropzone.addEventListener(evName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.add('is-dragover');
        });
      });
      ['dragleave', 'drop'].forEach(function (evName) {
        dropzone.addEventListener(evName, function (e) {
          e.preventDefault();
          e.stopPropagation();
          dropzone.classList.remove('is-dragover');
        });
      });
      dropzone.addEventListener('drop', function (e) {
        var files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length && fileInput) {
          if (actualizarVistaArchivo(files[0])) {
            try {
              var dtFiles = new DataTransfer();
              dtFiles.items.add(files[0]);
              fileInput.files = dtFiles.files;
            } catch (err) {}
          }
        }
      });
    }

    var modalSubir = byId('modalSubirRespaldo');
    if (modalSubir && !modalSubir.dataset.bound) {
      modalSubir.dataset.bound = '1';
      modalSubir.addEventListener('hidden.bs.modal', function () {
        if (formSubir) formSubir.reset();
        actualizarVistaArchivo(null);
      });
    }

    if (formSubir && !formSubir.dataset.bound) {
      formSubir.dataset.bound = '1';
      formSubir.addEventListener('submit', function (e) {
        var f = fileInput && fileInput.files && fileInput.files[0];
        if (!f || !actualizarVistaArchivo(f)) {
          e.preventDefault();
          if (!f) mostrarErrorSubida('Selecciona un archivo .sql antes de subir.');
          return;
        }
        var btn = byId('btnSubmitSubir');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Subiendo y registrando...';
        }
      });
    }
  }

  function initRespaldosPage() {
    if (!document.querySelector('.respaldos-container')) return;
    initAccionesRespaldos();
    initTablaRespaldos();
    initModalesYDropzone();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRespaldosPage);
  } else {
    initRespaldosPage();
  }

  if (document.body) {
    document.body.addEventListener('htmx:afterSettle', initRespaldosPage);
  }
})();
