/**
 * BODEGA.JS — Módulo de Bodega y Conteo
 * Agenda (tabs/acordeón), conteo, buscadores, validaciones de formularios y UI global
 */

// ═══════ UTILIDADES ═══════
function normalizar(texto) {
  return (texto || '')
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function ahoraLocalISO() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

// Limpiar backdrop huérfano SOLO si no hay modal abriendo
window.addEventListener('load', function () {
  setTimeout(function () {
    if (!document.querySelector('.modal.show')) {
      document.querySelectorAll('.modal-backdrop').forEach(function (b) { b.remove(); });
      document.body.classList.remove('modal-open');
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    }
  }, 300);
});

// Tooltips globales (incluye los botones dentro de modales)
window.addEventListener('load', function () {
  if (typeof bootstrap === 'undefined') return;
  document.querySelectorAll('[title]').forEach(function (el) {
    if (el.closest('.modal-header')) return;
    const tip = new bootstrap.Tooltip(el, { placement: 'top', trigger: 'hover', container: 'body' });
    el.addEventListener('click', function () { tip.hide(); });
  });
});

// ── ACORDEÓN "Inventarios Programados": recuerda si estaba abierto ──
(function () {
  const collapseEl = document.getElementById('agendaBody');
  if (!collapseEl) return;
  const KEY = 'cys_agenda_abierta';

  try {
    if (sessionStorage.getItem(KEY) === '0') {
      collapseEl.classList.remove('show');
    } else {
      collapseEl.classList.add('show');
    }
  } catch (e) { /* sessionStorage no disponible */ }

  collapseEl.addEventListener('shown.bs.collapse', function () {
    try { sessionStorage.setItem(KEY, '1'); } catch (e) {}
  });
  collapseEl.addEventListener('hidden.bs.collapse', function () {
    try { sessionStorage.setItem(KEY, '0'); } catch (e) {}
  });
})();

// ── TABS AGENDAS: recuerda el último tab visto (Activos / Historial) ──
(function () {
  const TAB_KEY = 'cys_agenda_tab';

  function filtrarAgendas(tab) {
    const items = document.querySelectorAll('.agenda-item');
    let visibles = 0;
    items.forEach(function (item) {
      const mostrar = item.dataset.categoria === tab;
      item.style.display = mostrar ? '' : 'none';
      if (mostrar) visibles++;
    });

    // Mensaje cuando la pestaña no tiene elementos (pero sí hay agendas en la otra)
    const vacio = document.getElementById('agenda-sin-items');
    if (vacio) {
      vacio.classList.toggle('d-none', items.length === 0 || visibles > 0);
      const txt = vacio.querySelector('[data-texto]');
      if (txt) txt.textContent = tab === 'activos' ? 'No hay inventarios activos.' : 'El historial está vacío.';
    }
  }

  document.querySelectorAll('.agenda-tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.agenda-tab-btn').forEach(function (b) {
        b.classList.remove('agenda-tab-activo');
        b.classList.add('agenda-tab-inactivo');
      });
      this.classList.remove('agenda-tab-inactivo');
      this.classList.add('agenda-tab-activo');
      try { sessionStorage.setItem(TAB_KEY, this.dataset.tab); } catch (e) {}
      filtrarAgendas(this.dataset.tab);
    });
  });

  let tabGuardado = 'activos';
  try { tabGuardado = sessionStorage.getItem(TAB_KEY) || 'activos'; } catch (e) {}
  document.querySelectorAll('.agenda-tab-btn').forEach(function (b) {
    const esGuardado = b.dataset.tab === tabGuardado;
    b.classList.toggle('agenda-tab-activo', esGuardado);
    b.classList.toggle('agenda-tab-inactivo', !esGuardado);
  });
  filtrarAgendas(tabGuardado);
})();

