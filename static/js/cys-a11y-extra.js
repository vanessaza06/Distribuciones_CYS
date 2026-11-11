(function () {
'use strict';

// Evita ejecutarse dos veces (htmx / carga doble)
if (window.CYS_A11Y_EXTRA) return;

const KEY = 'cys_a11y_extra';
const DEFAULTS = { animaciones: false, cursor: false, foco: false };
const CLASES = {
  animaciones: 'cys-x-sinanim',
  cursor:      'cys-x-cursor',
  foco:        'cys-x-foco',
};

// Cursores grandes (SVG codificado en data URI)
const svgFlecha = "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24'>" +
  "<path d='M4 2l16 9-7 2-3 7z' fill='black' stroke='white' stroke-width='1.5' stroke-linejoin='round'/></svg>";
const svgMano = "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 24 24'>" +
  "<path d='M9 3a1.5 1.5 0 0 1 3 0v6h1V7.5a1.5 1.5 0 0 1 3 0V9h1V8.5a1.5 1.5 0 0 1 3 0V15c0 3.5-2.5 6-6 6h-2c-2 0-3.2-1-4.2-2.4L4 14.5c-.6-.9.4-2 1.4-1.4L9 15z' " +
  "fill='black' stroke='white' stroke-width='1.2' stroke-linejoin='round'/></svg>";
const uri = (svg) => 'url("data:image/svg+xml,' + encodeURIComponent(svg) + '")';

const CSS = `
html.cys-x-sinanim *, html.cys-x-sinanim *::before, html.cys-x-sinanim *::after {
  animation-duration: .001ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: .001ms !important;
  scroll-behavior: auto !important;
}
html.cys-x-cursor, html.cys-x-cursor * { cursor: ${uri(svgFlecha)} 4 2, auto !important; }
html.cys-x-cursor a, html.cys-x-cursor button, html.cys-x-cursor [role="button"],
html.cys-x-cursor label, html.cys-x-cursor select, html.cys-x-cursor summary,
html.cys-x-cursor .cfg-opt, html.cys-x-cursor .cfg-chip, html.cys-x-cursor .switch,
html.cys-x-cursor .slider-sw { cursor: ${uri(svgMano)} 10 2, pointer !important; }
html.cys-x-cursor input[type="text"], html.cys-x-cursor input[type="email"],
html.cys-x-cursor input[type="password"], html.cys-x-cursor input[type="number"],
html.cys-x-cursor textarea { cursor: text !important; }
html.cys-x-foco :focus-visible {
  outline: 3px solid #ffbf00 !important;
  outline-offset: 3px !important;
  box-shadow: 0 0 0 6px rgba(255, 191, 0, .35) !important;
}
`;

function inyectarEstilo() {
  if (document.getElementById('cys-a11y-extra-style')) return;
  const st = document.createElement('style');
  st.id = 'cys-a11y-extra-style';
  st.textContent = CSS;
  document.head.appendChild(st);
}

function leer() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') };
  } catch (e) {
    return { ...DEFAULTS };
  }
}

function aplicar(cfg) {
  const root = document.documentElement;
  Object.keys(CLASES).forEach(k => root.classList.toggle(CLASES[k], !!cfg[k]));
}

function set(clave, valor) {
  if (!(clave in DEFAULTS)) return;
  const cfg = leer();
  cfg[clave] = !!valor;
  localStorage.setItem(KEY, JSON.stringify(cfg));
  aplicar(cfg);
}

function reset() {
  localStorage.removeItem(KEY);
  aplicar({ ...DEFAULTS });
}

inyectarEstilo();
aplicar(leer());

window.CYS_A11Y_EXTRA = { get: leer, set, reset };

})();