import os
import subprocess
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.utils.html import escape

from app.models import ConfiguracionEmpresa, BackupRegistro
from usuarios.models import RegistroActividad


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


# -- Vistas -----------------------------------------------------

@login_required
def index(request):
    config  = ConfiguracionEmpresa.get_config()
    backups = BackupRegistro.objects.all()[:10]

    request.session.pop('empresa_desbloqueada', None)

    context = {
        'config':   config,
        'db_stats': _db_stats(),
        'backups':  backups,
        'es_admin_empresa': _es_admin(request),
        'breadcrumb_items': [
            {'nombre': 'Configuracion', 'url': None},
        ],
    }
    return render(request, 'configuracion/configuracion.html', context)


@login_required
def actividad_usuarios(request):
    """Inicios de sesion: el admin ve todos, los demas solo los suyos."""
    es_admin = _es_admin(request)

    registros_qs = RegistroActividad.objects.select_related('usuario')
    if not es_admin:
        registros_qs = registros_qs.filter(usuario=request.user)

    registros = []
    for r in registros_qs[:100]:
        fecha = r.fecha_hora
        if timezone.is_aware(fecha):
            fecha = timezone.localtime(fecha)
        registros.append({
            'usuario':    escape(r.usuario.nombre_completo or r.usuario.username),
            'fecha_hora': fecha.strftime('%d/%m/%Y %H:%M:%S'),
            'ip':         r.ip_address or '—',
        })

    return JsonResponse({'es_admin': es_admin, 'registros': registros})


@login_required
@require_POST
def verificar_clave_empresa(request):
    if not _es_admin(request):
        return JsonResponse({'ok': False, 'error': 'Solo el administrador puede ver esta informacion.'}, status=403)

    clave = request.POST.get('clave', '')
    if not clave:
        return JsonResponse({'ok': False, 'error': 'Ingresa tu contrasena.'})

    if not request.user.check_password(clave):
        return JsonResponse({'ok': False, 'error': 'Contrasena incorrecta.'})

    request.session['empresa_desbloqueada'] = True

    config = ConfiguracionEmpresa.get_config()
    return JsonResponse({
        'ok': True,
        'empresa': {
            'nombre_empresa': config.nombre_empresa,
            'nit':            config.nit,
            'direccion':      config.direccion,
            'telefono':       config.telefono,
            'email':          config.email,
        }
    })


@login_required
@require_POST
def bloquear_empresa(request):
    request.session.pop('empresa_desbloqueada', None)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def guardar_empresa(request):
    if not _es_admin(request):
        return JsonResponse({'ok': False, 'error': 'Solo el administrador puede editar esta informacion.'}, status=403)

    if not request.session.get('empresa_desbloqueada'):
        return JsonResponse({'ok': False, 'error': 'Debes verificar tu contrasena antes de guardar.'}, status=403)

    config = ConfiguracionEmpresa.get_config()
    config.nombre_empresa = request.POST.get('nombre_empresa', config.nombre_empresa).strip()
    config.nit            = request.POST.get('nit',       config.nit).strip()
    config.direccion      = request.POST.get('direccion', config.direccion).strip()
    config.telefono       = request.POST.get('telefono',  config.telefono).strip()
    config.email          = request.POST.get('email',     config.email).strip()
    config.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def guardar_impuestos(request):
    config = ConfiguracionEmpresa.get_config()

    iva_raw = request.POST.get('iva_porcentaje')
    if iva_raw not in (None, ''):
        try:
            iva = Decimal(str(iva_raw))
        except InvalidOperation:
            return JsonResponse({'ok': False, 'error': 'El IVA no es un numero valido.'})
        if iva < 0 or iva > 100:
            return JsonResponse({'ok': False, 'error': 'El IVA debe estar entre 0 y 100.'})
        config.iva_porcentaje = iva

    config.moneda = request.POST.get('moneda', config.moneda)

    unidades = request.POST.getlist('unidades[]')
    if unidades:
        config.unidades_medida = [u.strip() for u in unidades if u.strip()]
    config.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def crear_backup(request):
    """Genera un dump de la base de datos MySQL con mysqldump."""
    try:
        db = settings.DATABASES['default']
        db_name     = db['NAME']
        db_user     = db['USER']
        db_password = db.get('PASSWORD', '')
        db_host     = db.get('HOST') or 'localhost'
        db_port     = str(db.get('PORT') or 3306)

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre    = f'backup_{timestamp}.sql'
        dest_path = os.path.join(backup_dir, nombre)

        comando = ['mysqldump', f'-u{db_user}', f'-h{db_host}', f'-P{db_port}', db_name]
        env = os.environ.copy()
        if db_password:
            env['MYSQL_PWD'] = db_password

        with open(dest_path, 'wb') as f:
            resultado = subprocess.run(comando, stdout=f, stderr=subprocess.PIPE, env=env)

        if resultado.returncode != 0:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return JsonResponse({
                'ok': False,
                'error': resultado.stderr.decode('utf-8', errors='ignore') or 'mysqldump fallo'
            })

        size_bytes = os.path.getsize(dest_path)
        if size_bytes < 1024 * 1024:
            tamano_str = f'{size_bytes / 1024:.1f} KB'
        else:
            tamano_str = f'{size_bytes / (1024 * 1024):.2f} MB'

        registro = BackupRegistro.objects.create(
            nombre    = nombre,
            ruta      = dest_path,
            tamaño_mb = round(size_bytes / (1024 * 1024), 4),
        )

        return JsonResponse({
            'ok':     True,
            'nombre': nombre,
            'fecha':  registro.fecha.strftime('%d/%m/%Y %H:%M'),
            'tamaño': tamano_str,
        })
    except FileNotFoundError:
        return JsonResponse({'ok': False, 'error': 'mysqldump no esta instalado o no esta en el PATH del servidor.'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})


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
    if tema not in ConfiguracionEmpresa.TEMAS_VALIDOS:
        return JsonResponse({'ok': False, 'error': 'Tema no válido.'}, status=400)

    config = ConfiguracionEmpresa.get_config()
    config.tema_predeterminado = tema
    config.save(update_fields=['tema_predeterminado'])
    return JsonResponse({'ok': True, 'tema': tema})