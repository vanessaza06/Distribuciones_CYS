import json
from decimal import Decimal, InvalidOperation
from functools import wraps
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.models import (
    Venta, DetalleVenta, Caja, Devolucion, DetalleDevolucion,
    Producto, Categoria, PresentacionProducto, Usuario
)

BILLETES_DENOM = [100000, 50000, 20000, 10000, 5000, 2000, 1000]
MONEDAS_DENOM  = [500, 200, 100, 50]


# ════════════════════════════════════════
# DECORADOR
# ════════════════════════════════════════

def session_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated and not request.session.get('usuario_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ════════════════════════════════════════
# VENTAS
# ════════════════════════════════════════

@session_required
def ventas_lista(request):
    ventas = Venta.objects.all().order_by('-fecha')
    categorias = Categoria.objects.all()
    hoy = timezone.localdate()
    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    total_dia = int(sum(v.total_venta for v in ventas_hoy))

    caja_abierta = Caja.objects.filter(fecha_hora__date=hoy).order_by('-fecha_hora').first()
    ultimo_cierre = Caja.objects.order_by('-fecha_hora').first()

    return render(request, 'ventas/ventas.html', {
        'ventas': ventas,
        'categorias': categorias,
        'total_dia': total_dia,
        'hoy': hoy,
        'caja_abierta': caja_abierta,
        'ultimo_cierre': ultimo_cierre,
        'billetes_denom': BILLETES_DENOM,
        'monedas_denom': MONEDAS_DENOM,
    })


# Alias para compatibilidad con urls.py y aside.html
ventas = ventas_lista


@session_required
def nueva_venta(request):
    if request.method != 'POST':
        return redirect('ventas')

    producto_ids = request.POST.getlist('producto_id[]')
    presentacion_ids = request.POST.getlist('presentacion_id[]')
    cantidades = request.POST.getlist('cantidad[]')
    precios = request.POST.getlist('precio[]')

    def to_decimal(key, default='0'):
        try:
            return Decimal(request.POST.get(key, default) or default)
        except (InvalidOperation, TypeError):
            return Decimal('0')

    descuento_pct = to_decimal('descuento_porcentaje')
    pago_efectivo = to_decimal('pago_efectivo')
    pago_tarjeta = to_decimal('pago_tarjeta')
    pago_transferencia = to_decimal('pago_transferencia')
    pago_nequi = to_decimal('pago_nequi')
    pago_daviplata = to_decimal('pago_daviplata')

    if not producto_ids:
        messages.error(request, "El carrito está vacío.")
        return redirect('ventas')

    vendedor = request.user if request.user.is_authenticated else None
    if not vendedor and request.session.get('usuario_id'):
        vendedor = Usuario.objects.filter(pk=request.session.get('usuario_id')).first()

    items_validados = []
    subtotal_venta = Decimal('0')

    for i, prod_id in enumerate(producto_ids):
        try:
            cantidad = int(cantidades[i])
            precio = Decimal(precios[i])
            if cantidad <= 0 or precio < 0:
                raise ValueError
        except (ValueError, TypeError, InvalidOperation, IndexError):
            messages.error(request, f"Datos inválidos en el ítem {i+1}.")
            return redirect('ventas')

        try:
            producto = Producto.objects.get(pk=prod_id)
        except Producto.DoesNotExist:
            messages.error(request, f"Producto {i+1} no encontrado.")
            return redirect('ventas')

        pres_id = presentacion_ids[i] if i < len(presentacion_ids) else ''
        presentacion = None

        if pres_id and pres_id != 'null':
            try:
                presentacion = PresentacionProducto.objects.get(pk=pres_id)
            except PresentacionProducto.DoesNotExist:
                messages.error(request, f"Presentación inválida para {producto.nombre}.")
                return redirect('ventas')

        items_validados.append({
            'producto': producto,
            'presentacion': presentacion,
            'cantidad': cantidad,
            'precio': precio,
        })
        subtotal_venta += precio * cantidad

    monto_descuento = (subtotal_venta * descuento_pct) / Decimal('100')
    total_final = subtotal_venta - monto_descuento
    total_pagado = pago_efectivo + pago_tarjeta + pago_transferencia + pago_nequi + pago_daviplata

    if total_pagado > Decimal('0') and total_pagado < total_final:
        messages.error(request, f"El total pagado (${total_pagado:,.0f}) no cubre el total (${total_final:,.0f}).".replace(',', '.'))
        return redirect('ventas')

    metodo_pago = 'efectivo'
    if pago_tarjeta > 0:
        metodo_pago = 'tarjeta'
    elif pago_transferencia > 0:
        metodo_pago = 'transferencia'
    elif pago_nequi > 0:
        metodo_pago = 'nequi'
    elif pago_daviplata > 0:
        metodo_pago = 'daviplata'

    venta = Venta.objects.create(
        total_venta=total_final,
        metodo_pago=metodo_pago,
        usuario=vendedor or Usuario.objects.first(),
    )

    for item in items_validados:
        DetalleVenta.objects.create(
            venta=venta,
            producto=item['producto'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio'],
            subtotal=item['precio'] * item['cantidad'],
            total=item['precio'] * item['cantidad'],
        )

    messages.success(request, f"Venta registrada — Total: ${total_final:,.0f}".replace(',', '.'))
    return redirect('ventas')


@session_required
def eliminar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.delete()
        messages.success(request, "Venta eliminada.")
    return redirect('ventas')


def producto_stock_json(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    presentaciones = []
    if hasattr(producto, 'presentaciones'):
        presentaciones = [
            {'id': p.id, 'nombre': p.nombre, 'cantidad': getattr(p, 'cantidad', 0), 'precio': float(getattr(p, 'precio_venta', 0))}
            for p in producto.presentaciones.all()
        ]
    return JsonResponse({
        'stock': getattr(producto, 'cantidad_disponible', 0),
        'precio': float(getattr(producto, 'precio_unitario', 0)),
        'unidad': getattr(producto, 'unidad', 'Unid'),
        'presentaciones': presentaciones,
    })


# ════════════════════════════════════════
# VENTAS DEL DÍA
# ════════════════════════════════════════

@session_required
def ventas_dia(request):
    hoy = timezone.localdate()

    ventas_qs = Venta.objects.filter(fecha__date=hoy).order_by('-fecha')

    ventas_list = list(ventas_qs)
    total_dia = sum(v.total_venta for v in ventas_list)
    total_productos = sum(det.cantidad for v in ventas_list for det in getattr(v, 'detalles', []))

    caja_abierta = Caja.objects.filter(fecha_hora__date=hoy).order_by('-fecha_hora').first()
    ultimo_cierre = Caja.objects.order_by('-fecha_hora').first()

    return render(request, 'ventas/ventas_dia.html', {
        'ventas': ventas_qs,
        'total_dia': total_dia,
        'total_productos': total_productos,
        'hoy': hoy,
        'caja_abierta': caja_abierta,
        'ultimo_cierre': ultimo_cierre,
    })


# ════════════════════════════════════════
# CAJA — APERTURA Y CIERRE
# ════════════════════════════════════════

@session_required
def caja(request):
    hoy = timezone.localdate()
    ultimo_cierre = Caja.objects.order_by('-fecha_hora').first()
    hay_cierre_hoy = Caja.objects.filter(fecha_hora__date=hoy).exists()

    return render(request, 'ventas/caja.html', {
        'ultimo_cierre': ultimo_cierre,
        'hay_cierre_hoy': hay_cierre_hoy,
    })


@require_POST
@session_required
def apertura_caja(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    hoy = timezone.localdate()

    if Caja.objects.filter(fecha_hora__date=hoy).exists():
        return JsonResponse({'ok': False, 'error': 'Ya existe un registro de caja para hoy.'}, status=400)

    try:
        monto_base = float(data.get('monto_base', 0))
        if monto_base < 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Monto base inválido.'}, status=400)

    usuario = request.user if request.user.is_authenticated else Usuario.objects.first()

    Caja.objects.create(
        monto_base=monto_base,
        total_efectivo=0,
        total_transferencias=0,
        total_retirado=0,
        usuario=usuario,
        observacion=data.get('observacion', ''),
        denominaciones=data.get('denominaciones', {}),
    )
    return JsonResponse({'ok': True})


@require_POST
@session_required
def cierre_caja(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'JSON inválido.'}, status=400)

    hoy = timezone.localdate()
    caja_reg = Caja.objects.filter(fecha_hora__date=hoy).first()

    if not caja_reg:
        return JsonResponse({'ok': False, 'error': 'No hay caja abierta para hoy.'}, status=400)

    try:
        total_contado = float(data.get('total_contado', 0))
        total_retirado = float(data.get('total_retirado', 0))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Valores numéricos inválidos.'}, status=400)

    caja_reg.total_efectivo = total_contado
    caja_reg.total_retirado = total_retirado
    if 'denominaciones' in data:
        caja_reg.denominaciones = data['denominaciones']
    caja_reg.save()

    return JsonResponse({'ok': True})


@require_POST
@session_required
def registrar_conteo(request):
    return apertura_caja(request)


# ════════════════════════════════════════
# DEVOLUCIONES
# ════════════════════════════════════════

@session_required
def lista_devoluciones(request):
    devoluciones = Devolucion.objects.all().order_by('-fecha')
    return render(request, 'ventas/devoluciones.html', {'devoluciones': devoluciones})


@session_required
def buscar_venta_devolucion(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'ventas': []})

    ventas_qs = Venta.objects.all().order_by('-fecha')
    if q.isdigit():
        ventas_qs = Venta.objects.filter(pk=int(q))

    return JsonResponse({'ventas': [
        {'id': v.pk, 'cliente': str(getattr(v, 'usuario', 'Cliente')),
         'fecha': v.fecha.strftime('%d/%m/%Y %H:%M'), 'total': float(v.total_venta)}
        for v in ventas_qs[:10]
    ]})


@session_required
def detalle_venta_devolucion(request, venta_id):
    venta = get_object_or_404(Venta, pk=venta_id)
    return JsonResponse({
        'venta_id': venta.pk,
        'cliente': str(getattr(venta, 'usuario', 'Cliente')),
        'fecha': venta.fecha.strftime('%d/%m/%Y %H:%M'),
        'total': float(venta.total_venta),
        'descuento': 0,
        'detalles': [
            {
                'detalle_id': d.pk,
                'producto_id': d.producto.pk,
                'producto': d.producto.nombre,
                'cantidad': d.cantidad,
                'precio': float(d.precio_unitario),
                'subtotal': float(d.subtotal),
            }
            for d in getattr(venta, 'detalles', [])
        ],
    })


@session_required
@transaction.atomic
def registrar_devolucion(request):
    if request.method != 'POST':
        return redirect('lista_devoluciones')

    venta_id = request.POST.get('venta_id')
    tiene_comprobante = request.POST.get('tiene_comprobante') == '1'
    motivo = request.POST.get('motivo', 'otro')
    observaciones = request.POST.get('observaciones', '')
    producto_ids = request.POST.getlist('producto_id[]')
    cantidades = request.POST.getlist('cantidad[]')
    precios = request.POST.getlist('precio[]')

    if not tiene_comprobante:
        messages.warning(request, 'No se puede registrar la devolución sin comprobante de compra.')
        return redirect('lista_devoluciones')

    venta = get_object_or_404(Venta, pk=venta_id)
    total_devuelto = sum(int(cantidades[i]) * float(precios[i]) for i in range(len(producto_ids)))

    devolucion = Devolucion.objects.create(
        venta=venta,
        motivo=motivo,
        tipo_devolucion='devolucion',
        observaciones=observaciones,
        presenta_comprobante=tiene_comprobante,
        total_devuelto=total_devuelto,
        estado='completado',
        cantidad_cambio=0,
        metodo_pago_devolucion=venta.metodo_pago,
        usuario=request.user if request.user.is_authenticated else Usuario.objects.first(),
    )

    for i in range(len(producto_ids)):
        producto = get_object_or_404(Producto, pk=producto_ids[i])
        cantidad = int(cantidades[i])

        DetalleDevolucion.objects.create(
            devolucion=devolucion,
            producto=producto,
            cantidad=cantidad,
            fecha_vencimiento=timezone.now().date(),
            descripcion=f"Devolución de {producto.nombre}",
        )

    messages.success(request, f'Devolución #{devolucion.codigo_devolucion} registrada correctamente.')
    return redirect('comprobante_devolucion', pk=devolucion.pk)


@session_required
def comprobante_devolucion(request, pk):
    devolucion = get_object_or_404(Devolucion, pk=pk)
    return render(request, 'ventas/comprobante_devolucion.html', {'devolucion': devolucion})
