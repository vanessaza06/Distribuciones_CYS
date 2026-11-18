import io
import logging
import os
import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from itertools import zip_longest
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
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
from openpyxl.worksheet.properties import PageSetupProperties

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.validators import (
    normalizar_nombre,
    validar_nombre_producto,
    validar_nombre_presentacion,
)
from app.forms import ProductoRegistroForm
from app.models import Categoria, Compra, PresentacionProducto, Producto

logger = logging.getLogger(__name__)

UMBRAL_STOCK_CRITICO = 5


# ===============================
# HELPERS
# ===============================
def _es_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _destino_seguro(request, destino):
    """Evita open redirect: solo acepta rutas del mismo sitio."""
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return reverse('lista_productos')


def _entero_positivo(valor):
    """Devuelve un entero >= 1, o None si no es válido."""
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def _decimal_positivo(valor):
    """Devuelve un Decimal > 0 con 2 decimales, o None si no es válido."""
    try:
        d = Decimal(str(valor).strip().replace(',', '.'))
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if not d.is_finite() or d <= 0:
        return None
    return d.quantize(Decimal('0.01'))


# ===============================
# LISTA / VISTA PRINCIPAL
# ===============================
@login_required
def lista_productos(request):
    productos_qs = (
        Producto.objects.select_related('categoria')
        .prefetch_related('presentaciones__lotes', 'detalles')
        .all()
    )

    categorias = Categoria.objects.filter(subcategoria__isnull=True).prefetch_related(
        Prefetch(
            'productos',
            queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria'),
        ),
        Prefetch(
            'subcategorias',
            queryset=Categoria.objects.prefetch_related(
                Prefetch(
                    'productos',
                    queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria'),
                )
            ),
        ),
    )

    resumen_categorias = []
    for cat in Categoria.objects.filter(subcategoria__isnull=True):
        total = Producto.objects.filter(categoria=cat).count()
        total += Producto.objects.filter(categoria__subcategoria=cat).count()
        resumen_categorias.append({'pk': cat.pk, 'nombre': cat.nombre, 'total': total})

    context = {
        'productos': productos_qs,
        'categorias': categorias,
        'todas_cats': Categoria.objects.all(),
        'resumen_categorias': resumen_categorias,
        'form': ProductoRegistroForm(),
        'breadcrumb_items': [
            {'nombre': 'Productos', 'url': None},
        ],
    }
    return render(request, 'productos/productos.html', context)


