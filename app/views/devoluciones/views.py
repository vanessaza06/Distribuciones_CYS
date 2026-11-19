import base64
import io
import os
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import F, Sum, Q
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
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.validators import entero_estricto, limpiar_texto, validar_texto_libre
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


def _pendiente_detalle(venta, detalle):
    """Unidades de un renglón de venta que aún se pueden devolver."""
    ya = DetalleDevolucion.objects.filter(
        devolucion__venta=venta, producto=detalle.producto
    ).aggregate(t=Sum('cantidad'))['t'] or 0
    return max(0, detalle.cantidad - ya)


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTIDAD VISUAL PARA EXPORTES (mismo diseño que el reporte de Marcas)
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
XL_FUENTE = "Calibri"

LOGO_ARCHIVO = "logo.20.png"
_LOGO_CACHE = {}


def _ruta_logo():
    """Busca el logo en las carpetas static. Devuelve la ruta o None."""
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
    """Logo redondo, redimensionado, con esquinas transparentes. Bytes PNG o None."""
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
    return timezone.localtime().strftime('%Y%m%d_%H%M')


# ═══════════════════════════════════════════════════════════════════════════════
# DATOS DE EXPORTACIÓN (clientes / proveedores) — un solo filtro para todo
# ═══════════════════════════════════════════════════════════════════════════════
ESTADOS_OK = ('completada', 'aprobada', 'aplicada')


def _fecha_txt(valor):
    if not valor:
        return "—"
    try:
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
    except Exception:
        pass
    return valor.strftime("%d/%m/%Y %H:%M")


def _estado_txt(estado):
    return (estado or "—").replace("_", " ").capitalize()


def _filtros_export(request):
    return {
        'q': request.GET.get('q', '').strip(),
        'estado': request.GET.get('estado', 'todos').strip(),
        'desde': request.GET.get('desde', '').strip(),
        'hasta': request.GET.get('hasta', '').strip(),
    }


def _aplicar_fechas(qs, filtros, campo='fecha'):
    f_desde = parse_date(filtros['desde']) if filtros['desde'] else None
    f_hasta = parse_date(filtros['hasta']) if filtros['hasta'] else None
    if f_desde:
        qs = qs.filter(**{f'{campo}__date__gte': f_desde})
    if f_hasta:
        qs = qs.filter(**{f'{campo}__date__lte': f_hasta})
    return qs


def _datos_cliente(request):
    filtros = _filtros_export(request)
    qs = Devolucion.objects.select_related('venta', 'usuario').order_by('-fecha')

    q = filtros['q']
    if q:
        cond = (Q(venta__cliente_nombre__icontains=q) |
                Q(usuario__nombre__icontains=q) |
                Q(motivo__icontains=q))
        if q.lstrip('#').isdigit():
            cond |= Q(venta__pk=int(q.lstrip('#')))
        qs = qs.filter(cond)
    if filtros['estado'] and filtros['estado'] != 'todos':
        qs = qs.filter(estado=filtros['estado'])
    qs = _aplicar_fechas(qs, filtros)

    motivos = dict(MOTIVO_CHOICES)
    tipos = dict(TIPO_DEVOLUCION_CHOICES)
    filas = []
    for d in qs:
        venta = d.venta
        cliente = (getattr(venta, 'cliente_nombre', '') or '').strip() or 'General'
        filas.append([
            d.codigo_devolucion,
            f"#{venta.pk}" if venta else "—",
            _fecha_txt(d.fecha),
            cliente,
            motivos.get(d.motivo, d.motivo or "—"),
            tipos.get(d.tipo_devolucion, d.tipo_devolucion or "—"),
            float(d.total_devuelto or 0),
            _estado_txt(d.estado),
        ])
    return {
        'titulo': 'Reporte de Devoluciones de Clientes',
        'archivo': 'devoluciones_clientes',
        'unidad': 'devoluciones',
        'encabezados': ['#', 'Venta', 'Fecha', 'Cliente', 'Motivo', 'Solución', 'Total devuelto', 'Estado'],
        'anchos_xl': [10, 12, 20, 28, 38, 32, 20, 16],
        'anchos_pdf': [40, 50, 85, 120, 170, 150, 85, 75],
        'izquierda': (3, 4, 5),
        'negrita': 3,
        'idx_moneda': 6,
        'idx_estado': 7,
        'filas': filas,
        'filtros': filtros,
    }


