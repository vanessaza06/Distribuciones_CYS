from app.models import ConfiguracionEmpresa

def config_empresa(request):
    try:
        return {'config': ConfiguracionEmpresa.get_config()}
    except Exception:
        return {}

def aside_stats(request):
    # Si tenías código previo aquí para las estadísticas del "aside" (como stock),
    # ponlo dentro de esta función. 
    # Por ahora devolvemos un diccionario vacío para solucionar el error y que tu app funcione:
    try:
        return {
            # 'total_productos': ...,
            # 'stock_critico': ...
        }
    except Exception:
        return {}