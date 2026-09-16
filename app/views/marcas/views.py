from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from app.models import Marca  # type: ignore


def lista_marcas(request):
    query = request.GET.get('q', '').strip()
    estado_filtro = request.GET.get('estado', 'todos')

    marcas_todas = Marca.objects.all()
    total_marcas = marcas_todas.count()
    total_activas = marcas_todas.filter(estado='activo').count()
    total_inactivas = marcas_todas.filter(estado='inactivo').count()

    marcas = marcas_todas.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')

    if query:
        marcas = marcas.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    if estado_filtro in ('activo', 'inactivo'):
        marcas = marcas.filter(estado=estado_filtro)

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
        'query': query,
        'estado_filtro': estado_filtro,
    })


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


def eliminar_marca(request, codigo_marca):
    marca = get_object_or_404(Marca, codigo_marca=codigo_marca)

    if request.method == 'POST':
        if marca.productos.exists():
            marca.estado = 'inactivo'
            marca.save()
            messages.success(request, f'La marca "{marca.nombre}" tiene productos asociados, se desactivó en su lugar.')
        else:
            nombre = marca.nombre
            marca.delete()
            messages.success(request, f'La marca "{nombre}" se eliminó correctamente.')

    return redirect('lista_marcas')