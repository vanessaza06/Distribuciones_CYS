// ══════════════════════════════════════════
// ayuda.js — CYS Ltda
// Búsqueda en vivo + Asistente Virtual (Chatbot CYS)
// ══════════════════════════════════════════

let aydCategoriaActiva = 'todas';

function aydFiltrarCategoria(btn) {
  document.querySelectorAll('.ayd-cat-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  aydCategoriaActiva = btn.dataset.cat;
  aydAplicarFiltros();
}

function aydAplicarFiltros() {
  const texto = (document.getElementById('ayd-buscador')?.value || '').trim().toLowerCase();
  const items = document.querySelectorAll('.ayd-item');
  let visibles = 0;

  items.forEach(item => {
    const coincideCat = aydCategoriaActiva === 'todas' || item.dataset.cat === aydCategoriaActiva;
    const coincideTexto = !texto || (item.dataset.texto || '').includes(texto);
    const mostrar = coincideCat && coincideTexto;
    item.classList.toggle('ayd-oculto', !mostrar);
    if (mostrar) visibles++;
  });

  const sinResultados = document.getElementById('ayd-sin-resultados');
  if (sinResultados) {
    sinResultados.classList.toggle('d-none', visibles !== 0);
  }
}
