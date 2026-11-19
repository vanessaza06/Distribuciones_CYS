import base64
import io
import json
import logging
import os
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import pixels_to_EMU
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.forms import NuevaCompraForm
from app.models import Compra, DetalleCompra, Proveedor, Usuario as AppUsuario
from app.validators import decimal_estricto, limpiar_texto, validar_referencia

logger = logging.getLogger(__name__)

MESES_ABREV = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
CERO = Decimal('0.00')
ESTADOS_COMPRA = ('pendiente', 'confirmada', 'recibida', 'cancelada')


# ── Utilidades ─────────────────────────────────────────────────────────────────
def cop(valor):
    """Formatea un monto como pesos colombianos: $80.000 (sin decimales, punto de miles)."""
    return f"${int(valor or 0):,}".replace(",", ".")


def _url_lista(proveedor_pk):
    return f"{reverse('lista_compras')}?proveedor={proveedor_pk}"


def _mensajes_validacion(request, error):
    """Muestra como mensajes los textos de un ValidationError de Django."""
    for texto in error.messages:
        messages.error(request, texto)


def _usuario_de_compra(user):
    """Resuelve la instancia de app.Usuario que firma la compra (o None si no existe)."""
    if isinstance(user, AppUsuario):
        return user
    ident = getattr(user, 'identificacion', None) or getattr(user, 'username', '')
    correo = getattr(user, 'email', '')
    usuario = (
        (AppUsuario.objects.filter(documento=ident).first() if ident else None)
        or (AppUsuario.objects.filter(correo=correo).first() if correo else None)
    )
    if not usuario and ident:
        usuario, _ = AppUsuario.objects.get_or_create(
            documento=str(ident),
            defaults={
                'nombre': getattr(user, 'first_name', '') or getattr(user, 'username', 'Usuario'),
                'apellido': getattr(user, 'last_name', '') or '',
                'correo': correo or f"{ident}@cys.com",
                'tipo_identificacion': 'CC',
                'rol': getattr(user, 'rol', 'empleado') or 'empleado',
                'estado': 'activo',
            },
        )
    return usuario


def _proveedores_disponibles():
    activos = list(Proveedor.objects.filter(estado='activo').order_by('nombre_empresa'))
    return activos if activos else list(Proveedor.objects.order_by('nombre_empresa'))


def _resolver_proveedor(request, disponibles):
    """Proveedor activo: parámetro GET -> sesión -> primero disponible."""
    candidatos = [request.GET.get('proveedor'), request.session.get('proveedor_id')]
    proveedor = None
    for pk in candidatos:
        if pk:
            pk_str = str(pk).strip()
            for p in disponibles:
                if str(p.pk) == pk_str:
                    proveedor = p
                    break
            if not proveedor:
                proveedor = Proveedor.objects.filter(pk=pk_str).first()
            if proveedor:
                break
    else:
        proveedor = disponibles[0] if disponibles else None
    if proveedor:
        request.session['proveedor_id'] = str(proveedor.pk)
    return proveedor


