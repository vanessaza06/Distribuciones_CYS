from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from app.models import Marca  # type: ignore


def lista_marcas(request):
    marcas = Marca.objects.all().order_by('nombre')
    return render(request, 'marca/marca.html', {'marcas': marcas})


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