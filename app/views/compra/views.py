"""
Vistas del módulo de Compras.
Distribuciones CYS
"""

import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone

from app.models import Proveedor, Compra, DetalleCompra, MetodoPago, Producto, Lote
from app.forms import NuevaCompraForm

logger = logging.getLogger(__name__)


# ── VISTA PRINCIPAL: LISTADO Y REGISTRO DE COMPRAS ─────────────────────────────
@login_required
def lista_compras(request):
    """
    Lista el historial de compras por proveedor, calcula KPIs,
    genera datos para gráficos y procesa el registro de nuevas compras.
    """
    todos_proveedores = Proveedor.objects.filter(estado='activo').order_by('nombre_empresa')
    if not todos_proveedores.exists():
        todos_proveedores = Proveedor.objects.all().order_by('nombre_empresa')

    # Identificar el proveedor activo (prioridad: POST -> GET -> sesión -> primer proveedor)
    proveedor_id = request.POST.get('proveedor_id') or request.GET.get('proveedor') or request.session.get('proveedor_id')
    proveedor = None

    if proveedor_id:
        try:
            proveedor = Proveedor.objects.filter(pk=proveedor_id).first()
            if proveedor:
                request.session['proveedor_id'] = str(proveedor.pk)
        except Exception:
            proveedor = None

    if not proveedor and todos_proveedores.exists():
        proveedor = todos_proveedores.first()
        request.session['proveedor_id'] = str(proveedor.pk)

    # ── Procesar registro de nueva compra (POST desde modal) ────────────────────
    form = NuevaCompraForm()
    if request.method == 'POST' and 'cantidad' in request.POST:
        if not proveedor:
            messages.error(request, 'Debe seleccionar un proveedor válido para registrar la compra.')
            return redirect('lista_compras')

        form = NuevaCompraForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            lote = form.cleaned_data.get('lote')
            cantidad = form.cleaned_data['cantidad']
            precio_unitario = form.cleaned_data['precio_unitario']
            total = Decimal(str(cantidad)) * precio_unitario

            try:
                with transaction.atomic():
                    # 1. Crear cabecera de compra
                    nueva_compra = Compra.objects.create(
                        proveedor=proveedor,
                        usuario=request.user,
                        fecha=timezone.now(),
                        valor=total,
                        saldo=total,
                        estado='pendiente',
                    )

                    # 2. Crear detalle de compra
                    DetalleCompra.objects.create(
                        compra=nueva_compra,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal_compra=total,
                        fecha_registro=timezone.now(),
                    )

                    # 3. Si se seleccionó lote, ingresar unidades al stock del lote
                    if lote:
                        lote.stock_actual = (lote.stock_actual or 0) + cantidad
                        lote.save(update_fields=['stock_actual'])

                messages.success(
                    request,
                    f'✅ Compra #{nueva_compra.codigo_compra} registrada exitosamente: '
                    f'{cantidad} und. de "{producto.nombre}" (${total:,.0f}).'
                )
                return redirect('lista_compras')
            except Exception as e:
                logger.error(f"Error al registrar compra: {e}")
                messages.error(request, f'Ocurrió un error al guardar la compra: {str(e)}')
        else:
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')

    # ── Consultar compras del proveedor seleccionado ───────────────────────────
    compras = []
    if proveedor:
        compras_qs = Compra.objects.filter(proveedor=proveedor).select_related(
            'proveedor', 'usuario'
        ).prefetch_related('detalles').order_by('-fecha')

        # Adecuar atributos para compras.html
        for c in compras_qs:
            c.id = c.codigo_compra
            primer_detalle = c.detalles.first()
            if primer_detalle:
                c.cantidad = primer_detalle.cantidad
                c.precio_unitario = primer_detalle.precio_unitario
            else:
                c.cantidad = 1
                c.precio_unitario = c.valor
            compras.append(c)

    # ── KPIs y Estadísticas ───────────────────────────────────────────────────
    hoy = timezone.now()
    mes_actual = hoy.month
    ano_actual = hoy.year

    compras_proveedor_qs = Compra.objects.filter(proveedor=proveedor) if proveedor else Compra.objects.none()
    subtotal_compras = compras_proveedor_qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

    compras_mes_qs = compras_proveedor_qs.filter(fecha__year=ano_actual, fecha__month=mes_actual)
    count_mes = compras_mes_qs.count()
    total_mes = compras_mes_qs.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

    # Total pagado hasta la fecha para este proveedor
    total_gastado = compras_proveedor_qs.aggregate(
        gastado=Sum(F('valor') - F('saldo'))
    )['gastado'] or Decimal('0.00')

    # ── Datos para los Gráficos (Chart.js) ─────────────────────────────────────
    # 1. Compras por mes (últimos 6 meses)
    meses_labels = []
    meses_data = []
    for i in range(5, -1, -1):
        m = (mes_actual - i - 1) % 12 + 1
        y = ano_actual if (mes_actual - i) > 0 else ano_actual - 1
        total_m = Compra.objects.filter(fecha__year=y, fecha__month=m).aggregate(s=Sum('valor'))['s'] or 0
        nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        meses_labels.append(f"{nombres_meses[m-1]} {y}")
        meses_data.append(float(total_m))

    # 2. Gastos por proveedor (Top 5 general)
    gastos_qs = (
        Compra.objects.values('proveedor__nombre_empresa')
        .annotate(total=Sum('valor'))
        .order_by('-total')[:5]
    )
    gastos_labels = [g['proveedor__nombre_empresa'] or 'Sin nombre' for g in gastos_qs]
    gastos_data = [float(g['total'] or 0) for g in gastos_qs]
    suma_gastos = sum(gastos_data) or 1
    gastos_porcentajes = [int((g / suma_gastos) * 100) for g in gastos_data]

    context = {
        'proveedor': proveedor,
        'todos_proveedores': todos_proveedores,
        'compras': compras,
        'compras_count': len(compras),
        'form': form,
        'subtotal_compras': subtotal_compras,
        'total_gastado': total_gastado,
        'count_mes': count_mes,
        'total_mes': total_mes,
        'producto_top': None,
        'meses_labels_json': json.dumps(meses_labels),
        'meses_data_json': json.dumps(meses_data),
        'productos_labels_json': json.dumps([]),
        'productos_data_json': json.dumps([]),
        'gastos_labels_json': json.dumps(gastos_labels),
        'gastos_data_json': json.dumps(gastos_data),
        'gastos_porcentajes_json': json.dumps(gastos_porcentajes),
        'breadcrumb_items': [
            {'nombre': 'Proveedores', 'url': reverse('lista_proveedores')},
            {'nombre': 'Compras', 'url': None},
        ],
    }

    return render(request, 'compras/compras.html', context)


