/* ══════════════════════════════════════════
   categorias.js — CYS Ltda
   1. Utilidades        5. Validación
   2. Exportar          6. Confirmar desactivación
   3. Filtros / select  7. Menú de fila
   4. Modal crear/editar 8. Ordenar tabla / alertas
   ══════════════════════════════════════════ */
(function () {
  "use strict";

  /* ---------- 1. UTILIDADES ---------- */
  const $ = (sel, ctx) => (ctx || document).querySelector(sel);
  const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

  const page = $(".cys-categorias-page");
  if (!page) return;

  const URL_CREAR = page.dataset.urlCrear;
  const URL_EXCEL = page.dataset.urlExcel;
  const URL_PDF = page.dataset.urlPdf;

  function abrirOverlay(overlay) {
    overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }
  function cerrarOverlay(overlay) {
    overlay.classList.remove("is-open");
    if (!$(".cys-modal-overlay.is-open")) document.body.style.overflow = "";
  }
  function cerrarOverlays() {
    $$(".cys-modal-overlay.is-open").forEach(cerrarOverlay);
  }

  /* ---------- 2. EXPORTAR ---------- */
  const exportWrap = $("#cysExport");
  const exportTrigger = $("#cysExportTrigger");

  exportTrigger.addEventListener("click", function (e) {
    e.stopPropagation();
    exportWrap.classList.toggle("is-open");
  });

  $$("#cysExportMenu li").forEach(function (li) {
    li.addEventListener("click", function () {
      const tipo = li.dataset.export;
      exportWrap.classList.remove("is-open");
      if (tipo === "excel") window.location.href = URL_EXCEL + window.location.search;
      else if (tipo === "pdf") window.location.href = URL_PDF + window.location.search;
      else if (tipo === "imprimir") window.print();
    });
  });

  /* ---------- 3. FILTROS / SELECT ESTADO ---------- */
  const filtroForm = $("#cysFiltroForm");
  const filtrosBtn = $("#cysFiltrosBtn");
  const filtrosPanel = $("#cysFiltrosPanel");

  filtrosBtn.addEventListener("click", function () {
    const abierto = filtrosBtn.getAttribute("aria-expanded") === "true";
    filtrosBtn.setAttribute("aria-expanded", String(!abierto));
    filtrosPanel.hidden = abierto;
  });

  const estadoSelect = $("#cysEstadoSelect");
  const estadoLabel = $("#cysEstadoLabel");
  const estadoField = $("#fieldEstadoFiltro");

  $$("#cysEstadoMenu li").forEach(function (li) {
    if (li.dataset.value === estadoField.value) li.classList.add("is-selected");
  });

  $("#cysEstadoTrigger").addEventListener("click", function (e) {
    e.stopPropagation();
    estadoSelect.classList.toggle("is-open");
  });

  $$("#cysEstadoMenu li").forEach(function (li) {
    li.addEventListener("click", function () {
      const valor = li.dataset.value;
      estadoField.value = valor === "todos" ? "" : valor;
      estadoLabel.textContent = li.textContent.trim();
      estadoSelect.classList.remove("is-open");
      filtroForm.submit();
    });
  });

  /* ---------- 4. MODAL CREAR / EDITAR ---------- */
  const modalOverlay = $("#cysModalOverlay");
  const form = $("#cysCategoriaForm");
  const fNombre = $("#fieldNombre");
  const fCodigo = $("#fieldCodigo");
  const fDesc = $("#fieldDescripcion");
  const charCount = $("#cysCharCount");

  function actualizarContador() {
    charCount.textContent = fDesc.value.length + "/" + (fDesc.maxLength > 0 ? fDesc.maxLength : 200);
  }

  function abrirModal(modo, datos) {
    form.reset();
    limpiarErrores();
    const editando = modo === "editar";
    form.action = editando ? datos.url : URL_CREAR;
    $("#cysModalTitle").textContent = editando ? "Editar categoría" : "Nueva categoría";
    $("#cysModalSubtitle").textContent = editando
      ? "Modifica los datos de la categoría"
      : "Registra una nueva categoría de productos";
    $("#cysGuardarLabel").textContent = editando ? "Guardar cambios" : "Crear categoría";
    if (editando) {
      fNombre.value = datos.nombre || "";
      fCodigo.value = datos.codigo || "";
      fDesc.value = datos.descripcion || "";
    }
    actualizarContador();
    abrirOverlay(modalOverlay);
    fNombre.focus();
  }

  $("#btnNuevaCategoria").addEventListener("click", function () { abrirModal("crear"); });

  $$(".cys-action-btn--edit").forEach(function (btn) {
    btn.addEventListener("click", function () {
      cerrarMenus();
      abrirModal("editar", {
        url: btn.dataset.url,
        nombre: btn.dataset.nombre,
        codigo: btn.dataset.codigo,
        descripcion: btn.dataset.descripcion,
      });
    });
  });

  $("#cysModalClose").addEventListener("click", function () { cerrarOverlay(modalOverlay); });
  $("#cysCancelBtn").addEventListener("click", function () { cerrarOverlay(modalOverlay); });
  fDesc.addEventListener("input", actualizarContador);

  /* ---------- 5. VALIDACIÓN ---------- */
  const INV_NOMBRE = /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]/g;
  const OK_NOMBRE = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$/;
  const INV_CODIGO = /[^A-Za-z0-9]/g;
  const OK_CODIGO = /^[A-Za-z0-9]+$/;
  const TIENE_NUMERO = /[0-9]/;

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

  function limpiarErrores() {
    [fNombre, fCodigo].forEach(function (i) { mostrarError(i, ""); });
  }

  function validarNombre() {
    const v = fNombre.value.replace(/\s+/g, " ").trim();
    if (!v) { mostrarError(fNombre, "El nombre es obligatorio."); return false; }
    if (!OK_NOMBRE.test(v)) { mostrarError(fNombre, "El nombre solo puede tener letras y espacios."); return false; }
    mostrarError(fNombre, "");
    fNombre.value = v;
    return true;
  }

  function validarCodigo() {
    const v = fCodigo.value.trim().toUpperCase();
    if (!v) { mostrarError(fCodigo, "El código es obligatorio."); return false; }
    if (!OK_CODIGO.test(v)) { mostrarError(fCodigo, "Solo letras y números, sin espacios ni símbolos."); return false; }
    if (!TIENE_NUMERO.test(v)) { mostrarError(fCodigo, "El código debe llevar al menos un número."); return false; }
    mostrarError(fCodigo, "");
    fCodigo.value = v;
    return true;
  }

  fNombre.addEventListener("input", function () {
    const limpio = fNombre.value.replace(INV_NOMBRE, "");
    mostrarError(fNombre, limpio !== fNombre.value ? "Solo se permiten letras y espacios." : "");
    fNombre.value = limpio;
  });

  fCodigo.addEventListener("input", function () {
    const cod = fCodigo.value.replace(INV_CODIGO, "").toUpperCase();
    mostrarError(fCodigo, cod !== fCodigo.value.toUpperCase() ? "El código solo puede tener letras y números." : "");
    fCodigo.value = cod;
  });

  form.addEventListener("submit", function (e) {
    const okN = validarNombre();
    const okC = validarCodigo();
    if (!okN || !okC) {
      e.preventDefault();
      (okN ? fCodigo : fNombre).focus();
    }
  });

  /* ---------- 6. CONFIRMAR DESACTIVACIÓN ---------- */
  const confirmOverlay = $("#cysConfirmOverlay");
  let formPendiente = null;

  $$(".cys-btn-confirmar-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      cerrarMenus();
      formPendiente = btn.closest("form");
      const nombre = formPendiente.dataset.nombre || "esta categoría";
      $("#cysConfirmText").textContent =
        "Las categorías no se eliminan, solo se desactivan para conservar el histórico de productos. " +
        '¿Deseas desactivar "' + nombre + '"?';
      abrirOverlay(confirmOverlay);
    });
  });

  $("#cysConfirmOk").addEventListener("click", function () {
    if (formPendiente) formPendiente.submit();
    cerrarOverlay(confirmOverlay);
  });
  $("#cysConfirmCancel").addEventListener("click", function () { cerrarOverlay(confirmOverlay); });
  $("#cysConfirmClose").addEventListener("click", function () { cerrarOverlay(confirmOverlay); });

  /* ---------- 7. MENÚ DE FILA ---------- */
  function cerrarMenus(excepto) {
    $$(".cys-row-menu.is-open").forEach(function (m) {
      if (m !== excepto) m.classList.remove("is-open");
    });
  }

  $$(".cys-row-menu").forEach(function (menu) {
    const trigger = $(".cys-row-menu__trigger", menu);
    const list = $(".cys-row-menu__list", menu);

    trigger.addEventListener("click", function (e) {
      e.stopPropagation();
      const abierto = menu.classList.contains("is-open");
      cerrarMenus();
      if (abierto) return;
      menu.classList.add("is-open");
      const r = trigger.getBoundingClientRect();
      let top = r.bottom + 4;
      if (top + list.offsetHeight > window.innerHeight) top = r.top - list.offsetHeight - 4;
      list.style.top = top + "px";
      list.style.left = Math.max(8, r.right - list.offsetWidth) + "px";
    });
  });

  window.addEventListener("scroll", function () { cerrarMenus(); }, true);
  window.addEventListener("resize", function () { cerrarMenus(); });

  /* ---------- 8. ORDENAR TABLA / ALERTAS ---------- */
  const tbody = $("#cysTableBody");
  let colActual = null;
  let dirActual = 1;

  $$(".cys-sortable").forEach(function (th) {
    th.addEventListener("click", function () {
      const col = parseInt(th.dataset.col, 10);
      const esNum = th.dataset.type === "num";
      dirActual = colActual === col ? -dirActual : 1;
      colActual = col;

      $$(".cys-sortable").forEach(function (h) { h.classList.remove("is-asc", "is-desc"); });
      th.classList.add(dirActual === 1 ? "is-asc" : "is-desc");

      const filas = $$("tr", tbody);
      const numeros = filas.map(function (f) { return f.cells[0].textContent; });

      filas.sort(function (a, b) {
        const va = a.cells[col].textContent.trim();
        const vb = b.cells[col].textContent.trim();
        if (esNum) return (parseFloat(va) - parseFloat(vb)) * dirActual;
        return va.localeCompare(vb, "es", { sensitivity: "base" }) * dirActual;
      });

      filas.forEach(function (f, i) {
        f.cells[0].textContent = numeros[i];
        tbody.appendChild(f);
      });
    });
  });

  $$(".cys-alert").forEach(function (a) {
    setTimeout(function () {
      a.style.opacity = "0";
      setTimeout(function () { a.remove(); }, 400);
    }, 5000);
  });

  /* ---------- CIERRES GLOBALES ---------- */
  document.addEventListener("click", function (e) {
    if (!e.target.closest("#cysExport")) exportWrap.classList.remove("is-open");
    if (!e.target.closest("#cysEstadoSelect")) estadoSelect.classList.remove("is-open");
    if (!e.target.closest(".cys-row-menu")) cerrarMenus();
    if (e.target.classList.contains("cys-modal-overlay")) cerrarOverlay(e.target);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    exportWrap.classList.remove("is-open");
    estadoSelect.classList.remove("is-open");
    cerrarMenus();
    cerrarOverlays();
  });
})();
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

  const btnNueva = $("#btnNuevaCategoria");
  btnNueva.addEventListener("click", function () {
    crearForm.scrollIntoView({ behavior: "smooth", block: "center" });
    cNombre.focus();
  }, opt);

  /* ---------- Modal editar ---------- */
  const modalOverlay = $("#cysModalOverlay");
  const editForm = $("#cysEditarForm");
  const fNombre = $("#fieldNombre");
  const fCodigo = $("#fieldCodigo");
  const fDesc = $("#fieldDescripcion");
  const charCount = $("#cysCharCount");
  activarValidacion(editForm, fNombre, fCodigo);

  function contador() { charCount.textContent = fDesc.value.length + "/" + (fDesc.maxLength > 0 ? fDesc.maxLength : 200); }
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