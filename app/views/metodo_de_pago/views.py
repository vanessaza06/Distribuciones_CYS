from decimal import Decimal
from datetime import datetime
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from app.models import MetodoPago, Compra, Venta, Caja


def session_required(view_func):
    """Permite el acceso a usuarios autenticados por Django o por sesión personalizada."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated and not request.session.get('usuario_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@session_required
def lista_metodos_pago(request):
    """
    Panel centralizado de Métodos de Pago integrando Ventas, Caja y Compras.
    Por defecto muestra los pagos y recaudos de Ventas organizados por turno de Caja.
    """
    tab = request.GET.get('tab', 'ventas').strip()
    q = request.GET.get('q', '').strip()
    metodo = request.GET.get('metodo', '').strip().lower()
    caja_id = request.GET.get('caja_id', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    # ═════════════════════════════════════════════════════════
    # 1. PESTAÑA PRINCIPAL: VENTAS Y CAJA (INGRESOS / COBROS)
    # ═════════════════════════════════════════════════════════
    ventas_qs = Venta.objects.select_related('caja', 'vendedor').prefetch_related(
        'detalles__producto', 'detalles__presentacion'
    ).order_by('-fecha')

    # Filtro por rango de fechas
    if fecha_inicio:
        try:
            fi = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            ventas_qs = ventas_qs.filter(fecha__date__gte=fi.date())
        except ValueError:
            pass

    if fecha_fin:
        try:
            ff = datetime.strptime(fecha_fin, '%Y-%m-%d')
            ventas_qs = ventas_qs.filter(fecha__date__lte=ff.date())
        except ValueError:
            pass

    # Filtro por Turno de Caja específico
    if caja_id and caja_id.isdigit():
        ventas_qs = ventas_qs.filter(caja_id=int(caja_id))

    # Filtro por método de pago o saldo pendiente
    if metodo == 'efectivo':
        ventas_qs = ventas_qs.filter(Q(pago_efectivo__gt=0) | Q(metodo_pago__icontains='efectivo'))
    elif metodo == 'nequi':
        ventas_qs = ventas_qs.filter(Q(pago_nequi__gt=0) | Q(metodo_pago__icontains='nequi'))
    elif metodo == 'daviplata':
        ventas_qs = ventas_qs.filter(Q(pago_daviplata__gt=0) | Q(metodo_pago__icontains='daviplata'))
    elif metodo == 'tarjeta':
        ventas_qs = ventas_qs.filter(Q(pago_tarjeta__gt=0) | Q(metodo_pago__icontains='tarjeta'))
    elif metodo == 'transferencia':
        ventas_qs = ventas_qs.filter(Q(pago_transferencia__gt=0) | Q(metodo_pago__icontains='transferencia'))
    elif metodo == 'pendiente':
        ventas_qs = ventas_qs.filter(saldo_pendiente__gt=0)

    # Buscador textual
    if q:
        if q.isdigit():
            ventas_qs = ventas_qs.filter(
                Q(codigo_venta=int(q)) |
                Q(caja_id=int(q)) |
                Q(cliente_nombre__icontains=q) |
                Q(observacion__icontains=q)
            )
        else:
            ventas_qs = ventas_qs.filter(
                Q(cliente_nombre__icontains=q) |
                Q(observacion__icontains=q) |
                Q(metodo_pago__icontains=q)
            )

    ventas_raw = list(ventas_qs)

    total_ventas_monto = Decimal('0')
    total_efectivo_ventas = Decimal('0')
    total_nequi_ventas = Decimal('0')
    total_daviplata_ventas = Decimal('0')
    total_tarjeta_ventas = Decimal('0')
    total_transferencia_ventas = Decimal('0')
    total_pendiente_ventas = Decimal('0')

    cant_efectivo = 0
    cant_nequi = 0
    cant_daviplata = 0
    cant_tarjeta = 0
    cant_transferencia = 0
    cant_pendiente = 0

    ventas_procesadas = []
    for v in ventas_raw:
        monto_total = Decimal(str(v.total_con_descuento if (v.total_con_descuento and v.total_con_descuento > 0) else (v.total_venta or 0)))
        pe = Decimal(str(v.pago_efectivo or 0))
        pt = Decimal(str(v.pago_tarjeta or 0))
        ptr = Decimal(str(v.pago_transferencia or 0))
        pn = Decimal(str(v.pago_nequi or 0))
        pd = Decimal(str(v.pago_daviplata or 0))
        sp = Decimal(str(v.saldo_pendiente or 0))

        # Si no se ingresaron desgloses explícitos, usar metodo_pago string
        if pe == 0 and pt == 0 and ptr == 0 and pn == 0 and pd == 0:
            mp_str = (v.metodo_pago or 'efectivo').lower()
            if 'efectivo' in mp_str:
                pe = max(Decimal('0'), monto_total - sp)
            elif 'nequi' in mp_str:
                pn = max(Decimal('0'), monto_total - sp)
            elif 'daviplata' in mp_str:
                pd = max(Decimal('0'), monto_total - sp)
            elif 'tarjeta' in mp_str:
                pt = max(Decimal('0'), monto_total - sp)
            else:
                ptr = max(Decimal('0'), monto_total - sp)

        total_ventas_monto += monto_total
        total_efectivo_ventas += pe
        total_nequi_ventas += pn
        total_daviplata_ventas += pd
        total_tarjeta_ventas += pt
        total_transferencia_ventas += ptr
        total_pendiente_ventas += sp

        if pe > 0: cant_efectivo += 1
        if pn > 0: cant_nequi += 1
        if pd > 0: cant_daviplata += 1
        if pt > 0: cant_tarjeta += 1
        if ptr > 0: cant_transferencia += 1
        if sp > 0: cant_pendiente += 1

        desglose_badges = []
        if pe > 0:
            desglose_badges.append({'tipo': 'Efectivo', 'monto': pe, 'color': '#2ed573', 'bg': 'rgba(46,213,115,0.15)', 'icon': 'bi-cash'})
        if pn > 0:
            desglose_badges.append({'tipo': 'Nequi', 'monto': pn, 'color': '#e84393', 'bg': 'rgba(232,67,147,0.15)', 'icon': 'bi-phone'})
        if pd > 0:
            desglose_badges.append({'tipo': 'Daviplata', 'monto': pd, 'color': '#ff7675', 'bg': 'rgba(255,118,117,0.15)', 'icon': 'bi-phone-fill'})
        if pt > 0:
            desglose_badges.append({'tipo': 'Tarjeta', 'monto': pt, 'color': '#74b9ff', 'bg': 'rgba(116,185,255,0.15)', 'icon': 'bi-credit-card'})
        if ptr > 0:
            desglose_badges.append({'tipo': 'Transferencia', 'monto': ptr, 'color': '#a55eea', 'bg': 'rgba(165,94,234,0.15)', 'icon': 'bi-bank'})

        # Determinar estado de la caja asignada
        caja_info = None
        if v.caja:
            obs_caja = v.caja.observacion or ''
            es_cerrada = '[CERRADO]' in obs_caja
            caja_info = {
                'id': v.caja.codigo_caja,
                'es_cerrada': es_cerrada,
                'label': f"Turno #{v.caja.codigo_caja}",
                'estado': 'CERRADO' if es_cerrada else 'ACTIVO'
            }

        ventas_procesadas.append({
            'venta': v,
            'monto_total': monto_total,
            'total_cobrado': max(Decimal('0'), monto_total - sp),
            'saldo_pendiente': sp,
            'observacion': v.observacion,
            'pago_efectivo': pe,
            'pago_nequi': pn,
            'pago_daviplata': pd,
            'pago_tarjeta': pt,
            'pago_transferencia': ptr,
            'desglose_badges': desglose_badges,
            'caja_info': caja_info,
        })

    total_digital_ventas = total_nequi_ventas + total_daviplata_ventas + total_tarjeta_ventas + total_transferencia_ventas

    # Lista de turnos/cajas disponibles para el filtro
    cajas_disponibles = []
    for c_obj in Caja.objects.all().order_by('-fecha_hora')[:40]:
        es_c = '[CERRADO]' in (c_obj.observacion or '')
        cajas_disponibles.append({
            'id': c_obj.codigo_caja,
            'label': f"Turno #{c_obj.codigo_caja} ({'Cerrado' if es_c else 'Activo'} - {c_obj.fecha_hora.strftime('%d/%m %I:%M %p')})",
            'es_cerrado': es_c,
        })

    # ═════════════════════════════════════════════════════════
    # 2. PESTAÑA SECUNDARIA: PAGOS A PROVEEDORES / COMPRAS
    # ═════════════════════════════════════════════════════════
    pagos_compras_qs = MetodoPago.objects.select_related('compra', 'compra__proveedor').order_by('-fecha')

    if fecha_inicio:
        try:
            fi = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            pagos_compras_qs = pagos_compras_qs.filter(fecha__date__gte=fi.date())
        except ValueError:
            pass

    if fecha_fin:
        try:
            ff = datetime.strptime(fecha_fin, '%Y-%m-%d')
            pagos_compras_qs = pagos_compras_qs.filter(fecha__date__lte=ff.date())
        except ValueError:
            pass

    if q:
        if q.isdigit():
            pagos_compras_qs = pagos_compras_qs.filter(
                Q(codigo_metodo=int(q)) |
                Q(compra__codigo_compra=int(q)) |
                Q(referencia__icontains=q)
            )
        else:
            pagos_compras_qs = pagos_compras_qs.filter(
                Q(referencia__icontains=q) |
                Q(observacion__icontains=q) |
                Q(compra__proveedor__nombre_proveedor__icontains=q)
            )

    pagos_compras_list = list(pagos_compras_qs)
    total_recaudado_compras = sum((p.valor or Decimal('0.00')) for p in pagos_compras_list)
    total_efectivo_compras = sum((p.efectivo or Decimal('0.00')) for p in pagos_compras_list)
    total_transaccion_compras = sum((p.transaccion or Decimal('0.00')) for p in pagos_compras_list)
    total_registros_compras = len(pagos_compras_list)

    compras_disponibles = Compra.objects.filter(estado__in=['pendiente', 'aprobada']).order_by('-fecha')[:30]

    context = {
        'tab': tab,
        # Ventas & Caja
        'ventas': ventas_procesadas,
        'total_ventas_monto': total_ventas_monto,
        'total_efectivo_ventas': total_efectivo_ventas,
        'total_digital_ventas': total_digital_ventas,
        'total_nequi_ventas': total_nequi_ventas,
        'total_daviplata_ventas': total_daviplata_ventas,
        'total_tarjeta_ventas': total_tarjeta_ventas,
        'total_transferencia_ventas': total_transferencia_ventas,
        'total_pendiente_ventas': total_pendiente_ventas,
        'ventas_count': len(ventas_procesadas),
        'cant_efectivo': cant_efectivo,
        'cant_nequi': cant_nequi,
        'cant_daviplata': cant_daviplata,
        'cant_tarjeta': cant_tarjeta,
        'cant_transferencia': cant_transferencia,
        'cant_pendiente': cant_pendiente,
        'cajas_disponibles': cajas_disponibles,
        'selected_caja': caja_id,
        'selected_metodo': metodo,
        # Compras
        'pagos_compras': pagos_compras_list,
        'total_recaudado_compras': total_recaudado_compras,
        'total_efectivo_compras': total_efectivo_compras,
        'total_transaccion_compras': total_transaccion_compras,
        'total_registros_compras': total_registros_compras,
        'compras_disponibles': compras_disponibles,
        # Filtros comunes
        'q': q,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'metodo_de_pago/lista.html', context)


@session_required
def crear_metodo_pago(request):
    """Crea un nuevo registro en la tabla metodo_pago (compras/proveedores)."""
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
                return redirect('/metodos-pago/?tab=compras')
        except Exception:
            messages.error(request, '⚠️ Formato de monto inválido.')
            return redirect('/metodos-pago/?tab=compras')

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

        if compra_obj:
            compra_obj.saldo = max(Decimal('0.00'), (compra_obj.saldo or Decimal('0.00')) - monto)
            compra_obj.save(update_fields=['saldo'])

        messages.success(request, f'✅ Registro de Pago #{pago.codigo_metodo} por ${monto:,.0f} guardado con éxito.')
        return redirect('/metodos-pago/?tab=compras')

    return redirect('/metodos-pago/?tab=compras')


@session_required
def eliminar_metodo_pago(request, pk):
    """Elimina un registro de método de pago de compras."""
    pago = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        codigo = pago.codigo_metodo
        monto = pago.valor
        pago.delete()
        messages.success(request, f'🗑️ Registro de Pago #{codigo} (${monto:,.0f}) eliminado.')
    return redirect('/metodos-pago/?tab=compras')


@session_required
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
                return redirect('/metodos-pago/?tab=compras')
        except Exception:
            messages.error(request, '⚠️ Formato de monto inválido.')
            return redirect('/metodos-pago/?tab=compras')

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
        return redirect('/metodos-pago/?tab=compras')

    return redirect('/metodos-pago/?tab=compras')