def _datos_proveedor(request):
    filtros = _filtros_export(request)
    qs = DevolucionProveedores.objects.select_related('proveedor').order_by('-fecha')

    q = filtros['q']
    if q:
        qs = qs.filter(
            Q(proveedor__nombre_empresa__icontains=q) |
            Q(observaciones__icontains=q) |
            Q(motivo__icontains=q)
        )
    if filtros['estado'] and filtros['estado'] != 'todos':
        qs = qs.filter(estado=filtros['estado'])
    qs = _aplicar_fechas(qs, filtros)

    motivos = dict(DevolucionProveedores.MOTIVO_CHOICES)
    filas = []
    for d in qs:
        extra = d.datos_extra or {}
        filas.append([
            d.numero,
            d.proveedor.nombre_empresa if d.proveedor else "—",
            _fecha_txt(d.fecha),
            extra.get('producto_nombre') or "—",
            int(extra.get('cantidad') or 0),
            motivos.get(d.motivo, d.motivo or "—"),
            float(d.total_devuelto or 0),
            _estado_txt(d.estado),
        ])
    return {
        'titulo': 'Reporte de Devoluciones a Proveedores',
        'archivo': 'devoluciones_proveedores',
        'unidad': 'devoluciones',
        'encabezados': ['N°', 'Proveedor', 'Fecha', 'Producto', 'Cantidad', 'Motivo', 'Total devuelto', 'Estado'],
        'anchos_xl': [16, 32, 20, 32, 12, 32, 20, 16],
        'anchos_pdf': [60, 125, 85, 130, 55, 120, 85, 75],
        'izquierda': (1, 3, 5),
        'negrita': 1,
        'idx_moneda': 6,
        'idx_estado': 7,
        'filas': filas,
        'filtros': filtros,
    }


def _datos_export(request):
    if request.GET.get('tab', 'cliente') == 'proveedor':
        return _datos_proveedor(request)
    return _datos_cliente(request)


def _texto_filtros(f):
    partes = []
    if f["q"]:
        partes.append(f"Búsqueda: {f['q']}")
    if f["estado"] and f["estado"] != "todos":
        partes.append(f"Estado: {_estado_txt(f['estado'])}")
    if f["desde"]:
        partes.append(f"Desde: {f['desde']}")
    if f["hasta"]:
        partes.append(f"Hasta: {f['hasta']}")
    return " | ".join(partes) if partes else "Sin filtros"


def _resumen(datos):
    filas = datos['filas']
    im, ie = datos['idx_moneda'], datos['idx_estado']
    monto = sum(f[im] for f in filas if f[ie].lower() != 'rechazada')
    ok = sum(1 for f in filas if f[ie].lower() in ESTADOS_OK)
    rech = sum(1 for f in filas if f[ie].lower() == 'rechazada')
    return len(filas), ok, rech, monto


def _moneda(v):
    return f"${v:,.0f}"


def _texto_resumen(datos):
    total, ok, rech, monto = _resumen(datos)
    return (f"Total: {total} devoluciones   ·   Completadas/Aplicadas: {ok}   ·   "
            f"Rechazadas: {rech}   ·   Monto devuelto: {_moneda(monto)}")


def _valor_celda(datos, i, valor):
    return _moneda(valor) if i == datos['idx_moneda'] else valor


def _es_rojo(estado):
    return estado.lower() == 'rechazada'


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEL
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