# ── CAMBIO DE ESTADO DE UNA COMPRA ─────────────────────────────────────────────
@login_required
@require_POST
def cambiar_estado_compra(request, id=None):
    """
    Actualiza el estado de una compra según el flujo:
    - pendiente  -> confirmada / cancelada
    - confirmada -> recibida / cancelada
    """
    compra_id = id or request.POST.get('compra_id')
    compra = get_object_or_404(Compra, pk=compra_id)
    nuevo_estado = request.POST.get('estado')

    transiciones_validas = {
        'pendiente': {'confirmada', 'cancelada'},
        'confirmada': {'recibida', 'cancelada'},
        'recibida': set(),
        'cancelada': set(),
    }

    if nuevo_estado not in transiciones_validas.get(compra.estado, set()):
        messages.error(request, f'No es posible cambiar la compra de "{compra.get_estado_display()}" a "{nuevo_estado}".')
        return redirect('lista_compras')

    compra.estado = nuevo_estado
    compra.save(update_fields=['estado'])
    messages.success(request, f'✅ Estado de la compra #{compra.codigo_compra} actualizado a "{nuevo_estado.capitalize()}".')
    return redirect('lista_compras')


# ── REGISTRO DE PAGO / ABONO DE COMPRA ─────────────────────────────────────────
@login_required
@require_POST
def registrar_pago_compra(request, id=None):
    """
    Registra un abono a la compra, reduce el saldo pendiente
    y registra el movimiento en MetodoPago.
    """
    compra_id = id or request.POST.get('compra_id')
    compra = get_object_or_404(Compra, pk=compra_id)

    if compra.estado == 'cancelada':
        messages.error(request, 'No se pueden registrar pagos en una compra cancelada.')
        return redirect('lista_compras')

    try:
        monto = Decimal(str(request.POST.get('monto_pagado', '0')))
    except Exception:
        monto = Decimal('0.00')

    if monto <= Decimal('0.00'):
        messages.error(request, 'El abono debe ser mayor a cero.')
        return redirect('lista_compras')

    if monto > compra.saldo:
        messages.error(request, f'El monto (${monto:,.0f}) supera el saldo pendiente (${compra.saldo:,.0f}).')
        return redirect('lista_compras')

    metodo = request.POST.get('metodo_pago', 'efectivo')
    numero_factura = request.POST.get('numero_factura', '').strip()

    with transaction.atomic():
        compra.saldo = max(Decimal('0.00'), compra.saldo - monto)
        compra.save(update_fields=['saldo'])

        # Registrar en la tabla metodo_pago del sistema
        MetodoPago.objects.create(
            compra=compra,
            valor=monto,
            referencia=numero_factura or f"Abono Compra #{compra.codigo_compra}",
            efectivo=monto if metodo == 'efectivo' else Decimal('0.00'),
            transaccion=monto if metodo != 'efectivo' else Decimal('0.00'),
            observacion=f"Pago vía {metodo.capitalize()}" + (f" - Factura {numero_factura}" if numero_factura else ""),
            fecha=timezone.now(),
        )

    messages.success(
        request,
        f'✅ Pago de ${monto:,.0f} registrado con éxito. '
        f'Saldo restante: ${compra.saldo:,.0f}.'
    )
    return redirect('lista_compras')
