import base64
import io
import json
import logging
import os
import re
import unicodedata
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValError
from django.http import HttpResponse, JsonResponse, Http404
from django.db import IntegrityError
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.html import escape

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import pixels_to_EMU
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Proveedor, Compra
from app.validators import limpiar_texto as _limpiar, validar_texto_libre

logger = logging.getLogger(__name__)


# ── VALIDACIÓN EN EL SERVIDOR (lista blanca de caracteres) ───────────────────
# Todo dato que llega del formulario se valida aquí, nunca se confía en el navegador.
NIT_RE = re.compile(r'[0-9]{5,15}')
TELEFONO_RE = re.compile(r'[0-9]{7,15}')
# Nombre: letras (con tildes/ñ), números, espacios y . , & ' ( ) - /
NOMBRE_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,&'()\-/]*")


def validar_datos_proveedor(post, *, editando=False, nit_actual=None):
    """Devuelve (datos_limpios, errores). `errores` es un dict {campo: mensaje}."""
    errores = {}
    datos = {}

    # NIT
    if editando:
        datos['nit'] = nit_actual
    else:
        nit = _limpiar(post.get('nit') or post.get('nit_proveedores'))
        if not nit:
            errores['nit'] = 'El NIT o documento es obligatorio.'
        elif not NIT_RE.fullmatch(nit):
            errores['nit'] = 'El NIT solo admite números (5 a 15 dígitos), sin puntos, comas ni guiones. Ej: 9001234567.'
        elif Proveedor.objects.filter(pk=nit).exists():
            errores['nit'] = 'Ya existe un proveedor registrado con ese NIT.'
        datos['nit'] = nit

    # Nombre
    nombre = _limpiar(post.get('nombre_empresa'))
    if not nombre:
        errores['nombre_empresa'] = 'El nombre de la empresa es obligatorio.'
    elif len(nombre) < 2 or len(nombre) > 200:
        errores['nombre_empresa'] = 'El nombre debe tener entre 2 y 200 caracteres.'
    elif not any(ch.isalpha() for ch in nombre):
        errores['nombre_empresa'] = 'El nombre debe incluir al menos una letra.'
    elif not NOMBRE_RE.fullmatch(nombre):
        errores['nombre_empresa'] = "El nombre solo admite letras, números, espacios y . , & ' ( ) - /"
    datos['nombre_empresa'] = nombre

    # Correo (opcional)
    correo = _limpiar(post.get('email') or post.get('correo')).lower()
    if correo:
        try:
            if len(correo) > 254 or ' ' in correo:
                raise DjangoValError('largo')
            validate_email(correo)
        except DjangoValError:
            errores['email'] = 'Ingresa un correo electrónico válido.'
    datos['correo'] = correo

    # Teléfono (opcional)
    telefono = _limpiar(post.get('telefono'))
    if telefono and not TELEFONO_RE.fullmatch(telefono):
        errores['telefono'] = 'El teléfono solo admite entre 7 y 15 dígitos, sin puntos, comas, guiones ni espacios.'
    datos['telefono'] = telefono

    # Tipo: solo valores del catálogo
    tipo = _limpiar(post.get('tipo_proveedor')) or 'distribuidor'
    if tipo not in dict(Proveedor.TIPO_CHOICES):
        errores['tipo_proveedor'] = 'Selecciona un tipo de proveedor válido.'
    datos['tipo_proveedor'] = tipo

    # Observación (opcional)
    obs = _limpiar(post.get('observacion'))
    obs_error = validar_texto_libre(obs)
    if obs_error:
        errores['observacion'] = obs_error
    datos['observacion'] = obs

    return datos, errores