def exportar_devoluciones_excel(request):
    datos = _datos_export(request)
    filas = datos['filas']
    encabezados = datos['encabezados']
    n = len(encabezados)
    ultima = get_column_letter(n)
    im, ie = datos['idx_moneda'], datos['idx_estado']

    wb = Workbook()
    ws = wb.active
    ws.title = "Devoluciones"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    anchos = datos['anchos_xl']
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
    ws["C1"] = datos['titulo']
    ws["C1"].font = Font(name=XL_FUENTE, size=28, bold=True, color=XL_NAVY)
    ws["C1"].alignment = Alignment(horizontal="left", vertical="center", indent=2)
    ws.merge_cells(f"C3:{ultima}3")
    ws["C3"] = "Calidad que llega más lejos"
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
    izquierda_idx = datos['izquierda']
    for k, fila in enumerate(filas):
        r = fila_enc + 1 + k
        ws.row_dimensions[r].height = 26
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila):
            col = i + 1
            if i == ie:
                valor = "●  " + valor
            c = ws.cell(r, col, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if col == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == datos['negrita']))
            izq = i in izquierda_idx
            c.alignment = Alignment(
                horizontal="left" if izq else "center",
                vertical="center",
                indent=1 if izq else 0,
                wrap_text=izq,
            )
            if i == im:
                c.number_format = '"$"#,##0'
        e = ws.cell(r, ie + 1)
        e.font = Font(name=XL_FUENTE, size=13, bold=True,
                      color=XL_ROJO if _es_rojo(fila[ie]) else XL_NAVY)

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        _texto_resumen(datos),
        f"{_texto_filtros(datos['filtros'])}   ·   Generado el {timezone.localtime():%d/%m/%Y %H:%M}",
    ]
    for j, texto in enumerate(textos_pie, start=1):
        rr = r + j
        ws.row_dimensions[rr].height = 22
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=n)
        p = ws.cell(rr, 1, texto)
        p.font = Font(name=XL_FUENTE, size=11, bold=(j == 1), italic=(j == 2), color=XL_NAVY)
        p.alignment = Alignment(horizontal="left", vertical="center", indent=1)

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
    resp["Content-Disposition"] = f'attachment; filename="{datos["archivo"]}_{_sello()}.xlsx"'
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# PDF
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
        c.setFont("Helvetica-Bold", 28)
        c.drawString(x_txt, self.height - 46, self.titulo)

        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, "Calidad que llega más lejos")

        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


