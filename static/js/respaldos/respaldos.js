document.addEventListener('DOMContentLoaded', function () {
  // ── Buscador en vivo de respaldos ──
  var searchInput = document.getElementById('respSearchInput');
  var table = document.getElementById('tablaRespaldos');
  
  if (searchInput && table) {
    searchInput.addEventListener('input', function () {
      var query = this.value.toLowerCase().trim();
      var rows = table.querySelectorAll('tbody tr.resp-row');
      var visibleCount = 0;

      rows.forEach(function (row) {
        var text = row.innerText.toLowerCase();
        if (text.indexOf(query) !== -1) {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });

      var emptyRow = document.getElementById('respNoResults');
      if (emptyRow) {
        emptyRow.style.display = (visibleCount === 0 && rows.length > 0) ? '' : 'none';
      }
    });
  }

  // ── Modal de Edición ──
  var modalEditar = document.getElementById('modalEditarRespaldo');
  if (modalEditar) {
    modalEditar.addEventListener('show.bs.modal', function (event) {
      var button = event.relatedTarget;
      var id = button.getAttribute('data-id');
      var nombre = button.getAttribute('data-nombre') || '';
      var desc = button.getAttribute('data-desc') || '';
      var url = button.getAttribute('data-url') || '';

      var form = document.getElementById('formEditarRespaldo');
      var inputNombre = document.getElementById('editRespaldoNombre');
      var inputDesc = document.getElementById('editRespaldoDesc');

      if (form && url) form.action = url;
      if (inputNombre) inputNombre.value = nombre;
      if (inputDesc) inputDesc.value = desc;
    });
  }

  // ── Modal de Restauración ──
  var modalRestaurar = document.getElementById('modalRestaurarRespaldo');
  if (modalRestaurar) {
    modalRestaurar.addEventListener('show.bs.modal', function (event) {
      var button = event.relatedTarget;
      var nombre = button.getAttribute('data-nombre') || '';
      var fecha = button.getAttribute('data-fecha') || '';
      var tamano = button.getAttribute('data-tamano') || '';
      var url = button.getAttribute('data-url') || '';

      var form = document.getElementById('formRestaurarRespaldo');
      var lblNombre = document.getElementById('restoreRespaldoNombre');
      var lblMeta = document.getElementById('restoreRespaldoMeta');
      var chkConfirm = document.getElementById('chkConfirmRestore');
      var btnSubmit = document.getElementById('btnSubmitRestore');

      if (form && url) form.action = url;
      if (lblNombre) lblNombre.textContent = nombre;
      if (lblMeta) lblMeta.textContent = fecha + (tamano ? ' · ' + tamano : '');
      if (chkConfirm) chkConfirm.checked = false;
      if (btnSubmit) btnSubmit.disabled = true;
    });

    var chkConfirm = document.getElementById('chkConfirmRestore');
    var btnSubmit = document.getElementById('btnSubmitRestore');
    if (chkConfirm && btnSubmit) {
      chkConfirm.addEventListener('change', function () {
        btnSubmit.disabled = !this.checked;
      });
    }

    // Feedback al enviar restauración
    var formRestaurar = document.getElementById('formRestaurarRespaldo');
    if (formRestaurar) {
      formRestaurar.addEventListener('submit', function () {
        if (btnSubmit) {
          btnSubmit.disabled = true;
          btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Restaurando base de datos...';
        }
      });
    }
  }

  // ── Modal de Eliminación ──
  var modalEliminar = document.getElementById('modalEliminarRespaldo');
  if (modalEliminar) {
    modalEliminar.addEventListener('show.bs.modal', function (event) {
      var button = event.relatedTarget;
      var nombre = button.getAttribute('data-nombre') || '';
      var url = button.getAttribute('data-url') || '';

      var form = document.getElementById('formEliminarRespaldo');
      var lblNombre = document.getElementById('deleteRespaldoNombre');

      if (form && url) form.action = url;
      if (lblNombre) lblNombre.textContent = nombre;
    });
  }

  // ── Feedback al Crear Respaldo ──
  var formCrear = document.getElementById('formCrearRespaldo');
  if (formCrear) {
    formCrear.addEventListener('submit', function () {
      var btn = document.getElementById('btnSubmitCrear');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Generando copia de seguridad...';
      }
    });
  }

  // ── Feedback al Subir Respaldo ──
  var formSubir = document.getElementById('formSubirRespaldo');
  if (formSubir) {
    formSubir.addEventListener('submit', function () {
      var btn = document.getElementById('btnSubmitSubir');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Subiendo y registrando...';
      }
    });
  }
});
