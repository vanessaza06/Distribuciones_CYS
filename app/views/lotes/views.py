
from decimal import Decimal, InvalidOperation
from io import BytesIO
import io
import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
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

from app.models import Producto, Lote, Bodega, PresentacionProducto
from app.forms import LoteForm

# Nombre del campo de fecha de ingreso en el modelo Lote.
# Si tu modelo lo llama distinto, cámbialo aquí.
CAMPO_FECHA_LOTE = 'fecha_registro'


def _stats_lotes(hoy):
    """Devuelve (unidades ingresadas hoy, lotes registrados en el mes)."""
    try:
        campo = Lote._meta.get_field(CAMPO_FECHA_LOTE)
    except FieldDoesNotExist:
        return 0, 0

    if isinstance(campo, models.DateTimeField):
        filtro_hoy = {f'{CAMPO_FECHA_LOTE}__date': hoy}
    else:
        filtro_hoy = {CAMPO_FECHA_LOTE: hoy}

    ingresos_hoy = (
        Lote.objects.filter(**filtro_hoy)
        .aggregate(total=Sum('cantidad_inicial'))['total'] or 0
    )
    lotes_mes = Lote.objects.filter(
        **{
            f'{CAMPO_FECHA_LOTE}__year': hoy.year,
            f'{CAMPO_FECHA_LOTE}__month': hoy.month,
        }
    ).count()
    return ingresos_hoy, lotes_mes


@login_required
def lote_list(request):
    """Página 'Lotes': formulario de registro + resumen.

    Si llega ?presentacion=<pk> (por ejemplo desde el botón "Crear Lote"
    de Bodega), esa presentación queda preseleccionada en el formulario.
    """
    hoy = timezone.localdate()

    # Si no hay ninguna bodega, se crea una por defecto para no bloquear el lote.
    if not Bodega.objects.exists():
        Bodega.objects.get_or_create(nombre='Bodega Principal')

    productos = Producto.objects.prefetch_related('presentaciones')
    bodegas = Bodega.objects.all()
    hay_presentaciones = PresentacionProducto.objects.exists()
    hay_bodegas = bodegas.exists()

    presentacion_preseleccionada = request.GET.get('presentacion', '')

    ingresos_hoy, ordenes_mes = _stats_lotes(hoy)

    top = (
        Lote.objects
        .values('presentacion__producto__nombre')
        .annotate(total=Sum('stock_actual'))
        .order_by('-total')[:5]
    )
    labels = [t['presentacion__producto__nombre'] for t in top]
    data = [int(t['total'] or 0) for t in top]

    context = {
        'productos': productos,
        'bodegas': bodegas,
        'hay_presentaciones': hay_presentaciones,
        'hay_bodegas': hay_bodegas,
        'presentacion_preseleccionada': presentacion_preseleccionada,
        'ingresos_hoy': ingresos_hoy,
        'ordenes_mes': ordenes_mes,
        'proveedores_labels': json.dumps(labels),
        'proveedores_data': json.dumps(data),
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Lotes', 'url': reverse('lote_list')},
        ],
    }
    return render(request, 'lotes/lotes.html', context)


@login_required
def gestion_stock(request):
    productos = Producto.objects.select_related('categoria').prefetch_related('presentaciones__lotes')
    lotes_activos = list(Lote.objects.select_related('presentacion__producto', 'bodega'))
    lotes_por_vencer = [l for l in lotes_activos if l.stock_actual > 0 and l.proximo_a_vencer]
    lotes_vencidos = [l for l in lotes_activos if l.stock_actual > 0 and l.esta_vencido]

    context = {
        'productos': productos,
        'lotes_activos': lotes_activos,
        'lotes_por_vencer': lotes_por_vencer,
        'lotes_vencidos': lotes_vencidos,
        'breadcrumb_items': [
            {'nombre': 'Stock & Productos', 'url': reverse('gestion_stock')},
        ],
    }
    return render(request, 'lotes/gestion.html', context)


