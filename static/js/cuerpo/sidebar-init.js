document.addEventListener('DOMContentLoaded', function () {
    // ── SIDEBAR: instancia del offcanvas y botón de apertura ──
    const sidebarEl = document.getElementById('sidebarRight');
    if (!sidebarEl) return;

    const bsSidebar = new bootstrap.Offcanvas(sidebarEl, {
        scroll: true,
        backdrop: false
    });

    // Abrir automáticamente según preferencia de Configuración (cys_config.sidebarAuto)
    // Solo en pantallas de escritorio, y solo en la carga inicial de la sesión —
    // no se repite en cada navegación para no pelear con lo que el usuario decida.
    let cysCfg = {};
    try { cysCfg = JSON.parse(localStorage.getItem('cys_config') || '{}'); } catch (e) {}
    const esEscritorio = window.innerWidth > 768;
    if (cysCfg.sidebarAuto === true && esEscritorio) {
        sidebarEl.classList.add('show');
        document.body.classList.add('sidebar-open');
        sidebarEl.style.visibility = 'visible';
    }

    // Delegación de eventos: menuBtn vive dentro del área que sí se reemplaza
    // en cada navegación con htmx, así que en vez de atarnos al nodo del botón
    // (que se recrea en cada página), escuchamos en document, que nunca se
    // reemplaza. Así el botón sigue funcionando sin importar cuántas veces
    // se haya regenerado el HTML a su alrededor.
    document.addEventListener('click', function (e) {
        if (e.target.closest('#menuBtn')) {
            bsSidebar.toggle();
        }
    });

    // En cada evento limpiar lo que Bootstrap intenta poner
    function limpiarBootstrap() {
        document.body.style.removeProperty('padding-right');
        document.body.style.removeProperty('overflow');
    }

    sidebarEl.addEventListener('show.bs.offcanvas', () => {
        document.body.classList.add('sidebar-open');
        limpiarBootstrap();
    });
    sidebarEl.addEventListener('shown.bs.offcanvas', limpiarBootstrap);
    sidebarEl.addEventListener('hide.bs.offcanvas', limpiarBootstrap);
    sidebarEl.addEventListener('hidden.bs.offcanvas', () => {
        document.body.classList.remove('sidebar-open');
        limpiarBootstrap();
    });
});