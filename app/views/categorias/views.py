import io
import os
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
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

from app.models import Categoria


# ============================================================
# VALIDACIÓN
# Nombre: solo letras (con tildes/ñ) y espacios.
# Código: letras y números, con al menos un número; sin espacios ni símbolos.
# ============================================================
PATRON_NOMBRE = re.compile(r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]+$')
PATRON_CODIGO = re.compile(r'^[A-Z0-9]+$')
TIENE_NUMERO = re.compile(r'[0-9]')

MSG_NOMBRE_INVALIDO = (
    '⚠️ El nombre solo puede tener letras y espacios, '
    'sin números ni caracteres especiales.'
)
MSG_CODIGO_INVALIDO = (
    '⚠️ El código solo puede tener letras y números, '
    'sin espacios ni símbolos.'
)
MSG_CODIGO_SIN_NUMERO = '⚠️ El código debe llevar al menos un número.'


def _limpiar_nombre(valor):
    return " ".join((valor or "").split())


def _nombre_valido(nombre):
    return bool(PATRON_NOMBRE.match(nombre))


def _codigo_valido(codigo):
    return bool(PATRON_CODIGO.match(codigo))


def _codigo_tiene_numero(codigo):
    return bool(TIENE_NUMERO.search(codigo))


@login_required
def categorias_lista(request):
    # Lista plana: ya no hay jerarquía padre/hijo
    categorias = Categoria.objects.prefetch_related('productos').all()

    context = {
        'categorias': categorias,
        'total_activas': categorias.filter(activo=True).count(),
        'total_inactivas': categorias.filter(activo=False).count(),
        'breadcrumb_items': [
            {'nombre': 'Categorías', 'url': None},
        ],
    }
    return render(request, 'categorias/categorias.html', context)


@login_required
def categoria_crear(request):
    if request.method == 'POST':
        nombre = _limpiar_nombre(request.POST.get('nombre'))
        codigo = (request.POST.get('codigo') or '').strip().upper()
        descripcion = (request.POST.get('descripcion') or '').strip()

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        if not _nombre_valido(nombre):
            messages.error(request, MSG_NOMBRE_INVALIDO)
            return redirect('categorias_lista')

        if not _codigo_valido(codigo):
            messages.error(request, MSG_CODIGO_INVALIDO)
            return redirect('categorias_lista')

        if not _codigo_tiene_numero(codigo):
            messages.error(request, MSG_CODIGO_SIN_NUMERO)
            return redirect('categorias_lista')

        if Categoria.objects.filter(codigo__iexact=codigo).exists():
            messages.error(request, f'⚠️ Ya existe una categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        Categoria.objects.create(
            nombre=nombre,
            codigo=codigo,
            descripcion=descripcion,
        )
        messages.success(request, f'✅ Categoría "{nombre}" creada con éxito.')

    return redirect('categorias_lista')


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        nombre = _limpiar_nombre(request.POST.get('nombre'))
        codigo = (request.POST.get('codigo') or '').strip().upper()
        descripcion = (request.POST.get('descripcion') or '').strip()

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        if not _nombre_valido(nombre):
            messages.error(request, MSG_NOMBRE_INVALIDO)
            return redirect('categorias_lista')

        if not _codigo_valido(codigo):
            messages.error(request, MSG_CODIGO_INVALIDO)
            return redirect('categorias_lista')

        if not _codigo_tiene_numero(codigo):
            messages.error(request, MSG_CODIGO_SIN_NUMERO)
            return redirect('categorias_lista')

        if Categoria.objects.filter(codigo__iexact=codigo).exclude(pk=pk).exists():
            messages.error(request, f'⚠️ Ya existe otra categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        categoria.nombre = nombre
        categoria.codigo = codigo
        categoria.descripcion = descripcion
        categoria.save()

        messages.success(request, f'✅ Categoría "{nombre}" actualizada correctamente.')

    return redirect('categorias_lista')


@login_required
def categoria_toggle_activo(request, pk):
    """Las categorías no se eliminan: solo se activan o desactivan."""
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        categoria.activo = not categoria.activo
        categoria.save(update_fields=['activo'])

        if categoria.activo:
            messages.success(request, f'✅ Categoría "{categoria.nombre}" activada.')
        else:
            messages.warning(
                request,
                f'⚠️ Categoría "{categoria.nombre}" desactivada. No se elimina para conservar el histórico de productos.'
            )

    return redirect('categorias_lista')


# ============================================================
# EXPORTACIONES  (mismo diseño que el reporte de Marcas)
# ============================================================

# Identidad visual
XL_NAVY = "061B3A"
XL_GOLD = "E8A317"
XL_ZEBRA = "EDF0F5"
XL_BORDE = "AEB9CC"
XL_ROJO = "9B1C1C"
XL_FUENTE = "Calibri"

LOGO_ARCHIVO = "logo.20.png"
_LOGO_CACHE = {}

ENCABEZADOS_EXPORT = ["Código", "Categoría", "Descripción", "Productos", "Estado"]


def _categorias_para_exportar():
    return Categoria.objects.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')


def _filas_categorias():
    filas = []
    for c in _categorias_para_exportar():
        filas.append([
            c.codigo,
            c.nombre,
            c.descripcion or "—",
            c.total_productos,
            "Activa" if c.activo else "Inactiva",
        ])
    return filas


def _resumen(filas):
    activas = sum(1 for f in filas if f[4] == "Activa")
    return len(filas), activas, len(filas) - activas


def _sello():
    return timezone.localtime().strftime('%Y%m%d_%H%M')


# ---------- Logo ----------
def _ruta_logo():
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


# ---------- EXCEL ----------
@login_required
def categoria_exportar_excel(request):
    filas = _filas_categorias()
    total, activas, inactivas = _resumen(filas)
    encabezados = ENCABEZADOS_EXPORT
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Categorías"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    anchos = [16, 34, 50, 16, 20]
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
    ws["C1"] = "Reporte de Categorías"
    ws["C1"].font = Font(name=XL_FUENTE, size=30, bold=True, color=XL_NAVY)
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
    for k, fila in enumerate(filas):
        r = fila_enc + 1 + k
        ws.row_dimensions[r].height = 26
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        activa = fila[4] == "Activa"
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila, start=1):
            if i == 5:
                valor = "●  " + valor
            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == 2))
            izquierda = i in (2, 3)
            c.alignment = Alignment(
                horizontal="left" if izquierda else "center",
                vertical="center",
                indent=1 if izquierda else 0,
                wrap_text=(i == 3),
            )
        e = ws.cell(r, 5)
        e.font = Font(name=XL_FUENTE, size=13, bold=True, color=XL_NAVY if activa else XL_ROJO)

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        f"Total: {total} categorías   ·   Activas: {activas}   ·   Inactivas: {inactivas}",
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
    response['Content-Disposition'] = f'attachment; filename="categorias_{_sello()}.xlsx"'
    return response


