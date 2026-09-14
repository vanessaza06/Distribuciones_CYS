from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


def reportes_home(request):
    """
    Vista principal del módulo de reportes.
    Muestra accesos rápidos a los distintos reportes disponibles.
    """
    return render(request, 'reportes/reportes_home.html')


def reporte_ventas(request):
    """
    Reporte de ventas (ajusta el modelo según tu app; aquí es un placeholder
    porque no vi un modelo de Venta en tus rutas actuales).
    """
    context = {
        # 'ventas': Venta.objects.all(),
    }
    return render(request, 'reportes/reporte_ventas.html', context)


def reporte_compras(request):
    """
    Reporte de compras usando el modelo Compra existente.
    """
    # compras = Compra.objects.all().order_by('-fecha')
    context = {
        # 'compras': compras,
    }
    return render(request, 'reportes/reporte_compras.html', context)


def reporte_inventario(request):
    """
    Reporte general de inventario (productos + stock por lote).
    """
    context = {
        # 'lotes': Lote.objects.select_related('presentacion').all(),
    }
    return render(request, 'reportes/reporte_inventario.html', context)


def reporte_stock_bajo(request):
    """
    Reporte de productos con stock por debajo de un umbral mínimo.
    """
    umbral = int(request.GET.get('umbral', 10))
    context = {
        'umbral': umbral,
        # 'productos': DetalleProducto.objects.filter(stock__lt=umbral),
    }
    return render(request, 'reportes/reporte_stock_bajo.html', context)


def reporte_proveedores(request):
    """
    Reporte de desempeño/estado de proveedores.
    """
    context = {
        # 'proveedores': Proveedor.objects.all(),
    }
    return render(request, 'reportes/reporte_proveedores.html', context)


def reporte_exportar(request, tipo):
    """
    Exporta el reporte solicitado en el formato indicado (pdf, excel, csv).
    'tipo' llega desde la URL: /reportes/exportar/<tipo>/
    """
    if tipo == 'pdf':
        # Aquí iría la lógica de generación de PDF (ej. con reportlab o weasyprint)
        return HttpResponse("Exportar a PDF (pendiente de implementar)")
    elif tipo == 'excel':
        # Aquí iría la lógica de generación de Excel (ej. con openpyxl)
        return HttpResponse("Exportar a Excel (pendiente de implementar)")
    else:
        return HttpResponse(f"Tipo de exportación no soportado: {tipo}", status=400)