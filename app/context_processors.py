from django.db.models import Sum
from app.models import ConfiguracionEmpresa, Lote, Categoria


def config_empresa(request):
    try:
        return {'config': ConfiguracionEmpresa.get_config()}
    except Exception:
        return {}


def aside_stats(request):
    try:
        total_stock = Lote.objects.filter(stock_actual__gt=0).aggregate(total=Sum('stock_actual'))['total'] or 0
        stock_criticos = Lote.objects.filter(stock_actual__gt=0, stock_actual__lte=10).count()
        total_cats = Categoria.objects.filter(activo=True).count()
        return {
            'sb_total_stock': total_stock,
            'sb_stock_criticos': stock_criticos,
            'sb_total_cats': total_cats,
        }
    except Exception:
        return {
            'sb_total_stock': 0,
            'sb_stock_criticos': 0,
            'sb_total_cats': 0,
        }
