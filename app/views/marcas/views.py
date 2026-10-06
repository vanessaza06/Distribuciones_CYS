"""
Vistas de Marcas (reemplaza tu archivo completo).
Requiere: pip install openpyxl reportlab
"""
import io

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Marca  # type: ignore


# ---------------------------------------------------------------------------
# Filtro compartido: lo usan el listado y las 3 exportaciones,
# así lo que ves en pantalla es exactamente lo que se exporta.
# ---------------------------------------------------------------------------
def _filtrar_marcas(request):
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', 'todos')
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()

    marcas = Marca.objects.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')

    if query:
        marcas = marcas.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    if estado_filtro in ('activo', 'inactivo'):
        marcas = marcas.filter(estado=estado_filtro)

    f_desde = parse_date(desde) if desde else None
    f_hasta = parse_date(hasta) if hasta else None
    if f_desde:
        marcas = marcas.filter(fecha_creacion__gte=f_desde)
    if f_hasta:
        marcas = marcas.filter(fecha_creacion__lte=f_hasta)

    filtros = {
        'q': query,
        'estado': estado_filtro,
        'desde': desde,
        'hasta': hasta,
    }
    return marcas, filtros


# ---------------------------------------------------------------------------
# LISTADO
# ---------------------------------------------------------------------------
def lista_marcas(request):
    marcas, filtros = _filtrar_marcas(request)

    marcas_todas = Marca.objects.all()
    total_marcas = marcas_todas.count()
    total_activas = marcas_todas.filter(estado='activo').count()
    total_inactivas = marcas_todas.filter(estado='inactivo').count()

    paginator = Paginator(marcas, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'marcas/marcas.html', {
        'marcas': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_marcas': total_marcas,
        'total_activas': total_activas,
        'total_inactivas': total_inactivas,
        'query': filtros['q'],
        'estado_filtro': filtros['estado'],
        'desde': filtros['desde'],
        'hasta': filtros['hasta'],
    })


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def crear_marca(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        estado = request.POST.get('estado', 'activo')

        Marca.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            estado=estado
        )
        messages.success(request, f'La marca "{nombre}" se creó correctamente.')
    return redirect('lista_marcas')


def editar_marca(request, codigo_marca):
    marca = get_object_or_404(Marca, codigo_marca=codigo_marca)

    if request.method == 'POST':
        marca.nombre = request.POST.get('nombre')
        marca.descripcion = request.POST.get('descripcion', '')
        marca.estado = request.POST.get('estado', marca.estado)
        marca.save()
        messages.success(request, f'La marca "{marca.nombre}" se actualizó correctamente.')

    return redirect('lista_marcas')


def cambiar_estado_marca(request, codigo_marca):
    marca = get_object_or_404(Marca, codigo_marca=codigo_marca)

    if request.method == 'POST':
        if marca.estado == 'activo':
            marca.estado = 'inactivo'
            messages.success(request, f'La marca "{marca.nombre}" se desactivó correctamente.')
        else:
            marca.estado = 'activo'
            messages.success(request, f'La marca "{marca.nombre}" se activó correctamente.')
        marca.save()

    return redirect('lista_marcas')


# ---------------------------------------------------------------------------
# Utilidades de exportación
# ---------------------------------------------------------------------------
ENCABEZADOS = ["#", "Marca", "Descripción", "Productos", "Estado", "Fecha creación"]


def _filas(qs):
    filas = []
    for i, m in enumerate(qs, start=1):
        filas.append([
            i,
            m.nombre,
            m.descripcion or "—",
            m.total_productos,
            "Activa" if m.estado == "activo" else "Inactiva",
            m.fecha_creacion.strftime("%d/%m/%Y") if m.fecha_creacion else "—",
        ])
    return filas


def _texto_filtros(f):
    partes = []
    if f["q"]:
        partes.append(f"Búsqueda: {f['q']}")
    if f["estado"] in ("activo", "inactivo"):
        partes.append("Estado: " + ("Activa" if f["estado"] == "activo" else "Inactiva"))
    if f["desde"]:
        partes.append(f"Desde: {f['desde']}")
    if f["hasta"]:
        partes.append(f"Hasta: {f['hasta']}")
    return " | ".join(partes) if partes else "Sin filtros"


