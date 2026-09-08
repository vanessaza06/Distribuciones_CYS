from django.shortcuts import render, get_object_or_404
from app.models import Marca # type: ignore


def lista_marcas(request):
    marcas = Marca.objects.filter(estado='activo')
    return render(request, 'marca/marca.html', {'marcas': marcas})


def detalle_marca(request, codigo_marca):
    marca = get_object_or_404(Marca, codigo_marca=codigo_marca)
    return render(request, 'marca/marca.html', {'marca': marca})