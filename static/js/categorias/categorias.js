/* ══════════════════════════════════════════
   categorias.js — CYS Ltda
   ══════════════════════════════════════════ */
(function () {
  "use strict";

  // htmx re-ejecuta el script en cada navegación: limpia la instancia anterior
  if (window.__cysCatCleanup) window.__cysCatCleanup();

  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => Array.from((c || document).querySelectorAll(s));

  const page = $(".cys-categorias-page");
  if (!page) return;

  const ctrl = new AbortController();
  const opt = { signal: ctrl.signal };
  window.__cysCatCleanup = function () {
    ctrl.abort();
    document.body.style.overflow = "";
  };

  const URL_EXCEL = page.dataset.urlExcel;
  const URL_PDF = page.dataset.urlPdf;

  /* ---------- Overlays ---------- */
  function abrirOverlay(o) { o.classList.add("is-open"); document.body.style.overflow = "hidden"; }
  function cerrarOverlay(o) {
    o.classList.remove("is-open");
    if (!$(".cys-modal-overlay.is-open")) document.body.style.overflow = "";
  }

  /* ---------- Exportar ---------- */
  const exportWrap = $("#cysExport");
  $("#cysExportTrigger").addEventListener("click", function (e) {
    e.stopPropagation();
    exportWrap.classList.toggle("is-open");
  }, opt);

  $$("#cysExportMenu li").forEach(function (li) {
    li.addEventListener("click", function () {
      exportWrap.classList.remove("is-open");
      const t = li.dataset.export;
      if (t === "excel") window.location.href = URL_EXCEL + window.location.search;
      else if (t === "pdf") window.location.href = URL_PDF + window.location.search;
      else window.print();
    }, opt);
  });

  /* ---------- Validación ---------- */
  const INV_NOMBRE = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g;
  const OK_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$/;
  const INV_CODIGO = /[^A-Za-z0-9]/g;
  const OK_CODIGO = /^[A-Za-z0-9]+$/;

  function mostrarError(input, msg) {
    const cont = input.closest(".cys-field");
    let err = cont.querySelector(".cys-error");
    if (!err) {
      err = document.createElement("small");
      err.className = "cys-error";
      cont.appendChild(err);
    }
    err.textContent = msg;
    err.style.display = msg ? "block" : "none";
    input.classList.toggle("is-invalid", !!msg);
  }

  function activarValidacion(form, fNombre, fCodigo) {
    function okNombre() {
      const v = fNombre.value.replace(/\s+/g, " ").trim();
      if (!v) { mostrarError(fNombre, "El nombre es obligatorio."); return false; }
      if (!OK_NOMBRE.test(v)) { mostrarError(fNombre, "Solo letras y espacios."); return false; }
      mostrarError(fNombre, ""); fNombre.value = v; return true;
    }
    function okCodigo() {
      const v = fCodigo.value.trim().toUpperCase();
      if (!v) { mostrarError(fCodigo, "El código es obligatorio."); return false; }
      if (!OK_CODIGO.test(v)) { mostrarError(fCodigo, "Solo letras y números, sin espacios ni símbolos."); return false; }
      if (!/[0-9]/.test(v)) { mostrarError(fCodigo, "El código debe llevar al menos un número."); return false; }
      mostrarError(fCodigo, ""); fCodigo.value = v; return true;
    }

    fNombre.addEventListener("input", function () {
      const limpio = fNombre.value.replace(INV_NOMBRE, "");
      mostrarError(fNombre, limpio !== fNombre.value ? "Solo se permiten letras y espacios." : "");
      fNombre.value = limpio;
    }, opt);

    fCodigo.addEventListener("input", function () {
      const cod = fCodigo.value.replace(INV_CODIGO, "").toUpperCase();
      mostrarError(fCodigo, cod !== fCodigo.value.toUpperCase() ? "Solo letras y números." : "");
      fCodigo.value = cod;
    }, opt);

    form.addEventListener("submit", function (e) {
      const a = okNombre();
      const b = okCodigo();
      if (!a || !b) { e.preventDefault(); (a ? fCodigo : fNombre).focus(); }
    }, opt);
  }

  /* ---------- Formulario crear (izquierda) ---------- */
  const crearForm = $("#cysCrearForm");
  const cNombre = $("#cNombre");
  const cCodigo = $("#cCodigo");
  activarValidacion(crearForm, cNombre, cCodigo);

  /* ---------- Modal editar ---------- */
  const modalOverlay = $("#cysModalOverlay");
  const editForm = $("#cysEditarForm");
  const fNombre = $("#fieldNombre");
  const fCodigo = $("#fieldCodigo");
  const fDesc = $("#fieldDescripcion");
  const charCount = $("#cysCharCount");
  activarValidacion(editForm, fNombre, fCodigo);

  function contador() {
    charCount.textContent = fDesc.value.length + "/" + (fDesc.maxLength > 0 ? fDesc.maxLength : 200);
  }
  fDesc.addEventListener("input", contador, opt);

  $$(".cys-action-btn--edit").forEach(function (btn) {
    btn.addEventListener("click", function () {
      editForm.action = btn.dataset.url;
      fNombre.value = btn.dataset.nombre || "";
      fCodigo.value = btn.dataset.codigo || "";
      fDesc.value = btn.dataset.descripcion || "";
      [fNombre, fCodigo].forEach(function (i) { mostrarError(i, ""); });
      contador();
      abrirOverlay(modalOverlay);
      fNombre.focus();
    }, opt);
  });

  $("#cysModalClose").addEventListener("click", function () { cerrarOverlay(modalOverlay); }, opt);
  $("#cysCancelBtn").addEventListener("click", function () { cerrarOverlay(modalOverlay); }, opt);

  /* ---------- Confirmar desactivación ---------- */
  const confirmOverlay = $("#cysConfirmOverlay");
  let formPendiente = null;

  $$(".cys-btn-confirmar-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      formPendiente = btn.closest("form");
      const nombre = formPendiente.dataset.nombre || "esta categoría";
      $("#cysConfirmText").textContent =
        "Las categorías no se eliminan, solo se desactivan para conservar el histórico de productos. " +
        '¿Deseas desactivar "' + nombre + '"?';
      abrirOverlay(confirmOverlay);
    }, opt);
  });

  $("#cysConfirmOk").addEventListener("click", function () {
    if (formPendiente) formPendiente.submit();
    cerrarOverlay(confirmOverlay);
  }, opt);
  $("#cysConfirmCancel").addEventListener("click", function () { cerrarOverlay(confirmOverlay); }, opt);
  $("#cysConfirmClose").addEventListener("click", function () { cerrarOverlay(confirmOverlay); }, opt);

  /* ---------- DATATABLES CATEGORÍAS ---------- */
  if (window.jQuery && jQuery.fn.DataTable) {
    const $tablaCat = jQuery("#tablaCategorias");
    if ($tablaCat.length && !jQuery.fn.DataTable.isDataTable($tablaCat)) {
      const dtCat = $tablaCat.DataTable({
        paging: true,
        pageLength: 10,
        lengthMenu: [5, 10, 25, 50, 100],
        searching: true,
        info: true,
        responsive: true,
        ordering: true,
        order: [[1, "asc"]],
        columnDefs: [{ targets: [5], orderable: false, searchable: false }],
        language: {
          emptyTable: "No hay categorías registradas.",
          zeroRecords: "Sin resultados para tu búsqueda.",
          info: "Mostrando _START_ a _END_ de _TOTAL_ categorías",
          infoEmpty: "Mostrando 0 a 0 de 0 categorías",
          infoFiltered: "(filtrado de _MAX_ totales)",
          lengthMenu: "Mostrar _MENU_ registros",
          search: "Buscar categoría:",
          paginate: { first: "«", previous: "‹", next: "›", last: "»" }
        }
      });

      // Filtros rápidos de estado (Todas, Activas, Inactivas)
      $$(".cys-filtro-estado-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {
          $$(".cys-filtro-estado-btn").forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
          const estado = btn.dataset.estado || "";
          // Búsqueda exacta (regex) para que "Activa" no coincida con "Inactiva"
          dtCat.column(4).search(estado ? "^" + estado + "$" : "", true, false).draw();
        }, opt);
      });
    }
  }

  /* ---------- Alertas ---------- */
  $$(".cys-alert").forEach(function (a) {
    setTimeout(function () {
      a.style.opacity = "0";
      setTimeout(function () { a.remove(); }, 400);
    }, 5000);
  });

  /* ---------- Cierres globales ---------- */
  document.addEventListener("click", function (e) {
    if (!e.target.closest("#cysExport")) exportWrap.classList.remove("is-open");
    if (e.target.classList.contains("cys-modal-overlay")) cerrarOverlay(e.target);
  }, opt);

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    exportWrap.classList.remove("is-open");
    $$(".cys-modal-overlay.is-open").forEach(cerrarOverlay);
  }, opt);
})();