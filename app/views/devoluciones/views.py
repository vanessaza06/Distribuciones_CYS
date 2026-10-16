from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.db.models import F, Sum, Q
from django.utils import timezone

from app.models import (
    Venta,
    DetalleVenta,
    Devolucion,
    DetalleDevolucion,
    DevolucionProveedores,
    Proveedor,
    Producto,
    Lote,
    Compra,
    DetalleCompra,
    Usuario,
    MetodoPago,
    PagoVenta
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y OPCIONES
# ═══════════════════════════════════════════════════════════════════════════════
MOTIVO_CHOICES = [
    ('defecto', 'Producto defectuoso o dañado'),
    ('vencido', 'Producto vencido / fecha próxima'),
    ('error_pedido', 'Error en el despacho / producto incorrecto'),
    ('insatisfaccion', 'Insatisfacción del cliente'),
    ('garantia', 'Aplicación de garantía'),
    ('otro', 'Otro motivo'),
]

TIPO_DEVOLUCION_CHOICES = [
    ('cambio', 'Cambio por otro producto'),
    ('nota_credito', 'Nota de crédito / saldo a favor'),
    ('reembolso', 'Reembolso de dinero'),
]

METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia bancaria'),
    ('nequi', 'Nequi / Daviplata'),
    ('tarjeta', 'Tarjeta débito / crédito'),
]


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO DEVOLUCIONES DE CLIENTES
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def lista_devoluciones(request):
    """Punto de entrada principal para devoluciones."""
    try:
        if request.GET.get('nuevo'):
            request.session['dev_paso'] = 1
            for key in list(request.session.keys()):
                if key.startswith('dev_'):
                    del request.session[key]
            request.session.modified = True

        return devoluciones_flujo(request)
    except Exception as e:
        messages.error(request, f'❌ Error al cargar devoluciones: {str(e)}')
        return redirect('principal')


