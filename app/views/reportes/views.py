import base64
import io
import os
from datetime import datetime
from decimal import Decimal

from django.conf import settings
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
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.worksheet.properties import PageSetupProperties
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models import (
    Compra,
    Devolucion,
    DevolucionProveedores,
    DetalleCompra,
    DetalleDevolucion,
    DetalleVenta,
    Producto,
    Proveedor,
    Venta,
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

# Estados de devolución (todo se compara en minúsculas)
ESTADOS_APROBADOS = {"activo", "completada", "aprobada", "aprobado"}
ESTADOS_REVISION = {"pendiente", "en_revision", "en revisión"}


def _estado_reporte(estado):
    """Traduce el estado guardado en BD al texto que muestra el reporte."""
    estado = (estado or "").strip().lower()
    if estado in ESTADOS_APROBADOS:
        return "Aprobada"
    if estado in ESTADOS_REVISION:
        return "En revisión"
    return "Rechazada"


def _fecha_local(valor):
    """Devuelve la fecha (date) local de un datetime o date."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.date()
    return valor


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


def _nombres_productos_devolucion(devolucion):
    """Nombres de los productos de una devolución (detalles o, si no hay, el detalle de venta)."""
    nombres = []
    for detalle in devolucion.detalles.all():
        producto = detalle.producto or (
            detalle.presentacion.producto if detalle.presentacion_id else None
        )
        if producto and producto.nombre not in nombres:
            nombres.append(producto.nombre)

    if not nombres and devolucion.detalle_venta:
        dv = devolucion.detalle_venta
        producto = dv.producto or (
            dv.presentacion.producto if dv.presentacion_id else None
        )
        if producto:
            nombres.append(producto.nombre)
    return nombres


def _nombres_productos_venta(venta):
    nombres = []
    for d in venta.detalles.all():
        producto = d.producto or (d.presentacion.producto if d.presentacion_id else None)
        if producto and producto.nombre not in nombres:
            nombres.append(producto.nombre)
    return ", ".join(nombres) or "—"


def _nombres_productos_compra(compra):
    nombres = []
    for d in compra.detalles.all():
        if d.producto and d.producto.nombre not in nombres:
            nombres.append(d.producto.nombre)
    return ", ".join(nombres) or "—"


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO DE DATOS (lo usan la pantalla y las exportaciones)
# ═══════════════════════════════════════════════════════════════════════════════

def _contexto_reportes(request):
    hoy = timezone.localdate()

    # ── Inventario ──
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

    # ── Proveedores y compras ──
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

    # ── Ventas (con filtro de fechas) ──
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

    # ── Resumen diario ──
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

    # ── Devoluciones de clientes ──
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

    # IDs de ventas del rango filtrado, para restar solo sus devoluciones
    ids_ventas_rango = set(ventas.values_list("pk", flat=True))

    devoluciones = []
    devoluciones_aprobadas = 0
    total_dev_hoy = Decimal("0")      # devoluciones aprobadas registradas hoy
    total_dev_rango = Decimal("0")    # devoluciones aprobadas de las ventas del rango

    for devolucion in devoluciones_qs:
        estado_reporte = _estado_reporte(devolucion.estado)
        valor = devolucion.total_devuelto or Decimal("0")

        if estado_reporte == "Aprobada":
            devoluciones_aprobadas += 1
            if _fecha_local(devolucion.fecha) == hoy:
                total_dev_hoy += valor
            if devolucion.venta_id in ids_ventas_rango:
                total_dev_rango += valor

        venta_dev = devolucion.venta
        cliente = (venta_dev.cliente_nombre if venta_dev else None) or "Consumidor final"

        devoluciones.append(
            {
                "fecha": devolucion.fecha,
                "cliente": cliente,
                "producto": ", ".join(_nombres_productos_devolucion(devolucion)) or "—",
                "motivo": devolucion.get_motivo_display(),
                "valor": valor,
                "estado": estado_reporte,
            }
        )

    total_devoluciones = (
        devoluciones_qs.aggregate(total=Sum("total_devuelto"))["total"]
        or Decimal("0")
    )
    cantidad_devoluciones = len(devoluciones)
    cantidad_ventas = Venta.objects.count()
    tasa_devolucion = (
        f"{cantidad_devoluciones / cantidad_ventas * 100:.1f}%"
        if cantidad_ventas
        else "0%"
    )

    # ── Valores netos (ventas menos devoluciones aprobadas) ──
    ingresos_hoy_neto = ingresos_hoy - total_dev_hoy
    total_ventas_neto = total_ventas - total_dev_rango

    # ── Devoluciones a proveedor ──
    devoluciones_proveedor = []
    total_dev_proveedor = Decimal("0")
    dev_prov_qs = (
        DevolucionProveedores.objects.select_related("proveedor").order_by("-fecha")
    )
    for dp in dev_prov_qs:
        extra = dp.datos_extra or {}
        try:
            valor_dp = Decimal(str(extra.get("total") or 0))
        except Exception:
            valor_dp = Decimal("0")

        if dp.estado != "rechazada":
            total_dev_proveedor += valor_dp

        devoluciones_proveedor.append(
            {
                "numero": getattr(dp, "numero", dp.pk),
                "fecha": dp.fecha,
                "proveedor": dp.proveedor.nombre_empresa if dp.proveedor_id else "—",
                "producto": extra.get("producto_nombre") or "—",
                "cantidad": extra.get("cantidad") or 0,
                "motivo": dp.get_motivo_display() if hasattr(dp, "get_motivo_display") else dp.motivo,
                "valor": valor_dp,
                "estado": dp.estado,
            }
        )
    cantidad_dev_proveedor = len(devoluciones_proveedor)

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "ventas_count": ventas.count(),
        "hoy": hoy,
        # Inventario
        "productos": productos,
        "total_registrados": total_registrados,
        "total_en_stock": total_en_stock,
        "total_stock_bajo": total_stock_bajo,
        "total_agotados": total_agotados,
        "entradas": entradas,
        "salidas": salidas,
        # Proveedores / compras
        "proveedores": proveedores,
        "compras": compras,
        "total_compras": total_compras,
        "total_ordenes": total_ordenes,
        # Ventas
        "ventas": ventas,
        "total_ventas": total_ventas,
        "total_productos": total_productos,
        "total_clientes": total_clientes,
        # Resumen diario
        "ventas_hoy": ventas_hoy,
        "ingresos_hoy": ingresos_hoy,
        "entradas_hoy": entradas_hoy,
        "total_entradas_hoy": total_entradas_hoy,
        "salidas_hoy": salidas_hoy,
        "total_salidas_hoy": total_salidas_hoy,
        "top_productos_hoy": top_productos_hoy,
        "top_productos": top_productos,
        # Devoluciones de clientes
        "devoluciones": devoluciones,
        "total_devoluciones": total_devoluciones,
        "cantidad_devoluciones": cantidad_devoluciones,
        "tasa_devolucion": tasa_devolucion,
        "devoluciones_aprobadas": devoluciones_aprobadas,
        # Valores netos
        "total_dev_hoy": total_dev_hoy,
        "total_dev_rango": total_dev_rango,
        "ingresos_hoy_neto": ingresos_hoy_neto,
        "total_ventas_neto": total_ventas_neto,
        # Devoluciones a proveedor
        "devoluciones_proveedor": devoluciones_proveedor,
        "total_dev_proveedor": total_dev_proveedor,
        "cantidad_dev_proveedor": cantidad_dev_proveedor,
        "breadcrumb_items": [
            {"nombre": "Reportes", "url": reverse("reportes")},
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VISTA PRINCIPAL (también atiende ?export=excel|pdf|imprimir&seccion=...)
# ═══════════════════════════════════════════════════════════════════════════════

def reportes(request):
    context = _contexto_reportes(request)

    tipo = request.GET.get("export")
    if tipo in ("excel", "pdf", "imprimir"):
        secciones = _secciones(context, request.GET.get("seccion"))
        if tipo == "excel":
            return _exportar_excel(context, secciones)
        if tipo == "pdf":
            return _exportar_pdf(context, secciones)
        return _exportar_imprimir(context, secciones)

    return render(request, "reportes/reportes.html", context)


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTIDAD VISUAL (misma que Marcas)
# ═══════════════════════════════════════════════════════════════════════════════

NAVY = "0B1B30"
GOLD = "C48F3C"
CREAM = "F0E7DA"
ZEBRA = "FAF5EA"
BORDE = "E3D3B5"
VERDE = "1E8449"
ROJO = "B03A2E"

XL_NAVY = "061B3A"
XL_GOLD = "E8A317"
XL_ZEBRA = "EDF0F5"
XL_BORDE = "AEB9CC"
XL_ROJO = "9B1C1C"
XL_AMBAR = "B7791F"
XL_FUENTE = "Calibri"

LOGO_ARCHIVO = "logo.20.png"
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


def _sello():
    return timezone.localtime().strftime("%Y%m%d_%H%M")


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIONES EXPORTABLES
# ═══════════════════════════════════════════════════════════════════════════════
# Tipos de columna:
#   txt   texto a la izquierda        txtb  texto en negrita a la izquierda
#   txtr  texto a la derecha          int   número entero centrado
#   money valor en pesos a la derecha fecha fecha dd/mm/aaaa centrada
#   ctr   texto centrado

def _moneda(valor):
    try:
        valor = Decimal(str(valor or 0))
    except Exception:
        valor = Decimal("0")
    return "$" + f"{valor:,.0f}".replace(",", ".")


def _fmt_fecha(valor):
    f = _fecha_local(valor)
    return f.strftime("%d/%m/%Y") if f else "—"


def _fmt(valor, tipo):
    if tipo == "money":
        return _moneda(valor)
    if tipo == "fecha":
        return _fmt_fecha(valor)
    if tipo == "int":
        try:
            return str(int(valor or 0))
        except Exception:
            return str(valor)
    return "—" if valor in (None, "") else str(valor)


def _alineacion(tipo):
    if tipo in ("txt", "txtb"):
        return "left"
    if tipo in ("money", "txtr"):
        return "right"
    return "center"


def _color_estado(texto):
    """Devuelve (color_excel_pdf, color_html) según el estado."""
    t = (texto or "").strip().lower()
    if t in ("agotado", "rechazada", "rechazado", "cancelada", "inactiva"):
        return XL_ROJO
    if t in ("stock bajo", "en revisión", "en revision", "pendiente"):
        return XL_AMBAR
    return XL_NAVY


def _sec(clave, titulo, hoja, encabezados, tipos, anchos, filas, col_estado=None, pie=""):
    return {
        "clave": clave, "titulo": titulo, "hoja": hoja,
        "encabezados": encabezados, "tipos": tipos, "anchos": anchos,
        "filas": filas, "col_estado": col_estado, "pie": pie,
    }


def _secciones(ctx, solo=None):
    """Arma todas las secciones del reporte a partir del contexto."""
    secciones = []

    # ── Resumen ──
    filas = [
        ("Ventas brutas (rango filtrado)", _moneda(ctx["total_ventas"])),
        ("Devoluciones aprobadas (rango)", _moneda(ctx["total_dev_rango"])),
        ("Ventas netas (rango)", _moneda(ctx["total_ventas_neto"])),
        ("Ingresos de hoy (brutos)", _moneda(ctx["ingresos_hoy"])),
        ("Devoluciones aprobadas de hoy", _moneda(ctx["total_dev_hoy"])),
        ("Ingresos netos de hoy", _moneda(ctx["ingresos_hoy_neto"])),
        ("Unidades vendidas (rango)", str(ctx["total_productos"])),
        ("Clientes atendidos (rango)", str(ctx["total_clientes"])),
        ("Total compras", _moneda(ctx["total_compras"])),
        ("Órdenes de compra", str(ctx["total_ordenes"])),
        ("Devoluciones a proveedor", _moneda(ctx["total_dev_proveedor"])),
        ("Tasa de devolución", ctx["tasa_devolucion"]),
    ]
    secciones.append(_sec(
        "resumen", "Resumen general", "Resumen",
        ["#", "Indicador", "Valor"], ["int", "txtb", "txtr"], [10, 52, 28],
        [[i, a, b] for i, (a, b) in enumerate(filas, start=1)],
    ))

    # ── Inventario ──
    filas = []
    for i, p in enumerate(ctx["productos"], start=1):
        cant = int(p.cantidad_disponible or 0)
        estado = "Agotado" if cant == 0 else ("Stock bajo" if cant <= 10 else "En stock")
        filas.append([i, p.nombre, cant, estado])
    secciones.append(_sec(
        "inventario", "Inventario", "Inventario",
        ["#", "Producto", "Stock", "Estado"], ["int", "txtb", "int", "ctr"],
        [10, 50, 16, 20], filas, col_estado=3,
        pie=(f"Registrados: {ctx['total_registrados']}   ·   En stock: {ctx['total_en_stock']}"
             f"   ·   Stock bajo: {ctx['total_stock_bajo']}   ·   Agotados: {ctx['total_agotados']}"),
    ))

    # ── Ventas ──
    filas = [
        [v.pk, v.fecha, v.cliente_nombre or "Consumidor final",
         _nombres_productos_venta(v), v.total_venta or Decimal("0")]
        for v in ctx["ventas"]
    ]
    secciones.append(_sec(
        "ventas", "Ventas", "Ventas",
        ["#", "Fecha", "Cliente", "Productos", "Total"],
        ["int", "fecha", "txtb", "txt", "money"],
        [10, 16, 30, 50, 18], filas,
        pie=(f"Ventas: {ctx['ventas_count']}   ·   Total: {_moneda(ctx['total_ventas'])}"
             f"   ·   Neto: {_moneda(ctx['total_ventas_neto'])}"),
    ))

    # ── Productos más vendidos ──
    filas = [
        [i, nombre, d["cantidad"], d["subtotal"]]
        for i, (nombre, d) in enumerate(ctx["top_productos"], start=1)
    ]
    secciones.append(_sec(
        "top", "Productos más vendidos", "Más vendidos",
        ["#", "Producto", "Unidades", "Subtotal"], ["int", "txtb", "int", "money"],
        [10, 50, 16, 20], filas,
    ))

    # ── Compras ──
    filas = [
        [c.codigo_compra, c.fecha,
         c.proveedor.nombre_empresa if c.proveedor_id else "—",
         _nombres_productos_compra(c), c.valor or Decimal("0"),
         str(c.estado or "").capitalize()]
        for c in ctx["compras"]
    ]
    secciones.append(_sec(
        "compras", "Compras", "Compras",
        ["Código", "Fecha", "Proveedor", "Productos", "Valor", "Estado"],
        ["int", "fecha", "txtb", "txt", "money", "ctr"],
        [12, 16, 30, 44, 18, 16], filas, col_estado=5,
        pie=f"Órdenes: {ctx['total_ordenes']}   ·   Total: {_moneda(ctx['total_compras'])}",
    ))

    # ── Devoluciones de clientes ──
    filas = [
        [d["fecha"], d["cliente"], d["producto"], d["motivo"], d["valor"], d["estado"]]
        for d in ctx["devoluciones"]
    ]
    secciones.append(_sec(
        "devoluciones", "Devoluciones de clientes", "Devoluciones",
        ["Fecha", "Cliente", "Producto", "Motivo", "Valor", "Estado"],
        ["fecha", "txtb", "txt", "txt", "money", "ctr"],
        [16, 28, 40, 28, 18, 16], filas, col_estado=5,
        pie=(f"Devoluciones: {ctx['cantidad_devoluciones']}   ·   Aprobadas: {ctx['devoluciones_aprobadas']}"
             f"   ·   Total: {_moneda(ctx['total_devoluciones'])}   ·   Tasa: {ctx['tasa_devolucion']}"),
    ))

    # ── Devoluciones a proveedor ──
    filas = [
        [d["numero"], d["fecha"], d["proveedor"], d["producto"], d["cantidad"],
         d["motivo"], d["valor"], str(d["estado"] or "").capitalize()]
        for d in ctx["devoluciones_proveedor"]
    ]
    secciones.append(_sec(
        "dev_proveedor", "Devoluciones a proveedor", "Dev. proveedor",
        ["N°", "Fecha", "Proveedor", "Producto", "Cant.", "Motivo", "Valor", "Estado"],
        ["int", "fecha", "txtb", "txt", "int", "txt", "money", "ctr"],
        [8, 14, 26, 32, 10, 24, 16, 14], filas, col_estado=7,
        pie=(f"Devoluciones: {ctx['cantidad_dev_proveedor']}   ·   "
             f"Total (sin rechazadas): {_moneda(ctx['total_dev_proveedor'])}"),
    ))

    if solo:
        elegidas = [s for s in secciones if s["clave"] == solo]
        if elegidas:
            return elegidas
    return secciones


def _titulo_reporte(secciones):
    return f"Reporte de {secciones[0]['titulo']}" if len(secciones) == 1 else "Reporte General"


def _texto_filtros(ctx):
    partes = []
    if ctx["fecha_inicio"]:
        partes.append(f"Desde: {ctx['fecha_inicio']}")
    if ctx["fecha_fin"]:
        partes.append(f"Hasta: {ctx['fecha_fin']}")
    if not partes:
        return "Sin filtro de fechas"
    return "Ventas filtradas · " + " | ".join(partes)


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEL (misma estética que Marcas: una hoja por sección)
# ═══════════════════════════════════════════════════════════════════════════════

def _xl_fill(hex_):
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def _poner_imagen(ws, datos_png, col, fila, ancho, alto, off_x=0, off_y=0):
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


def _hoja_excel(ws, sec, titulo_banner, filtros_txt):
    encabezados = sec["encabezados"]
    tipos = sec["tipos"]
    filas = sec["filas"]
    anchos = sec["anchos"]
    n = len(encabezados)
    ultima = get_column_letter(n)

    ws.title = sec["hoja"][:31]
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False
    for idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = ancho

    # ---------- Banner ----------
    for r, h in {1: 30, 2: 34, 3: 30}.items():
        ws.row_dimensions[r].height = h

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

    lado_oro = Side(style="medium", color=XL_GOLD)
    for r in (1, 2, 3):
        ws.cell(r, 3).border = Border(left=lado_oro)

    ws.merge_cells(f"C1:{ultima}2")
    ws["C1"] = titulo_banner
    ws["C1"].font = Font(name=XL_FUENTE, size=28, bold=True, color=XL_NAVY)
    ws["C1"].alignment = Alignment(horizontal="left", vertical="center", indent=2)
    ws.merge_cells(f"C3:{ultima}3")
    ws["C3"] = sec["titulo"] if titulo_banner == "Reporte General" else "Calidad que llega más lejos"
    ws["C3"].font = Font(name=XL_FUENTE, size=16, italic=True, color=XL_NAVY)
    ws["C3"].alignment = Alignment(horizontal="left", vertical="top", indent=2)

    ws.row_dimensions[4].height = 10
    barra = _barra_dorada(140, 5)
    if barra:
        _poner_imagen(ws, barra, 2, 3, 140, 5, off_x=22, off_y=2)
    ws.row_dimensions[5].height = 16

    # ---------- Encabezado de tabla ----------
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
        for i, valor in enumerate(fila, start=1):
            tipo = tipos[i - 1]
            if tipo == "money":
                try:
                    valor = float(valor or 0)
                except Exception:
                    valor = 0.0
            elif tipo == "int":
                try:
                    valor = int(valor or 0)
                except Exception:
                    pass
            else:
                valor = _fmt(valor, tipo)

            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            negrita = tipo == "txtb"
            color = "1F2937"
            if sec["col_estado"] == i - 1:
                negrita = True
                color = _color_estado(str(valor))
                c.value = "●  " + str(valor)
            c.font = Font(name=XL_FUENTE, size=13, color=color, bold=negrita)
            alin = _alineacion(tipo)
            c.alignment = Alignment(
                horizontal=alin, vertical="center",
                indent=1 if alin != "center" else 0,
                wrap_text=(tipo == "txt"),
            )
            if tipo == "money":
                c.number_format = '"$"#,##0'

    if not filas:
        r = fila_enc + 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=n)
        c = ws.cell(r, 1, "No hay registros para mostrar.")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.font = Font(name=XL_FUENTE, size=13, italic=True, color=XL_NAVY)
        ws.row_dimensions[r].height = 26

    # ---------- Pie ----------
    r = fila_enc + max(len(filas), 1) + 1
    ws.row_dimensions[r].height = 8
    textos = []
    if sec["pie"]:
        textos.append(sec["pie"])
    textos.append(f"{filtros_txt}   ·   Generado el {timezone.localtime():%d/%m/%Y %H:%M}")
    for j, texto in enumerate(textos, start=1):
        rr = r + j
        ws.row_dimensions[rr].height = 22
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=n)
        p = ws.cell(rr, 1, texto)
        es_ultimo = j == len(textos)
        p.font = Font(name=XL_FUENTE, size=11, bold=not es_ultimo, italic=es_ultimo, color=XL_NAVY)
        p.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    # ---------- Extras ----------
    if filas:
        ws.auto_filter.ref = f"A{fila_enc}:{ultima}{fila_enc + len(filas)}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_title_rows = f"{fila_enc}:{fila_enc}"
    ws.print_options.horizontalCentered = True


def _exportar_excel(ctx, secciones):
    wb = Workbook()
    titulo = _titulo_reporte(secciones)
    filtros_txt = _texto_filtros(ctx)

    for idx, sec in enumerate(secciones):
        ws = wb.active if idx == 0 else wb.create_sheet()
        _hoja_excel(ws, sec, titulo, filtros_txt)

    buffer = io.BytesIO()
    wb.save(buffer)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    nombre = secciones[0]["clave"] if len(secciones) == 1 else "general"
    resp["Content-Disposition"] = f'attachment; filename="reporte_{nombre}_{_sello()}.xlsx"'
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# PDF (mismo diseño: banner blanco + tablas azul marino con esquinas redondeadas)
# ═══════════════════════════════════════════════════════════════════════════════

class _BannerPDF(Flowable):
    """Banner: logo circular | divisor dorado | título | lema | barrita dorada."""

    def __init__(self, ancho, titulo, logo_bytes=None):
        super().__init__()
        self.width = ancho
        self.height = 96
        self.titulo = titulo
        self.logo_bytes = logo_bytes

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        navy = colors.HexColor("#" + XL_NAVY)
        oro = colors.HexColor("#" + XL_GOLD)

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

        x_div = x_logo + diam + 26
        c.setStrokeColor(oro)
        c.setLineWidth(2.5)
        c.line(x_div, 8, x_div, self.height - 8)

        x_txt = x_div + 26
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(x_txt, self.height - 46, self.titulo)

        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, "Calidad que llega más lejos")

        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


def _exportar_pdf(ctx, secciones):
    c_navy = colors.HexColor("#" + XL_NAVY)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen
    titulo = _titulo_reporte(secciones)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title=f"{titulo} — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=10, leading=12.5, textColor=c_texto)
    st_bold = ParagraphStyle("bold", parent=st_base, fontName="Helvetica-Bold",
                             textColor=c_navy, leftIndent=6)
    st_izq = ParagraphStyle("izq", parent=st_base, leftIndent=6)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_der = ParagraphStyle("der", parent=st_base, alignment=TA_RIGHT, rightIndent=6)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=11.5,
                             textColor=colors.white, alignment=TA_CENTER, leading=14)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10)
    st_sec = ParagraphStyle("sec", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=15, leading=18)

    estilo_tipo = {
        "txt": st_izq, "txtb": st_bold, "txtr": st_der,
        "money": st_der, "int": st_centro, "fecha": st_centro, "ctr": st_centro,
    }

    elementos = [_BannerPDF(ancho_util, titulo, _logo_png(300)), Spacer(1, 10)]

    for sec in secciones:
        tipos = sec["tipos"]
        n = len(sec["encabezados"])

        elementos.append(Paragraph(escape(sec["titulo"]), st_sec))
        elementos.append(Spacer(1, 6))

        data = [[Paragraph(escape(h), st_head) for h in sec["encabezados"]]]
        for f in sec["filas"]:
            fila = []
            for i, valor in enumerate(f):
                texto = escape(_fmt(valor, tipos[i]))
                if sec["col_estado"] == i:
                    color = "#" + _color_estado(str(valor))
                    texto = (
                        f'<font color="{color}"><font name="ZapfDingbats" size="8">l</font>'
                        f'&nbsp;&nbsp;{texto}</font>'
                    )
                    fila.append(Paragraph(texto, st_estado))
                else:
                    fila.append(Paragraph(texto, estilo_tipo[tipos[i]]))
            data.append(fila)

        if not sec["filas"]:
            data.append([Paragraph("No hay registros para mostrar.", st_centro)] + [""] * (n - 1))

        escala = ancho_util / sum(sec["anchos"])
        tabla = Table(data, colWidths=[a * escala for a in sec["anchos"]], repeatRows=1)
        estilo = [
            ("BACKGROUND", (0, 0), (-1, 0), c_navy),
            ("LINEBEFORE", (1, 0), (-1, 0), 0.6, colors.HexColor("#3B4F6B")),
            ("TOPPADDING", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_zebra]),
            ("LINEBEFORE", (1, 1), (-1, -1), 0.6, c_borde),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 1, c_navy),
            ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ]
        if not sec["filas"]:
            estilo.append(("SPAN", (0, 1), (-1, 1)))
        tabla.setStyle(TableStyle(estilo))
        elementos.append(tabla)

        if sec["pie"]:
            elementos += [Spacer(1, 8), Paragraph(escape(sec["pie"]).replace("   ", " &nbsp; "), st_tot)]
        elementos.append(Spacer(1, 22))

    elementos.append(Paragraph(
        escape(_texto_filtros(ctx)) + " &nbsp;·&nbsp; Generado el "
        + timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        st_meta))

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(margen, 20, "CYS Ltda · Distribuciones")
        canvas.drawRightString(pagina[0] - margen, 20, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)

    resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    nombre = secciones[0]["clave"] if len(secciones) == 1 else "general"
    resp["Content-Disposition"] = f'attachment; filename="reporte_{nombre}_{_sello()}.pdf"'
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# IMPRIMIR
# ═══════════════════════════════════════════════════════════════════════════════

def _exportar_imprimir(ctx, secciones):
    titulo = _titulo_reporte(secciones)

    logo = _logo_png(300)
    logo_html = ""
    if logo:
        logo_html = (f"<img class='logo' src='data:image/png;base64,"
                     f"{base64.b64encode(logo).decode()}' alt='CYS Ltda'>")

    bloques = []
    for sec in secciones:
        tipos = sec["tipos"]
        encab = "".join(f"<th>{escape(h)}</th>" for h in sec["encabezados"])

        filas_html = ""
        for f in sec["filas"]:
            celdas = ""
            for i, valor in enumerate(f):
                texto = escape(_fmt(valor, tipos[i]))
                clases = [_alineacion(tipos[i])]
                if tipos[i] == "txtb":
                    clases.append("marca")
                estilo = ""
                if sec["col_estado"] == i:
                    estilo = f" style='color:#{_color_estado(str(valor))};font-weight:bold'"
                celdas += f"<td class='{' '.join(clases)}'{estilo}>{texto}</td>"
            filas_html += f"<tr>{celdas}</tr>"
        if not filas_html:
            filas_html = (f"<tr><td colspan='{len(sec['encabezados'])}' class='center'>"
                          "No hay registros para mostrar.</td></tr>")

        pie = f"<div class='total'>{escape(sec['pie'])}</div>" if sec["pie"] else ""
        bloques.append(
            f"<h2>{escape(sec['titulo'])}</h2>"
            f"<table><thead><tr>{encab}</tr></thead><tbody>{filas_html}</tbody></table>{pie}"
        )

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>{escape(titulo)} — CYS Ltda</title>
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
  h2 {{ color: #{NAVY}; font-size: 16px; margin: 22px 0 8px; border-left: 4px solid #{GOLD}; padding-left: 8px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #{NAVY}; color: #{GOLD}; padding: 8px 10px; border-bottom: 3px solid #{GOLD}; text-align: center; }}
  td {{ padding: 7px 10px; border: 1px solid #{BORDE}; }}
  td.center {{ text-align: center; }}
  td.left {{ text-align: left; }}
  td.right {{ text-align: right; }}
  td.marca {{ font-weight: bold; color: #{NAVY}; }}
  tr:nth-child(even) td {{ background: #{ZEBRA}; }}
  .total {{ margin-top: 6px; background: #{CREAM}; border-top: 3px solid #{GOLD}; padding: 8px 14px;
           text-align: right; font-weight: bold; color: #{NAVY}; font-size: 12px; }}
  .pie {{ margin-top: 14px; font-size: 10px; color: #888; text-align: center; }}
</style></head>
<body>
  <div class="banner">
    {logo_html}
    <div><h1>CYS LTDA · DISTRIBUCIONES</h1><p>{escape(titulo)}</p></div>
  </div>
  <div class="meta">{escape(_texto_filtros(ctx))} &nbsp;·&nbsp; Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</div>
  {''.join(bloques)}
  <div class="pie">CYS Ltda · Distribuciones</div>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)