def _procesar_nueva_compra(request, form, proveedor_activo):
    """
    Registra la compra del modal. Devuelve la URL de redirección si todo salió bien
    o None si hay que volver a mostrar la página con los errores.
    """
    if not form.is_valid():
        for campo, errores in form.errors.items():
            etiqueta = form.fields[campo].label if campo in form.fields else ''
            texto = ", ".join(errores)
            messages.error(request, f'{etiqueta}: {texto}' if etiqueta else texto)
        return None

    datos = form.cleaned_data
    proveedor = datos.get('proveedor') or proveedor_activo
    if not proveedor:
        messages.error(request, 'Debe seleccionar un proveedor válido para registrar la compra.')
        return None

    usuario = _usuario_de_compra(request.user)
    if not usuario:
        messages.error(request, 'No se pudo identificar al usuario que registra la compra.')
        return None

    try:
        compra = Compra.registrar(
            proveedor=proveedor,
            usuario=usuario,
            producto=datos['producto'],
            lote=datos.get('lote'),
            cantidad=datos['cantidad'],
            precio_unitario=datos['precio_unitario'],
            estado=datos.get('estado') or 'recibida',
            monto_pagado=datos.get('monto_pagado') or CERO,
            metodo_pago=datos.get('metodo_pago') or 'efectivo',
            referencia=datos.get('numero_factura') or '',
        )
    except ValidationError as e:
        _mensajes_validacion(request, e)
        return None
    except Exception:
        logger.exception("Error al registrar compra")
        messages.error(request, 'Ocurrió un error al guardar la compra. Intenta de nuevo.')
        return None

    request.session['proveedor_id'] = str(proveedor.pk)
    messages.success(
        request,
        f'✅ Compra #{compra.codigo_compra} registrada: {datos["cantidad"]} und. de '
        f'"{datos["producto"].nombre}" ({cop(compra.valor)}) para {proveedor.nombre_empresa}.'
    )
    return _url_lista(proveedor.pk)


def _ultimos_meses(cantidad=6):
    """Lista de (año, mes) de los últimos `cantidad` meses, del más antiguo al actual."""
    hoy = timezone.localdate()
    indice = hoy.year * 12 + (hoy.month - 1)
    return [divmod(i, 12) for i in range(indice - cantidad + 1, indice + 1)]


def _estadisticas(compras_validas):
    """KPIs y datos de gráficos de las compras (no canceladas) de un proveedor."""
    hoy = timezone.localdate()
    del_mes = compras_validas.filter(fecha__year=hoy.year, fecha__month=hoy.month)

    top = list(
        DetalleCompra.objects.filter(compra__in=compras_validas, producto__isnull=False)
        .values('producto__nombre')
        .annotate(total_und=Sum('cantidad'))
        .order_by('-total_und')[:5]
    )

    meses = _ultimos_meses(6)
    totales = {m: CERO for m in meses}
    desde = timezone.make_aware(datetime(meses[0][0], meses[0][1] + 1, 1))
    for fecha, valor in compras_validas.filter(fecha__gte=desde).values_list('fecha', 'valor'):
        local = timezone.localtime(fecha)
        clave = (local.year, local.month - 1)
        if clave in totales:
            totales[clave] += valor

    agg_totales = compras_validas.aggregate(
        s=Sum('valor'),
        g=Sum(F('valor') - F('saldo')),
    )
    agg_mes = del_mes.aggregate(
        c=Count('codigo_compra'),
        s=Sum('valor'),
    )

    return {
        'subtotal_compras': agg_totales['s'] or CERO,
        'total_gastado': agg_totales['g'] or CERO,
        'count_mes': agg_mes['c'] or 0,
        'total_mes': agg_mes['s'] or CERO,
        'producto_top': top[0] if top else None,
        'meses_labels_json': json.dumps([f"{MESES_ABREV[m]} {y}" for y, m in meses]),
        'meses_data_json': json.dumps([float(totales[k]) for k in meses]),
        'productos_labels_json': json.dumps([p['producto__nombre'] for p in top]),
        'productos_data_json': json.dumps([int(p['total_und']) for p in top]),
    }