def exportar_devoluciones_pdf(request):
    datos = _datos_export(request)
    filas = datos['filas']
    encabezados = datos['encabezados']
    im, ie = datos['idx_moneda'], datos['idx_estado']
    izquierda_idx = datos['izquierda']

    c_navy = colors.HexColor("#" + XL_NAVY)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_rojo = "#" + XL_ROJO
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title=f"{datos['titulo']} — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=9.5, leading=12, textColor=c_texto)
    st_bold = ParagraphStyle("bold", parent=st_base, fontName="Helvetica-Bold",
                             textColor=c_navy, leftIndent=6)
    st_izq = ParagraphStyle("izq", parent=st_base, leftIndent=6)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=11,
                             textColor=colors.white, alignment=TA_CENTER, leading=14)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    elementos = [
        _BannerPDF(ancho_util, datos['titulo'], _logo_png(300)),
        Spacer(1, 14),
    ]

    data = [[Paragraph(h, st_head) for h in encabezados]]
    for f in filas:
        fila = []
        for i, valor in enumerate(f):
            if i == ie:
                color = c_rojo if _es_rojo(valor) else "#" + XL_NAVY
                html = (f'<font color="{color}"><font name="ZapfDingbats" size="8">l</font>'
                        f'&nbsp;&nbsp;{escape(valor)}</font>')
                fila.append(Paragraph(html, st_estado))
            else:
                txt = escape(str(_valor_celda(datos, i, valor)))
                if i == datos['negrita']:
                    fila.append(Paragraph(txt, st_bold))
                elif i in izquierda_idx:
                    fila.append(Paragraph(txt, st_izq))
                else:
                    fila.append(Paragraph(txt, st_centro))
        data.append(fila)

    if not filas:
        data.append([Paragraph("No hay devoluciones para mostrar.", st_centro)]
                    + [""] * (len(encabezados) - 1))

    anchos = datos['anchos_pdf']
    escala = ancho_util / sum(anchos)
    tabla = Table(data, colWidths=[a * escala for a in anchos], repeatRows=1)

    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), c_navy),
        ("LINEBEFORE", (1, 0), (-1, 0), 0.6, colors.HexColor("#3B4F6B")),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_zebra]),
        ("LINEBEFORE", (1, 1), (-1, -1), 0.6, c_borde),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, c_navy),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
    ]
    if not filas:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)

    total, ok, rech, monto = _resumen(datos)
    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {total} devoluciones &nbsp;·&nbsp; Completadas/Aplicadas: {ok} "
            f"&nbsp;·&nbsp; Rechazadas: {rech} &nbsp;·&nbsp; Monto devuelto: {_moneda(monto)}",
            st_tot),
        Spacer(1, 2),
        Paragraph(
            escape(_texto_filtros(datos['filtros'])) + " &nbsp;·&nbsp; Generado el "
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
    resp["Content-Disposition"] = f'attachment; filename="{datos["archivo"]}_{_sello()}.pdf"'
    return resp


# ═══════════════════════════════════════════════════════════════════════════════
# IMPRIMIR
# ═══════════════════════════════════════════════════════════════════════════════
def exportar_devoluciones_imprimir(request):
    datos = _datos_export(request)
    filas = datos['filas']
    encab = datos['encabezados']
    im, ie = datos['idx_moneda'], datos['idx_estado']
    izquierda_idx = datos['izquierda']
    total, ok, rech, monto = _resumen(datos)

    def fila_html(f):
        celdas = []
        for i, valor in enumerate(f):
            txt = escape(str(_valor_celda(datos, i, valor)))
            if i == ie:
                clase = "no" if _es_rojo(valor) else "ok"
                celdas.append(f"<td class='c {clase}'>{txt}</td>")
            elif i == datos['negrita']:
                celdas.append(f"<td class='marca'>{txt}</td>")
            elif i in izquierda_idx:
                celdas.append(f"<td>{txt}</td>")
            else:
                celdas.append(f"<td class='c'>{txt}</td>")
        return "<tr>" + "".join(celdas) + "</tr>"

    filas_html = "".join(fila_html(f) for f in filas) or \
        f"<tr><td colspan='{len(encab)}' class='c'>No hay devoluciones para mostrar.</td></tr>"
    encabezados = "".join(f"<th>{escape(h)}</th>" for h in encab)

    logo = _logo_png(300)
    logo_html = ""
    if logo:
        logo_html = f"<img class='logo' src='data:image/png;base64,{base64.b64encode(logo).decode()}' alt='CYS Ltda'>"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>{escape(datos['titulo'])} — CYS Ltda</title>
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
  td.marca {{ font-weight: bold; color: #{NAVY}; }}
  td.ok {{ color: #{VERDE}; font-weight: bold; }}
  td.no {{ color: #{ROJO}; font-weight: bold; }}
  tr:nth-child(even) td {{ background: #{ZEBRA}; }}
  .total {{ margin-top: 8px; background: #{CREAM}; border-top: 3px solid #{GOLD}; padding: 9px 14px;
           text-align: right; font-weight: bold; color: #{NAVY}; font-size: 13px; }}
  .pie {{ margin-top: 14px; font-size: 10px; color: #888; text-align: center; }}
</style></head>
<body>
  <div class="banner">
    {logo_html}
    <div><h1>CYS LTDA · DISTRIBUCIONES</h1><p>{escape(datos['titulo'])}</p></div>
  </div>
  <div class="meta">{escape(_texto_filtros(datos['filtros']))} &nbsp;·&nbsp; Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</div>
  <table><thead><tr>{encabezados}</tr></thead><tbody>{filas_html}</tbody></table>
  <div class="total">Total: {total} devoluciones &nbsp;·&nbsp; Completadas/Aplicadas: {ok} &nbsp;·&nbsp; Rechazadas: {rech} &nbsp;·&nbsp; Monto devuelto: {_moneda(monto)}</div>
  <div class="pie">CYS Ltda · Distribuciones</div>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)


# ═══════════════════════════════════════════════════════════════════════════════
# MÓDULO DEVOLUCIONES DE CLIENTES
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def lista_devoluciones(request):
    """Punto de entrada principal para devoluciones.
    También atiende ?export=excel|pdf|imprimir (&tab=cliente|proveedor)."""
    try:
        # ---- Exportación: se llama a esta misma URL con ?export=... ----
        tipo_export = request.GET.get('export')
        if tipo_export == 'excel':
            return exportar_devoluciones_excel(request)
        if tipo_export == 'pdf':
            return exportar_devoluciones_pdf(request)
        if tipo_export == 'imprimir':
            return exportar_devoluciones_imprimir(request)

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
            Q(vendedor__first_name__icontains=q) | Q(vendedor__username__icontains=q) |
            Q(vendedor__last_name__icontains=q) |
            Q(vendedor__identificacion__icontains=q) |
            Q(cliente_nombre__icontains=q)
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
                det_id = entero_estricto(detalle_id, minimo=1, maximo=2_000_000_000)
                detalle = venta_actual.detalles.select_related('producto').get(pk=det_id)
            except (ValueError, DetalleVenta.DoesNotExist):
                messages.error(request, '⚠️ Error en los datos del producto seleccionado.')
                return redirect('lista_devoluciones')

            pendiente = _pendiente_detalle(venta_actual, detalle)
            nombre = detalle.producto.nombre if detalle.producto else 'el producto'
            try:
                cant = entero_estricto(request.POST.get(f'cantidad_devolucion_{det_id}'), minimo=1, maximo=max(pendiente, 1))
            except ValueError as e:
                messages.error(request, f'⚠️ Cantidad inválida para {nombre}: {e}')
                return redirect('lista_devoluciones')
            if pendiente <= 0 or cant > pendiente:
                messages.error(request, f'⚠️ De {nombre} solo puedes devolver {pendiente} unidades (ya devueltas o vendidas).')
                return redirect('lista_devoluciones')

            productos_con_cantidad[det_id] = cant

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
        observaciones = limpiar_texto(request.POST.get('observaciones'))

        motivos_validos = [m[0] for m in MOTIVO_CHOICES]
        error_obs = validar_texto_libre(observaciones)
        if error_obs:
            messages.error(request, f'⚠️ Observaciones: {error_obs}')
        elif motivo in motivos_validos:
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
            try:
                prod_cambio_id = entero_estricto(request.POST.get('producto_cambio'), minimo=1, maximo=2_000_000_000)
                cant_cambio = entero_estricto(request.POST.get('cantidad_cambio'), minimo=1, maximo=10_000)
            except ValueError as e:
                messages.error(request, f'⚠️ Producto o cantidad de cambio inválidos: {e}')
            else:
                if not Producto.objects.filter(pk=prod_cambio_id, activo=True).exists():
                    messages.error(request, '⚠️ El producto de cambio no existe o está inactivo.')
                else:
                    request.session['dev_producto_cambio_id'] = prod_cambio_id
                    request.session['dev_cantidad_cambio'] = cant_cambio
                    request.session['dev_paso'] = 6
                    request.session.modified = True
                    return redirect('lista_devoluciones')

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
                    if cant_dev <= 0 or cant_dev > _pendiente_detalle(venta, det):
                        messages.error(request, '⚠️ Una de las cantidades ya no está disponible para devolver. Revisa la venta.')
                        request.session['dev_paso'] = 2
                        request.session.modified = True
                        return redirect('lista_devoluciones')
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
        cantidad = entero_estricto(request.POST.get('cantidad'), minimo=1, maximo=1_000_000)
    except ValueError as e:
        return error(f'⚠️ Cantidad a devolver: {e}')

    observaciones = limpiar_texto(request.POST.get('observaciones'))
    error_obs = validar_texto_libre(observaciones)
    if error_obs:
        return error(f'⚠️ Observaciones: {error_obs}')

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
        'obs': observaciones,
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
            Q(venta__vendedor__first_name__icontains=q) | Q(venta__vendedor__last_name__icontains=q) | Q(venta__vendedor__username__icontains=q) | Q(venta__cliente_nombre__icontains=q)
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