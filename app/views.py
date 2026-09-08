from django.shortcuts import render

def inicio(request):
    """Página principal / Tablero de Control."""
    return render(request, 'partials/base.html')