# ===============================
# CREAR PRODUCTO
# ===============================
@login_required
def crear_producto(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    ajax = _es_ajax(request)
    destino = _destino_seguro(request, request.POST.get('next') or request.GET.get('next'))

    categoria_pk = request.POST.get('categoria', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()

    errores = {}
    try:
        nombre = validar_nombre_producto(request.POST.get('nombre', ''))
    except ValidationError as e:
        nombre = ''
        errores['nombre'] = e.messages

    categoria = None
    if not categoria_pk:
        errores['categoria'] = ['La categoría es obligatoria.']
    elif not categoria_pk.isdigit():
        errores['categoria'] = ['Categoría no válida.']
    else:
        categoria = Categoria.objects.filter(pk=int(categoria_pk), activo=True).first()
        if categoria is None:
            errores['categoria'] = ['La categoría no existe o está desactivada.']

    if errores:
        if ajax:
            return JsonResponse({'ok': False, 'errores': errores}, status=400)
        messages.error(request, 'Corrige los errores del formulario.')
        return redirect(destino)

    # La fecha de vencimiento se registra después, en Detalle de Producto.
    producto = Producto.objects.create(
        nombre=nombre,
        categoria=categoria,
        descripcion=descripcion,
    )

    messages.success(request, f'✅ Producto "{producto.nombre}" creado correctamente.')

    if ajax:
        return JsonResponse({'ok': True, 'pk': producto.pk, 'nombre': producto.nombre})
    return redirect(destino)


# ===============================
# DETALLE PRODUCTO
# ===============================
@login_required
def producto_detalle(request, pk):
    """Vuelve a la lista; ?producto=<pk> queda disponible para el frontend."""
    get_object_or_404(Producto, pk=pk)
    return redirect(f"{reverse('lista_productos')}?producto={pk}")


# ===============================
# EDITAR PRODUCTO
# ===============================
@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method != 'POST':
        return redirect('lista_productos')

    cambios = []
    avisos = []

    with transaction.atomic():
        # ── Datos básicos ──
        nombre_raw = request.POST.get('nombre')
        if nombre_raw is not None and normalizar_nombre(nombre_raw) != producto.nombre:
            try:
                producto.nombre = validar_nombre_producto(nombre_raw)
                cambios.append('nombre')
            except ValidationError as e:
                avisos.append(f'Nombre no actualizado: {e.messages[0]}')

        descripcion = request.POST.get('descripcion')
        if descripcion is not None:
            descripcion = descripcion.strip()
            if descripcion != (producto.descripcion or ''):
                producto.descripcion = descripcion
                cambios.append('descripción')

        categoria_pk = request.POST.get('categoria', '').strip()
        if categoria_pk.isdigit() and int(categoria_pk) != producto.categoria_id:
            nueva_cat = Categoria.objects.filter(pk=int(categoria_pk)).first()
            if nueva_cat:
                producto.categoria = nueva_cat
                cambios.append('categoría')
            else:
                avisos.append('La categoría elegida no existe.')

        if cambios:
            producto.save()

        # ── Presentaciones existentes ──
        # OJO: ya NO se copia el precio de venta al costo de los lotes.
        for key, valor in request.POST.items():
            if not key.startswith('pres_nombre_'):
                continue
            pres_id = key.replace('pres_nombre_', '')
            if not pres_id.isdigit():
                continue
            pres = PresentacionProducto.objects.filter(pk=int(pres_id), producto=producto).first()
            if pres is None:
                continue

            modificado = False

            if valor.strip() and normalizar_nombre(valor) != pres.nombre:
                try:
                    pres.nombre = validar_nombre_presentacion(valor)
                    modificado = True
                except ValidationError as e:
                    avisos.append(f'Nombre de presentación no actualizado: {e.messages[0]}')

            cant_raw = request.POST.get(f'pres_cantidad_{pres_id}', '').strip()
            if cant_raw:
                nueva_cant = _entero_positivo(cant_raw)
                if nueva_cant is None:
                    avisos.append(f'Cantidad inválida en "{pres.nombre}" (debe ser 1 o más).')
                elif nueva_cant != pres.cantidad:
                    pres.cantidad = nueva_cant
                    modificado = True

            precio_raw = request.POST.get(f'pres_precio_{pres_id}', '').strip()
            if precio_raw:
                nuevo_precio = _decimal_positivo(precio_raw)
                if nuevo_precio is None:
                    avisos.append(f'Precio inválido en "{pres.nombre}" (debe ser mayor a 0).')
                elif nuevo_precio != pres.precio_venta:
                    pres.precio_venta = nuevo_precio
                    modificado = True

            if modificado:
                pres.save()
                cambios.append(f'presentación "{pres.nombre}"')

        # ── Nuevas presentaciones ──
        nombres = request.POST.getlist('nueva_pres_nombre[]')
        cantidades = request.POST.getlist('nueva_pres_cantidad[]')
        precios = request.POST.getlist('nueva_pres_precio[]')

        for nombre_pres, cant_raw, precio_raw in zip_longest(nombres, cantidades, precios, fillvalue=''):
            if not nombre_pres.strip():
                continue
            try:
                nombre_pres = validar_nombre_presentacion(nombre_pres)
            except ValidationError as e:
                avisos.append(f'Presentación "{nombre_pres.strip()}" no creada: {e.messages[0]}')
                continue

            cantidad_pres = _entero_positivo(cant_raw)
            precio_pres = _decimal_positivo(precio_raw)
            if cantidad_pres is None or precio_pres is None:
                avisos.append(
                    f'Presentación "{nombre_pres}" no creada: cantidad y precio deben ser mayores a 0.'
                )
                continue

            if producto.presentaciones.filter(nombre__iexact=nombre_pres).exists():
                avisos.append(f'Presentación "{nombre_pres}" no creada: ya existe en este producto.')
                continue

            PresentacionProducto.objects.create(
                producto=producto,
                nombre=nombre_pres,
                cantidad=cantidad_pres,
                precio_venta=precio_pres,
            )
            cambios.append(f'nueva presentación "{nombre_pres}"')

    for aviso in avisos:
        messages.warning(request, f'⚠️ {aviso}')

    if cambios:
        messages.success(request, f"✅ Producto '{producto.nombre}' actualizado.")
    elif not avisos:
        messages.info(request, 'ℹ️ No se detectaron cambios en el producto.')

    return redirect('lista_productos')


# ===============================
# REGISTRO PRODUCTO
# ===============================
@login_required
def producto_registro(request):
    """Guarda y vuelve a la lista."""
    if request.method == 'POST':
        form = ProductoRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Producto registrado correctamente.')
        else:
            for campo, errs in form.errors.items():
                messages.error(request, f'{campo}: {", ".join(errs)}')
    return redirect('lista_productos')


# ===============================
# STOCK STATUS & NOTIFICACIONES
# ===============================
@login_required
def stock_status(request):
    """Retorna productos con stock crítico y compras pendientes."""
    productos = Producto.objects.filter(activo=True).annotate(total=Sum('lotes__stock_actual'))

    criticos = [
        {'nombre': p.nombre, 'total_stock': p.total or 0}
        for p in productos
        if (p.total or 0) <= UMBRAL_STOCK_CRITICO
    ]

    compras_pendientes_qs = (
        Compra.objects.filter(estado__in=['pendiente', 'confirmada'])
        .select_related('proveedor')
        .order_by('-fecha')[:20]
    )

    compras_pendientes = [
        {
            'id': c.codigo_compra,
            'proveedor': c.proveedor.nombre_empresa if c.proveedor else 'Proveedor',
            'estado': c.get_estado_display(),
            'estado_raw': c.estado,
            'valor': float(c.valor),
            'saldo': float(c.saldo),
            'fecha': timezone.localtime(c.fecha).strftime('%d/%m %H:%M') if c.fecha else '',
            'url': reverse('detalle_compra', args=[c.codigo_compra]),
        }
        for c in compras_pendientes_qs
    ]

    return JsonResponse({
        'criticos': criticos,
        'compras_pendientes': compras_pendientes,
        'total_compras_pendientes': len(compras_pendientes),
        'total_alertas': len(criticos) + len(compras_pendientes),
    })


# ===============================
# BUSCAR PRODUCTO
# ===============================
@login_required
def buscar_producto(request):
    q = request.GET.get('q', '').strip()
    modo = request.GET.get('modo', '')

    if not q:
        if modo == 'sugerencias':
            return JsonResponse({'resultados': []})
        return JsonResponse({'encontrado': False, 'mensaje': 'Escribe un nombre.'})

    if modo == 'sugerencias':
        productos = Producto.objects.filter(nombre__icontains=q).select_related('categoria')[:8]
        resultados = [{
            'pk': p.pk,
            'nombre': p.nombre,
            'categoria': p.categoria.nombre if p.categoria else '—',
        } for p in productos]
        return JsonResponse({'resultados': resultados})

    producto = Producto.objects.filter(nombre__icontains=q).order_by('nombre').first()

    if not producto:
        return JsonResponse({'encontrado': False, 'mensaje': f'No se encontró "{q}".'})

    stock_total = producto.presentaciones.aggregate(
        total=Sum('lotes__stock_actual')
    )['total'] or 0

    presentaciones = []
    for pres in producto.presentaciones.all():
        stock_pres = pres.lotes.aggregate(total=Sum('stock_actual'))['total'] or 0
        presentaciones.append({
            'id': pres.pk,
            'nombre': pres.nombre,
            'cantidad': pres.cantidad,
            'precio': str(pres.precio_venta),
            'stock_actual': stock_pres,
        })

    return JsonResponse({
        'encontrado': True,
        'producto': {
            'pk': producto.pk,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre if producto.categoria else '—',
            'stock_total': stock_total,
            'descripcion': producto.descripcion or '',
            'presentaciones': presentaciones,
        },
    })


# ===============================
# ACTIVAR / DESACTIVAR
# ===============================
@login_required
def producto_toggle_activo(request, pk):
    # TODO: pasar a @require_POST cuando el template/JS envíe POST con CSRF.
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = not producto.activo
    producto.save(update_fields=['activo'])
    estado = 'activado' if producto.activo else 'desactivado'
    if _es_ajax(request):
        return JsonResponse({'ok': True, 'nombre': producto.nombre, 'activo': producto.activo})
    messages.success(request, f'Producto "{producto.nombre}" {estado}.')
    return redirect('lista_productos')


# ===============================
# EXPORTAR PRODUCTOS (PDF / EXCEL / IMPRIMIR)
# Mismo diseño que el reporte de Marcas
# ===============================
ENCABEZADOS_EXPORT_PROD = [
    '#', 'Producto', 'Categoría', 'Código', 'Presentaciones', 'Stock total', 'Estado',
]

# Identidad visual
XL_NAVY = "061B3A"
XL_GOLD = "E8A317"
XL_ZEBRA = "EDF0F5"
XL_BORDE = "AEB9CC"
XL_ROJO = "9B1C1C"
XL_FUENTE = "Calibri"

LOGO_ARCHIVO = "logo.20.png"
_LOGO_CACHE = {}


def _reportlab_soporta_esquinas_redondeadas():
    """ROUNDEDCORNERS existe desde reportlab 3.5."""
    try:
        partes = tuple(int(x) for x in re.findall(r'\d+', reportlab.Version)[:2])
        return partes >= (3, 5)
    except Exception:
        return False


def _presentaciones_texto(producto):
    """Lista de textos, uno por presentación: 'Caja (x24) · $50,000'."""
    textos = []
    for pres in producto.presentaciones.all():
        precio = pres.precio_venta or 0
        textos.append(f'{pres.nombre} (x{pres.cantidad}) · ${precio:,.0f}')
    return textos


def _filas_productos():
    """Devuelve las filas (listas) de todos los productos para exportar."""
    productos = (
        Producto.objects
        .select_related('categoria')
        .prefetch_related('presentaciones', 'detalles')
        .annotate(stock_calc=Sum('presentaciones__lotes__stock_actual'))
        .order_by('nombre')
    )
    filas = []
    for i, p in enumerate(productos, start=1):
        detalles = list(p.detalles.all())
        codigo = detalles[0].codigo_barras if detalles and detalles[0].codigo_barras else ''
        filas.append([
            i,
            p.nombre,
            p.categoria.nombre if p.categoria else '—',
            codigo,
            _presentaciones_texto(p),
            p.stock_calc or 0,
            'Activo' if p.activo else 'Inactivo',
        ])
    return filas


def _resumen_productos(filas):
    activos = sum(1 for f in filas if f[6] == 'Activo')
    return len(filas), activos, len(filas) - activos


def _nombre_archivo_prod(extension):
    return f'productos_{timezone.localtime():%Y%m%d_%H%M}.{extension}'


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
def _exportar_excel_productos():
    filas = _filas_productos()
    total, activos, inactivos = _resumen_productos(filas)
    encabezados = ENCABEZADOS_EXPORT_PROD
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    anchos = [10, 36, 24, 20, 46, 16, 16]
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
    ws["C1"] = "Reporte de Productos"
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
        lineas = max(len(fila[4]), 1)
        ws.row_dimensions[r].height = max(26, 20 * lineas + 6)
        bg = "FFFFFF" if k % 2 == 0 else XL_ZEBRA
        activo = fila[6] == "Activo"
        ultima_fila = (k == len(filas) - 1)
        for i, valor in enumerate(fila, start=1):
            if i == 5:
                valor = "\n".join(valor) if valor else "—"
            elif i == 7:
                valor = "●  " + valor
            elif i == 4 and not valor:
                valor = "—"
            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == 2))
            izquierda = i in (2, 3, 5)
            c.alignment = Alignment(
                horizontal="left" if izquierda else "center",
                vertical="center",
                indent=1 if izquierda else 0,
                wrap_text=(i in (2, 5)),
            )
        e = ws.cell(r, 7)
        e.font = Font(name=XL_FUENTE, size=13, bold=True, color=XL_NAVY if activo else XL_ROJO)

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        f"Total: {total} productos   ·   Activos: {activos}   ·   Inactivos: {inactivos}",
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
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_title_rows = f"{fila_enc}:{fila_enc}"
    ws.print_options.horizontalCentered = True

    buffer = BytesIO()
    wb.save(buffer)
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo_prod("xlsx")}"'
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