# ---------------------------------------------------------------------------
# Filtro compartido: lo usan el listado y las 3 exportaciones,
# así lo que ves en pantalla es exactamente lo que se exporta.
# Parámetros GET: q, estado, desde, hasta (+ proveedor)
# ---------------------------------------------------------------------------
def _filtrar_compras(request, proveedor):
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', 'todos')
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()

    if proveedor:
        compras = Compra.objects.filter(proveedor=proveedor)
    else:
        compras = Compra.objects.none()

    compras = (
        compras.select_related('proveedor', 'usuario')
        .prefetch_related('detalles__producto', 'detalles__lote')
        .order_by('-fecha', '-codigo_compra')
    )

    if query:
        condicion = (
            Q(detalles__producto__nombre__icontains=query)
            | Q(usuario__nombre__icontains=query)
        )
        if query.lstrip('#').isdigit():
            condicion |= Q(codigo_compra=int(query.lstrip('#')))
        compras = compras.filter(condicion).distinct()

    if estado_filtro in ESTADOS_COMPRA:
        compras = compras.filter(estado=estado_filtro)

    f_desde = parse_date(desde) if desde else None
    f_hasta = parse_date(hasta) if hasta else None
    if f_desde:
        compras = compras.filter(fecha__date__gte=f_desde)
    if f_hasta:
        compras = compras.filter(fecha__date__lte=f_hasta)

    filtros = {
        'q': query,
        'estado': estado_filtro,
        'desde': desde,
        'hasta': hasta,
        'proveedor': proveedor.nombre_empresa if proveedor else '',
    }
    return compras, filtros


# ── LISTADO Y REGISTRO DE COMPRAS (también atiende ?export=excel|pdf|imprimir) ──
@login_required
def lista_compras(request):
    """Historial de compras por proveedor, KPIs, gráficos y registro de nuevas compras."""
    disponibles = _proveedores_disponibles()
    proveedor = _resolver_proveedor(request, disponibles)

    # ---- Exportación: el JS llama a esta misma URL con ?export=... ----
    tipo = request.GET.get('export')
    if tipo == 'excel':
        return exportar_compras_excel(request, proveedor)
    if tipo == 'pdf':
        return exportar_compras_pdf(request, proveedor)
    if tipo == 'imprimir':
        return exportar_compras_imprimir(request, proveedor)

    # ---- Registro de nueva compra ----
    form = NuevaCompraForm()
    if request.method == 'POST' and 'cantidad' in request.POST:
        form = NuevaCompraForm(request.POST)
        destino = _procesar_nueva_compra(request, form, proveedor)
        if destino:
            return redirect(destino)

    # ---- Listado normal ----
    # (la búsqueda y paginación de la tabla las hace DataTables en el navegador)
    compras_qs, filtros = _filtrar_compras(request, proveedor)
    compras = list(compras_qs)

    if proveedor:
        todas = Compra.objects.filter(proveedor=proveedor)
        estadisticas = _estadisticas(todas.exclude(estado='cancelada'))
    else:
        estadisticas = _estadisticas(Compra.objects.none())

    context = {
        'proveedor': proveedor,
        'todos_proveedores': disponibles,
        'compras': compras,
        'compras_count': len(compras),
        'form': form,
        'breadcrumb_items': [{'nombre': 'Compras', 'url': None}],
        **estadisticas,
    }
    return render(request, 'compras/compras.html', context)


# ── CAMBIO DE ESTADO ───────────────────────────────────────────────────────────
@login_required
@require_POST
def cambiar_estado_compra(request, id=None):
    """pendiente -> confirmada/cancelada; confirmada -> recibida/cancelada."""
    compra = get_object_or_404(Compra, pk=id or request.POST.get('compra_id'))
    nuevo_estado = request.POST.get('estado')

    try:
        compra.cambiar_estado(nuevo_estado)
    except ValidationError as e:
        _mensajes_validacion(request, e)
    else:
        messages.success(
            request,
            f'✅ Estado de la compra #{compra.codigo_compra} actualizado a "{compra.get_estado_display()}".'
        )

    destino = request.POST.get('next') or _url_lista(compra.proveedor_id)
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = _url_lista(compra.proveedor_id)
    return redirect(destino)