// ═══════ BUSCADORES ═══════
function activarBuscador(opciones) {
  const input = document.getElementById(opciones.inputId);
  if (!input) return;
  const items = document.querySelectorAll(opciones.itemSelector);
  const vacio = document.getElementById(opciones.vacioId);

  input.addEventListener('input', function () {
    const q = normalizar(this.value);
    let visibles = 0;
    items.forEach(function (item) {
      const texto = opciones.atributos.map(function (a) { return normalizar(item.dataset[a]); }).join(' ');
      const coincide = !q || texto.includes(q);
      item.style.display = coincide ? '' : 'none';
      if (coincide) visibles++;
    });
    if (vacio) vacio.classList.toggle('d-none', visibles !== 0 || !q);
  });
}

// Buscador nuevo: Presentaciones sin Lote
activarBuscador({
  inputId: 'buscarPresSinLote',
  itemSelector: '.pres-card-col',
  atributos: ['nombre', 'pres'],
  vacioId: 'sinResultadosPres'
});

// Buscador: Lotes en Bodega
activarBuscador({
  inputId: 'buscarLoteBodega',
  itemSelector: '.lote-card-col',
  atributos: ['nombre', 'lote', 'bodega'],
  vacioId: 'sinResultadosLotesBodega'
});

// ═══════ VALIDACIÓN DE FORMULARIOS ═══════
function mostrarError(campo, mensaje) {
  campo.classList.add('is-invalid');
  const wrap = campo.closest('.campo-validar');
  const err = wrap && wrap.querySelector('.inv-error');
  if (err) {
    err.textContent = mensaje;
    err.classList.add('visible');
  }
}

function limpiarError(campo) {
  if (!campo || !campo.classList) return;
  campo.classList.remove('is-invalid');
  const wrap = campo.closest('.campo-validar');
  const err = wrap && wrap.querySelector('.inv-error');
  if (err) {
    err.textContent = '';
    err.classList.remove('visible');
  }
}

function limpiarFormulario(form) {
  form.querySelectorAll('.is-invalid').forEach(limpiarError);
  form.querySelectorAll('.inv-error.visible').forEach(function (e) {
    e.textContent = '';
    e.classList.remove('visible');
  });
}

// Se bloquea con setTimeout 0 para que el navegador alcance a incluir el
// name/value del botón submit en el POST (si se deshabilita antes, la vista
// no recibe "Agendar" / "iniciar_sesion").
function bloquearEnvio(form) {
  setTimeout(function () {
    form.querySelectorAll('button[type="submit"]').forEach(function (b) {
      if (b.disabled) return;
      b.disabled = true;
      b.dataset.bloqueado = '1';
    });
  }, 0);
}

// Si el usuario vuelve con el botón "atrás", se reactivan los botones bloqueados
window.addEventListener('pageshow', function (e) {
  if (!e.persisted) return;
  document.querySelectorAll('button[data-bloqueado="1"]').forEach(function (b) {
    b.disabled = false;
    delete b.dataset.bloqueado;
  });
});

function conectarValidacion(formId, validador) {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener('submit', function (e) {
    limpiarFormulario(form);
    if (!validador(form)) {
      e.preventDefault();
      const primero = form.querySelector('.is-invalid');
      if (primero && typeof primero.focus === 'function') primero.focus();
      return;
    }
    bloquearEnvio(form);
  });

  // El error desaparece apenas el usuario corrige el campo
  form.addEventListener('input', function (e) { limpiarError(e.target); });
}