def _exportar_pdf_productos():
    filas = _filas_productos()
    total, activos, inactivos = _resumen_productos(filas)

    c_navy = colors.HexColor("#" + XL_NAVY)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_rojo = "#" + XL_ROJO
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title="Reporte de productos — CYS Ltda",
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
        _BannerPDF(ancho_util, "Reporte de Productos", _logo_png(300)),
        Spacer(1, 14),
    ]

    data = [[Paragraph(xml_escape(h), st_head) for h in ENCABEZADOS_EXPORT_PROD]]
    for f in filas:
        activo = f[6] == "Activo"
        color = "#" + XL_NAVY if activo else c_rojo
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="9">l</font>'
            f'&nbsp;&nbsp;{f[6]}</font>'
        )
        presentaciones = '<br/>'.join(xml_escape(t) for t in f[4]) or '—'
        data.append([
            Paragraph(str(f[0]), st_centro),
            Paragraph(xml_escape(f[1]), st_bold),
            Paragraph(xml_escape(f[2]), st_izq),
            Paragraph(xml_escape(str(f[3])) or '—', st_centro),
            Paragraph(presentaciones, st_izq),
            Paragraph(str(f[5]), st_centro),
            Paragraph(estado_html, st_estado),
        ])

    if not filas:
        data.append([Paragraph("No hay productos para mostrar.", st_centro)]
                    + [""] * (len(ENCABEZADOS_EXPORT_PROD) - 1))

    anchos = [35, 185, 115, 100, 230, 70, 85]
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
    ]
    if _reportlab_soporta_esquinas_redondeadas():
        estilo.append(("ROUNDEDCORNERS", [10, 10, 10, 10]))
    if not filas:
        estilo.append(("SPAN", (0, 1), (-1, 1)))
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)

    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {total} productos &nbsp;·&nbsp; Activos: {activos} &nbsp;·&nbsp; Inactivos: {inactivos}",
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
    response['Content-Disposition'] = f'attachment; filename="{_nombre_archivo_prod("pdf")}"'
    return response


