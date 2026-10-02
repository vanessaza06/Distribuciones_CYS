import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from app.forms import NuevaCompraForm
from app.models import Compra, DetalleCompra, Proveedor, Usuario as AppUsuario

logger = logging.getLogger(__name__)

MESES_ABREV = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
CERO = Decimal('0.00')


# ── Utilidades ─────────────────────────────────────────────────────────────────
def cop(valor):
    """Formatea un monto como pesos colombianos: $80.000 (sin decimales, punto de miles)."""
    return f"${int(valor or 0):,}".replace(",", ".")


def _url_lista(proveedor_pk):
    return f"{reverse('lista_compras')}?proveedor={proveedor_pk}"


def _mensajes_validacion(request, error):
    """Muestra como mensajes los textos de un ValidationError de Django."""
    for texto in error.messages:
        messages.error(request, texto)


def _usuario_de_compra(user):
    """Resuelve la instancia de app.Usuario que firma la compra (o None si no existe)."""
    if isinstance(user, AppUsuario):
        return user
    ident = getattr(user, 'identificacion', None) or getattr(user, 'username', '')
    correo = getattr(user, 'email', '')
    usuario = (
        (AppUsuario.objects.filter(documento=ident).first() if ident else None)
        or (AppUsuario.objects.filter(correo=correo).first() if correo else None)
    )
    if not usuario and ident:
        usuario, _ = AppUsuario.objects.get_or_create(
            documento=str(ident),
            defaults={
                'nombre': getattr(user, 'first_name', '') or getattr(user, 'username', 'Usuario'),
                'apellido': getattr(user, 'last_name', '') or '',
                'correo': correo or f"{ident}@cys.com",
                'tipo_identificacion': 'CC',
                'rol': getattr(user, 'rol', 'empleado') or 'empleado',
                'estado': 'activo',
            },
        )
    return usuario


def _proveedores_disponibles():
    activos = Proveedor.objects.filter(estado='activo').order_by('nombre_empresa')
    return activos if activos.exists() else Proveedor.objects.order_by('nombre_empresa')


def _resolver_proveedor(request, disponibles):
    """Proveedor activo: parámetro GET -> sesión -> primero disponible."""
    candidatos = [request.GET.get('proveedor'), request.session.get('proveedor_id')]
    for pk in candidatos:
        if pk:
            proveedor = Proveedor.objects.filter(pk=str(pk).strip()).first()
            if proveedor:
                break
    else:
        proveedor = disponibles.first()
    if proveedor:
        request.session['proveedor_id'] = str(proveedor.pk)
    return proveedor


def _procesar_nueva_compra(request, form, proveedor_activo):
    """
    Registra la compra del modal. Devuelve la URL de redirección si todo salió bien
    o None si hay que volver a mostrar la página con los errores.
    """
    if not form.is_valid():
        for campo, errores in form.errors.items():
            etiqueta = form.fields[campo].label if campo in form.fields else ''
            texto = ", ".join(errores)
            messages.error(request, f'{etiqueta}: {texto}' if etiqueta else texto)
        return None

    datos = form.cleaned_data
    proveedor = datos.get('proveedor') or proveedor_activo
    if not proveedor:
        messages.error(request, 'Debe seleccionar un proveedor válido para registrar la compra.')
        return None

    usuario = _usuario_de_compra(request.user)
    if not usuario:
        messages.error(request, 'No se pudo identificar al usuario que registra la compra.')
        return None

    try:
        compra = Compra.registrar(
            proveedor=proveedor,
            usuario=usuario,
            producto=datos['producto'],
            lote=datos.get('lote'),
            cantidad=datos['cantidad'],
            precio_unitario=datos['precio_unitario'],
            estado=datos.get('estado') or 'recibida',
            monto_pagado=datos.get('monto_pagado') or CERO,
            metodo_pago=datos.get('metodo_pago') or 'efectivo',
            referencia=datos.get('numero_factura') or '',
        )
    except ValidationError as e:
        _mensajes_validacion(request, e)
        return None
    except Exception:
        logger.exception("Error al registrar compra")
        messages.error(request, 'Ocurrió un error al guardar la compra. Intenta de nuevo.')
        return None

    request.session['proveedor_id'] = str(proveedor.pk)
    messages.success(
        request,
        f'✅ Compra #{compra.codigo_compra} registrada: {datos["cantidad"]} und. de '
        f'"{datos["producto"].nombre}" ({cop(compra.valor)}) para {proveedor.nombre_empresa}.'
    )
    return _url_lista(proveedor.pk)


def _ultimos_meses(cantidad=6):
    """Lista de (año, mes) de los últimos `cantidad` meses, del más antiguo al actual."""
    hoy = timezone.localdate()
    indice = hoy.year * 12 + (hoy.month - 1)
    return [divmod(i, 12) for i in range(indice - cantidad + 1, indice + 1)]


def _estadisticas(compras_validas):
    """KPIs y datos de gráficos de las compras (no canceladas) de un proveedor."""
    hoy = timezone.localdate()
    del_mes = compras_validas.filter(fecha__year=hoy.year, fecha__month=hoy.month)

    top = list(
        DetalleCompra.objects.filter(compra__in=compras_validas, producto__isnull=False)
        .values('producto__nombre')
        .annotate(total_und=Sum('cantidad'))
        .order_by('-total_und')[:5]
    )

    meses = _ultimos_meses(6)
    totales = {m: CERO for m in meses}
    desde = timezone.make_aware(datetime(meses[0][0], meses[0][1] + 1, 1))
    for fecha, valor in compras_validas.filter(fecha__gte=desde).values_list('fecha', 'valor'):
        local = timezone.localtime(fecha)
        clave = (local.year, local.month - 1)
        if clave in totales:
            totales[clave] += valor

    return {
        'subtotal_compras': compras_validas.aggregate(s=Sum('valor'))['s'] or CERO,
        'total_gastado': compras_validas.aggregate(g=Sum(F('valor') - F('saldo')))['g'] or CERO,
        'count_mes': del_mes.count(),
        'total_mes': del_mes.aggregate(s=Sum('valor'))['s'] or CERO,
        'producto_top': top[0] if top else None,
        'meses_labels_json': json.dumps([f"{MESES_ABREV[m]} {y}" for y, m in meses]),
        'meses_data_json': json.dumps([float(totales[k]) for k in meses]),
        'productos_labels_json': json.dumps([p['producto__nombre'] for p in top]),
        'productos_data_json': json.dumps([int(p['total_und']) for p in top]),
    }


