from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from usuarios.models import RegistroActividad
from app.models import BackupRegistro, ConfiguracionEmpresa


# -- Helpers --------------------------------------------------

def _db_stats():
    """Estadisticas basicas de la base de datos MySQL."""
    stats = {'registros': 0, 'tablas': 0, 'tamaño': '-'}
    try:
        db_name = settings.DATABASES['default']['NAME']
        with connection.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                [db_name]
            )
            stats['tablas'] = cur.fetchone()[0]

            tables = connection.introspection.table_names()
            total = 0
            for t in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM `{t}`')
                    total += cur.fetchone()[0]
                except Exception:
                    pass
            stats['registros'] = total

            cur.execute(
                "SELECT SUM(data_length + index_length) FROM information_schema.tables "
                "WHERE table_schema = %s",
                [db_name]
            )
            size_bytes = cur.fetchone()[0] or 0
            if size_bytes < 1024 * 1024:
                stats['tamaño'] = f'{size_bytes / 1024:.1f} KB'
            else:
                stats['tamaño'] = f'{size_bytes / (1024 * 1024):.2f} MB'
    except Exception:
        pass
    return stats


def _es_admin(request):
    u = request.user
    return u.is_authenticated and (
        getattr(u, 'rol', '') == 'admin'
        or getattr(u, 'is_admin', False)
        or getattr(u, 'is_superuser', False)
    )


@login_required
def index(request):
    return render(request, 'configuracion/configuracion.html', {
        'es_admin_empresa': _es_admin(request),
        'breadcrumb_items': [
            {'nombre': 'Configuracion', 'url': None},
        ],
    })


@login_required
@require_POST
def guardar_tema_sistema(request):
    """Fija el tema predeterminado de todo el sistema (solo administradores)."""
    if not _es_admin(request):
        return JsonResponse(
            {'ok': False, 'error': 'Solo un administrador puede hacer esto.'},
            status=403,
        )

    tema = request.POST.get('tema', '')
    if tema not in TEMAS_VALIDOS:
        return JsonResponse({'ok': False, 'error': 'Tema no válido.'}, status=400)

    try:
        guardar_tema(tema)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'No se pudo guardar el tema.'}, status=500)

    return JsonResponse({'ok': True, 'tema': tema})