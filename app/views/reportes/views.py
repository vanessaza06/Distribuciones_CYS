from decimal import Decimal

from django.contrib import messages
from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from app.models import (
    Compra,
    Devolucion,
    DetalleCompra,
    DetalleDevolucion,
    DetalleVenta,
    Producto,
    Proveedor,
    Venta,
)


def _productos_mas_vendidos(ventas):
    detalles = (
        DetalleVenta.objects.filter(venta__in=ventas)
        .annotate(
            nombre_producto=Coalesce(
                "producto__nombre",
                "presentacion__producto__nombre",
                Value("Producto sin nombre"),
            ),
            importe=ExpressionWrapper(
                F("cantidad") * F("precio_unitario"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .values("nombre_producto")
        .annotate(cantidad=Sum("cantidad"), subtotal=Sum("importe"))
        .order_by("-cantidad", "nombre_producto")
    )
    return [
        (
            detalle["nombre_producto"],
            {"cantidad": detalle["cantidad"], "subtotal": detalle["subtotal"] or Decimal("0")},
        )
        for detalle in detalles
    ]


def _filtrar_fechas(ventas, request):
    fecha_inicio_texto = request.GET.get("fecha_inicio", "").strip()
    fecha_fin_texto = request.GET.get("fecha_fin", "").strip()
    fecha_inicio = parse_date(fecha_inicio_texto) if fecha_inicio_texto else None
    fecha_fin = parse_date(fecha_fin_texto) if fecha_fin_texto else None

    if fecha_inicio_texto and fecha_inicio is None:
        messages.warning(request, "La fecha inicial no es válida.")
    if fecha_fin_texto and fecha_fin is None:
        messages.warning(request, "La fecha final no es válida.")
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        messages.warning(request, "La fecha inicial no puede ser posterior a la fecha final.")
        return ventas, fecha_inicio_texto, fecha_fin_texto

    if fecha_inicio:
        ventas = ventas.filter(fecha__date__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(fecha__date__lte=fecha_fin)
    return ventas, fecha_inicio_texto, fecha_fin_texto


def reportes(request):
    hoy = timezone.localdate()

    productos = list(
        Producto.objects.annotate(
            cantidad_disponible=Coalesce(
                Sum("lotes__stock_actual"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=0),
            )
        ).order_by("nombre")
    )
    total_registrados = len(productos)
    total_en_stock = sum(producto.cantidad_disponible > 10 for producto in productos)
    total_stock_bajo = sum(
        0 < producto.cantidad_disponible <= 10 for producto in productos
    )
    total_agotados = sum(producto.cantidad_disponible == 0 for producto in productos)

    entradas = (
        DetalleCompra.objects.filter(compra__estado="recibida")
        .select_related("compra", "producto")
        .order_by("-compra__fecha")
    )
    salidas = (
        DetalleVenta.objects.select_related(
            "venta", "venta__vendedor", "producto", "presentacion__producto"
        )
        .order_by("-venta__fecha")
    )

    proveedores = Proveedor.objects.filter(estado="activo").order_by("nombre_empresa")

    compras = (
        Compra.objects.exclude(estado="cancelada")
        .select_related("proveedor")
        .prefetch_related("detalles__producto")
        .order_by("-fecha")
    )
    resumen_compras = compras.aggregate(
        valor=Sum("valor"),
        ordenes=Count("codigo_compra"),
    )
    total_compras = resumen_compras["valor"] or Decimal("0")
    total_ordenes = resumen_compras["ordenes"] or 0

    ventas, fecha_inicio, fecha_fin = _filtrar_fechas(
        Venta.objects.all().order_by("-fecha"), request
    )
    ventas = ventas.prefetch_related(
        "detalles__producto",
        "detalles__presentacion__producto",
    )
    resumen_ventas = ventas.aggregate(
        total=Sum("total_venta"),
        clientes=Count("cliente_nombre", distinct=True),
    )
    total_ventas = resumen_ventas["total"] or Decimal("0")
    total_productos = (
        DetalleVenta.objects.filter(venta__in=ventas).aggregate(
            productos=Sum("cantidad")
        )["productos"]
        or 0
    )
    total_clientes = resumen_ventas["clientes"] or 0
    if ventas.filter(Q(cliente_nombre__isnull=True) | Q(cliente_nombre="")).exists():
        total_clientes += 1

    ventas_hoy = (
        Venta.objects.filter(fecha__date=hoy)
        .prefetch_related(
            "detalles__producto",
            "detalles__presentacion__producto",
        )
        .order_by("-fecha")
    )
    ingresos_hoy = ventas_hoy.aggregate(total=Sum("total_venta"))["total"] or Decimal("0")

    entradas_hoy = entradas.filter(compra__fecha__date=hoy)
    total_entradas_hoy = entradas_hoy.aggregate(total=Sum("cantidad"))["total"] or 0
    salidas_hoy = salidas.filter(venta__fecha__date=hoy)
    total_salidas_hoy = salidas_hoy.aggregate(total=Sum("cantidad"))["total"] or 0

    top_productos_hoy = _productos_mas_vendidos(
        Venta.objects.filter(fecha__date=hoy)
    )
    top_productos = _productos_mas_vendidos(ventas)

    devoluciones_qs = (
        Devolucion.objects.select_related(
            "venta",
            "detalle_venta__producto",
            "detalle_venta__presentacion__producto",
        )
        .prefetch_related(
            "detalles__producto",
            "detalles__presentacion__producto",
        )
        .order_by("-fecha")
    )
    devoluciones = []
    estados_aprobados = {"activo", "completada", "aprobada", "aprobado"}
    estados_revision = {"pendiente", "en_revision", "en revisión"}
    for devolucion in devoluciones_qs:
        nombres_productos = []
        for detalle in devolucion.detalles.all():
            producto = detalle.producto or (
                detalle.presentacion.producto if detalle.presentacion_id else None
            )
            if producto and producto.nombre not in nombres_productos:
                nombres_productos.append(producto.nombre)
        if not nombres_productos and devolucion.detalle_venta:
            detalle_venta = devolucion.detalle_venta
            producto = detalle_venta.producto or (
                detalle_venta.presentacion.producto
                if detalle_venta.presentacion_id
                else None
            )
            if producto:
                nombres_productos.append(producto.nombre)

        estado = devolucion.estado.lower()
        if estado in estados_aprobados:
            estado_reporte = "Aprobada"
        elif estado in estados_revision:
            estado_reporte = "En revisión"
        else:
            estado_reporte = "Rechazada"
        devoluciones.append(
            {
                "fecha": devolucion.fecha,
                "cliente": devolucion.venta.cliente_nombre or "Consumidor final",
                "producto": ", ".join(nombres_productos) or "—",
                "motivo": devolucion.get_motivo_display(),
                "valor": devolucion.total_devuelto,
                "estado": estado_reporte,
            }
        )

    total_devoluciones = (
        devoluciones_qs.aggregate(total=Sum("total_devuelto"))["total"]
        or Decimal("0")
    )
    cantidad_devoluciones = devoluciones_qs.count()
    cantidad_ventas = Venta.objects.count()
    tasa_devolucion = (
        f"{cantidad_devoluciones / cantidad_ventas * 100:.1f}%"
        if cantidad_ventas
        else "0%"
    )
    devoluciones_aprobadas = devoluciones_qs.filter(
        estado__in=estados_aprobados
    ).count()

    context = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ventas_count": ventas.count(),
        "hoy": hoy,
        "productos": productos,
        "total_registrados": total_registrados,
        "total_en_stock": total_en_stock,
        "total_stock_bajo": total_stock_bajo,
        "total_agotados": total_agotados,
        "entradas": entradas,
        "salidas": salidas,
        "proveedores": proveedores,
        "compras": compras,
        "total_compras": total_compras,
        "total_ordenes": total_ordenes,
        "ventas": ventas,
        "total_ventas": total_ventas,
        "total_productos": total_productos,
        "total_clientes": total_clientes,
        "ventas_hoy": ventas_hoy,
        "ingresos_hoy": ingresos_hoy,
        "entradas_hoy": entradas_hoy,
        "total_entradas_hoy": total_entradas_hoy,
        "salidas_hoy": salidas_hoy,
        "total_salidas_hoy": total_salidas_hoy,
        "top_productos_hoy": top_productos_hoy,
        "top_productos": top_productos,
        "devoluciones": devoluciones,
        "total_devoluciones": total_devoluciones,
        "cantidad_devoluciones": cantidad_devoluciones,
        "tasa_devolucion": tasa_devolucion,
        "devoluciones_aprobadas": devoluciones_aprobadas,
        "breadcrumb_items": [
            {"nombre": "Reportes", "url": reverse("reportes")},
        ],
    }
    return render(request, "reportes/reportes.html", context)