import base64
import io
import os
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme

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
from reportlab.platypus import (
    Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app.forms import PresentacionForm
from app.models import PresentacionProducto, Producto


def _volver(request, producto_pk, resaltar=None):
    """Si el formulario manda 'next' (ej: desde la página de Presentaciones),
    vuelve ahí; si no, mantiene el comportamiento anterior.
    Con 'resaltar' agrega ?resaltar=<pk> para marcar esa fila en la tabla."""
    destino = request.POST.get('next', '')
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        if resaltar:
            separador = '&' if '?' in destino else '?'
            destino = f"{destino}{separador}{urlencode({'resaltar': resaltar})}"
        return redirect(destino)
    return redirect('producto_detalle', pk=producto_pk)


@login_required
def presentacion_crear(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)

    if request.method != 'POST':
        return redirect('producto_detalle', pk=producto_pk)

    form = PresentacionForm(request.POST)

    if not form.is_valid():
        for campo, errores in form.errors.items():
            for error in errores:
                messages.error(request, f'{campo}: {error}')
        return _volver(request, producto_pk)

    nombre = form.cleaned_data['nombre'].strip()
    if producto.presentaciones.filter(nombre__iexact=nombre).exists():
        messages.error(request, f'Ya existe una presentación "{nombre}" en este producto.')
        return _volver(request, producto_pk)

    presentacion = form.save(commit=False)
    presentacion.producto = producto
    presentacion.save()

    messages.success(request, f'Presentación "{presentacion.nombre}" agregada.')
    return _volver(request, producto_pk, resaltar=presentacion.pk)


@login_required
def presentacion_editar(request, pk):
    pres = get_object_or_404(PresentacionProducto, pk=pk)

    if request.method != 'POST':
        return redirect('producto_detalle', pk=pres.producto_id)

    form = PresentacionForm(request.POST, instance=pres)

    if not form.is_valid():
        for campo, errores in form.errors.items():
            for error in errores:
                messages.error(request, f'{campo}: {error}')
        return _volver(request, pres.producto_id)

    nombre_nuevo = form.cleaned_data['nombre'].strip()
    duplicado = (
        pres.producto.presentaciones
        .filter(nombre__iexact=nombre_nuevo)
        .exclude(pk=pres.pk)
        .exists()
    )
    if duplicado:
        messages.error(request, f'Ya existe otra presentación "{nombre_nuevo}" en este producto.')
        return _volver(request, pres.producto_id)

    # OJO: ya NO se copia precio_venta al costo_unitario de los lotes.
    form.save()

    messages.success(request, f'Presentación "{pres.nombre}" actualizada.')
    return _volver(request, pres.producto_id, resaltar=pres.pk)


@login_required
def presentacion_toggle_activo(request, pk):
    # TODO: pasar a @require_POST cuando el template/JS envíe POST con CSRF.
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    pres.activo = not pres.activo
    pres.save(update_fields=['activo'])
    estado = 'activada' if pres.activo else 'desactivada'
    messages.success(request, f'Presentación "{pres.nombre}" {estado}.')
    return _volver(request, pres.producto_id, resaltar=pres.pk)


@login_required
def presentacion_lista(request):
    presentaciones = (
        PresentacionProducto.objects
        .select_related('producto', 'producto__categoria')
        .order_by('producto__nombre', 'nombre')
    )
    productos = Producto.objects.filter(activo=True).order_by('nombre')

    resaltar = request.GET.get('resaltar', '')
    resaltar_pk = int(resaltar) if resaltar.isdigit() else None

    context = {
        'presentaciones': presentaciones,
        'productos': productos,
        'resaltar_pk': resaltar_pk,
        'breadcrumb_items': [
            {'nombre': 'Presentaciones', 'url': None},
        ],
    }
    return render(request, 'presentaciones/presentaciones.html', context)


# ===========================================================================
# EXPORTAR PRESENTACIONES (EXCEL / PDF / IMPRIMIR)
# Mismo diseño que el reporte de Marcas: banner con logo + tabla azul marino.
# ===========================================================================

# ---- Identidad visual ----
XL_NAVY = "061B3A"       # títulos, encabezado de tabla y texto
XL_GOLD = "E8A317"       # divisor y barrita dorada
XL_ZEBRA = "EDF0F5"      # fila alterna
XL_BORDE = "AEB9CC"      # líneas verticales de la tabla
XL_ROJO = "9B1C1C"       # estado inactiva
XL_FUENTE = "Calibri"

# Colores para la vista "Imprimir"
NAVY = "0B1B30"
GOLD = "C48F3C"
CREAM = "F0E7DA"
ZEBRA = "FAF5EA"
BORDE = "E3D3B5"
VERDE = "1E8449"
ROJO = "B03A2E"

TITULO_REPORTE = "Reporte de Presentaciones"
LEMA = "Calidad que llega más lejos"

LOGO_ARCHIVO = "logo.20.png"   # nombre del logo dentro de la carpeta static
_LOGO_CACHE = {}

ENCABEZADOS_EXPORT_PRES = [
    '#', 'Producto', 'Categoría', 'Presentación', 'Cantidad',
    'Precio venta', 'Stock real', 'Estado',
]
# Índices de columnas (0-indexados) dentro de cada fila
I_ID, I_PROD, I_CAT, I_PRES, I_CANT, I_PRECIO, I_STOCK, I_ESTADO = range(8)


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def _filas_presentaciones():
    """Devuelve las filas (listas) de todas las presentaciones para exportar."""
    presentaciones = (
        PresentacionProducto.objects
        .select_related('producto', 'producto__categoria')
        .order_by('producto__nombre', 'nombre')
    )
    filas = []
    for p in presentaciones:
        filas.append([
            p.pk,
            p.producto.nombre,
            p.producto.categoria.nombre if p.producto.categoria else '—',
            p.nombre,
            p.cantidad,
            p.precio_venta or 0,
            p.stock_real or 0,
            'Activa' if p.activo else 'Inactiva',
        ])
    return filas


def _resumen_pres(filas):
    activas = sum(1 for f in filas if f[I_ESTADO] == 'Activa')
    return len(filas), activas, len(filas) - activas


def _nombre_archivo_pres(extension):
    return f'presentaciones_{timezone.localtime():%Y%m%d_%H%M}.{extension}'


def _num(valor):
    """Convierte Decimal/None a float para Excel."""
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# EXCEL
# ---------------------------------------------------------------------------
def _xl_fill(hex_):
    return PatternFill("solid", start_color=hex_, end_color=hex_)


def _poner_imagen(ws, datos_png, col, fila, ancho, alto, off_x=0, off_y=0):
    """Pega una imagen PNG (bytes) en la celda (col, fila) 0-indexada, con desplazamiento en px."""
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


def _exportar_excel_presentaciones():
    filas = _filas_presentaciones()
    total, activas, inactivas = _resumen_pres(filas)
    encabezados = ENCABEZADOS_EXPORT_PRES
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Presentaciones"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    #          #   Producto Categoría Present. Cant.  Precio Stock  Estado
    anchos = [10,  34,      24,       26,      13,    18,    14,    16]
    for idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = ancho

    # ---------- Banner (filas 1-3, fondo blanco) ----------
    for r, h in {1: 30, 2: 34, 3: 30}.items():
        ws.row_dimensions[r].height = h

    # Logo circular (columnas A:B, centrado)
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

    # Divisor dorado vertical
    lado_oro = Side(style="medium", color=XL_GOLD)
    for r in (1, 2, 3):
        ws.cell(r, 3).border = Border(left=lado_oro)

    # Título y lema
    ws.merge_cells(f"C1:{ultima}2")
    ws["C1"] = TITULO_REPORTE
    ws["C1"].font = Font(name=XL_FUENTE, size=30, bold=True, color=XL_NAVY)
    ws["C1"].alignment = Alignment(horizontal="left", vertical="center", indent=2)
    ws.merge_cells(f"C3:{ultima}3")
    ws["C3"] = LEMA
    ws["C3"].font = Font(name=XL_FUENTE, size=16, italic=True, color=XL_NAVY)
    ws["C3"].alignment = Alignment(horizontal="left", vertical="top", indent=2)

    # Barrita dorada corta bajo el lema
    ws.row_dimensions[4].height = 10
    barra = _barra_dorada(140, 5)
    if barra:
        _poner_imagen(ws, barra, 2, 3, 140, 5, off_x=22, off_y=2)
    ws.row_dimensions[5].height = 16

    # ---------- Encabezado de tabla (fila 6) ----------
    fila_enc = 6
    ws.row_dimensions[fila_enc].height = 34
    blanco = Side(style="thin", color="FFFFFF")
    for i, texto in enumerate(encabezados, start=1):
        c = ws.cell(fila_enc, i, texto)
        c.font = Font(name=XL_FUENTE, size=14, bold=True, color="FFFFFF")
        c.fill = _xl_fill(XL_NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = Border(left=blanco if i > 1 else None)

    # ---------- Datos ----------
    vertical = Side(style="thin", color=XL_BORDE)
    for k, fila in enumerate(filas):
        r = fila_enc + 1 + k
        ws.row_dimensions[r].height = 26
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        activa = fila[I_ESTADO] == "Activa"
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila, start=1):
            col0 = i - 1
            if col0 == I_ESTADO:
                valor = "●  " + valor
            elif col0 in (I_CANT, I_STOCK):
                valor = _num(valor)
                if valor == int(valor):
                    valor = int(valor)
            elif col0 == I_PRECIO:
                valor = _num(valor)

            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=12, color="1F2937", bold=(col0 == I_PROD))
            izquierda = col0 in (I_PROD, I_CAT, I_PRES)
            c.alignment = Alignment(
                horizontal="left" if izquierda else "center",
                vertical="center",
                indent=1 if izquierda else 0,
                wrap_text=(col0 == I_PRES),
            )
            if col0 == I_PRECIO:
                c.number_format = '"$"#,##0'

        # Estado
        e = ws.cell(r, I_ESTADO + 1)
        e.font = Font(name=XL_FUENTE, size=12, bold=True, color=XL_NAVY if activa else XL_ROJO)

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        f"Total: {total} presentaciones   ·   Activas: {activas}   ·   Inactivas: {inactivas}",
        f"Generado el {timezone.localtime():%d/%m/%Y %H:%M}",
    ]
    for j, texto in enumerate(textos_pie, start=1):
        rr = r + j
        ws.row_dimensions[rr].height = 22
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=n)
        p = ws.cell(rr, 1, texto)
        p.font = Font(name=XL_FUENTE, size=11, bold=(j == 1), italic=(j == 2), color=XL_NAVY)
        p.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    # ---------- Extras ----------
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
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo_pres("xlsx")}"'
    return response


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
class _BannerPDF(Flowable):
    """Banner: logo circular | divisor dorado | título | lema | barrita dorada."""

    def __init__(self, ancho, logo_bytes=None):
        super().__init__()
        self.width = ancho
        self.height = 96
        self.logo_bytes = logo_bytes

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        navy = colors.HexColor("#" + XL_NAVY)
        oro = colors.HexColor("#" + XL_GOLD)

        # Logo circular
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

        # Divisor dorado vertical
        x_div = x_logo + diam + 26
        c.setStrokeColor(oro)
        c.setLineWidth(2.5)
        c.line(x_div, 8, x_div, self.height - 8)

        # Título
        x_txt = x_div + 26
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 30)
        c.drawString(x_txt, self.height - 46, TITULO_REPORTE)

        # Lema en cursiva
        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, LEMA)

        # Barrita dorada corta
        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


