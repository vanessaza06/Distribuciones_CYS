from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime

from app.models import MetodoPago, Compra


@login_required
def lista_metodos_pago(request):
    """Muestra la lista de registros de métodos de pago con KPIs, filtros y buscador."""
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    pagos_qs = MetodoPago.objects.select_related('compra', 'compra__proveedor').order_by('-fecha')

    # Filtros de fecha
    if fecha_inicio:
        try:
            fi = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            pagos_qs = pagos_qs.filter(fecha__date__gte=fi.date())
        except ValueError:
            pass

    if fecha_fin:
        try:
            ff = datetime.strptime(fecha_fin, '%Y-%m-%d')
            pagos_qs = pagos_qs.filter(fecha__date__lte=ff.date())
        except ValueError:
            pass

    # Filtro por tipo de pago
    if tipo == 'efectivo':
        pagos_qs = pagos_qs.filter(efectivo__gt=0)
    elif tipo == 'transaccion':
        pagos_qs = pagos_qs.filter(transaccion__gt=0)

    # Buscador textual
    if q:
        if q.isdigit():
            pagos_qs = pagos_qs.filter(
                Q(codigo_metodo=int(q)) |
                Q(compra__codigo_compra=int(q)) |
                Q(referencia__icontains=q)
            )
        else:
            pagos_qs = pagos_qs.filter(
                Q(referencia__icontains=q) |
                Q(observacion__icontains=q) |
                Q(compra__proveedor__nombre_proveedor__icontains=q)
            )

    pagos_list = list(pagos_qs)

    # Métricas KPI
    total_recaudado = sum((p.valor or Decimal('0.00')) for p in pagos_list)
    total_efectivo = sum((p.efectivo or Decimal('0.00')) for p in pagos_list)
    total_transaccion = sum((p.transaccion or Decimal('0.00')) for p in pagos_list)
    total_registros = len(pagos_list)

    # Lista de compras abiertas para el modal de creación
    compras_disponibles = Compra.objects.filter(estado__in=['pendiente', 'aprobada']).order_by('-fecha')[:30]

    context = {
        'pagos': pagos_list,
        'total_recaudado': total_recaudado,
        'total_efectivo': total_efectivo,
        'total_transaccion': total_transaccion,
        'total_registros': total_registros,
        'compras_disponibles': compras_disponibles,
        'q': q,
        'tipo': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'metodo_de_pago/lista.html', context)


@login_required
def crear_metodo_pago(request):
    """Crea un nuevo registro en la tabla metodo_pago."""
    if request.method == 'POST':
        monto_raw = request.POST.get('valor', '0').replace(',', '.').strip()
        referencia = request.POST.get('referencia', '').strip()
        tipo_pago = request.POST.get('tipo_pago', 'efectivo').strip()
        compra_id = request.POST.get('compra_id', '').strip()
        observacion = request.POST.get('observacion', '').strip()

        try:
            monto = Decimal(monto_raw)
            if monto <= Decimal('0.00'):
                messages.error(request, '⚠️ El valor del pago debe ser mayor a 0.')
                return redirect('lista_metodos_pago')
        except Exception:
            messages.error(request, '⚠️ Formato de monto inválido.')
            return redirect('lista_metodos_pago')

        compra_obj = None
        if compra_id and compra_id.isdigit():
            compra_obj = Compra.objects.filter(pk=int(compra_id)).first()

        efectivo_val = monto if tipo_pago == 'efectivo' else Decimal('0.00')
        transaccion_val = monto if tipo_pago == 'transaccion' else Decimal('0.00')

        pago = MetodoPago.objects.create(
            fecha=timezone.now(),
            valor=monto,
            referencia=referencia or f"Pago Manual #{timezone.now().strftime('%Y%m%d%H%M')}",
            efectivo=efectivo_val,
            transaccion=transaccion_val,
            observacion=observacion,
            compra=compra_obj,
        )

        # Si se vinculó a una compra, actualizar el saldo de la compra si aplica
        if compra_obj:
            compra_obj.saldo = max(Decimal('0.00'), (compra_obj.saldo or Decimal('0.00')) - monto)
            compra_obj.save(update_fields=['saldo'])

        messages.success(request, f'✅ Registro de Pago #{pago.codigo_metodo} por ${monto:,.0f} guardado con éxito.')
        return redirect('lista_metodos_pago')

    return redirect('lista_metodos_pago')


@login_required
def eliminar_metodo_pago(request, pk):
    """Elimina un registro de método de pago."""
    pago = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        codigo = pago.codigo_metodo
        monto = pago.valor
        pago.delete()
        messages.success(request, f'🗑️ Registro de Pago #{codigo} (${monto:,.0f}) eliminado.')
    return redirect('lista_metodos_pago')


@login_required
def editar_metodo_pago(request, pk):
    """Edita un registro existente en la tabla metodo_pago."""
    pago = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        monto_raw = request.POST.get('valor', '0').replace(',', '.').strip()
        referencia = request.POST.get('referencia', '').strip()
        tipo_pago = request.POST.get('tipo_pago', 'efectivo').strip()
        observacion = request.POST.get('observacion', '').strip()

        try:
            monto = Decimal(monto_raw)
            if monto <= Decimal('0.00'):
                messages.error(request, '⚠️ El valor del pago debe ser mayor a 0.')
                return redirect('lista_metodos_pago')
        except Exception:
            messages.error(request, '⚠️ Formato de monto inválido.')
            return redirect('lista_metodos_pago')

        pago.valor = monto
        pago.referencia = referencia
        pago.observacion = observacion
        if tipo_pago == 'efectivo':
            pago.efectivo = monto
            pago.transaccion = Decimal('0.00')
        else:
            pago.efectivo = Decimal('0.00')
            pago.transaccion = monto

        pago.save()
        messages.success(request, f'✏️ Registro de Pago #{pago.codigo_metodo} actualizado con éxito.')
        return redirect('lista_metodos_pago')

    return redirect('lista_metodos_pago')