# ── REGISTRO DE PAGO / ABONO ───────────────────────────────────────────────────
@login_required
@require_POST
def registrar_pago_compra(request, id=None):
    """Registra un abono, reduce el saldo y deja el movimiento en MetodoPago."""
    compra = get_object_or_404(Compra, pk=id or request.POST.get('compra_id'))

    destino = request.POST.get('next') or _url_lista(compra.proveedor_id)
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = _url_lista(compra.proveedor_id)

    if compra.saldo <= CERO:
        messages.warning(request, f'⚠️ La compra #{compra.codigo_compra} ya se encuentra completamente pagada.')
        return redirect(destino)

    try:
        monto = decimal_estricto(request.POST.get('monto_pagado'), minimo=Decimal('0.01'))
    except ValueError as e:
        messages.error(request, f'⚠️ Monto del abono: {e}')
        return redirect(destino)

    referencia = limpiar_texto(request.POST.get('numero_factura'))
    error_ref = validar_referencia(referencia)
    if error_ref:
        messages.error(request, f'⚠️ {error_ref}')
        return redirect(destino)

    metodo = request.POST.get('metodo_pago') or 'efectivo'
    if metodo not in Compra.METODOS_PAGO:
        messages.error(request, '⚠️ Selecciona un método de pago válido.')
        return redirect(destino)

    if monto > compra.saldo:
        messages.error(request, f'⚠️ El abono ({cop(monto)}) no puede superar el saldo pendiente ({cop(compra.saldo)}).')
        return redirect(destino)

    fecha_pago = parse_datetime(request.POST.get('fecha_pago') or '')
    if fecha_pago and timezone.is_naive(fecha_pago):
        fecha_pago = timezone.make_aware(fecha_pago)

    try:
        compra.registrar_pago(
            monto,
            metodo=metodo,
            referencia=referencia,
            fecha=fecha_pago,
        )
    except ValidationError as e:
        _mensajes_validacion(request, e)
        return redirect(destino)

    if compra.saldo <= CERO:
        messages.success(
            request,
            f'✅ Pago de {cop(monto)} registrado. La compra #{compra.codigo_compra} quedó completamente PAGADA.'
        )
    else:
        messages.success(
            request,
            f'✅ Abono de {cop(monto)} registrado en la compra #{compra.codigo_compra}. '
            f'Saldo pendiente: {cop(compra.saldo)}.'
        )
    return redirect(destino)


# ── DETALLE ────────────────────────────────────────────────────────────────────
@login_required
def detalle_compra(request, id):
    """Detalle completo de una compra."""
    compra = get_object_or_404(
        Compra.objects.select_related('proveedor', 'usuario')
        .prefetch_related('detalles__producto__categoria', 'detalles__lote'),
        pk=id,
    )
    url_lista = _url_lista(compra.proveedor_id)
    context = {
        'compra': compra,
        'proveedor': compra.proveedor,
        'pagos': compra.metodopago_set.order_by('-fecha', '-codigo_metodo'),
        'url_lista': url_lista,
        'breadcrumb_items': [
            {'nombre': 'Compras', 'url': url_lista},
            {'nombre': f'Compra #{compra.codigo_compra}', 'url': None},
        ],
    }
    return render(request, 'compras/detalle_compra.html', context)


@login_required
def ultima_compra(request):
    """Redirige al detalle de la compra más reciente."""
    ultima = Compra.objects.order_by('-fecha', '-codigo_compra').first()
    if ultima:
        return redirect('detalle_compra', id=ultima.pk)
    messages.info(request, 'Aún no hay compras registradas.')
    return redirect('lista_compras')


# ===========================================================================
# EXPORTACIONES (mismo diseño del reporte de Marcas)
# ===========================================================================

# ---------------------------------------------------------------------------
# Identidad visual (colores tomados del logo de CYS Ltda)
# ---------------------------------------------------------------------------
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
XL_VERDE = "1E8449"
XL_AMBAR = "B7791F"
XL_FUENTE = "Calibri"

# Color del texto de estado según el estado de la compra
COLOR_ESTADO = {
    'recibida': XL_VERDE,
    'confirmada': XL_NAVY,
    'pendiente': XL_AMBAR,
    'cancelada': XL_ROJO,
}

LOGO_ARCHIVO = "logo.20.png"   # <- nombre de tu logo dentro de la carpeta static
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


