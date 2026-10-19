import json
import logging
import re
import unicodedata
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValError
from django.http import JsonResponse, Http404
from django.db import IntegrityError
from django.db.models import Sum, Count, Q

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

    # Correo
    correo = _limpiar(post.get('email') or post.get('correo')).lower()
    if not correo:
        errores['email'] = 'El correo electrónico es obligatorio.'
    else:
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


# ── LISTA PRINCIPAL DE PROVEEDORES ─────────────────────────────────────────────
@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all().order_by('-fecha_registro')

    # Filtros de búsqueda
    q = request.GET.get('q', '').strip()[:100]
    estado = request.GET.get('estado', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    if estado not in dict(Proveedor.ESTADO_CHOICES):
        estado = ''
    if tipo not in dict(Proveedor.TIPO_CHOICES):
        tipo = ''

    if q:
        proveedores = proveedores.filter(
            Q(nombre_empresa__icontains=q) |
            Q(correo__icontains=q) |
            Q(nit_proveedores__icontains=q)
        )

    if estado:
        proveedores = proveedores.filter(estado=estado)

    if tipo:
        proveedores = proveedores.filter(tipo_proveedor=tipo)

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