def _json_seguro(valor):
    """json.dumps seguro para incrustar dentro de <script> (evita cerrar la etiqueta)."""
    return (json.dumps(valor)
            .replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026'))


# ---------------------------------------------------------------------------
# Filtro compartido: lo usan el listado y las 3 exportaciones,
# así lo que ves en pantalla es exactamente lo que se exporta.
# Parámetros GET: q, nit, tipo, estado
# ---------------------------------------------------------------------------
def _filtrar_proveedores(request):
    q = request.GET.get('q', '').strip()[:100]
    nit = request.GET.get('nit', '').strip()[:20]
    estado = request.GET.get('estado', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    if estado not in dict(Proveedor.ESTADO_CHOICES):
        estado = ''
    if tipo not in dict(Proveedor.TIPO_CHOICES):
        tipo = ''

    proveedores = Proveedor.objects.all().order_by('-fecha_registro')

    if q:
        proveedores = proveedores.filter(
            Q(nombre_empresa__icontains=q) |
            Q(correo__icontains=q) |
            Q(telefono__icontains=q) |
            Q(nit_proveedores__icontains=q)
        )
    if nit:
        proveedores = proveedores.filter(nit_proveedores__icontains=nit)
    if estado:
        proveedores = proveedores.filter(estado=estado)
    if tipo:
        proveedores = proveedores.filter(tipo_proveedor=tipo)

    filtros = {'q': q, 'nit': nit, 'estado': estado, 'tipo': tipo}
    return proveedores, filtros


# ── LISTA PRINCIPAL DE PROVEEDORES (también atiende ?export=excel|pdf|imprimir) ──
@login_required
def lista_proveedores(request):
    # ---- Exportación: el JS llama a esta misma URL con ?export=... ----
    exportar = request.GET.get('export')
    if exportar == 'excel':
        return exportar_proveedores_excel(request)
    if exportar == 'pdf':
        return exportar_proveedores_pdf(request)
    if exportar == 'imprimir':
        return exportar_proveedores_imprimir(request)

    # ---- Listado normal ----
    proveedores, _filtros = _filtrar_proveedores(request)

    # Calcular estadísticas de compras por proveedor
    for p in proveedores:
        compras_p = Compra.objects.filter(proveedor=p)
        p.total_compras = compras_p.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
        p.total_ordenes = compras_p.count()
        # Aliases para el template HTML
        p.id = p.pk
        p.nit = p.nit_proveedores
        p.email = p.correo

    # Estadísticas generales (KPIs)
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(estado='activo').count()
    proveedores_inactivos = Proveedor.objects.filter(estado='inactivo').count()
    proveedores_sancionados = Proveedor.objects.filter(estado='sancionado').count()
    porcentaje_activos = int((proveedores_activos / total_proveedores) * 100) if total_proveedores > 0 else 0

    # Normalización para barra de progreso
    max_compras = max([p.total_compras for p in proveedores], default=1) or 1
    for p in proveedores:
        p.bar_width = int((p.total_compras / max_compras) * 100) if p.total_compras > 0 else 1

    # Paginación
    paginator = Paginator(proveedores, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Top 5 gastos por proveedor para el gráfico (ORM nativo)
    gastos_qs = (
        Compra.objects.values('proveedor__nombre_empresa')
        .annotate(total=Sum('valor'))
        .order_by('-total')[:5]
    )
    gastos_labels = [g['proveedor__nombre_empresa'] for g in gastos_qs]
    gastos_data = [float(g['total'] or 0) for g in gastos_qs]
    gastos_total = sum(gastos_data) or 1
    gastos_porcentajes = [int((g / gastos_total) * 100) for g in gastos_data]

    context = {
        'proveedores': proveedores,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_proveedores': total_proveedores,
        'proveedores_activos': proveedores_activos,
        'proveedores_inactivos': proveedores_inactivos,
        'proveedores_sancionados': proveedores_sancionados,
        'porcentaje_activos': porcentaje_activos,
        'max_compras': max_compras,
        'gastos_labels_json': _json_seguro(gastos_labels),
        'gastos_data_json': _json_seguro(gastos_data),
        'gastos_porcentajes_json': _json_seguro(gastos_porcentajes),
        'breadcrumb_items': [{'nombre': 'Proveedores', 'url': None}],
    }
    return render(request, 'proveedores/proveedores.html', context)


# ── CRUD TRADICIONAL ──────────────────────────────────────────────────────────
@login_required
def crear_proveedor(request):
    if request.method != 'POST':
        return redirect('lista_proveedores')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    datos, errors = validar_datos_proveedor(request.POST)

    if errors:
        if is_ajax:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        for msg in errors.values():
            messages.error(request, f'⚠️ {msg}')
        return redirect('lista_proveedores')

    try:
        proveedor = Proveedor.objects.create(
            nit_proveedores=datos['nit'],
            nombre_empresa=datos['nombre_empresa'],
            correo=datos['correo'],
            telefono=datos['telefono'],
            tipo_proveedor=datos['tipo_proveedor'],
            observacion=datos['observacion'] or None,
            estado='activo',
        )
    except IntegrityError:
        errors = {'nit': 'Ya existe un proveedor registrado con ese NIT.'}
        if is_ajax:
            return JsonResponse({'success': False, 'errors': errors}, status=400)
        messages.error(request, f'⚠️ {errors["nit"]}')
        return redirect('lista_proveedores')

    mensaje = f'Proveedor {proveedor.nombre_empresa} registrado correctamente.'
    if is_ajax:
        return JsonResponse({'success': True, 'message': mensaje})
    messages.success(request, f'✅ {mensaje}')
    return redirect('lista_proveedores')


@login_required
def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)

    if request.method == 'POST':
        datos, errors = validar_datos_proveedor(request.POST, editando=True, nit_actual=proveedor.pk)

        if errors:
            for err in errors.values():
                messages.error(request, f'⚠️ {err}')
        else:
            proveedor.nombre_empresa = datos['nombre_empresa']
            proveedor.correo = datos['correo']
            proveedor.telefono = datos['telefono']
            proveedor.tipo_proveedor = datos['tipo_proveedor']
            proveedor.observacion = datos['observacion']
            proveedor.save()

            messages.success(request, f'✅ Proveedor {proveedor.nombre_empresa} actualizado con éxito.')
            return redirect('lista_proveedores')

    # Aliases para template
    proveedor.id = proveedor.pk
    proveedor.nit = proveedor.nit_proveedores
    proveedor.email = proveedor.correo

    context = {
        'proveedor': proveedor,
        'tipos_proveedor': Proveedor.TIPO_CHOICES,
        'breadcrumb_items': [
            {'nombre': 'Proveedores', 'url': reverse('lista_proveedores')},
            {'nombre': f'Editar: {proveedor.nombre_empresa}', 'url': None},
        ],
    }
    return render(request, 'proveedores/editar_proveedor.html', context)


@login_required
def detalle_proveedor(request, id):
    from app.models import DevolucionProveedores

    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.id = proveedor.pk
    proveedor.nit = proveedor.nit_proveedores
    proveedor.email = proveedor.correo

    todas = Compra.objects.filter(proveedor=proveedor)
    vigentes = todas.exclude(estado='cancelada')
    resumen = vigentes.aggregate(total=Sum('valor'), saldo=Sum('saldo'))
    total_compras = resumen['total'] or Decimal('0.00')
    saldo_pendiente = resumen['saldo'] or Decimal('0.00')
    ultima_compra = todas.order_by('-fecha').first()

    recientes = (todas.prefetch_related('detalles__producto')
                 .order_by('-fecha', '-codigo_compra')[:8])

    devs = [d for d in DevolucionProveedores.objects.filter(proveedor=proveedor).exclude(estado='rechazada')]
    total_devuelto = sum((d.total_devuelto for d in devs), Decimal('0.00'))

    context = {
        'proveedor': proveedor,
        'compras': recientes,
        'compras_count': vigentes.count(),
        'total_compras': total_compras,
        'saldo_pendiente': saldo_pendiente,
        'ultima_compra': ultima_compra,
        'devoluciones_count': len(devs),
        'total_devuelto': total_devuelto,
        'breadcrumb_items': [
            {'nombre': 'Proveedores', 'url': reverse('lista_proveedores')},
            {'nombre': proveedor.nombre_empresa, 'url': None},
        ],
    }
    return render(request, 'proveedores/detalle_proveedor.html', context)


@login_required
@require_POST
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    # Borrar un proveedor arrastra sus compras (CASCADE): se bloquea si tiene historial
    if Compra.objects.filter(proveedor=proveedor).exists() or proveedor.devolucionproveedores_set.exists():
        messages.error(
            request,
            f'⚠️ {proveedor.nombre_empresa} tiene compras o devoluciones registradas y no se puede eliminar. '
            'Puedes desactivarlo.'
        )
        return redirect('lista_proveedores')
    nombre = proveedor.nombre_empresa
    proveedor.delete()
    messages.success(request, f'Proveedor {nombre} eliminado correctamente.')
    return redirect('lista_proveedores')


@login_required
@require_POST
def activar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.estado = 'activo'
    proveedor.save(update_fields=['estado'])
    messages.success(request, f'Proveedor {proveedor.nombre_empresa} activado.')
    return redirect('lista_proveedores')


@login_required
@require_POST
def desactivar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.estado = 'inactivo'
    proveedor.save(update_fields=['estado'])
    messages.success(request, f'Proveedor {proveedor.nombre_empresa} desactivado.')
    return redirect('lista_proveedores')


@login_required
@require_POST
def sancionar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    observacion = _limpiar(request.POST.get('observacion'))
    if not observacion:
        messages.error(request, 'Debe indicar el motivo de la sanción.')
    elif validar_texto_libre(observacion):
        messages.error(request, f'⚠️ Motivo de sanción: {validar_texto_libre(observacion)}')
    else:
        proveedor.estado = 'sancionado'
        proveedor.observacion = observacion
        proveedor.save(update_fields=['estado', 'observacion'])
        messages.success(request, f'Proveedor {proveedor.nombre_empresa} sancionado.')
    return redirect('lista_proveedores')


# ── VISTAS MODALES / AJAX (Usadas por proveedores.js) ─────────────────────────
@login_required
def detalle_proveedor_modal(request, id):
    try:
        proveedor = get_object_or_404(Proveedor, pk=id)
        compras_p = Compra.objects.filter(proveedor=proveedor)
        total_gastado = compras_p.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

        data = {
            'success': True,
            'proveedor': {
                'id': proveedor.pk,
                'nombre_empresa': proveedor.nombre_empresa,
                'nit': proveedor.nit_proveedores,
                'email': proveedor.correo,
                'telefono': proveedor.telefono or '—',
                'tipo_proveedor': proveedor.get_tipo_proveedor_display(),
                'estado': proveedor.get_estado_display(),
                'estado_value': proveedor.estado,
                'observacion': proveedor.observacion or 'Sin observaciones',
                'fecha_registro': proveedor.fecha_registro.strftime('%d/%m/%Y'),
                'total_compras': compras_p.count(),
                'total_gastado': f'${total_gastado:,.2f}',
            }
        }
        return JsonResponse(data)
    except Http404:
        return JsonResponse({'success': False, 'error': 'Proveedor no encontrado.'}, status=404)
    except Exception:
        logger.exception('Error en detalle_proveedor_modal')
        return JsonResponse({'success': False, 'error': 'No se pudo cargar el proveedor.'}, status=400)


@login_required
def desactivar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'inactivo'
        proveedor.save(update_fields=['estado'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} desactivado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def reactivar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'activo'
        proveedor.save(update_fields=['estado'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} reactivado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def sancionar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        observacion = _limpiar(request.POST.get('observacion'))
        if not observacion:
            return JsonResponse({'success': False, 'error': 'Debe indicar el motivo de la sanción.'}, status=400)
        error_texto = validar_texto_libre(observacion)
        if error_texto:
            return JsonResponse({'success': False, 'error': f'Motivo de sanción: {error_texto}'}, status=400)
        proveedor.estado = 'sancionado'
        proveedor.observacion = observacion
        proveedor.save(update_fields=['estado', 'observacion'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} sancionado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_required
def levantar_sancion_proveedor(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'activo'
        proveedor.observacion = ''
        proveedor.save(update_fields=['estado', 'observacion'])
        return JsonResponse({'success': True, 'message': f'Sanción levantada para {proveedor.nombre_empresa}.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ===========================================================================
# EXPORTACIONES (mismo diseño del reporte de Marcas)
# Excel / PDF / Imprimir  ->  /proveedores/?export=excel|pdf|imprimir
# ===========================================================================

# ---------------------------------------------------------------------------
# Identidad visual (colores tomados del logo de CYS Ltda)
# ---------------------------------------------------------------------------
NAVY = "0B1B30"      # azul noche del logo
GOLD = "C48F3C"      # dorado del logo
CREAM = "F0E7DA"     # crema del texto "CYS"
ZEBRA = "FAF5EA"     # fila alterna suave
BORDE = "E3D3B5"     # bordes finos dorados claros
VERDE = "1E8449"
ROJO = "B03A2E"

XL_NAVY = "061B3A"       # títulos, encabezado de tabla y texto
XL_GOLD = "E8A317"       # divisor y barrita dorada
XL_ZEBRA = "EDF0F5"      # fila alterna
XL_BORDE = "AEB9CC"      # líneas verticales de la tabla
XL_ROJO = "9B1C1C"       # estado sancionado
XL_VERDE = "1E8449"      # estado activo
XL_AMBAR = "B7791F"      # estado inactivo
XL_FUENTE = "Calibri"

# Color del texto de estado según el estado del proveedor
COLOR_ESTADO = {
    'activo': XL_VERDE,
    'inactivo': XL_AMBAR,
    'sancionado': XL_ROJO,
}

LOGO_ARCHIVO = "logo.20.png"   # <- nombre de tu logo dentro de la carpeta static
_LOGO_CACHE = {}


def _ruta_logo():
    """Busca el logo en tus carpetas static. Devuelve la ruta o None."""
    if "ruta" in _LOGO_CACHE:
        return _LOGO_CACHE["ruta"]

    from django.contrib.staticfiles import finders

    ruta = None
    for candidato in (LOGO_ARCHIVO, f"img/{LOGO_ARCHIVO}", f"images/{LOGO_ARCHIVO}",
                      f"imagenes/{LOGO_ARCHIVO}", f"img/logo/{LOGO_ARCHIVO}"):
        try:
            ruta = finders.find(candidato)
        except Exception:
            ruta = None
        if ruta:
            break

    if not ruta:
        base = getattr(settings, "BASE_DIR", ".")
        carpetas = [str(d) for d in getattr(settings, "STATICFILES_DIRS", [])]
        carpetas += [os.path.join(str(base), "static"), os.path.join(str(base), "app", "static")]
        for carpeta in carpetas:
            for raiz, _dirs, archivos in os.walk(carpeta):
                if LOGO_ARCHIVO in archivos:
                    ruta = os.path.join(raiz, LOGO_ARCHIVO)
                    break
            if ruta:
                break

    _LOGO_CACHE["ruta"] = ruta
    return ruta


def _logo_png(px):
    """Logo redondo, redimensionado, con esquinas transparentes. Devuelve bytes PNG o None."""
    clave = ("png", px)
    if clave in _LOGO_CACHE:
        return _LOGO_CACHE[clave]

    datos = None
    ruta = _ruta_logo()
    if ruta:
        try:
            from PIL import Image, ImageDraw
            img = Image.open(ruta).convert("RGBA")
            mascara = Image.new("L", img.size, 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, img.size[0] - 1, img.size[1] - 1), fill=255)
            img.putalpha(mascara)
            img = img.resize((px, px), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            datos = buf.getvalue()
        except Exception:
            datos = None

    _LOGO_CACHE[clave] = datos
    return datos


# ---------------------------------------------------------------------------
# Datos del reporte
# Columnas visibles: #, Empresa, NIT, Correo, Teléfono, Tipo, Estado, Fecha registro
# Cada fila lleva al final (índice 8) el código de estado crudo.
# ---------------------------------------------------------------------------
IDX_ESTADO = 6


def _encabezados():
    return ["#", "Empresa", "NIT", "Correo", "Teléfono", "Tipo", "Estado", "Fecha registro"]


def _fecha_txt(valor):
    if not valor:
        return "—"
    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.strftime("%d/%m/%Y %H:%M")
    return valor.strftime("%d/%m/%Y")


def _filas(qs):
    filas = []
    for i, p in enumerate(qs, start=1):
        filas.append([
            i,
            p.nombre_empresa,
            str(p.nit_proveedores) if p.nit_proveedores else "—",
            p.correo or "—",
            p.telefono or "—",
            p.get_tipo_proveedor_display(),
            p.get_estado_display(),
            _fecha_txt(p.fecha_registro),
            p.estado,          # código crudo (no se muestra)
        ])
    return filas


def _texto_filtros(f):
    partes = []
    if f.get("q"):
        partes.append(f"Búsqueda: {f['q']}")
    if f.get("nit"):
        partes.append(f"NIT: {f['nit']}")
    if f.get("tipo"):
        partes.append(f"Tipo: {dict(Proveedor.TIPO_CHOICES).get(f['tipo'], f['tipo'])}")
    if f.get("estado"):
        partes.append(f"Estado: {dict(Proveedor.ESTADO_CHOICES).get(f['estado'], f['estado'])}")
    return " | ".join(partes) if partes else "Sin filtros"


def _sello():
    return timezone.localtime().strftime('%Y%m%d_%H%M')


def _resumen(filas):
    """(total, activos, inactivos, sancionados)."""
    activos = sum(1 for f in filas if f[8] == 'activo')
    inactivos = sum(1 for f in filas if f[8] == 'inactivo')
    sancionados = sum(1 for f in filas if f[8] == 'sancionado')
    return len(filas), activos, inactivos, sancionados


def _texto_totales(filas):
    n, a, i, s = _resumen(filas)
    return (f"Total: {n} proveedores   ·   Activos: {a}   ·   "
            f"Inactivos: {i}   ·   Sancionados: {s}")


# ---------------------------------------------------------------------------
# EXCEL  (diseño "Reporte de Marcas": logo + título, tabla azul marino)
# ---------------------------------------------------------------------------
def _xl_fill(hex_):
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def _poner_imagen(ws, datos_png, col, fila, ancho, alto, off_x=0, off_y=0):
    """Pega una imagen PNG (bytes) en la celda (col, fila) 0-indexada, con desplazamiento en px."""
    img = XLImage(io.BytesIO(datos_png))
    img.width, img.height = ancho, alto
    marcador = AnchorMarker(col=col, row=fila,
                            colOff=pixels_to_EMU(off_x), rowOff=pixels_to_EMU(off_y))
    img.anchor = OneCellAnchor(
        _from=marcador,
        ext=XDRPositiveSize2D(pixels_to_EMU(ancho), pixels_to_EMU(alto)),
    )
    ws.add_image(img)


def _barra_dorada(ancho, alto):
    try:
        from PIL import Image
    except ImportError:
        return None
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), "#" + XL_GOLD).save(buf, "PNG")
    return buf.getvalue()


def exportar_proveedores_excel(request):
    qs, filtros = _filtrar_proveedores(request)
    filas = _filas(qs)

    encabezados = _encabezados()
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Proveedores"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    # A+B dan el mismo espacio de banner que en Marcas (logo centrado + divisor dorado)
    anchos = [10, 34, 18, 34, 18, 18, 18, 20]
    for idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = ancho

    # ---------- Banner (filas 1-3, fondo blanco) ----------
    for r, h in {1: 30, 2: 34, 3: 30}.items():
        ws.row_dimensions[r].height = h

    # Logo circular (columnas A:B, centrado)
    logo = _logo_png(300)
    if logo:
        tam = 112
        ancho_ab = int((anchos[0] + anchos[1]) * 7 + 10)
        _poner_imagen(ws, logo, 0, 0, tam, tam, off_x=max((ancho_ab - tam) // 2, 0), off_y=6)
    else:
        ws.merge_cells("A1:B3")
        ws["A1"] = "CYS LTDA"
        ws["A1"].font = Font(name=XL_FUENTE, size=30, bold=True, color=XL_NAVY)
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")

    # Divisor dorado vertical
    lado_oro = Side(style="medium", color=XL_GOLD)
    for r in (1, 2, 3):
        ws.cell(r, 3).border = Border(left=lado_oro)

    # Título y lema
    ws.merge_cells(f"C1:{ultima}2")
    ws["C1"] = "Reporte de Proveedores"
    ws["C1"].font = Font(name=XL_FUENTE, size=30, bold=True, color=XL_NAVY)
    ws["C1"].alignment = Alignment(horizontal="left", vertical="center", indent=2)
    ws.merge_cells(f"C3:{ultima}3")
    ws["C3"] = "Calidad que llega más lejos"
    ws["C3"].font = Font(name=XL_FUENTE, size=16, italic=True, color=XL_NAVY)
    ws["C3"].alignment = Alignment(horizontal="left", vertical="top", indent=2)

    # Barrita dorada corta bajo el lema
    ws.row_dimensions[4].height = 10
    barra = _barra_dorada(140, 5)
    if barra:
        _poner_imagen(ws, barra, 2, 3, 140, 5, off_x=22, off_y=2)
    ws.row_dimensions[5].height = 16

    # ---------- Encabezado de tabla (fila 6) ----------
    fila_enc = 6
    ws.row_dimensions[fila_enc].height = 34
    blanco = Side(style="thin", color="FFFFFF")
    for i, texto in enumerate(encabezados, start=1):
        c = ws.cell(fila_enc, i, texto)
        c.font = Font(name=XL_FUENTE, size=15, bold=True, color="FFFFFF")
        c.fill = _xl_fill(XL_NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = Border(left=blanco if i > 1 else None)

    # ---------- Datos ----------
    vertical = Side(style="thin", color=XL_BORDE)
    for k, fila in enumerate(filas):
        r = fila_enc + 1 + k
        ws.row_dimensions[r].height = 26
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila[:n], start=1):
            if i == IDX_ESTADO + 1:
                valor = "●  " + valor
            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == 2))
            izquierda = i in (2, 4)
            c.alignment = Alignment(
                horizontal="left" if izquierda else "center",
                vertical="center",
                indent=1 if izquierda else 0,
                wrap_text=izquierda,
            )
        # Estado con color
        e = ws.cell(r, IDX_ESTADO + 1)
        e.font = Font(name=XL_FUENTE, size=13, bold=True,
                      color=COLOR_ESTADO.get(fila[8], XL_NAVY))

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        _texto_totales(filas),
        f"{_texto_filtros(filtros)}   ·   Generado el {timezone.localtime():%d/%m/%Y %H:%M}",
    ]
    for j, texto in enumerate(textos_pie, start=1):
        rr = r + j
        ws.row_dimensions[rr].height = 22
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=n)
        p = ws.cell(rr, 1, texto)
        p.font = Font(name=XL_FUENTE, size=11, bold=(j == 1), italic=(j == 2), color=XL_NAVY)
        p.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    # ---------- Extras (sin freeze_panes para que el banner no se repita) ----------
    if filas:
        ws.auto_filter.ref = f"A{fila_enc}:{ultima}{fila_enc + len(filas)}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{fila_enc}:{fila_enc}"
    ws.print_options.horizontalCentered = True

    buffer = io.BytesIO()
    wb.save(buffer)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="proveedores_{_sello()}.xlsx"'
    return resp


# ---------------------------------------------------------------------------
# PDF  (mismo diseño que el Excel: banner blanco con logo + título,
#       tabla azul marino con esquinas redondeadas)
# ---------------------------------------------------------------------------
class _BannerPDF(Flowable):
    """Banner: logo circular | divisor dorado | título | lema | barrita dorada."""

    def __init__(self, ancho, logo_bytes=None, titulo="Reporte de Proveedores"):
        super().__init__()
        self.width = ancho
        self.height = 96
        self.logo_bytes = logo_bytes
        self.titulo = titulo

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        navy = colors.HexColor("#" + XL_NAVY)
        oro = colors.HexColor("#" + XL_GOLD)

        # Logo circular
        diam = 84
        x_logo, y_logo = 14, (self.height - diam) / 2
        if self.logo_bytes:
            c.drawImage(ImageReader(io.BytesIO(self.logo_bytes)), x_logo, y_logo,
                        width=diam, height=diam, mask="auto")
        else:
            c.setFillColor(navy)
            c.circle(x_logo + diam / 2, y_logo + diam / 2, diam / 2, stroke=0, fill=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(x_logo + diam / 2, y_logo + diam / 2 - 6, "CYS")

        # Divisor dorado vertical
        x_div = x_logo + diam + 26
        c.setStrokeColor(oro)
        c.setLineWidth(2.5)
        c.line(x_div, 8, x_div, self.height - 8)

        # Título
        x_txt = x_div + 26
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 34)
        c.drawString(x_txt, self.height - 46, self.titulo)

        # Lema en cursiva
        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, "Calidad que llega más lejos")

        # Barrita dorada corta
        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


def exportar_proveedores_pdf(request):
    qs, filtros = _filtrar_proveedores(request)
    filas = _filas(qs)
    encabezados = _encabezados()

    c_navy = colors.HexColor("#" + XL_NAVY)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title="Reporte de proveedores — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=10, leading=12.5, textColor=c_texto)
    st_emp = ParagraphStyle("emp", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, leftIndent=8)
    st_izq = ParagraphStyle("izq", parent=st_base, leftIndent=8)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=12,
                             textColor=colors.white, alignment=TA_CENTER, leading=15)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    # --- Banner ---
    elementos = [
        _BannerPDF(ancho_util, _logo_png(300)),
        Spacer(1, 14),
    ]

    # --- Tabla ---
    data = [[Paragraph(h, st_head) for h in encabezados]]
    for f in filas:
        color = "#" + COLOR_ESTADO.get(f[8], XL_NAVY)
        # El punto "●" se dibuja con ZapfDingbats (Helvetica no trae ese símbolo)
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="9">l</font>'
            f'&nbsp;&nbsp;{escape(f[6])}</font>'
        )
        data.append([
            Paragraph(str(f[0]), st_centro),
            Paragraph(escape(f[1]), st_emp),
            Paragraph(escape(f[2]), st_centro),
            Paragraph(escape(f[3]), st_izq),
            Paragraph(escape(f[4]), st_centro),
            Paragraph(escape(f[5]), st_centro),
            Paragraph(estado_html, st_estado),
            Paragraph(escape(f[7]), st_centro),
        ])

    if not filas:
        data.append([Paragraph("No hay proveedores para mostrar.", st_centro)]
                    + [""] * (len(encabezados) - 1))

    anchos = [35, 150, 80, 150, 80, 80, 90, 90]
    escala = ancho_util / sum(anchos)
    tabla = Table(data, colWidths=[a * escala for a in anchos], repeatRows=1)

    estilo = [
        # Encabezado azul marino
        ("BACKGROUND", (0, 0), (-1, 0), c_navy),
        ("LINEBEFORE", (1, 0), (-1, 0), 0.6, colors.HexColor("#3B4F6B")),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        # Filas con cebra y líneas verticales
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_zebra]),
        ("LINEBEFORE", (1, 1), (-1, -1), 0.6, c_borde),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Contorno azul marino con esquinas redondeadas
        ("BOX", (0, 0), (-1, -1), 1, c_navy),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
    ]
    if not filas:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)

    # --- Totales y filtros (discretos, debajo de la tabla) ---
    n, a, i, s = _resumen(filas)
    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {n} proveedores &nbsp;·&nbsp; Activos: {a} &nbsp;·&nbsp; "
            f"Inactivos: {i} &nbsp;·&nbsp; Sancionados: {s}",
            st_tot),
        Spacer(1, 2),
        Paragraph(
            escape(_texto_filtros(filtros)) + " &nbsp;·&nbsp; Generado el "
            + timezone.localtime().strftime("%d/%m/%Y %H:%M"),
            st_meta),
    ]

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(margen, 20, "CYS Ltda · Distribuciones")
        canvas.drawRightString(pagina[0] - margen, 20, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)

    resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="proveedores_{_sello()}.pdf"'
    return resp