# ---------------------------------------------------------------------------
# Datos del reporte
# Columnas visibles: #, Fecha, Productos, Cantidad, Valor, Pagado, Saldo, Estado
# Cada fila lleva al final (índice 8) el código de estado crudo.
# ---------------------------------------------------------------------------
IDX_ESTADO = 7


def _encabezados():
    return ["#", "Fecha", "Productos", "Cantidad", "Valor total", "Pagado", "Saldo", "Estado"]


def _filas(qs):
    filas = []
    for c in qs:
        detalles = list(c.detalles.all())
        nombres = []
        cantidad = 0
        for d in detalles:
            nombre = d.producto.nombre if getattr(d, 'producto', None) else "Producto eliminado"
            nombres.append(f"{nombre} (x{d.cantidad})")
            cantidad += d.cantidad or 0
        valor = c.valor or CERO
        saldo = c.saldo or CERO
        fecha = timezone.localtime(c.fecha).strftime("%d/%m/%Y %H:%M") if c.fecha else "—"
        filas.append([
            c.codigo_compra,
            fecha,
            ", ".join(nombres) or "—",
            cantidad,
            valor,
            valor - saldo,
            saldo,
            c.get_estado_display(),
            c.estado,          # código crudo (no se muestra)
        ])
    return filas


def _texto_filtros(f):
    partes = []
    if f.get("proveedor"):
        partes.append(f"Proveedor: {f['proveedor']}")
    if f["q"]:
        partes.append(f"Búsqueda: {f['q']}")
    if f["estado"] in ESTADOS_COMPRA:
        partes.append(f"Estado: {f['estado'].capitalize()}")
    if f["desde"]:
        partes.append(f"Desde: {f['desde']}")
    if f["hasta"]:
        partes.append(f"Hasta: {f['hasta']}")
    return " | ".join(partes) if partes else "Sin filtros"


def _sello():
    return timezone.localtime().strftime('%Y%m%d_%H%M')


def _resumen(filas):
    """(n compras, valor total, pagado, saldo). Las canceladas no suman a los montos."""
    validas = [f for f in filas if f[8] != 'cancelada']
    valor = sum((f[4] for f in validas), CERO)
    pagado = sum((f[5] for f in validas), CERO)
    saldo = sum((f[6] for f in validas), CERO)
    return len(filas), valor, pagado, saldo


def _texto_totales(filas):
    n, valor, pagado, saldo = _resumen(filas)
    return (f"Total: {n} compras   ·   Valor: {cop(valor)}   ·   "
            f"Pagado: {cop(pagado)}   ·   Saldo: {cop(saldo)}")


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


