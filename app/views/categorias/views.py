from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import Categoria


@login_required
def categorias_lista(request):
    # Lista plana: ya no hay jerarquía padre/hijo
    categorias = Categoria.objects.prefetch_related('productos').all()

    context = {
        'categorias': categorias,
        'total_activas': categorias.filter(activo=True).count(),
        'total_inactivas': categorias.filter(activo=False).count(),
        'breadcrumb_items': [
            {'nombre': 'Categorías', 'url': None},
        ],
    }
    return render(request, 'categorias/categorias.html', context)


@login_required
def categoria_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        descripcion = request.POST.get('descripcion', '').strip()

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        if Categoria.objects.filter(codigo__iexact=codigo).exists():
            messages.error(request, f'⚠️ Ya existe una categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        Categoria.objects.create(
            nombre=nombre,
            codigo=codigo,
            descripcion=descripcion,
        )
        messages.success(request, f'✅ Categoría "{nombre}" creada con éxito.')

    return redirect('categorias_lista')


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip().upper()
        descripcion = request.POST.get('descripcion', '').strip()

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        if Categoria.objects.filter(codigo__iexact=codigo).exclude(pk=pk).exists():
            messages.error(request, f'⚠️ Ya existe otra categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        categoria.nombre = nombre
        categoria.codigo = codigo
        categoria.descripcion = descripcion
        categoria.save()

        messages.success(request, f'✅ Categoría "{nombre}" actualizada correctamente.')

    return redirect('categorias_lista')


@login_required
def categoria_toggle_activo(request, pk):
    """Las categorías no se eliminan: solo se activan o desactivan."""
    categoria = get_object_or_404(Categoria, pk=pk)

    if request.method == 'POST':
        categoria.activo = not categoria.activo
        categoria.save(update_fields=['activo'])

        if categoria.activo:
            messages.success(request, f'✅ Categoría "{categoria.nombre}" activada.')
        else:
            messages.warning(
                request,
                f'⚠️ Categoría "{categoria.nombre}" desactivada. No se elimina para conservar el histórico de productos.'
            )

    return redirect('categorias_lista')