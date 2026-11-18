import time
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.validators import validate_email
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from app.models import BackupRegistro, ConfiguracionEmpresa, Usuario


# -- Constantes -----------------------------------------------

LOGO_DIR = 'empresa'
LOGO_EXTS = ('png', 'jpg', 'jpeg', 'webp', 'gif')
LOGO_FORMATOS = {'PNG', 'JPEG', 'WEBP', 'GIF'}
LOGO_MAX_BYTES = 2 * 1024 * 1024

SESION_DESBLOQUEO = 'empresa_desbloqueada_hasta'
SESION_FALLOS = 'empresa_fallos'
SESION_BLOQUEO_HASTA = 'empresa_bloqueo_hasta'
MINUTOS_DESBLOQUEO = 30
MAX_FALLOS = 5
SEGUNDOS_BLOQUEO = 60


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

            total = 0
            for t in connection.introspection.table_names():
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
        str(getattr(u, 'rol', '')).lower() in ('admin', 'administrador')
        or getattr(u, 'is_admin', False)
        or getattr(u, 'is_superuser', False)
    )


def _solo_admin():
    return JsonResponse(
        {'ok': False, 'error': 'Solo un administrador puede hacer esto.'},
        status=403,
    )


def _logo_url():
    """URL del logo guardado, o '' si no hay."""
    for ext in LOGO_EXTS:
        ruta = f'{LOGO_DIR}/logo.{ext}'
        if default_storage.exists(ruta):
            return default_storage.url(ruta)
    return ''


def _guardar_logo(archivo):
    """Valida y guarda el logo, reemplazando el anterior. Lanza ValueError si no es válido."""
    ext = Path(archivo.name).suffix.lower().lstrip('.')
    if ext not in LOGO_EXTS:
        raise ValueError('El logo debe ser PNG, JPG, WEBP o GIF.')
    if archivo.size > LOGO_MAX_BYTES:
        raise ValueError('El logo no puede pesar más de 2 MB.')

    try:
        from PIL import Image
        img = Image.open(archivo)
        formato = img.format
        img.verify()
    except Exception:
        raise ValueError('El archivo no es una imagen válida.')
    if formato not in LOGO_FORMATOS:
        raise ValueError('Formato de imagen no permitido.')
    archivo.seek(0)

    for e in LOGO_EXTS:
        anterior = f'{LOGO_DIR}/logo.{e}'
        if default_storage.exists(anterior):
            default_storage.delete(anterior)
    default_storage.save(f'{LOGO_DIR}/logo.{ext}', archivo)


def _empresa_dict(cfg):
    return {
        'nombre_empresa': cfg.nombre_empresa,
        'nit': cfg.nit,
        'direccion': cfg.direccion,
        'telefono': cfg.telefono,
        'email': cfg.email,
        'logo_url': _logo_url(),
    }


def _empresa_desbloqueada(request):
    return request.session.get(SESION_DESBLOQUEO, 0) > time.time()


# -- Vistas ---------------------------------------------------

@login_required
def index(request):
    cfg = ConfiguracionEmpresa.get_config()
    return render(request, 'configuracion/configuracion.html', {
        'es_admin_empresa': _es_admin(request),
        'config': cfg,
        'tema_sistema': cfg.tema_predeterminado,
        'db_stats': _db_stats(),
        'breadcrumb_items': [
            {'nombre': 'Configuracion', 'url': None},
        ],
    })


@login_required
@require_POST
def guardar_tema_sistema(request):
    """Fija el tema predeterminado de todo el sistema (solo administradores)."""
    if not _es_admin(request):
        return _solo_admin()

    tema = request.POST.get('tema', '')
    if tema not in ConfiguracionEmpresa.TEMAS_VALIDOS:
        return JsonResponse({'ok': False, 'error': 'Tema no válido.'}, status=400)

    try:
        cfg = ConfiguracionEmpresa.get_config()
        cfg.tema_predeterminado = tema
        cfg.save(update_fields=['tema_predeterminado'])
    except Exception:
        return JsonResponse({'ok': False, 'error': 'No se pudo guardar el tema.'}, status=500)

    return JsonResponse({'ok': True, 'tema': tema})


@login_required
@require_POST
def verificar_clave_empresa(request):
    """Pide la contraseña del admin logueado para ver/editar los datos de la empresa."""
    if not _es_admin(request):
        return _solo_admin()

    ahora = time.time()
    bloqueado_hasta = request.session.get(SESION_BLOQUEO_HASTA, 0)
    if bloqueado_hasta > ahora:
        espera = int(bloqueado_hasta - ahora) + 1
        return JsonResponse(
            {'ok': False, 'error': f'Demasiados intentos. Espera {espera} s.'},
            status=429,
        )

    clave = request.POST.get('clave', '')
    if not clave or not request.user.check_password(clave):
        fallos = request.session.get(SESION_FALLOS, 0) + 1
        if fallos >= MAX_FALLOS:
            request.session[SESION_BLOQUEO_HASTA] = ahora + SEGUNDOS_BLOQUEO
            fallos = 0
        request.session[SESION_FALLOS] = fallos
        return JsonResponse({'ok': False, 'error': 'Contraseña incorrecta.'}, status=400)

    request.session[SESION_FALLOS] = 0
    request.session[SESION_DESBLOQUEO] = ahora + MINUTOS_DESBLOQUEO * 60
    cfg = ConfiguracionEmpresa.get_config()
    return JsonResponse({'ok': True, 'empresa': _empresa_dict(cfg)})