def exportar_compras_excel(request, proveedor):
    qs, filtros = _filtrar_compras(request, proveedor)
    filas = _filas(qs)

    encabezados = _encabezados()
    n = len(encabezados)
    ultima = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Compras"
    ws.sheet_properties.tabColor = XL_NAVY
    ws.sheet_view.showGridLines = False

    anchos = [10, 20, 50, 12, 18, 18, 18, 18]
    for idx, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = ancho

    # ---------- Banner (filas 1-3, fondo blanco) ----------
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
    ws["C1"] = "Reporte de Compras"
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

    # ---------- Encabezado de tabla (fila 6) ----------
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
        for i, valor in enumerate(fila[:n], start=1):
            if i == IDX_ESTADO + 1:
                valor = "●  " + valor
            if i in (5, 6, 7):
                valor = float(valor)
            c = ws.cell(r, i, valor)
            c.fill = _xl_fill(bg)
            c.border = Border(
                left=vertical,
                right=vertical if i == n else None,
                bottom=Side(style="thin", color=XL_NAVY) if ultima_fila else None,
            )
            c.font = Font(name=XL_FUENTE, size=13, color="1F2937", bold=(i == 3))
            izquierda = i == 3
            derecha = i in (5, 6, 7)
            c.alignment = Alignment(
                horizontal="left" if izquierda else ("right" if derecha else "center"),
                vertical="center",
                indent=1 if (izquierda or derecha) else 0,
                wrap_text=(i == 3),
            )
            if derecha:
                c.number_format = '"$"#,##0'
        # Estado con color
        e = ws.cell(r, IDX_ESTADO + 1)
        e.font = Font(name=XL_FUENTE, size=13, bold=True,
                      color=COLOR_ESTADO.get(fila[8], XL_NAVY))

    # ---------- Pie ----------
    r = fila_enc + len(filas) + 1
    ws.row_dimensions[r].height = 8
    textos_pie = [
        _texto_totales(filas),
        f"{_texto_filtros(filtros)}   ·   Generado el {timezone.localtime():%d/%m/%Y %H:%M}",
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

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="compras_{_sello()}.xlsx"'
    return resp


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
class _BannerPDF(Flowable):
    """Banner: logo circular | divisor dorado | título | lema | barrita dorada."""

    def __init__(self, ancho, logo_bytes=None, titulo="Reporte de Compras"):
        super().__init__()
        self.width = ancho
        self.height = 96
        self.logo_bytes = logo_bytes
        self.titulo = titulo

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


def exportar_compras_pdf(request, proveedor):
    qs, filtros = _filtrar_compras(request, proveedor)
    filas = _filas(qs)
    encabezados = _encabezados()

    c_navy = colors.HexColor("#" + XL_NAVY)
    c_borde = colors.HexColor("#" + XL_BORDE)
    c_zebra = colors.HexColor("#" + XL_ZEBRA)
    c_texto = colors.HexColor("#1F2937")

    pagina = landscape(A4)
    margen = 30
    ancho_util = pagina[0] - 2 * margen

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=margen, rightMargin=margen, topMargin=22, bottomMargin=40,
        title="Reporte de compras — CYS Ltda",
    )

    estilos = getSampleStyleSheet()
    st_base = ParagraphStyle("base", parent=estilos["BodyText"], fontName="Helvetica",
                             fontSize=10, leading=12.5, textColor=c_texto)
    st_prod = ParagraphStyle("prod", parent=st_base, fontName="Helvetica-Bold",
                             textColor=c_navy, leftIndent=8)
    st_centro = ParagraphStyle("centro", parent=st_base, alignment=TA_CENTER)
    st_der = ParagraphStyle("der", parent=st_base, alignment=TA_RIGHT, rightIndent=8)
    st_estado = ParagraphStyle("estado", parent=st_base, alignment=TA_CENTER,
                               fontName="Helvetica-Bold")
    st_head = ParagraphStyle("head", parent=st_base, fontName="Helvetica-Bold", fontSize=12,
                             textColor=colors.white, alignment=TA_CENTER, leading=15)
    st_meta = ParagraphStyle("meta", parent=st_base, fontSize=8.5,
                             textColor=colors.HexColor("#6B7280"), leading=12)
    st_tot = ParagraphStyle("tot", parent=st_base, fontName="Helvetica-Bold",
                            textColor=c_navy, fontSize=10.5)

    elementos = [
        _BannerPDF(ancho_util, _logo_png(300)),
        Spacer(1, 14),
    ]

    data = [[Paragraph(h, st_head) for h in encabezados]]
    for f in filas:
        color = "#" + COLOR_ESTADO.get(f[8], XL_NAVY)
        estado_html = (
            f'<font color="{color}"><font name="ZapfDingbats" size="9">l</font>'
            f'&nbsp;&nbsp;{escape(f[7])}</font>'
        )
        data.append([
            Paragraph(str(f[0]), st_centro),
            Paragraph(escape(f[1]), st_centro),
            Paragraph(escape(f[2]), st_prod),
            Paragraph(str(f[3]), st_centro),
            Paragraph(cop(f[4]), st_der),
            Paragraph(cop(f[5]), st_der),
            Paragraph(cop(f[6]), st_der),
            Paragraph(estado_html, st_estado),
        ])

    if not filas:
        data.append([Paragraph("No hay compras para mostrar.", st_centro)]
                    + [""] * (len(encabezados) - 1))

    anchos = [40, 85, 230, 60, 85, 85, 85, 95]
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

    n, valor, pagado, saldo = _resumen(filas)
    elementos += [
        Spacer(1, 10),
        Paragraph(
            f"Total: {n} compras &nbsp;·&nbsp; Valor: {cop(valor)} &nbsp;·&nbsp; "
            f"Pagado: {cop(pagado)} &nbsp;·&nbsp; Saldo: {cop(saldo)}",
            st_tot),
        Spacer(1, 2),
        Paragraph(
            escape(_texto_filtros(filtros)) + " &nbsp;·&nbsp; Generado el "
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
    resp["Content-Disposition"] = f'attachment; filename="compras_{_sello()}.pdf"'
    return resp


# ---------------------------------------------------------------------------
# IMPRIMIR
# ---------------------------------------------------------------------------
def exportar_compras_imprimir(request, proveedor):
    qs, filtros = _filtrar_compras(request, proveedor)
    filas = _filas(qs)
    n, valor, pagado, saldo = _resumen(filas)
    encab = _encabezados()

    clase_estado = {'recibida': 'ok', 'confirmada': 'nv', 'pendiente': 'pe', 'cancelada': 'no'}

    def fila_html(f):
        clase = clase_estado.get(f[8], 'nv')
        return (
            "<tr>"
            f"<td class='c'>{f[0]}</td>"
            f"<td class='c'>{escape(f[1])}</td>"
            f"<td class='prod'>{escape(f[2])}</td>"
            f"<td class='c'>{f[3]}</td>"
            f"<td class='d'>{cop(f[4])}</td>"
            f"<td class='d'>{cop(f[5])}</td>"
            f"<td class='d'>{cop(f[6])}</td>"
            f"<td class='c {clase}'>{escape(f[7])}</td>"
            "</tr>"
        )

    filas_html = "".join(fila_html(f) for f in filas) or \
        f"<tr><td colspan='{len(encab)}' class='c'>No hay compras para mostrar.</td></tr>"
    encabezados = "".join(f"<th>{h}</th>" for h in encab)

    logo = _logo_png(300)
    logo_html = ""
    if logo:
        logo_html = f"<img class='logo' src='data:image/png;base64,{base64.b64encode(logo).decode()}' alt='CYS Ltda'>"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Reporte de compras — CYS Ltda</title>
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
  td.d {{ text-align: right; white-space: nowrap; }}
  td.prod {{ font-weight: bold; color: #{NAVY}; }}
  td.ok {{ color: #{VERDE}; font-weight: bold; }}
  td.nv {{ color: #{NAVY}; font-weight: bold; }}
  td.pe {{ color: #B7791F; font-weight: bold; }}
  td.no {{ color: #{ROJO}; font-weight: bold; }}
  tr:nth-child(even) td {{ background: #{ZEBRA}; }}
  .total {{ margin-top: 8px; background: #{CREAM}; border-top: 3px solid #{GOLD}; padding: 9px 14px;
           text-align: right; font-weight: bold; color: #{NAVY}; font-size: 13px; }}
  .pie {{ margin-top: 14px; font-size: 10px; color: #888; text-align: center; }}
</style></head>
<body>
  <div class="banner">
    {logo_html}
    <div><h1>CYS LTDA · DISTRIBUCIONES</h1><p>Reporte de compras</p></div>
  </div>
  <div class="meta">{escape(_texto_filtros(filtros))} &nbsp;·&nbsp; Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</div>
  <table><thead><tr>{encabezados}</tr></thead><tbody>{filas_html}</tbody></table>
  <div class="total">Total: {n} compras &nbsp;·&nbsp; Valor: {cop(valor)} &nbsp;·&nbsp; Pagado: {cop(pagado)} &nbsp;·&nbsp; Saldo: {cop(saldo)}</div>
  <div class="pie">CYS Ltda · Distribuciones</div>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)