# ---------------------------------------------------------------------------
# IMPRIMIR
# ---------------------------------------------------------------------------
def exportar_proveedores_imprimir(request):
    qs, filtros = _filtrar_proveedores(request)
    filas = _filas(qs)
    n, a, i, s = _resumen(filas)
    encab = _encabezados()

    clase_estado = {'activo': 'ok', 'inactivo': 'pe', 'sancionado': 'no'}

    def fila_html(f):
        clase = clase_estado.get(f[8], 'nv')
        return (
            "<tr>"
            f"<td class='c'>{f[0]}</td>"
            f"<td class='prod'>{escape(f[1])}</td>"
            f"<td class='c'>{escape(f[2])}</td>"
            f"<td>{escape(f[3])}</td>"
            f"<td class='c'>{escape(f[4])}</td>"
            f"<td class='c'>{escape(f[5])}</td>"
            f"<td class='c {clase}'>{escape(f[6])}</td>"
            f"<td class='c'>{escape(f[7])}</td>"
            "</tr>"
        )

    filas_html = "".join(fila_html(f) for f in filas) or \
        f"<tr><td colspan='{len(encab)}' class='c'>No hay proveedores para mostrar.</td></tr>"
    encabezados = "".join(f"<th>{h}</th>" for h in encab)

    logo = _logo_png(300)
    logo_html = ""
    if logo:
        logo_html = f"<img class='logo' src='data:image/png;base64,{base64.b64encode(logo).decode()}' alt='CYS Ltda'>"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Reporte de proveedores — CYS Ltda</title>
