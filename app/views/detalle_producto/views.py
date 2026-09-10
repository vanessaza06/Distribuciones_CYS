from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from app.models import DetalleProducto, Producto
from app.forms import DetalleProductoForm


@login_required
def detalle_producto_lista(request):
    detalles = DetalleProducto.objects.select_related('producto', 'marca').all()
    context = {
        'detalles': detalles,
        'breadcrumb_items': [
            {'nombre': 'Detalle de Producto', 'url': None},
        ],
    }
    return render(request, 'detalle_producto/detalle_producto.html', context)


@login_required
def detalle_producto_crear(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    if request.method == 'POST':
        form = DetalleProductoForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.producto = producto
            detalle.save()
            messages.success(request, 'Detalle de producto registrado.')
        else:
            messages.error(request, 'Revisa los datos: ' + str(form.errors))

    return redirect('productos:producto_detalle', pk=producto_pk)


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
            messages.error(request, 'Revisa los datos del formulario.')

    return redirect('detalle_producto:lista')


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