@login_required
def lote_create(request):
    if request.method == 'POST':
        datos = request.POST.copy()

        # Si no llegó bodega, se usa la primera disponible.
        if not datos.get('bodega'):
            bodega_default = Bodega.objects.first()
            if bodega_default:
                datos['bodega'] = bodega_default.pk

        form = LoteForm(datos, request.FILES)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.stock_actual = lote.cantidad_inicial
            lote.costo_total = lote.costo_unitario * lote.cantidad_inicial
            lote.save()
            messages.success(request, f'Lote {lote.numero_lote} registrado.')
        else:
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')
    return redirect('lote_list')


@login_required
def lote_update(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    cantidad_inicial_original = lote.cantidad_inicial

    if request.method == 'POST':
        form = LoteForm(request.POST, request.FILES, instance=lote)
        if form.is_valid():
            lote_actualizado = form.save(commit=False)
            # La cantidad inicial no se edita aquí: representa el ingreso
            # original del lote. Para cambiar el stock disponible se usa
            # "Ajustar stock".
            lote_actualizado.cantidad_inicial = cantidad_inicial_original
            lote_actualizado.costo_total = lote_actualizado.costo_unitario * cantidad_inicial_original
            lote_actualizado.save()
            messages.success(request, f'Lote {lote.numero_lote} actualizado.')
            return redirect('lote_list')
        else:
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')
    else:
        form = LoteForm(instance=lote)

    return render(request, 'lotes/lote_form.html', {'form': form, 'lote': lote})


@login_required
def lote_detail(request, numero_lote):
    """Reutiliza el mismo formulario de edición completa del lote."""
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    form = LoteForm(instance=lote)
    return render(request, 'lotes/lote_form.html', {'form': form, 'lote': lote})


@login_required
def lote_ajustar_stock(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)

    if request.method != 'POST':
        return redirect('gestion_stock')

    nuevo_stock_raw = request.POST.get('nuevo_stock', '').strip()
    costo_unitario_raw = request.POST.get('costo_unitario', '').strip()

    try:
        nuevo_stock = int(nuevo_stock_raw)
    except (TypeError, ValueError):
        messages.error(request, 'El nuevo stock debe ser un número entero.')
        return redirect('gestion_stock')

    if nuevo_stock < 0:
        messages.error(request, 'El stock no puede ser negativo.')
        return redirect('gestion_stock')

    lote.stock_actual = nuevo_stock

    if costo_unitario_raw:
        try:
            nuevo_costo = Decimal(costo_unitario_raw.replace(',', '.'))
        except (InvalidOperation, ValueError):
            messages.error(request, 'El costo unitario no es válido.')
            return redirect('gestion_stock')

        if nuevo_costo <= 0:
            messages.error(request, 'El costo unitario debe ser mayor a 0.')
            return redirect('gestion_stock')

        lote.costo_unitario = nuevo_costo
        # Se recalcula el costo total con la cantidad inicial del lote.
        lote.costo_total = nuevo_costo * lote.cantidad_inicial
        lote.save(update_fields=['stock_actual', 'costo_unitario', 'costo_total'])
    else:
        lote.save(update_fields=['stock_actual'])

    messages.success(request, 'Stock ajustado.')
    return redirect('gestion_stock')


# ─────────────────────────── EXPORTAR LOTES ───────────────────────────

ENCABEZADOS_EXPORT = [
    'Nº Lote', 'Producto', 'Presentación', 'Bodega', 'Fecha ingreso',
    'Cant. inicial', 'Stock actual', 'Costo unitario', 'Costo total', 'Estado',
]

# Identidad visual (igual que Marcas)
XL_NAVY = "061B3A"
XL_GOLD = "E8A317"
XL_ZEBRA = "EDF0F5"
XL_BORDE = "AEB9CC"
XL_ROJO = "9B1C1C"
XL_NARANJA = "B45309"
XL_GRIS = "6B7280"
XL_FUENTE = "Calibri"

LOGO_ARCHIVO = "logo.20.png"
_LOGO_CACHE = {}

COLOR_ESTADO = {
    'Vigente': XL_NAVY,
    'Por vencer': XL_NARANJA,
    'Vencido': XL_ROJO,
    'Agotado': XL_GRIS,
}


def _estado_lote(lote):
    if lote.stock_actual > 0 and lote.esta_vencido:
        return 'Vencido'
    if lote.stock_actual > 0 and lote.proximo_a_vencer:
        return 'Por vencer'
    if lote.stock_actual <= 0:
        return 'Agotado'
    return 'Vigente'


def _fecha_lote(lote):
    valor = getattr(lote, CAMPO_FECHA_LOTE, None)
    if not valor:
        return ''
    if hasattr(valor, 'astimezone'):          # DateTimeField
        valor = timezone.localtime(valor)
    return valor.strftime('%d/%m/%Y')


def _filas_lotes():
    """Devuelve las filas (listas) de todos los lotes para exportar."""
    lotes = (
        Lote.objects
        .select_related('presentacion__producto', 'bodega')
        .order_by('numero_lote')
    )
    filas = []
    for l in lotes:
        filas.append([
            l.numero_lote,
            l.presentacion.producto.nombre,
            l.presentacion.nombre,
            l.bodega.nombre if l.bodega else '',
            _fecha_lote(l),
            l.cantidad_inicial,
            l.stock_actual,
            l.costo_unitario,
            l.costo_total,
            _estado_lote(l),
        ])
    return filas


def _nombre_archivo(extension):
    return f'lotes_{timezone.localtime():%Y%m%d_%H%M}.{extension}'


def _resumen_lotes(filas):
    cuenta = {'Vigente': 0, 'Por vencer': 0, 'Vencido': 0, 'Agotado': 0}
    for f in filas:
        cuenta[f[9]] = cuenta.get(f[9], 0) + 1
    return len(filas), cuenta


def _texto_pie_lotes(filas):
    total, c = _resumen_lotes(filas)
    return (
        f"Total: {total} lotes   ·   Vigentes: {c['Vigente']}   ·   "
        f"Por vencer: {c['Por vencer']}   ·   Vencidos: {c['Vencido']}   ·   "
        f"Agotados: {c['Agotado']}"
    )


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
def _exportar_excel():
    filas = _filas_lotes()
    encabezados = ENCABEZADOS_EXPORT
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Lotes"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    anchos = [14, 34, 24, 20, 16, 14, 14, 16, 16, 16]
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
    ws["C1"] = "Reporte de Lotes"
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
        c.font = Font(name=XL_FUENTE, size=14, bold=True, color="FFFFFF")
        c.fill = _xl_fill(XL_NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(left=blanco if i > 1 else None)

    # ---------- Datos ----------
    vertical = Side(style="thin", color=XL_BORDE)
    for k, fila in enumerate(filas):
        r = fila_enc + 1 + k
        ws.row_dimensions[r].height = 26
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        estado = fila[9]
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila, start=1):
            if i in (8, 9):
                valor = float(valor or 0)
            if i == 10:
                valor = "●  " + valor
            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == 2))
            izquierda = i in (2, 3, 4)
            c.alignment = Alignment(
                horizontal="left" if izquierda else "center",
                vertical="center",
                indent=1 if izquierda else 0,
            )
            if i in (8, 9):
                c.number_format = '"$"#,##0'
        e = ws.cell(r, 10)
        e.font = Font(name=XL_FUENTE, size=13, bold=True, color=COLOR_ESTADO.get(estado, XL_NAVY))

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        _texto_pie_lotes(filas),
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

    buffer = BytesIO()
    wb.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo("xlsx")}"'
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
        c.setFont("Helvetica-Bold", 34)
        c.drawString(x_txt, self.height - 46, self.titulo)

        # Lema en cursiva
        c.setFont("Helvetica-Oblique", 15)
        c.drawString(x_txt, self.height - 70, "Calidad que llega más lejos")

        # Barrita dorada corta
        c.setFillColor(oro)
        c.roundRect(x_txt, 8, 72, 4.5, 2, stroke=0, fill=1)


