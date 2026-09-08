from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from app.models import Categoria


#@login_required
def categorias_lista(request):
    categorias = Categoria.objects.prefetch_related(
        'productos', 'subcategorias__productos'
    ).filter(subcategoria__isnull=True)
    todas_cats = Categoria.objects.all()
    context = {
        'categorias': categorias,
        'todas_cats': todas_cats,
        'breadcrumb_items': [
            {'nombre': 'Categorías', 'url': None},
        ],
    }
    return render(request, 'categorias/categorias.html', context)


#@login_required
def categoria_crear(request):
    if request.method == 'POST':
        nombre        = request.POST.get('nombre', '').strip()
        codigo        = request.POST.get('codigo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        subcategoria_id = request.POST.get('subcategoria') or None

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias:lista')

        if Categoria.objects.filter(codigo=codigo).exists():
            messages.error(request, f'⚠️ Ya existe una categoría con el código "{codigo}".')
            return redirect('categorias:lista')

        subcategoria = get_object_or_404(Categoria, pk=subcategoria_id) if subcategoria_id else None
        Categoria.objects.create(nombre=nombre, codigo=codigo, descripcion=descripcion, subcategoria=subcategoria)
        tipo = 'Subcategoría' if subcategoria else 'Categoría'
        messages.success(request, f'✅ {tipo} "{nombre}" creada.')

    return redirect('categorias:lista')


#@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre        = request.POST.get('nombre', '').strip()
        codigo        = request.POST.get('codigo', '').strip()
        descripcion   = request.POST.get('descripcion', '').strip()
        subcategoria_id = request.POST.get('subcategoria') or None

        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias:lista')

        if Categoria.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f'⚠️ Ya existe otra categoría con el código "{codigo}".')
            return redirect('categorias:lista')

        categoria.nombre        = nombre
        categoria.codigo        = codigo
        categoria.descripcion   = descripcion
        categoria.subcategoria  = get_object_or_404(Categoria, pk=subcategoria_id) if subcategoria_id else None
        categoria.save()
        messages.success(request, f'✅ Categoría "{nombre}" actualizada.')

    return redirect('categorias:lista')


#@login_required
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        if categoria.productos.exists() or categoria.subcategorias.exists():
            categoria.activo = False
            categoria.save()
            messages.warning(request, f'⚠️ "{categoria.nombre}" tiene productos o subcategorías asociadas — se desactivó en lugar de eliminarse.')
        else:
            nombre = categoria.nombre
            categoria.delete()
            messages.success(request, f'✅ Categoría "{nombre}" eliminada.')
    return redirect('categorias:lista')