<style>
  @page {{ margin: 14mm; }}
  * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  body {{ font-family: Arial, sans-serif; margin: 0; color: #1f2937; }}
  .banner {{ background: #{NAVY}; border-bottom: 4px solid #{GOLD}; padding: 14px 20px;
            display: flex; align-items: center; gap: 18px; border-radius: 6px 6px 0 0; }}
  .logo {{ width: 70px; height: 70px; }}
  .banner h1 {{ margin: 0; font: bold 24px Georgia, 'Times New Roman', serif; color: #{GOLD}; letter-spacing: 1px; }}
  .banner p {{ margin: 3px 0 0; font-size: 14px; color: #{CREAM}; }}
  .meta {{ font-size: 11px; color: #6b6b6b; margin: 10px 2px 12px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #{NAVY}; color: #{GOLD}; padding: 9px 10px; border-bottom: 3px solid #{GOLD}; text-align: center; }}
  td {{ padding: 8px 10px; border: 1px solid #{BORDE}; }}
  td.c {{ text-align: center; }}
  td.prod {{ font-weight: bold; color: #{NAVY}; }}
  td.ok {{ color: #{VERDE}; font-weight: bold; }}
  td.nv {{ color: #{NAVY}; font-weight: bold; }}
  td.pe {{ color: #B7791F; font-weight: bold; }}
  td.no {{ color: #{ROJO}; font-weight: bold; }}
  tr:nth-child(even) td {{ background: #{ZEBRA}; }}
  .total {{ margin-top: 8px; background: #{CREAM}; border-top: 3px solid #{GOLD}; padding: 9px 14px;
           text-align: right; font-weight: bold; color: #{NAVY}; font-size: 13px; }}
  .pie {{ margin-top: 14px; font-size: 10px; color: #888; text-align: center; }}
</style></head>
<body>
  <div class="banner">
    {logo_html}
    <div><h1>CYS LTDA · DISTRIBUCIONES</h1><p>Reporte de proveedores</p></div>
  </div>
  <div class="meta">{escape(_texto_filtros(filtros))} &nbsp;·&nbsp; Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</div>
  <table><thead><tr>{encabezados}</tr></thead><tbody>{filas_html}</tbody></table>
  <div class="total">Total: {n} proveedores &nbsp;·&nbsp; Activos: {a} &nbsp;·&nbsp; Inactivos: {i} &nbsp;·&nbsp; Sancionados: {s}</div>
  <div class="pie">CYS Ltda · Distribuciones</div>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)