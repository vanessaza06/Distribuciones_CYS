from app.models import PresentacionProducto
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from app.models import Producto



#@login_required
def presentacion_crear(request, producto_pk):
    producto = get_object_or_404(Producto, pk=producto_pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '').strip()
        precio_venta = request.POST.get('precio_venta', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()

        if not nombre or not cantidad or not precio_venta:
            messages.error(request, 'Nombre, cantidad y precio son obligatorios.')
            return redirect('producto_detalle', pk=producto_pk)

        PresentacionProducto.objects.create(
            producto=producto,
            nombre=nombre,
            cantidad=int(cantidad),
            precio_venta=float(precio_venta),
            observaciones=observaciones,
        )
        messages.success(request, f'Presentación "{nombre}" agregada.')

    return redirect('producto_detalle', pk=producto_pk)


#@login_required
def presentacion_editar(request, pk):
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cantidad = request.POST.get('cantidad', '').strip()
        precio_venta = request.POST.get('precio_venta', '').strip()

        if nombre:
            pres.nombre = nombre
        if cantidad:
            pres.cantidad = int(cantidad)
        if precio_venta:
            pres.precio_venta = float(precio_venta)
            pres.lotes.all().update(costo_unitario=pres.precio_venta)

        pres.observaciones = request.POST.get('observaciones', pres.observaciones)
        pres.save()
        messages.success(request, f'Presentación "{pres.nombre}" actualizada.')

    return redirect('producto_detalle', pk=pres.producto_id)


@login_required
def presentacion_toggle_activo(request, pk):
    """Reemplaza a 'presentacion_eliminar': ya no se borra, se activa/desactiva."""
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    pres.activo = not pres.activo
    pres.save(update_fields=['activo'])
    estado = 'activada' if pres.activo else 'desactivada'
    messages.success(request, f'Presentación "{pres.nombre}" {estado}.')
    return redirect('producto_detalle', pk=pres.producto_id)