def _exportar_pdf_presentaciones():
    filas = _filas_presentaciones()
    total, activas, inactivas = _resumen_pres(filas)

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
        title="Reporte de Presentaciones — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=10, leading=12.5, textColor=c_texto)
    st_bold = ParagraphStyle("bold", parent=st_base, fontName="Helvetica-Bold",
                             textColor=c_navy, leftIndent=8)
    st_left = ParagraphStyle("left", parent=st_base, leftIndent=8)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=11,
                             textColor=colors.white, alignment=TA_CENTER, leading=14)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    # --- Banner ---
    elementos = [
        _BannerPDF(ancho_util, _logo_png(300)),
        Spacer(1, 14),
    ]

    # --- Tabla ---
    data = [[Paragraph(escape(h), st_head) for h in ENCABEZADOS_EXPORT_PRES]]
    for f in filas:
        activa = f[I_ESTADO] == "Activa"
        color = "#" + XL_NAVY if activa else c_rojo
        # El punto "●" se dibuja con ZapfDingbats (Helvetica no trae ese símbolo)
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="9">l</font>'
            f'&nbsp;&nbsp;{f[I_ESTADO]}</font>'
        )
        data.append([
            Paragraph(str(f[I_ID]), st_centro),
            Paragraph(escape(str(f[I_PROD])), st_bold),
            Paragraph(escape(str(f[I_CAT])), st_left),
            Paragraph(escape(str(f[I_PRES])), st_left),
            Paragraph(escape(str(f[I_CANT])), st_centro),
            Paragraph(f'${_num(f[I_PRECIO]):,.0f}', st_centro),
            Paragraph(escape(str(f[I_STOCK])), st_centro),
            Paragraph(estado_html, st_estado),
        ])

    if not filas:
        data.append([Paragraph("No hay presentaciones para mostrar.", st_centro)]
                    + [""] * (len(ENCABEZADOS_EXPORT_PRES) - 1))

    anchos = [35, 170, 115, 140, 60, 80, 65, 80]
    escala = ancho_util / sum(anchos)
    tabla = Table(data, colWidths=[a * escala for a in anchos], repeatRows=1)

    estilo = [
        # Encabezado azul marino
        ("BACKGROUND", (0, 0), (-1, 0), c_navy),
        ("LINEBEFORE", (1, 0), (-1, 0), 0.6, colors.HexColor("#3B4F6B")),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        # Filas con cebra y líneas verticales
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_zebra]),
        ("LINEBEFORE", (1, 1), (-1, -1), 0.6, c_borde),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Contorno azul marino con esquinas redondeadas
        ("BOX", (0, 0), (-1, -1), 1, c_navy),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
    ]
    if not filas:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)

    # --- Totales (discretos, debajo de la tabla) ---
    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {total} presentaciones &nbsp;·&nbsp; Activas: {activas} "
            f"&nbsp;·&nbsp; Inactivas: {inactivas}",
            st_tot),
        Spacer(1, 2),
        Paragraph("Generado el " + timezone.localtime().strftime("%d/%m/%Y %H:%M"), st_meta),
    ]

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(margen, 20, "CYS Ltda · Distribuciones")
        canvas.drawRightString(pagina[0] - margen, 20, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo_pres("pdf")}"'
    return response