# ── LISTADO Y REGISTRO DE COMPRAS ──────────────────────────────────────────────
@login_required
def lista_compras(request):
    """Historial de compras por proveedor, KPIs, gráficos y registro de nuevas compras."""
    disponibles = _proveedores_disponibles()
    proveedor = _resolver_proveedor(request, disponibles)

    form = NuevaCompraForm()
    if request.method == 'POST' and 'cantidad' in request.POST:
        form = NuevaCompraForm(request.POST)
        destino = _procesar_nueva_compra(request, form, proveedor)
        if destino:
            return redirect(destino)

    compras = []
    estadisticas = {}
    if proveedor:
        todas = Compra.objects.filter(proveedor=proveedor)
        compras = list(
            todas.select_related('proveedor', 'usuario')
            .prefetch_related('detalles__producto', 'detalles__lote')
            .order_by('-fecha', '-codigo_compra')
        )
        estadisticas = _estadisticas(todas.exclude(estado='cancelada'))
    else:
        estadisticas = _estadisticas(Compra.objects.none())

    context = {
        'proveedor': proveedor,
        'todos_proveedores': disponibles,
        'compras': compras,
        'compras_count': len(compras),
        'form': form,
        'breadcrumb_items': [{'nombre': 'Compras', 'url': None}],
        **estadisticas,
    }
    return render(request, 'compras/compras.html', context)


# ── CAMBIO DE ESTADO ───────────────────────────────────────────────────────────
@login_required
@require_POST
def cambiar_estado_compra(request, id=None):
    """pendiente -> confirmada/cancelada; confirmada -> recibida/cancelada."""
    compra = get_object_or_404(Compra, pk=id or request.POST.get('compra_id'))
    nuevo_estado = request.POST.get('estado')

    try:
        compra.cambiar_estado(nuevo_estado)
    except ValidationError as e:
        _mensajes_validacion(request, e)
    else:
        messages.success(
            request,
            f'✅ Estado de la compra #{compra.codigo_compra} actualizado a "{compra.get_estado_display()}".'
        )

    destino = request.POST.get('next') or _url_lista(compra.proveedor_id)
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = _url_lista(compra.proveedor_id)
    return redirect(destino)


# ── REGISTRO DE PAGO / ABONO ───────────────────────────────────────────────────
@login_required
@require_POST
def registrar_pago_compra(request, id=None):
    """Registra un abono, reduce el saldo y deja el movimiento en MetodoPago."""
    compra = get_object_or_404(Compra, pk=id or request.POST.get('compra_id'))

    destino = request.POST.get('next') or _url_lista(compra.proveedor_id)
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = _url_lista(compra.proveedor_id)

    try:
        monto = Decimal(str(request.POST.get('monto_pagado', '0')).strip())
        if not monto.is_finite():
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        monto = CERO

    fecha_pago = parse_datetime(request.POST.get('fecha_pago') or '')
    if fecha_pago and timezone.is_naive(fecha_pago):
        fecha_pago = timezone.make_aware(fecha_pago)

    try:
        compra.registrar_pago(
            monto,
            metodo=request.POST.get('metodo_pago') or 'efectivo',
            referencia=request.POST.get('numero_factura', ''),
            fecha=fecha_pago,
        )
    except ValidationError as e:
        _mensajes_validacion(request, e)
        return redirect(destino)

    if compra.saldo <= CERO:
        messages.success(
            request,
            f'✅ Pago de {cop(monto)} registrado. La compra #{compra.codigo_compra} quedó completamente PAGADA.'
        )
    else:
        messages.success(
            request,
            f'✅ Abono de {cop(monto)} registrado en la compra #{compra.codigo_compra}. '
            f'Saldo pendiente: {cop(compra.saldo)}.'
        )
    return redirect(destino)


# ── DETALLE ────────────────────────────────────────────────────────────────────
@login_required
def detalle_compra(request, id):
    """Detalle completo de una compra."""
    compra = get_object_or_404(
        Compra.objects.select_related('proveedor', 'usuario')
        .prefetch_related('detalles__producto__categoria', 'detalles__lote'),
        pk=id,
    )
    url_lista = _url_lista(compra.proveedor_id)
    context = {
        'compra': compra,
        'proveedor': compra.proveedor,
        'pagos': compra.metodopago_set.order_by('-fecha', '-codigo_metodo'),
        'url_lista': url_lista,
        'breadcrumb_items': [
            {'nombre': 'Compras', 'url': url_lista},
            {'nombre': f'Compra #{compra.codigo_compra}', 'url': None},
        ],
    }
    return render(request, 'compras/detalle_compra.html', context)


@login_required
def ultima_compra(request):
    """Redirige al detalle de la compra más reciente."""
    ultima = Compra.objects.order_by('-fecha', '-codigo_compra').first()
    if ultima:
        return redirect('detalle_compra', id=ultima.pk)
    messages.info(request, 'Aún no hay compras registradas.')
    return redirect('lista_compras')