@login_required
def buscar_venta_devolucion(request):
    """Búsqueda AJAX de ventas por código o cajero."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'ventas': []})

    ventas = Venta.objects.select_related('vendedor').all().order_by('-fecha')
    if q.isdigit():
        ventas = ventas.filter(pk=int(q))[:10]
    else:
        ventas = ventas.filter(
            Q(vendedor__nombre__icontains=q) |
            Q(vendedor__apellido__icontains=q) |
            Q(vendedor__documento__icontains=q) |
            Q(cliente__nombre__icontains=q)
        )[:10]

    return JsonResponse({'ventas': [
        {
            'id':      v.pk,
            'usuario': v.usuario.nombre if v.usuario else 'General',
            'fecha':   v.fecha.strftime('%d/%m/%Y %H:%M'),
            'total':   float(v.total_venta),
        }
        for v in ventas
    ]})


@login_required
def detalle_venta_devolucion(request, venta_id):
    """Detalle AJAX de una venta seleccionada."""
    venta = get_object_or_404(Venta.objects.prefetch_related('detalles__producto'), pk=venta_id)
    detalles = venta.detalles.select_related('producto').all()

    return JsonResponse({
        'venta_id': venta.pk,
        'usuario':  venta.usuario.nombre if venta.usuario else 'General',
        'fecha':    venta.fecha.strftime('%d/%m/%Y %H:%M'),
        'total':    float(venta.total_venta),
        'detalles': [
            {
                'detalle_id':  d.pk,
                'producto_id': d.producto.pk if d.producto else None,
                'producto':    d.producto.nombre if d.producto else '',
                'cantidad':    d.cantidad,
                'precio':      float(d.precio_unitario),
                'subtotal':    float(d.subtotal),
            }
            for d in detalles
        ],
    })


@login_required
def seleccionar_venta_devolucion(request, venta_id):
    """Selecciona la venta y avanza al paso 2 del flujo de devolución."""
    venta = get_object_or_404(Venta, pk=venta_id)
    request.session['dev_venta_id'] = venta.pk
    request.session['dev_paso'] = 2
    request.session.modified = True
    messages.success(request, f'✅ Venta #{venta.pk} seleccionada.')
    return redirect('lista_devoluciones')


@login_required
@transaction.atomic
def registrar_devolucion(request, venta_id):
    """Acceso directo para registrar devolución de una venta."""
    if request.method == 'POST':
        request.session['dev_venta_id'] = venta_id
        request.session['dev_paso'] = 6
        request.session.modified = True
        return devoluciones_flujo(request)
    return redirect('lista_devoluciones')


@login_required
def comprobante_devolucion(request, pk):
    """Muestra el comprobante individual de una devolución."""
    devolucion = get_object_or_404(
        Devolucion.objects.select_related('venta', 'usuario', 'detalle_venta__producto')
        .prefetch_related('detalles__producto'),
        pk=pk
    )
    return render(request, 'devoluciones/comprobante_devolucion.html', {
        'devolucion': devolucion,
        'breadcrumb_items': [
            {'nombre': 'Devoluciones', 'url': reverse('lista_devoluciones')},
            {'nombre': f'Comprobante #{devolucion.codigo_devolucion}', 'url': None},
        ],
    })


@login_required
def detalle_devolucion(request, pk):
    """Muestra el detalle completo de una devolución de cliente."""
    devolucion = get_object_or_404(
        Devolucion.objects.select_related(
            'venta',
            'usuario',
            'detalle_venta__producto',
        ).prefetch_related(
            'detalles__producto',
            'detalles__presentacion',
        ),
        pk=pk
    )
    return render(request, 'devoluciones/detalle_devolucion.html', {
        'devolucion': devolucion,
        'breadcrumb_items': [
            {'nombre': 'Devoluciones', 'url': reverse('lista_devoluciones')},
            {'nombre': devolucion.numero, 'url': None},
        ],
    })


@login_required
def ultima_devolucion(request):
    """Redirige al detalle de la devolución más reciente."""
    ultima = Devolucion.objects.order_by('-codigo_devolucion').first()
    if ultima:
        return redirect('detalle_devolucion', pk=ultima.pk)
    messages.info(request, 'Aún no hay devoluciones registradas.')
    return redirect('lista_devoluciones')


@login_required
def devoluciones_flujo(request):
    """Flujo paso a paso para el registro guiado de devoluciones."""
    paso = request.session.get('dev_paso', 1)
    venta_id = request.session.get('dev_venta_id')

    if paso > 1 and not venta_id:
        request.session['dev_paso'] = 1
        request.session.modified = True
        return redirect('lista_devoluciones')

    usuario_actual = None
    if request.user.is_authenticated:
        if isinstance(request.user, Usuario):
            usuario_actual = request.user
        else:
            ident = getattr(request.user, 'identificacion', None) or getattr(request.user, 'username', '')
            usuario_actual = (
                Usuario.objects.filter(documento=ident).first() or
                Usuario.objects.filter(correo=getattr(request.user, 'email', '')).first() or
                Usuario.objects.first()
            )

    # ── PASO 1: Seleccionar Venta ──
    if request.method == 'POST' and paso == 1:
        venta_id_post = request.POST.get('venta_id', '').strip()
        if venta_id_post:
            try:
                venta = Venta.objects.get(pk=int(venta_id_post))
                request.session['dev_venta_id'] = venta.pk
                request.session['dev_paso'] = 2
                request.session.modified = True
                messages.success(request, f'✅ Venta #{venta.pk} seleccionada.')
                return redirect('lista_devoluciones')
            except (Venta.DoesNotExist, ValueError):
                messages.error(request, '⚠️ Venta no válida. Intenta nuevamente.')
        else:
            messages.error(request, '⚠️ Debes seleccionar una venta.')

    # ── PASO 2: Seleccionar Productos y Cantidades ──
    elif request.method == 'POST' and paso == 2:
        action = request.POST.get('action', 'continuar')
        if action == 'atras':
            request.session['dev_paso'] = 1
            request.session.modified = True
            return redirect('lista_devoluciones')

        productos_ids = request.POST.getlist('producto_id')
        if not productos_ids:
            messages.error(request, '⚠️ Selecciona al menos un producto para devolver.')
            return redirect('lista_devoluciones')

        venta_actual = get_object_or_404(Venta, pk=venta_id)
        productos_con_cantidad = {}

        for detalle_id in productos_ids:
            try:
                det_id = int(detalle_id)
                cant = int(request.POST.get(f'cantidad_devolucion_{det_id}', '0'))
                detalle = venta_actual.detalles.get(pk=det_id)

                if cant <= 0 or cant > detalle.cantidad:
                    messages.error(request, f'⚠️ Cantidad inválida para {detalle.producto.nombre}.')
                    return redirect('lista_devoluciones')

                productos_con_cantidad[det_id] = cant
            except (ValueError, TypeError, DetalleVenta.DoesNotExist):
                messages.error(request, '⚠️ Error en los datos del producto seleccionado.')
                return redirect('lista_devoluciones')

        if productos_con_cantidad:
            request.session['dev_productos'] = productos_con_cantidad
            request.session['dev_paso'] = 3
            request.session.modified = True
            return redirect('lista_devoluciones')

    # ── PASO 3: Motivo y Observaciones ──
    elif request.method == 'POST' and paso == 3:
        if request.POST.get('action') == 'atras':
            request.session['dev_paso'] = 2
            request.session.modified = True
            return redirect('lista_devoluciones')

        motivo = request.POST.get('motivo', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        motivos_validos = [m[0] for m in MOTIVO_CHOICES]
        if motivo in motivos_validos:
            request.session['dev_motivo'] = motivo
            request.session['dev_observaciones'] = observaciones
            request.session['dev_paso'] = 4
            request.session.modified = True
            return redirect('lista_devoluciones')
        else:
            messages.error(request, '⚠️ Selecciona un motivo válido.')

    # ── PASO 4: Tipo de Solución / Devolución ──
    elif request.method == 'POST' and paso == 4:
        if request.POST.get('action') == 'atras':
            request.session['dev_paso'] = 3
            request.session.modified = True
            return redirect('lista_devoluciones')

        tipo = request.POST.get('tipo_reembolso', '').strip()
        tipos_validos = [t[0] for t in TIPO_DEVOLUCION_CHOICES]

        if tipo in tipos_validos:
            request.session['dev_tipo_reembolso'] = tipo
            request.session['dev_paso'] = 5 if tipo in ('cambio', 'reembolso') else 6
            request.session.modified = True
            return redirect('lista_devoluciones')
        else:
            messages.error(request, '⚠️ Selecciona una solución válida.')

    # ── PASO 5: Detalles Específicos (Cambio o Medio de Pago) ──
    elif request.method == 'POST' and paso == 5:
        if request.POST.get('action') == 'atras':
            request.session['dev_paso'] = 4
            request.session.modified = True
            return redirect('lista_devoluciones')

        tipo = request.session.get('dev_tipo_reembolso')

        if tipo == 'cambio':
            prod_cambio_id = request.POST.get('producto_cambio', '').strip()
            cant_cambio = request.POST.get('cantidad_cambio', '1').strip()
            if prod_cambio_id and cant_cambio.isdigit() and int(cant_cambio) > 0:
                request.session['dev_producto_cambio_id'] = int(prod_cambio_id)
                request.session['dev_cantidad_cambio'] = int(cant_cambio)
                request.session['dev_paso'] = 6
                request.session.modified = True
                return redirect('lista_devoluciones')
            messages.error(request, '⚠️ Selecciona un producto y cantidad válida para el cambio.')

        elif tipo == 'reembolso':
            metodo = request.POST.get('metodo_pago_devolucion', '').strip()
            if metodo in [m[0] for m in METODO_PAGO_CHOICES]:
                request.session['dev_metodo_devolucion'] = metodo
                request.session['dev_paso'] = 6
                request.session.modified = True
                return redirect('lista_devoluciones')
            messages.error(request, '⚠️ Selecciona un medio de reembolso válido.')

    # ── PASO 6: Confirmación y Guardado en Base de Datos ──
    elif request.method == 'POST' and paso == 6:
        if request.POST.get('action') == 'atras':
            tipo = request.session.get('dev_tipo_reembolso')
            request.session['dev_paso'] = 5 if tipo in ('cambio', 'reembolso') else 4
            request.session.modified = True
            return redirect('lista_devoluciones')

        try:
            with transaction.atomic():
                venta = Venta.objects.get(pk=venta_id)
                productos_data = request.session.get('dev_productos', {})
                motivo = request.session.get('dev_motivo')
                tipo_devolucion = request.session.get('dev_tipo_reembolso')
                observaciones = request.session.get('dev_observaciones', '')
                cantidad_cambio = request.session.get('dev_cantidad_cambio', 0)
                metodo_pago_dev = request.session.get('dev_metodo_devolucion', 'efectivo')

                detalles_dict = {int(k): v for k, v in productos_data.items()}
                detalles_venta = venta.detalles.filter(pk__in=detalles_dict.keys())

                if not detalles_venta.exists():
                    messages.error(request, '⚠️ No se encontraron los productos a devolver.')
                    return redirect('lista_devoluciones')

                total_devuelto = Decimal('0')
                for det in detalles_venta:
                    cant_dev = detalles_dict.get(det.pk, det.cantidad)
                    total_devuelto += Decimal(str(cant_dev)) * det.precio_unitario

                detalle_principal = detalles_venta.first()

                # Crear cabecera de Devolución
                devolucion = Devolucion.objects.create(
                    venta=venta,
                    detalle_venta=detalle_principal,
                    usuario=usuario_actual or venta.usuario,
                    motivo=motivo,
                    tipo_devolucion=tipo_devolucion,
                    observaciones=observaciones,
                    total_devuelto=total_devuelto,
                    tiene_comprobante=True,
                    estado='completada',
                    cantidad_cambio=cantidad_cambio,
                    metodo_pago_devolucion=metodo_pago_dev
                )

                # Crear detalles de la devolución y actualizar stock del producto
                hoy = timezone.now().date()
                for det_item in detalles_venta:
                    cant_a_devolver = detalles_dict.get(det_item.pk, det_item.cantidad)
                    
                    DetalleDevolucion.objects.create(
                        devolucion=devolucion,
                        producto=det_item.producto,
                        presentacion=det_item.presentacion,
                        lote=det_item.lote,
                        precio_unitario=det_item.precio_unitario,
                        cantidad=cant_a_devolver,
                        fecha_vencimiento=hoy,
                        descripcion=f"Devolución de venta #{venta.pk}",
                        observacion=motivo
                    )

                    # Restaurar stock: el stock vive en los lotes, no en Producto
                    lote = det_item.lote
                    if lote is None and det_item.producto_id:
                        lotes = Lote.objects.filter(producto_id=det_item.producto_id)
                        if det_item.presentacion_id:
                            lotes = lotes.filter(presentacion_id=det_item.presentacion_id)
                        lote = lotes.order_by('-fecha_registro').first()
                    if lote:
                        Lote.objects.filter(pk=lote.pk).update(
                            stock_actual=F('stock_actual') + cant_a_devolver
                        )

                # Limpiar variables de sesión del flujo
                for key in list(request.session.keys()):
                    if key.startswith('dev_'):
                        del request.session[key]
                request.session.modified = True

                messages.success(request, f'✅ Devolución #{devolucion.codigo_devolucion} registrada con éxito.')
                return redirect('comprobante_devolucion', pk=devolucion.pk)

        except Exception as e:
            messages.error(request, f'⚠️ Error al procesar la devolución: {str(e)}')
            return redirect('lista_devoluciones')

    # ── RENDERIZADO DEL TEMPLATE ──
    ventas = Venta.objects.select_related('vendedor').prefetch_related('detalles__producto').order_by('-fecha')[:50]
    devoluciones = Devolucion.objects.select_related('venta', 'usuario').order_by('-fecha')[:50]

    venta = None
    detalles_con_estado = []
    total_devolver = Decimal('0')

    if venta_id:
        try:
            venta = Venta.objects.prefetch_related('detalles__producto').get(pk=venta_id)
            detalles_venta = venta.detalles.select_related('producto').all()

            for det in detalles_venta:
                cant_devuelta = DetalleDevolucion.objects.filter(
                    devolucion__venta=venta,
                    producto=det.producto
                ).aggregate(tot=Sum('cantidad'))['tot'] or 0

                cant_pendiente = max(0, det.cantidad - cant_devuelta)
                detalles_con_estado.append({
                    'detalle': det,
                    'cantidad_devuelta': cant_devuelta,
                    'cantidad_pendiente': cant_pendiente,
                    'puede_devolver': cant_pendiente > 0,
                })

            productos_data = request.session.get('dev_productos', {})
            if productos_data:
                det_dict = {int(k): v for k, v in productos_data.items()}
                for d in detalles_venta.filter(pk__in=det_dict.keys()):
                    cant = det_dict.get(d.pk, d.cantidad)
                    total_devolver += Decimal(str(cant)) * d.precio_unitario

        except (Venta.DoesNotExist, ValueError):
            request.session['dev_paso'] = 1
            request.session.modified = True

    motivo_dict = dict(MOTIVO_CHOICES)
    tipo_dict = dict(TIPO_DEVOLUCION_CHOICES)

    context = {
        'ventas':                       ventas,
        'venta':                        venta,
        'detalles_con_estado':          detalles_con_estado,
        'devoluciones':                 devoluciones,
        'paso':                         paso,
        'venta_id':                     venta_id,
        'motivo_choices':               MOTIVO_CHOICES,
        'motivo_seleccionado':          motivo_dict.get(request.session.get('dev_motivo'), ''),
        'tipo_reembolso_seleccionado':  tipo_dict.get(request.session.get('dev_tipo_reembolso'), ''),
        'observaciones':                request.session.get('dev_observaciones', ''),
        'productos':                    Producto.objects.filter(activo=True).order_by('nombre') if paso >= 5 else [],
        'metodos_pago':                 METODO_PAGO_CHOICES,
        'total_devolver':               total_devolver,
        'tab_activo':                   request.GET.get('tab', 'cliente'),
        'todos_productos':              Producto.objects.filter(activo=True).annotate(
                                            stock_total_anotado=Sum('lotes__stock_actual')
                                        ).order_by('nombre'),
        # Devoluciones a Proveedor (usando app.models.DevolucionProveedores)
        'todos_proveedores':            Proveedor.objects.filter(estado='activo').order_by('nombre_empresa'),
        'devoluciones_proveedor':       DevolucionProveedores.objects.select_related('proveedor').order_by('-fecha')[:50],
        'prov_total':                   DevolucionProveedores.objects.count(),
        'prov_monto':                   sum((d.total_devuelto for d in DevolucionProveedores.objects.exclude(estado='rechazada')), Decimal('0')),
        'prov_monto_pendiente':         sum((d.total_devuelto for d in DevolucionProveedores.objects.filter(estado='pendiente')), Decimal('0')),
        'prov_pendientes':              DevolucionProveedores.objects.filter(estado='pendiente').count(),
        'breadcrumb_items': [
            {'nombre': 'Devoluciones', 'url': None},
        ],
    }

    return render(request, 'devoluciones/devoluciones.html', context)


def _cantidad_ya_devuelta(detalle_id):
    """Unidades de un detalle de compra ya reclamadas al proveedor (sin contar rechazadas)."""
    total = 0
    for d in DevolucionProveedores.objects.exclude(estado='rechazada'):
        extra = d.datos_extra
        if extra.get('detalle_compra_id') == detalle_id:
            total += int(extra.get('cantidad') or 0)
    return total


@login_required
def compras_proveedor_json(request, nit):
    """Compras de un proveedor con sus productos y la cantidad aún devolvible."""
    proveedor = Proveedor.objects.filter(pk=nit).first()
    if not proveedor:
        return JsonResponse({'compras': []})

    devueltas = {}
    for d in DevolucionProveedores.objects.filter(proveedor=proveedor).exclude(estado='rechazada'):
        extra = d.datos_extra
        did = extra.get('detalle_compra_id')
        if did:
            devueltas[did] = devueltas.get(did, 0) + int(extra.get('cantidad') or 0)

    compras = (Compra.objects.filter(proveedor=proveedor)
               .exclude(estado='cancelada')
               .prefetch_related('detalles__producto', 'detalles__lote')
               .order_by('-fecha'))
    data = []
    for c in compras:
        items = []
        for det in c.detalles.all():
            ya = devueltas.get(det.pk, 0)
            items.append({
                'detalle_id': det.pk,
                'producto': det.producto.nombre if det.producto else 'Producto eliminado',
                'comprada': det.cantidad,
                'devuelta': ya,
                'disponible': max(0, det.cantidad - ya),
                'precio': float(det.precio_unitario),
                'lote': det.lote.numero_lote if det.lote else '',
            })
        data.append({
            'id': c.pk,
            'fecha': c.fecha.strftime('%d/%m/%Y'),
            'estado': c.estado,
            'estado_label': c.get_estado_display(),
            'devolvible': c.estado == 'recibida',
            'valor': float(c.valor),
            'items': items,
        })
    return JsonResponse({'compras': data})


@login_required
@require_POST
def registrar_devolucion_proveedor(request):
    """Registra una devolución sobre un producto de una compra real al proveedor."""
    import json
    destino = f"{reverse('lista_devoluciones')}?tab=proveedor"

    def error(msg):
        messages.error(request, msg)
        return redirect(destino)

    proveedor = Proveedor.objects.filter(pk=request.POST.get('proveedor', '').strip()).first()
    if not proveedor:
        return error('⚠️ Debes seleccionar un proveedor válido.')

    detalle = (DetalleCompra.objects.select_related('compra', 'producto', 'lote')
               .filter(pk=request.POST.get('detalle_compra') or 0, compra__proveedor=proveedor).first())
    if not detalle:
        return error('⚠️ Selecciona una compra de este proveedor y el producto a devolver.')
    if detalle.compra.estado != 'recibida':
        return error(f'⚠️ La compra #{detalle.compra.pk} aún no fue recibida; solo se devuelve mercancía recibida.')

    try:
        cantidad = int(request.POST.get('cantidad', '0').strip())
        if cantidad <= 0:
            raise ValueError
    except ValueError:
        return error('⚠️ La cantidad a devolver debe ser un número entero mayor a cero.')

    disponible = detalle.cantidad - _cantidad_ya_devuelta(detalle.pk)
    if cantidad > disponible:
        return error(
            f'⚠️ De "{detalle.producto.nombre if detalle.producto else "este producto"}" en la compra '
            f'#{detalle.compra.pk} solo puedes devolver {max(disponible, 0)} unidades.'
        )

    producto = detalle.producto

    motivo = request.POST.get('motivo', 'otro').strip()
    if motivo not in dict(DevolucionProveedores.MOTIVO_CHOICES):
        motivo = 'otro'
    tipo_resolucion = request.POST.get('tipo_resolucion', 'nota_credito').strip()
    if tipo_resolucion not in dict(DevolucionProveedores.RESOLUCION_CHOICES):
        tipo_resolucion = 'nota_credito'

    precio_unitario = detalle.precio_unitario
    total = Decimal(cantidad) * precio_unitario

    metadata = {
        'total': float(total),
        'cantidad': cantidad,
        'precio_unitario': float(precio_unitario),
        'compra_id': detalle.compra.pk,
        'detalle_compra_id': detalle.pk,
        'lote_id': detalle.lote_id,
        'producto_id': producto.pk if producto else None,
        'producto_nombre': producto.nombre if producto else 'Mercancía general',
        'tipo_resolucion': tipo_resolucion,
        'obs': request.POST.get('observaciones', '').strip(),
    }

    dev_prov = DevolucionProveedores.objects.create(
        proveedor=proveedor,
        motivo=motivo,
        estado='pendiente',
        observaciones=json.dumps(metadata, ensure_ascii=False),
        fecha=timezone.now(),
    )

    messages.success(
        request,
        f'✅ Devolución {dev_prov.numero} registrada: {cantidad} × {metadata["producto_nombre"]} '
        f'de la compra #{detalle.compra.pk} (${total:,.0f}).'
    )
    return redirect(destino)


TRANSICIONES_DEV_PROVEEDOR = {
    'pendiente': ('aprobada', 'rechazada'),
    'aprobada': ('aplicada', 'rechazada'),
    'aplicada': (),
    'rechazada': (),
}

ACCIONES_DEV_PROVEEDOR = {
    'aprobada': ('Aprobar', 'bi-check-lg', 'ok',
                 'La devolución quedará aprobada y lista para aplicarse.'),
    'rechazada': ('Rechazar', 'bi-x-lg', 'no',
                  'La devolución se cerrará como rechazada. Las unidades quedan otra vez disponibles para devolver.'),
    'aplicada': ('Aplicar', 'bi-check-all', 'apply',
                 'Se descontará del inventario lo que exista de este producto y la devolución se cerrará.'),
}


@login_required
def detalle_devolucion_proveedor(request, pk):
    """Detalle de una devolución a proveedor. Con ?accion=… muestra la confirmación (sin JavaScript)."""
    dev = get_object_or_404(DevolucionProveedores.objects.select_related('proveedor'), pk=pk)
    extra = dev.datos_extra
    compra = Compra.objects.filter(pk=extra.get('compra_id')).first()

    accion = request.GET.get('accion', '')
    confirmar = None
    if accion in TRANSICIONES_DEV_PROVEEDOR.get(dev.estado, ()):
        etiqueta, icono, tono, texto = ACCIONES_DEV_PROVEEDOR[accion]
        confirmar = {'estado': accion, 'etiqueta': etiqueta, 'icono': icono, 'tono': tono, 'texto': texto}
    elif accion:
        messages.error(request, f'⚠️ No se puede pasar {dev.numero} de "{dev.estado}" a "{accion}".')

    acciones = [
        {'estado': e, 'etiqueta': ACCIONES_DEV_PROVEEDOR[e][0], 'icono': ACCIONES_DEV_PROVEEDOR[e][1],
         'tono': ACCIONES_DEV_PROVEEDOR[e][2]}
        for e in TRANSICIONES_DEV_PROVEEDOR.get(dev.estado, ())
    ]
    return render(request, 'devoluciones/detalle_devolucion_proveedor.html', {
        'dev': dev,
        'extra': extra,
        'compra': compra,
        'confirmar': confirmar,
        'acciones': acciones,
        'breadcrumb_items': [
            {'nombre': 'Devoluciones', 'url': f"{reverse('lista_devoluciones')}?tab=proveedor"},
            {'nombre': dev.numero, 'url': None},
        ],
    })


@login_required
@require_POST
def cambiar_estado_devolucion_proveedor(request, pk):
    """Cambia el estado de una devolución a proveedor respetando el flujo
    pendiente → aprobada → aplicada (o rechazada). Al aplicar descuenta el inventario."""
    import json
    destino = f"{reverse('lista_devoluciones')}?tab=proveedor"
    transiciones = TRANSICIONES_DEV_PROVEEDOR
    nuevo_estado = request.POST.get('nuevo_estado', '').strip()

    try:
        with transaction.atomic():
            dev_prov = get_object_or_404(DevolucionProveedores.objects.select_for_update(), pk=pk)

            if nuevo_estado not in transiciones.get(dev_prov.estado, ()):
                messages.error(
                    request,
                    f'⚠️ No se puede pasar {dev_prov.numero} de "{dev_prov.estado}" a "{nuevo_estado or "?"}".'
                )
                return redirect(destino)

            if nuevo_estado == 'aplicada':
                datos = dict(dev_prov.datos_extra)
                prod_id = datos.get('producto_id')
                pendiente = int(datos.get('cantidad') or 0)
                if prod_id and pendiente > 0 and not datos.get('stock_descontado'):
                    lote_id = datos.get('lote_id')
                    lotes = list(Lote.objects.select_for_update()
                                 .filter(producto_id=prod_id, stock_actual__gt=0)
                                 .order_by('fecha_registro'))
                    # El lote de la compra se descuenta primero
                    lotes.sort(key=lambda l: 0 if l.pk == lote_id else 1)
                    # Se descuenta solo lo que exista en inventario (nunca queda negativo)
                    quitado_total = 0
                    for lote in lotes:
                        if pendiente <= 0:
                            break
                        quitar = min(lote.stock_actual, pendiente)
                        Lote.objects.filter(pk=lote.pk).update(stock_actual=F('stock_actual') - quitar)
                        pendiente -= quitar
                        quitado_total += quitar
                    datos['unidades_descontadas'] = quitado_total
                    datos['stock_descontado'] = True
                    dev_prov.observaciones = json.dumps(datos, ensure_ascii=False)

            dev_prov.estado = nuevo_estado
            dev_prov.save()
    except Exception as e:
        messages.error(request, f'⚠️ No se pudo actualizar la devolución: {e}')
        return redirect(destino)

    extra = ''
    if nuevo_estado == 'aplicada':
        desc = dev_prov.datos_extra.get('unidades_descontadas')
        total_u = dev_prov.datos_extra.get('cantidad')
        if desc is not None and total_u is not None:
            extra = f' Inventario descontado: {desc} de {total_u} unidades.'
            if desc < total_u:
                extra += ' (El resto no estaba registrado en inventario.)'
    messages.success(request, f'✅ {dev_prov.numero} ahora está "{nuevo_estado.capitalize()}".{extra}')
    return redirect(f"{reverse('detalle_devolucion_proveedor', args=[dev_prov.pk])}")


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO MÉTODOS DE PAGO
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def metodos_pago_lista(request):
    """Lista de pagos recibidos en ventas."""
    pagos_qs = PagoVenta.objects.select_related('metodo', 'venta', 'venta__vendedor').order_by('-fecha_pago')

    q = request.GET.get('q', '').strip()
    if q:
        pagos_qs = pagos_qs.filter(
            Q(metodo__referencia__icontains=q) |
            Q(metodo__observacion__icontains=q) |
            Q(observaciones__icontains=q) |
            Q(venta__vendedor__nombre__icontains=q)
        ).distinct()

    total_monto = pagos_qs.aggregate(total=Sum('monto'))['total'] or Decimal('0')

    context = {
        'pagos': pagos_qs,
        'total_monto': total_monto,
        'q': q,
        'breadcrumb_items': [
            {'nombre': 'Ventas', 'url': reverse('principal')},
            {'nombre': 'Métodos de Pago', 'url': None},
        ],
    }
    return render(request, 'ventas/metodos_pago.html', context)