@login_required
@require_POST
def bloquear_empresa(request):
    request.session.pop(SESION_DESBLOQUEO, None)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def guardar_empresa(request):
    if not _es_admin(request):
        return _solo_admin()
    if not _empresa_desbloqueada(request):
        return JsonResponse(
            {'ok': False, 'error': 'Sección bloqueada. Vuelve a ingresar tu contraseña.'},
            status=403,
        )

    nombre = request.POST.get('nombre_empresa', '').strip()
    nit = request.POST.get('nit', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    email = request.POST.get('email', '').strip()
    direccion = request.POST.get('direccion', '').strip()

    if not nombre:
        return JsonResponse({'ok': False, 'error': 'El nombre de la empresa es obligatorio.'}, status=400)
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'ok': False, 'error': 'El correo no es válido.'}, status=400)

    campos = {
        'nombre_empresa': (nombre, 200),
        'nit': (nit, 50),
        'telefono': (telefono, 50),
        'direccion': (direccion, 300),
    }
    for nombre_campo, (valor, maximo) in campos.items():
        if len(valor) > maximo:
            return JsonResponse(
                {'ok': False, 'error': f'El campo {nombre_campo} supera {maximo} caracteres.'},
                status=400,
            )

    archivo = request.FILES.get('logo')
    if archivo:
        try:
            _guardar_logo(archivo)
        except ValueError as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    cfg = ConfiguracionEmpresa.get_config()
    cfg.nombre_empresa = nombre
    cfg.nit = nit
    cfg.telefono = telefono
    cfg.email = email
    cfg.direccion = direccion
    cfg.save()

    return JsonResponse({'ok': True, 'logo_url': _logo_url()})


@login_required
@require_POST
def guardar_impuestos(request):
    if not _es_admin(request):
        return _solo_admin()

    from decimal import Decimal, InvalidOperation
    try:
        iva = Decimal(request.POST.get('iva_porcentaje', '').replace(',', '.'))
    except (InvalidOperation, AttributeError):
        return JsonResponse({'ok': False, 'error': 'El IVA no es un número válido.'}, status=400)
    if iva < 0 or iva > 100:
        return JsonResponse({'ok': False, 'error': 'El IVA debe estar entre 0 y 100.'}, status=400)

    moneda = request.POST.get('moneda', '').strip().upper()
    if not moneda or len(moneda) > 10:
        return JsonResponse({'ok': False, 'error': 'Moneda no válida.'}, status=400)

    unidades = request.POST.getlist('unidades[]') or request.POST.getlist('unidades')
    unidades = [u.strip() for u in unidades if u.strip()]
    vistas = set()
    unidades = [u for u in unidades if not (u.lower() in vistas or vistas.add(u.lower()))]

    cfg = ConfiguracionEmpresa.get_config()
    cfg.iva_porcentaje = iva
    cfg.moneda = moneda
    cfg.unidades_medida = unidades
    cfg.save(update_fields=['iva_porcentaje', 'moneda', 'unidades_medida'])

    return JsonResponse({'ok': True})


@login_required
@require_POST
def crear_backup(request):
    """Genera un respaldo JSON (dumpdata) en BASE_DIR/backups y lo registra."""
    if not _es_admin(request):
        return _solo_admin()

    carpeta = Path(settings.BASE_DIR) / 'backups'
    carpeta.mkdir(parents=True, exist_ok=True)
    ahora = timezone.localtime()
    nombre = f'backup_{ahora:%Y%m%d_%H%M%S}.json'
    ruta = carpeta / nombre

    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                exclude=['contenttypes', 'sessions', 'admin.logentry', 'auth.permission'],
                indent=2,
                stdout=f,
            )
        tam_mb = round(ruta.stat().st_size / (1024 * 1024), 2)
        reg = BackupRegistro.objects.create(
            nombre=nombre,
            descripcion=f'Respaldo manual creado por {request.user.get_full_name()}',
            ruta=str(ruta),
            tamaño_mb=tam_mb,
        )
    except Exception:
        ruta.unlink(missing_ok=True)
        return JsonResponse({'ok': False, 'error': 'No se pudo crear el respaldo.'}, status=500)

    return JsonResponse({
        'ok': True,
        'nombre': reg.nombre,
        'tamaño_mb': reg.tamaño_mb,
        'fecha': timezone.localtime(reg.fecha).strftime('%d/%m/%Y %H:%M'),
    })


@login_required
@require_GET
def actividad(request):
    """Últimos inicios de sesión: todos si es admin, solo los propios si no."""
    es_admin = _es_admin(request)
    qs = Usuario.objects.exclude(last_login__isnull=True)
    if not es_admin:
        qs = qs.filter(pk=request.user.pk)

    registros = [
        {
            'usuario': u.nombre_completo,
            'fecha_hora': timezone.localtime(u.last_login).strftime('%d/%m/%Y %H:%M'),
            'ip': '-',
        }
        for u in qs.order_by('-last_login')[:100]
    ]
    return JsonResponse({'es_admin': es_admin, 'registros': registros})