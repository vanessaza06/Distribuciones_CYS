"""
Middleware TEMPORAL de diagnóstico de rendimiento (solo con DEBUG=True).
Escribe en perf.log: método, ruta, si fue htmx, código, ms totales,
nº de consultas SQL y ms gastados en SQL, más las 3 consultas más lentas.
Quitar de MIDDLEWARE en settings.py cuando termine el diagnóstico.
"""
import time
from pathlib import Path

from django.conf import settings
from django.db import connection, reset_queries

LOG = Path(settings.BASE_DIR) / 'perf.log'


class PerfLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG or request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        reset_queries()
        t0 = time.perf_counter()
        response = self.get_response(request)
        # Forzar render de respuestas perezosas (TemplateResponse)
        if hasattr(response, 'render') and callable(response.render) and not getattr(response, 'is_rendered', True):
            response.render()
        total_ms = (time.perf_counter() - t0) * 1000

        queries = connection.queries
        sql_ms = sum(float(q.get('time') or 0) for q in queries) * 1000
        lentas = sorted(queries, key=lambda q: float(q.get('time') or 0), reverse=True)[:3]

        lineas = [
            f"{time.strftime('%H:%M:%S')} {request.method} {request.path} "
            f"htmx={'si' if request.headers.get('HX-Request') else 'no'} "
            f"status={response.status_code} total={total_ms:.0f}ms "
            f"queries={len(queries)} sql={sql_ms:.0f}ms"
        ]
        for q in lentas:
            lineas.append(f"    {float(q.get('time') or 0) * 1000:.0f}ms  {q['sql'][:300]}")
        with LOG.open('a', encoding='utf-8') as f:
            f.write('\n'.join(lineas) + '\n')
        return response