def _exportar_pdf():
    filas = _filas_lotes()

    c_navy = colors.HexColor("#" + XL_NAVY)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title="Reporte de lotes — CYS Ltda",
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
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=10.5,
                             textColor=colors.white, alignment=TA_CENTER, leading=13)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    elementos = [
        _BannerPDF(ancho_util, "Reporte de Lotes", _logo_png(300)),
        Spacer(1, 14),
    ]

    data = [[Paragraph(escape(h), st_head) for h in ENCABEZADOS_EXPORT]]
    for f in filas:
        color = "#" + COLOR_ESTADO.get(f[9], XL_NAVY)
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="8">l</font>'
            f'&nbsp;&nbsp;{escape(f[9])}</font>'
        )
        data.append([
            Paragraph(escape(str(f[0])), st_centro),
            Paragraph(escape(str(f[1])), st_bold),
            Paragraph(escape(str(f[2])), st_izq),
            Paragraph(escape(str(f[3])), st_izq),
            Paragraph(escape(str(f[4])), st_centro),
            Paragraph(str(f[5]), st_centro),
            Paragraph(str(f[6]), st_centro),
            Paragraph(f'${(f[7] or 0):,.0f}', st_centro),
            Paragraph(f'${(f[8] or 0):,.0f}', st_centro),
            Paragraph(estado_html, st_estado),
        ])

    if not filas:
        data.append([Paragraph("No hay lotes para mostrar.", st_centro)]
                    + [""] * (len(ENCABEZADOS_EXPORT) - 1))

    anchos = [60, 150, 105, 90, 75, 62, 62, 80, 80, 80]
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
        Paragraph(escape(_texto_pie_lotes(filas)).replace("   ", " &nbsp; "), st_tot),
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
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo("pdf")}"'
    return response


