from django.db.models import Sum
from app.models import Lote, Producto, Categoria


def aside_stats(request):
    if not request.user.is_authenticated:
        return {}

    # Navegación con htmx (hx-boost): solo se reemplaza #cys-page-wrap y el aside
    # tiene hx-preserve, así que estas estadísticas se descartarían. No se calculan.
    if request.headers.get('HX-Request') == 'true':
        return {}

    total_stock = Lote.objects.aggregate(total=Sum('stock_actual'))['total'] or 0
    total_cats  = Categoria.objects.count()

    # Críticos: productos con 1 a 5 unidades en total (una sola consulta)
    stock_criticos = (
        Producto.objects
        .annotate(total_stock=Sum('presentaciones__lotes__stock_actual'))
        .filter(total_stock__gt=0, total_stock__lte=5)
        .count()
    )

    return {
        'sb_total_stock':    total_stock,
        'sb_stock_criticos': stock_criticos,
        'sb_total_cats':     total_cats,
    }