// ── Agendar inventario ──
function validarAgendar(form) {
  let ok = true;
  const titulo = form.elements['titulo'];
  const fecha = form.elements['fecha_programada'];
  const descripcion = form.elements['descripcion'];

  const t = titulo.value.trim();
  titulo.value = t;
  if (t.length < 3) {
    mostrarError(titulo, 'El título debe tener al menos 3 caracteres.');
    ok = false;
  } else if (t.length > 100) {
    mostrarError(titulo, 'El título no puede superar los 100 caracteres.');
    ok = false;
  }

  if (!fecha.value) {
    mostrarError(fecha, 'Selecciona la fecha y la hora del inventario.');
    ok = false;
  } else {
    const elegida = new Date(fecha.value);
    if (isNaN(elegida.getTime())) {
      mostrarError(fecha, 'La fecha no es válida.');
      ok = false;
    } else if (elegida.getTime() < Date.now() - 60000) {
      mostrarError(fecha, 'La fecha y hora no pueden estar en el pasado.');
      ok = false;
    }
  }

  if (descripcion.value.length > 300) {
    mostrarError(descripcion, 'La descripción no puede superar los 300 caracteres.');
    ok = false;
  }
  return ok;
}

// ── Iniciar / reiniciar sesión de conteo ──
function validarSesion(form) {
  if (form.dataset.confirmar) return confirm(form.dataset.confirmar);
  return true;
}

// ── Registrar conteo ──
function validarConteo(form) {
  let ok = true;
  const prod = form.elements['producto_id'];
  const cant = form.elements['cantidad_contada'];
  const btnProd = document.getElementById('conteo-prod-btn');

  // El input hidden no lo valida el navegador, por eso se revisa aquí
  if (!prod.value) {
    mostrarError(btnProd, 'Selecciona un producto de la lista.');
    ok = false;
  }

  const raw = cant.value.trim();
  if (raw === '') {
    mostrarError(cant, 'Ingresa la cantidad contada.');
    ok = false;
  } else if (!/^\d+$/.test(raw)) {
    mostrarError(cant, 'Solo números enteros, sin decimales ni negativos.');
    ok = false;
  } else if (Number(raw) > 1000000) {
    mostrarError(cant, 'La cantidad es demasiado alta.');
    ok = false;
  }
  return ok;
}

conectarValidacion('form-agendar', validarAgendar);
conectarValidacion('form-sesion', validarSesion);
conectarValidacion('form-conteo', validarConteo);

// Evitar doble clic en el stepper de estados de la agenda
document.querySelectorAll('.agenda-form-inline').forEach(function (form) {
  form.addEventListener('submit', function () { bloquearEnvio(form); });
});

// Modal Agendar: no dejar elegir fechas pasadas y limpiar errores al abrir/cerrar
(function () {
  const modalEl = document.getElementById('modalAgendar');
  if (!modalEl) return;
  modalEl.addEventListener('show.bs.modal', function () {
    const fecha = document.getElementById('agendar-fecha');
    if (fecha) fecha.min = ahoraLocalISO();
  });
  modalEl.addEventListener('hidden.bs.modal', function () {
    const form = document.getElementById('form-agendar');
    if (form) limpiarFormulario(form);
  });
})();

// Modal Conteo: limpiar errores al cerrar
(function () {
  const modalEl = document.getElementById('modalConteo');
  if (!modalEl) return;
  modalEl.addEventListener('hidden.bs.modal', function () {
    const form = document.getElementById('form-conteo');
    if (form) limpiarFormulario(form);
  });
})();

// ── DROPDOWN CONTEO PRODUCTO ──
document.querySelectorAll('.conteo-prod-item').forEach(function (item) {
  item.addEventListener('click', function (e) {
    e.preventDefault();
    document.getElementById('conteo-prod-label').textContent = this.textContent.trim();
    document.getElementById('conteo-prod-hidden').value = this.dataset.value;
    limpiarError(document.getElementById('conteo-prod-btn'));
  });
});

// ── COMPARAR: "Con Diferencia" cuenta solo los que no están OK ──
(function () {
  const el = document.getElementById('cmp-con-diferencia');
  if (!el) return;
  const conDiferencia = document.querySelectorAll('.comparar-lista-wrap .conteo-item-card:not(.borde-ok)').length;
  el.textContent = conDiferencia;
  if (conDiferencia === 0) {
    el.classList.remove('text-danger');
    el.classList.add('text-success');
  }
})();