# ---------- IMPRIMIR ----------
def _exportar_imprimir():
    filas = _filas_lotes()

    encabezados_html = ''.join(f'<th>{escape(e)}</th>' for e in ENCABEZADOS_EXPORT)

    filas_html = ''
    for f in filas:
        filas_html += (
            '<tr>'
            f'<td>{escape(f[0])}</td>'
            f'<td>{escape(f[1])}</td>'
            f'<td>{escape(f[2])}</td>'
            f'<td>{escape(f[3])}</td>'
            f'<td>{escape(f[4])}</td>'
            f'<td class="num">{f[5]}</td>'
            f'<td class="num">{f[6]}</td>'
            f'<td class="num">${(f[7] or 0):,.0f}</td>'
            f'<td class="num">${(f[8] or 0):,.0f}</td>'
            f'<td>{escape(f[9])}</td>'
            '</tr>'
        )
    if not filas_html:
        filas_html = '<tr><td colspan="10">No hay lotes registrados.</td></tr>'

    plural = '' if len(filas) == 1 else 's'
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte de Lotes — CYS Ltda</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 12px; color: #111; margin: 24px; }}
    h1 {{ font-size: 20px; margin: 0 0 4px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #0d2a4f; color: #fff; padding: 6px; text-align: left; }}
    td {{ border-bottom: 1px solid #ccc; padding: 5px 6px; }}
    tr:nth-child(even) td {{ background: #f3f6fb; }}
    td.num {{ text-align: right; }}
    @media print {{
      body {{ margin: 0; }}
      th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <h1>Reporte de Lotes — CYS Ltda</h1>
  <div class="meta">Generado el {timezone.localdate():%d/%m/%Y} · {len(filas)} lote{plural}</div>
  <table>
    <thead><tr>{encabezados_html}</tr></thead>
    <tbody>{filas_html}</tbody>
  </table>
  <script>window.onload = function () {{ window.print(); }};</script>
</body>
</html>"""
    return HttpResponse(html)


@login_required
def lote_exportar(request, formato):
    if formato == 'excel':
        return _exportar_excel()
    if formato == 'pdf':
        return _exportar_pdf()
    if formato == 'imprimir':
        return _exportar_imprimir()
    raise Http404('Formato de exportación no válido.')
