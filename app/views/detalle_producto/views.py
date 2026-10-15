from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from app.models import Categoria, DetalleProducto, Producto, Marca
from app.forms import DetalleProductoForm
from django.urls import reverse


@login_required
def detalle_producto_lista(request):
    productos_qs = Producto.objects.select_related('categoria__subcategoria')

    con_codigo = productos_qs.filter(detalles__codigo_barras__isnull=False).exclude(detalles__codigo_barras='').distinct().count()

    # Una sola pasada: stock anotado + relaciones precargadas (antes ~6800 consultas)
    productos = list(
        productos_qs
        .annotate(stock_total_anotado=Sum('lotes__stock_actual'))
        .prefetch_related('detalles', 'presentaciones__lotes')
    )
    sin_codigo = len(productos) - con_codigo

    # Se evalúa una vez: la plantilla recorre las categorías dentro de cada modal
    categorias = list(
        Categoria.objects.filter(subcategoria__isnull=True).prefetch_related('subcategorias')
    )

    context = {
        'productos': productos,
        'categorias': categorias,  # solo principales
        'con_codigo': con_codigo,
        'sin_codigo': sin_codigo,
        'marcas': Marca.objects.all(),
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Detalle de Producto', 'url': None},
        ],
    }
    return render(request, 'detalle_producto/detalle_producto.html', context)

@login_required
def detalle_producto_crear_rapido(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    if DetalleProducto.objects.filter(producto=producto).exists():
        return JsonResponse({'ok': False, 'error': 'Este producto ya tiene un detalle.'}, status=400)

    form = DetalleProductoForm(request.POST)
    if not form.is_valid():
        primer_error = next(iter(form.errors.values()))[0]
        return JsonResponse({'ok': False, 'error': primer_error}, status=400)

    detalle = form.save(commit=False)
    detalle.producto = producto
    detalle.save()

    return JsonResponse({
        'ok': True,
        'detalle_pk': detalle.pk,
        'codigo_barras': detalle.codigo_barras,
        'guardar_url': reverse('guardar_codigo', args=[detalle.pk]),
    })

@login_required
def detalle_producto_crear(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)

    if request.method == 'POST':
        if DetalleProducto.objects.filter(producto=producto).exists():
            messages.error(request, 'Este producto ya tiene un detalle registrado.')
            return redirect('producto_detalle', pk=producto_pk)

        form = DetalleProductoForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.producto = producto
            detalle.save()
            messages.success(request, 'Detalle de producto registrado.')
        else:
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')

    return redirect('producto_detalle', pk=producto_pk)


@login_required
def detalle_producto_editar(request, pk):
    detalle = get_object_or_404(DetalleProducto, pk=pk)

    if request.method == 'POST':
        form = DetalleProductoForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
            messages.success(request, 'Detalle de producto actualizado.')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'errores': form.errors}, status=400)
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')

    return redirect('detalle_producto_lista')


@login_required
def guardar_codigo(request, pk):
    """Endpoint rápido solo para el código de barras (ej: desde escaneo con cámara)."""
    detalle = get_object_or_404(DetalleProducto, pk=pk)
    if request.method == 'POST':
        codigo = request.POST.get('codigo_barras', '').strip()
        if not codigo:
            return JsonResponse({'ok': False, 'error': 'Código vacío.'}, status=400)
        if DetalleProducto.objects.filter(codigo_barras=codigo).exclude(pk=detalle.pk).exists():
            return JsonResponse({'ok': False, 'error': 'Ese código ya existe.'}, status=400)

        detalle.codigo_barras = codigo
        detalle.save(update_fields=['codigo_barras'])
        return JsonResponse({'ok': True, 'codigo_barras': detalle.codigo_barras})

    return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)