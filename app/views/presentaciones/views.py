from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from app.models import Producto, PresentacionProducto


def _volver(request, producto_pk):
    """Si el formulario manda 'next' (ej: desde la página de Presentaciones),
    vuelve ahí. Si no, mantiene el comportamiento anterior."""
    destino = request.POST.get('next', '')
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)
    return redirect('producto_detalle', pk=producto_pk)


@login_required
def presentacion_crear(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '').strip()
        precio_venta = request.POST.get('precio_venta', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        if not nombre or not cantidad or not precio_venta:
            messages.error(request, 'Nombre, cantidad y precio son obligatorios.')
            return _volver(request, producto_pk)

        try:
            cantidad_int = int(cantidad)
            precio_float = float(precio_venta)
            if cantidad_int < 0 or precio_float < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Cantidad y precio deben ser números válidos.')
            return _volver(request, producto_pk)

        PresentacionProducto.objects.create(
            producto=producto,
            nombre=nombre,
            cantidad=cantidad_int,
            precio_venta=precio_float,
            observaciones=observaciones,
        )
        messages.success(request, f'Presentación "{nombre}" agregada.')

    return _volver(request, producto_pk)


@login_required
def presentacion_editar(request, pk):
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '').strip()
        precio_venta = request.POST.get('precio_venta', '').strip()

        try:
            nueva_cantidad = int(cantidad) if cantidad else None
            nuevo_precio = float(precio_venta) if precio_venta else None
            if (nueva_cantidad is not None and nueva_cantidad < 0) or \
               (nuevo_precio is not None and nuevo_precio < 0):
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Cantidad y precio deben ser números válidos.')
            return _volver(request, pres.producto_id)

        if nombre:
            pres.nombre = nombre
        if nueva_cantidad is not None:
            pres.cantidad = nueva_cantidad
        if nuevo_precio is not None:
            pres.precio_venta = nuevo_precio
            pres.lotes.all().update(costo_unitario=pres.precio_venta)

        pres.observaciones = request.POST.get('observaciones', pres.observaciones)
        pres.save()
        messages.success(request, f'Presentación "{pres.nombre}" actualizada.')

    return _volver(request, pres.producto_id)


@login_required
def presentacion_toggle_activo(request, pk):
    """Reemplaza a 'presentacion_eliminar': ya no se borra, se activa/desactiva."""
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    pres.activo = not pres.activo
    pres.save(update_fields=['activo'])
    estado = 'activada' if pres.activo else 'desactivada'
    messages.success(request, f'Presentación "{pres.nombre}" {estado}.')
    return _volver(request, pres.producto_id)


@login_required
def presentacion_lista(request):
    presentaciones = (
        PresentacionProducto.objects
        .select_related('producto', 'producto__categoria')
        .order_by('producto__nombre', 'nombre')
    )
    productos = Producto.objects.filter(activo=True).order_by('nombre')

    context = {
        'presentaciones': presentaciones,
        'productos': productos,
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Presentaciones', 'url': None},
        ],
    }
    return render(request, 'presentaciones/presentaciones.html', context)   