# ---------- IMPRIMIR ----------
def _exportar_imprimir_productos():
    filas = _filas_productos()

    encabezados_html = ''.join(f'<th>{escape(e)}</th>' for e in ENCABEZADOS_EXPORT_PROD)

    filas_html = ''
    for f in filas:
        presentaciones = '<br>'.join(escape(t) for t in f[4]) or '—'
        filas_html += (
            '<tr>'
            f'<td>{f[0]}</td>'
            f'<td>{escape(f[1])}</td>'
            f'<td>{escape(f[2])}</td>'
            f'<td>{escape(str(f[3]))}</td>'
            f'<td>{presentaciones}</td>'
            f'<td class="num">{f[5]}</td>'
            f'<td>{escape(f[6])}</td>'
            '</tr>'
        )
    if not filas_html:
        filas_html = '<tr><td colspan="7">No hay productos registrados.</td></tr>'

    plural = '' if len(filas) == 1 else 's'
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Reporte de Productos — CYS Ltda</title>
  <style>
    body {{ font-family: Arial, sans-serif; font-size: 12px; color: #111; margin: 24px; }}
    h1 {{ font-size: 20px; margin: 0 0 4px; }}
    .meta {{ color: #555; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #0d2a4f; color: #fff; padding: 6px; text-align: left; }}
    td {{ border-bottom: 1px solid #ccc; padding: 5px 6px; vertical-align: top; }}
    tr:nth-child(even) td {{ background: #f3f6fb; }}
    td.num {{ text-align: right; }}
    @media print {{
      body {{ margin: 0; }}
      th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
  </style>
</head>
<body>
  <h1>Reporte de Productos — CYS Ltda</h1>
  <div class="meta">Generado el {timezone.localdate():%d/%m/%Y} · {len(filas)} producto{plural}</div>
  <table>
    <thead><tr>{encabezados_html}</tr></thead>
    <tbody>{filas_html}</tbody>
  </table>
  <script>window.onload = function () {{ window.print(); }};</script>
</body>
</html>"""
    return HttpResponse(html)


@login_required
def producto_exportar(request, formato):
    exportadores = {
        'excel': _exportar_excel_productos,
        'pdf': _exportar_pdf_productos,
        'imprimir': _exportar_imprimir_productos,
    }
    funcion = exportadores.get(formato)
    if funcion is None:
        raise Http404('Formato de exportación no válido.')

    try:
        return funcion()
    except Exception:
        # El traceback completo queda en la consola de runserver / logs.
        logger.exception('Error exportando productos (%s)', formato)
        if settings.DEBUG:
            raise  # en desarrollo, Django muestra la página de error con el detalle
        messages.error(request, f'No se pudo generar el reporte ({formato}). Revisa los logs.')
        return redirect('lista_productos')