from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from app.models import Categoria

@login_required
def categorias_lista(request):
    # Traemos las categorías principales y precargamos las subcategorías y productos
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
    # Ruta corregida: apunta a la subcarpeta 'categorias'
    return render(request, 'categorias/categorias.html', context)


@login_required
def categoria_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        
        # En el HTML personalizaste el nombre del input hidden a 'padre'
        padre_id = request.POST.get('padre') or None

        # Validación 1: Campos vacíos
        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        # Validación 2: Código duplicado
        if Categoria.objects.filter(codigo=codigo).exists():
            messages.error(request, f'⚠️ Ya existe una categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        subcategoria = get_object_or_404(Categoria, pk=padre_id) if padre_id else None
        
        # Creación
        Categoria.objects.create(
            nombre=nombre, 
            codigo=codigo, 
            descripcion=descripcion, 
            subcategoria=subcategoria
        )
        
        tipo = 'Subcategoría' if subcategoria else 'Categoría'
        messages.success(request, f'✅ {tipo} "{nombre}" creada con éxito.')

    return redirect('categorias_lista')


@login_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        padre_id = request.POST.get('padre') or None

        # Validación 1: Campos vacíos
        if not nombre or not codigo:
            messages.error(request, '⚠️ Nombre y código son obligatorios.')
            return redirect('categorias_lista')

        # Validación 2: Código duplicado en otra categoría que no sea la actual
        if Categoria.objects.filter(codigo=codigo).exclude(pk=pk).exists():
            messages.error(request, f'⚠️ Ya existe otra categoría con el código "{codigo}".')
            return redirect('categorias_lista')

        # Actualización
        categoria.nombre = nombre
        categoria.codigo = codigo
        categoria.descripcion = descripcion
        categoria.subcategoria = get_object_or_404(Categoria, pk=padre_id) if padre_id else None
        categoria.save()
        
        messages.success(request, f'✅ Categoría "{nombre}" actualizada correctamente.')

    return redirect('categorias_lista')


@login_required
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        # Validación 1: Si tiene productos o subcategorías, no se borra, se inactiva.
        if categoria.productos.exists() or categoria.subcategorias.exists():
            categoria.activo = False
            categoria.save()
            messages.warning(request, f'⚠️ "{categoria.nombre}" tiene productos o subcategorías asociadas — se desactivó en lugar de eliminarse.')
        else:
            # Si está limpia, se borra definitivamente
            nombre = categoria.nombre
            categoria.delete()
            messages.success(request, f'✅ Categoría "{nombre}" eliminada correctamente.')
            
    return redirect('categorias_lista')

@login_required
def categoria_toggle_activo(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.activo = not categoria.activo
    categoria.save(update_fields=['activo'])
    estado = 'activada' if categoria.activo else 'desactivada'
    messages.success(request, f'Categoría "{categoria.nombre}" {estado}.')
    return redirect('categorias:categoria_list')