# ---------- PDF ----------
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
        c.setFont("Helvetica-Bold", 34)
        c.drawString(x_txt, self.height - 46, self.titulo)

        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, "Calidad que llega más lejos")

        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


@login_required
def categoria_exportar_pdf(request):
    filas = _filas_categorias()
    total, activas, inactivas = _resumen(filas)

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
        title="Reporte de categorías — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=10.5, leading=13, textColor=c_texto)
    st_marca = ParagraphStyle("marca", parent=st_base, fontName="Helvetica-Bold",
                              textColor=c_navy, leftIndent=8)
    st_desc = ParagraphStyle("desc", parent=st_base, leftIndent=8)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=12,
                             textColor=colors.white, alignment=TA_CENTER, leading=15)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    elementos = [
        _BannerPDF(ancho_util, "Reporte de Categorías", _logo_png(300)),
        Spacer(1, 14),
    ]

    data = [[Paragraph(escape(h), st_head) for h in ENCABEZADOS_EXPORT]]
    for f in filas:
        activa = f[4] == "Activa"
        color = "#" + XL_NAVY if activa else c_rojo
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="9">l</font>'
            f'&nbsp;&nbsp;{f[4]}</font>'
        )
        data.append([
            Paragraph(escape(str(f[0])), st_centro),
            Paragraph(escape(f[1]), st_marca),
            Paragraph(escape(f[2]), st_desc),
            Paragraph(str(f[3]), st_centro),
            Paragraph(estado_html, st_estado),
        ])

    if not filas:
        data.append([Paragraph("No hay categorías para mostrar.", st_centro)]
                    + [""] * (len(ENCABEZADOS_EXPORT) - 1))

    anchos = [70, 210, 330, 90, 100]
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

    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {total} categorías &nbsp;·&nbsp; Activas: {activas} &nbsp;·&nbsp; Inactivas: {inactivas}",
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
    response['Content-Disposition'] = f'attachment; filename="categorias_{_sello()}.pdf"'
    return response