# ---------------------------------------------------------------------------
# IMPRIMIR
# ---------------------------------------------------------------------------
def _exportar_imprimir_presentaciones():
    filas = _filas_presentaciones()
    total, activas, inactivas = _resumen_pres(filas)

    encabezados_html = ''.join(f'<th>{escape(e)}</th>' for e in ENCABEZADOS_EXPORT_PRES)

    filas_html = ''
    for f in filas:
        clase = 'ok' if f[I_ESTADO] == 'Activa' else 'no'
        filas_html += (
            '<tr>'
            f"<td class='c'>{f[I_ID]}</td>"
            f"<td class='marca'>{escape(str(f[I_PROD]))}</td>"
            f"<td>{escape(str(f[I_CAT]))}</td>"
            f"<td>{escape(str(f[I_PRES]))}</td>"
            f"<td class='c'>{escape(str(f[I_CANT]))}</td>"
            f"<td class='c'>${_num(f[I_PRECIO]):,.0f}</td>"
            f"<td class='c'>{escape(str(f[I_STOCK]))}</td>"
            f"<td class='c {clase}'>{f[I_ESTADO]}</td>"
            '</tr>'
        )
    if not filas_html:
        filas_html = (
            f"<tr><td colspan='{len(ENCABEZADOS_EXPORT_PRES)}' class='c'>"
            "No hay presentaciones para mostrar.</td></tr>"
        )

    logo = _logo_png(300)
    logo_html = ''
    if logo:
        logo_html = (
            f"<img class='logo' src='data:image/png;base64,"
            f"{base64.b64encode(logo).decode()}' alt='CYS Ltda'>"
        )

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Reporte de Presentaciones — CYS Ltda</title>
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
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
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
    <div><h1>CYS LTDA · DISTRIBUCIONES</h1><p>{TITULO_REPORTE}</p></div>
  </div>
  <div class="meta">Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</div>
  <table><thead><tr>{encabezados_html}</tr></thead><tbody>{filas_html}</tbody></table>
  <div class="total">Total: {total} presentaciones &nbsp;·&nbsp; Activas: {activas} &nbsp;·&nbsp; Inactivas: {inactivas}</div>
  <div class="pie">CYS Ltda · Distribuciones</div>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)


@login_required
def presentacion_exportar(request, formato):
    if formato == 'excel':
        return _exportar_excel_presentaciones()
    if formato == 'pdf':
        return _exportar_pdf_presentaciones()
    if formato == 'imprimir':
        return _exportar_imprimir_presentaciones()
    raise Http404('Formato de exportación no válido.')