def _sello():
    return timezone.localtime().strftime('%Y%m%d_%H%M')


# ---------------------------------------------------------------------------
# EXCEL
# ---------------------------------------------------------------------------
def exportar_marcas_excel(request):
    qs, filtros = _filtrar_marcas(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Marcas"

    ws.append(["Reporte de marcas — CYS Ltda"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([_texto_filtros(filtros)])
    ws.append([])
    ws.append(ENCABEZADOS)

    fila_enc = 4
    for c in range(1, len(ENCABEZADOS) + 1):
        cell = ws.cell(row=fila_enc, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0F2036")
        cell.alignment = Alignment(horizontal="center")

    for fila in _filas(qs):
        ws.append(fila)

    for i, ancho in enumerate([6, 28, 45, 12, 12, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho
    for row in ws.iter_rows(min_row=fila_enc + 1):
        for idx in (0, 3, 4, 5):
            row[idx].alignment = Alignment(horizontal="center")

    buffer = io.BytesIO()
    wb.save(buffer)

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="marcas_{_sello()}.xlsx"'
    return resp


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def exportar_marcas_pdf(request):
    qs, filtros = _filtrar_marcas(request)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30,
        title="Reporte de marcas",
    )
    estilos = getSampleStyleSheet()
    celda = estilos["BodyText"]
    celda.fontSize = 9

    elementos = [
        Paragraph("Reporte de marcas — CYS Ltda", estilos["Title"]),
        Paragraph(escape(_texto_filtros(filtros)), estilos["Normal"]),
        Paragraph("Generado: " + timezone.localtime().strftime("%d/%m/%Y %H:%M"), estilos["Normal"]),
        Spacer(1, 14),
    ]

    data = [ENCABEZADOS]
    for f in _filas(qs):
        data.append([
            f[0],
            Paragraph(escape(f[1]), celda),
            Paragraph(escape(f[2]), celda),
            f[3], f[4], f[5],
        ])

    tabla = Table(data, colWidths=[30, 150, 290, 65, 70, 90], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2036")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (5, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2d3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f4f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla)
    doc.build(elementos)

    resp = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="marcas_{_sello()}.pdf"'
    return resp


# ---------------------------------------------------------------------------
# IMPRIMIR
# ---------------------------------------------------------------------------
def exportar_marcas_imprimir(request):
    qs, filtros = _filtrar_marcas(request)

    filas_html = "".join(
        "<tr>"
        f"<td class='c'>{f[0]}</td><td>{escape(f[1])}</td><td>{escape(f[2])}</td>"
        f"<td class='c'>{f[3]}</td><td class='c'>{f[4]}</td><td class='c'>{f[5]}</td>"
        "</tr>"
        for f in _filas(qs)
    ) or "<tr><td colspan='6' class='c'>No hay marcas para mostrar.</td></tr>"

    encabezados = "".join(f"<th>{h}</th>" for h in ENCABEZADOS)
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Reporte de marcas</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; }}
  h1 {{ margin: 0 0 4px; font-size: 20px; }}
  p {{ margin: 2px 0; font-size: 12px; color: #444; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
  th, td {{ border: 1px solid #bbb; padding: 7px 10px; text-align: left; }}
  th {{ background: #0f2036; color: #fff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  td.c {{ text-align: center; }}
  tr:nth-child(even) td {{ background: #f3f5f9; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
</style></head>
<body>
  <h1>Reporte de marcas — CYS Ltda</h1>
  <p>{escape(_texto_filtros(filtros))}</p>
  <p>Generado: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}</p>
  <table><thead><tr>{encabezados}</tr></thead><tbody>{filas_html}</tbody></table>
  <script>window.onload = function () {{ window.print(); }};</script>
</body></html>"""
    return HttpResponse(html)