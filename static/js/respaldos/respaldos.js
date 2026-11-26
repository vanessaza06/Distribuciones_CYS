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
        var errEdit = byId('respEditarError');
        var modalE = byId('modalEditarRespaldo');
        if (formE) formE.action = btnEditar.dataset.url || '';
        if (inNom) {
          inNom.value = btnEditar.dataset.nombre || '';
          inNom.classList.remove('is-invalid');
        }
        if (inDesc) inDesc.value = btnEditar.dataset.desc || '';
        if (errEdit) {
          errEdit.textContent = '';
          errEdit.classList.add('d-none');
        }
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

  // ── Validaciones de nombre de respaldo y contenido .sql ──
  var RE_LETRAS_INICIO = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3}/;
  var RE_NOMBRE_RESPALDO = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3}[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _.-]*$/;
  var RE_SQL_DATA = /\b(?:INSERT\s+(?:LOW_PRIORITY\s+|DELAYED\s+|HIGH_PRIORITY\s+)?(?:IGNORE\s+)?INTO\s+[`"'\w.]+(?:\s*\([^)]*\))?\s+(?:(?:VALUES|VALUE)\s*\(\s*[^)\s]|SET\s+\S|SELECT\s+\S)|REPLACE\s+(?:LOW_PRIORITY\s+|DELAYED\s+)?INTO\s+[`"'\w.]+(?:\s*\([^)]*\))?\s+(?:(?:VALUES|VALUE)\s*\(\s*[^)\s]|SET\s+\S|SELECT\s+\S)|LOAD\s+DATA\s+(?:LOW_PRIORITY\s+|CONCURRENT\s+)?(?:LOCAL\s+)?INFILE\s+\S)/i;
  var RE_SQL_ESTRUCTURA = /\b(?:CREATE|DROP|ALTER|TRUNCATE|LOCK|UNLOCK|SET|USE)\s+(?:TABLE|DATABASE|SCHEMA|VIEW|INDEX|TRIGGER|TABLES|NAMES)\b/i;

  function validarNombreRespaldo(valor, obligatorio) {
    var raw = (valor || '').trim();
    if (!raw) {
      return obligatorio ? 'El nombre de la copia de seguridad es obligatorio.' : '';
    }
    if (raw.indexOf('/') !== -1 || raw.indexOf('\\') !== -1) {
      return 'El nombre no puede contener barras (/ o \\).';
    }
    var base = raw.toLowerCase().endsWith('.sql') ? raw.slice(0, -4) : raw;
    if (base.length > 80) {
      return 'El nombre de la copia de seguridad no puede superar 80 caracteres.';
    }
    if (!RE_LETRAS_INICIO.test(base)) {
      return 'El nombre de la copia de seguridad debe comenzar con 3 letras (no se permiten números, puntos ni símbolos al principio).';
    }
    if (base.indexOf('..') !== -1 || base.endsWith('.')) {
      return 'El nombre no puede contener puntos seguidos (..) ni terminar en punto.';
    }
    if (!RE_NOMBRE_RESPALDO.test(base)) {
      return 'El nombre contiene caracteres no permitidos. Usa solo letras, números, espacios, puntos, guiones (-) o guion bajo (_).';
    }
    return '';
  }

  function quitarComentariosSql(texto) {
    var out = [];
    var i = 0;
    var n = texto.length;
    var enBloque = false;
    var enLinea = false;
    var comilla = null;
    var escape = false;

    while (i < n) {
      var ch = texto[i];
      if (enLinea) {
        if (ch === '\n') {
          enLinea = false;
          out.push('\n');
        }
        i += 1;
        continue;
      }
      if (enBloque) {
        if (ch === '*' && i + 1 < n && texto[i + 1] === '/') {
          enBloque = false;
          out.push(' ');
          i += 2;
        } else {
          i += 1;
        }
        continue;
      }
      if (comilla) {
        out.push(ch);
        if (escape) {
          escape = false;
        } else if (ch === '\\') {
          escape = true;
        } else if (ch === comilla) {
          comilla = null;
        }
        i += 1;
        continue;
      }
      if (ch === "'" || ch === '"') {
        comilla = ch;
        out.push(ch);
        i += 1;
        continue;
      }
      if (ch === '#') {
        enLinea = true;
        out.push(' ');
        i += 1;
        continue;
      }
      if (ch === '-' && i + 1 < n && texto[i + 1] === '-') {
        var sig = i + 2 < n ? texto[i + 2] : '\n';
        if (sig === ' ' || sig === '\t' || sig === '\r' || sig === '\n' || sig === '-') {
          enLinea = true;
          out.push(' ');
          i += 2;
          continue;
        }
      }
      if (ch === '/' && i + 1 < n && texto[i + 1] === '*') {
        enBloque = true;
        out.push(' ');
        i += 2;
        continue;
      }
      out.push(ch);
      i += 1;
    }
    return out.join('');
  }

  function validarContenidoSqlTexto(texto, esMuestraParcial) {
    if (!texto) {
      return 'El archivo seleccionado está vacío.';
    }
    if (texto.indexOf('\u0000') !== -1) {
      return 'El archivo no es un archivo .sql de texto válido.';
    }
    var sinBom = texto.charCodeAt(0) === 0xFEFF ? texto.slice(1) : texto;
    var limpio = quitarComentariosSql(sinBom);
    if (!limpio.trim()) {
      return 'El archivo .sql está vacío o solo contiene comentarios, sin datos.';
    }
    if (RE_SQL_DATA.test(limpio)) {
      return '';
    }
    // Si el archivo supera 5 MB y solo leímos el inicio, el servidor validará el resto
    if (esMuestraParcial) {
      return '';
    }
    if (RE_SQL_ESTRUCTURA.test(limpio)) {
      return 'El archivo .sql solo contiene estructura y no tiene datos (registros INSERT) para restaurar.';
    }
    return 'El archivo .sql no contiene datos ni sentencias SQL válidas para restaurar.';
  }

  function mostrarErrorCampo(input, errBox, msg) {
    if (errBox) {
      errBox.textContent = msg || '';
      errBox.classList.toggle('d-none', !msg);
    }
    if (input) {
      input.classList.toggle('is-invalid', Boolean(msg));
    }
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

    // Modal Crear copia de seguridad
    var formCrear = byId('formCrearRespaldo');
    var inCrearNom = byId('crearRespaldoNombre');
    var errCrear = byId('respCrearError');
    var modalCrear = byId('modalCrearRespaldo');

    if (inCrearNom && !inCrearNom.dataset.bound) {
      inCrearNom.dataset.bound = '1';
      inCrearNom.addEventListener('input', function () {
        var val = this.value.trim();
        var msg = val ? validarNombreRespaldo(val, false) : '';
        mostrarErrorCampo(inCrearNom, errCrear, msg);
      });
    }

    if (modalCrear && !modalCrear.dataset.bound) {
      modalCrear.dataset.bound = '1';
      modalCrear.addEventListener('hidden.bs.modal', function () {
        if (formCrear) formCrear.reset();
        mostrarErrorCampo(inCrearNom, errCrear, '');
      });
    }

    if (formCrear && !formCrear.dataset.bound) {
      formCrear.dataset.bound = '1';
      formCrear.addEventListener('submit', function (e) {
        var msg = validarNombreRespaldo(inCrearNom ? inCrearNom.value : '', false);
        if (msg) {
          e.preventDefault();
          mostrarErrorCampo(inCrearNom, errCrear, msg);
          if (inCrearNom) inCrearNom.focus();
          return;
        }
        mostrarErrorCampo(inCrearNom, errCrear, '');
        var btn = byId('btnSubmitCrear');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando respaldo...';
        }
      });
    }

    // Modal Editar copia de seguridad
    var formEditar = byId('formEditarRespaldo');
    var inEditarNom = byId('editRespaldoNombre');
    var errEditar = byId('respEditarError');
    var modalEditar = byId('modalEditarRespaldo');

    if (inEditarNom && !inEditarNom.dataset.bound) {
      inEditarNom.dataset.bound = '1';
      inEditarNom.addEventListener('input', function () {
        var msg = validarNombreRespaldo(this.value, true);
        mostrarErrorCampo(inEditarNom, errEditar, msg);
      });
    }

    if (modalEditar && !modalEditar.dataset.bound) {
      modalEditar.dataset.bound = '1';
      modalEditar.addEventListener('hidden.bs.modal', function () {
        mostrarErrorCampo(inEditarNom, errEditar, '');
      });
    }

    if (formEditar && !formEditar.dataset.bound) {
      formEditar.dataset.bound = '1';
      formEditar.addEventListener('submit', function (e) {
        var msg = validarNombreRespaldo(inEditarNom ? inEditarNom.value : '', true);
        if (msg) {
          e.preventDefault();
          mostrarErrorCampo(inEditarNom, errEditar, msg);
          if (inEditarNom) inEditarNom.focus();
          return;
        }
        mostrarErrorCampo(inEditarNom, errEditar, '');
      });
    }

    // Drag & Drop para Subir .sql
    var dropzone = byId('respDropzone');
    var fileInput = byId('subirArchivoSql');
    var dzTitle = byId('respDropzoneTitle');
    var dzSub = byId('respDropzoneSub');
    var errBox = byId('respSubirError');
    var formSubir = byId('formSubirRespaldo');
    var btnSubmitSubir = byId('btnSubmitSubir');
    var MAX_CLIENT_READ_BYTES = 5 * 1024 * 1024;
    var estadoArchivo = {
      valido: false,
      validando: false,
      seq: 0,
      error: ''
    };

    function mostrarErrorSubida(msg) {
      if (!errBox) return;
      errBox.textContent = msg || '';
      errBox.classList.toggle('d-none', !msg);
    }

    function resetDropzoneVisual() {
      if (dropzone) dropzone.classList.remove('has-file');
      if (dzTitle) dzTitle.textContent = 'Haz clic o arrastra tu archivo .sql aquí';
      if (dzSub) dzSub.textContent = 'Solo archivos .sql · Máximo 500 MB';
    }

    function invalidarArchivoSubida(msg) {
      estadoArchivo.valido = false;
      estadoArchivo.validando = false;
      estadoArchivo.error = msg || '';
      mostrarErrorSubida(msg);
      if (fileInput) fileInput.value = '';
      resetDropzoneVisual();
      if (btnSubmitSubir) btnSubmitSubir.disabled = false;
    }

    function actualizarVistaArchivo(file, onDone) {
      estadoArchivo.seq += 1;
      var mySeq = estadoArchivo.seq;
      mostrarErrorSubida('');

      if (!file) {
        estadoArchivo.valido = false;
        estadoArchivo.validando = false;
        estadoArchivo.error = '';
        resetDropzoneVisual();
        if (btnSubmitSubir) btnSubmitSubir.disabled = false;
        if (onDone) onDone(false);
        return false;
      }

      if (!file.name.toLowerCase().endsWith('.sql')) {
        invalidarArchivoSubida('El archivo debe tener extensión .sql.');
        if (onDone) onDone(false);
        return false;
      }

      var errNomArchivo = validarNombreRespaldo(file.name, true);
      if (errNomArchivo) {
        invalidarArchivoSubida(errNomArchivo);
        if (onDone) onDone(false);
        return false;
      }

      if (file.size === 0) {
        invalidarArchivoSubida('El archivo seleccionado está vacío.');
        if (onDone) onDone(false);
        return false;
      }

      if (file.size > 500 * 1024 * 1024) {
        invalidarArchivoSubida('El archivo supera el límite permitido de 500 MB.');
        if (onDone) onDone(false);
        return false;
      }

      // Inspección de contenido del archivo .sql (evitar archivos vacíos, solo comentarios o sin datos)
      estadoArchivo.valido = false;
      estadoArchivo.validando = true;
      estadoArchivo.error = '';
      if (dropzone) dropzone.classList.add('has-file');
      if (dzTitle) dzTitle.textContent = file.name;
      if (dzSub) dzSub.textContent = formatBytes(file.size) + ' · Verificando contenido SQL...';
      if (btnSubmitSubir) btnSubmitSubir.disabled = true;

      var esParcial = file.size > MAX_CLIENT_READ_BYTES;
      var blob = esParcial ? file.slice(0, MAX_CLIENT_READ_BYTES) : file;
      var reader = new FileReader();

      reader.onload = function () {
        if (mySeq !== estadoArchivo.seq) return;
        var texto = typeof reader.result === 'string' ? reader.result : '';
        var errSql = validarContenidoSqlTexto(texto, esParcial);
        if (errSql) {
          invalidarArchivoSubida(errSql);
          if (onDone) onDone(false);
          return;
        }
        estadoArchivo.valido = true;
        estadoArchivo.validando = false;
        estadoArchivo.error = '';
        if (dropzone) dropzone.classList.add('has-file');
        if (dzTitle) dzTitle.textContent = file.name;
        if (dzSub) dzSub.textContent = formatBytes(file.size) + ' · Listo para subir';
        if (btnSubmitSubir) btnSubmitSubir.disabled = false;
        if (onDone) onDone(true);
      };

      reader.onerror = function () {
        if (mySeq !== estadoArchivo.seq) return;
        invalidarArchivoSubida('No se pudo leer el archivo seleccionado.');
        if (onDone) onDone(false);
      };

      reader.readAsText(blob, 'UTF-8');
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
          var dropped = files[0];
          actualizarVistaArchivo(dropped, function (ok) {
            if (ok) {
              try {
                var dtFiles = new DataTransfer();
                dtFiles.items.add(dropped);
                fileInput.files = dtFiles.files;
              } catch (err) {}
            }
          });
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
        if (!f) {
          e.preventDefault();
          mostrarErrorSubida('Selecciona un archivo .sql antes de subir.');
          return;
        }
        if (estadoArchivo.validando) {
          e.preventDefault();
          mostrarErrorSubida('Espera un momento mientras se valida el archivo .sql...');
          return;
        }
        if (!estadoArchivo.valido) {
          e.preventDefault();
          mostrarErrorSubida(estadoArchivo.error || 'El archivo .sql seleccionado no es válido.');
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
