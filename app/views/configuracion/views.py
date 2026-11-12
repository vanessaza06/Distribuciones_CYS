from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from app.config_sistema import TEMAS_VALIDOS, guardar_tema


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