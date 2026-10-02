from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from app.forms import PresentacionForm
from app.models import PresentacionProducto, Producto


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

    if request.method != 'POST':
        return redirect('producto_detalle', pk=producto_pk)

    form = PresentacionForm(request.POST)

    if not form.is_valid():
        for campo, errores in form.errors.items():
            for error in errores:
                messages.error(request, f'{campo}: {error}')
        return redirect('producto_detalle', pk=producto_pk)

    nombre = form.cleaned_data['nombre'].strip()
    if producto.presentaciones.filter(nombre__iexact=nombre).exists():
        messages.error(request, f'Ya existe una presentación "{nombre}" en este producto.')
        return redirect('producto_detalle', pk=producto_pk)

    presentacion = form.save(commit=False)
    presentacion.producto = producto
    presentacion.save()

    messages.success(request, f'Presentación "{presentacion.nombre}" agregada.')
    return redirect('producto_detalle', pk=producto_pk)


@login_required
def presentacion_editar(request, pk):
    pres = get_object_or_404(PresentacionProducto, pk=pk)

    if request.method != 'POST':
        return redirect('producto_detalle', pk=pres.producto_id)

    form = PresentacionForm(request.POST, instance=pres)

    if not form.is_valid():
        for campo, errores in form.errors.items():
            for error in errores:
                messages.error(request, f'{campo}: {error}')
        return redirect('producto_detalle', pk=pres.producto_id)

    nombre_nuevo = form.cleaned_data['nombre'].strip()
    duplicado = (
        pres.producto.presentaciones
        .filter(nombre__iexact=nombre_nuevo)
        .exclude(pk=pres.pk)
        .exists()
    )
    if duplicado:
        messages.error(request, f'Ya existe otra presentación "{nombre_nuevo}" en este producto.')
        return redirect('producto_detalle', pk=pres.producto_id)

    # OJO: ya NO se copia precio_venta al costo_unitario de los lotes.
    form.save()

    messages.success(request, f'Presentación "{pres.nombre}" actualizada.')
    return redirect('producto_detalle', pk=pres.producto_id)


@login_required
def presentacion_toggle_activo(request, pk):
    # TODO: pasar a @require_POST cuando el template/JS envíe POST con CSRF.
    pres = get_object_or_404(PresentacionProducto, pk=pk)
    pres.activo = not pres.activo
    pres.save(update_fields=['activo'])
    estado = 'activada' if pres.activo else 'desactivada'
    messages.success(request, f'Presentación "{pres.nombre}" {estado}.')
    return redirect('producto_detalle', pk=pres.producto_id)


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