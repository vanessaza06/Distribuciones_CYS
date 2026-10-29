import json
from datetime import date, datetime, time, timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count

from app.models import Venta, Categoria

DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
MESES       = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
               'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
MESES_LABEL = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
               'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


# ════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════

def _autenticado(request):
    """Misma regla que session_required en ventas."""
    return bool(request.user.is_authenticated or request.session.get('usuario_id'))


def _inicio_dia(d):
    return timezone.make_aware(datetime.combine(d, time.min))


def _ventas_entre(d_ini, d_fin):
    """
    Ventas con fecha entre d_ini y d_fin (ambos inclusive, hora local).
    Usa rangos aware (compatible con MySQL sin tablas de zona horaria).
    """
    return Venta.objects.filter(
        fecha__gte=_inicio_dia(d_ini),
        fecha__lt=_inicio_dia(d_fin + timedelta(days=1)),
    )


def _lunes_de_semana(offset=0):
    hoy = timezone.localdate()
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    return lunes_actual - timedelta(weeks=offset)


def _resumen_dia(dia):
    total = pendiente = 0.0
    n = 0
    for t, s in _ventas_entre(dia, dia).values_list('total_venta', 'saldo_pendiente'):
        total += float(t or 0)
        pendiente += float(s or 0)
        n += 1
    return total, pendiente, n


# ════════════════════════════════════════
# DATOS
# ════════════════════════════════════════

def _datos_semana(offset=0):
    offset = max(0, offset)
    lunes = _lunes_de_semana(offset)
    domingo = lunes + timedelta(days=6)
    hoy = timezone.localdate()
    es_actual = (offset == 0)

    data = [0.0] * 7          # facturado por día
    pendientes = [0.0] * 7    # saldo pendiente por día
    data_count = [0] * 7      # transacciones por día

    filas = _ventas_entre(lunes, domingo).values_list(
        'fecha', 'total_venta', 'saldo_pendiente'
    )
    for fecha, total, saldo in filas:
        idx = (timezone.localtime(fecha).date() - lunes).days
        if 0 <= idx < 7:
            data[idx] += float(total or 0)
            pendientes[idx] += float(saldo or 0)
            data_count[idx] += 1

    # Resumen de "hoy"
    if es_actual:
        i = hoy.weekday()
        total_hoy, pendiente_hoy, ventas_hoy_num = data[i], pendientes[i], data_count[i]
    else:
        total_hoy, pendiente_hoy, ventas_hoy_num = _resumen_dia(hoy)

    dias_con_datos = sum(1 for d in data if d > 0)
    prom_diario = (sum(data) / dias_con_datos) if dias_con_datos else 0

    if any(data):
        idx_mejor = data.index(max(data))
        mejor_dia = DIAS_SEMANA[idx_mejor]
        mejor_dia_val = data[idx_mejor]
    else:
        mejor_dia, mejor_dia_val = '—', 0

    if lunes.month == domingo.month:
        semana_label = f"{lunes.day} - {domingo.day} {MESES_LABEL[lunes.month - 1]}"
    else:
        semana_label = (f"{lunes.day} {MESES_LABEL[lunes.month - 1]} - "
                        f"{domingo.day} {MESES_LABEL[domingo.month - 1]}")

    return {
        'labels':           list(DIAS_SEMANA),
        'data':             data,
        'data_count':       data_count,
        'semana_label':     semana_label,
        'offset':           offset,
        'es_actual':        es_actual,
        'hoy_idx':          hoy.weekday() if es_actual else -1,
        'total_hoy':        total_hoy,
        'pendiente_hoy':    pendiente_hoy,
        'ventas_hoy_num':   ventas_hoy_num,
        'total_semana':     sum(data),
        'pendiente_semana': sum(pendientes),
        'ventas_semana':    sum(data_count),
        'prom_diario':      prom_diario,
        'mejor_dia':        mejor_dia,
        'mejor_dia_val':    mejor_dia_val,
    }


def _datos_mensuales():
    anio = timezone.localdate().year
    data = [0.0] * 12
    data_count = [0] * 12

    filas = _ventas_entre(date(anio, 1, 1), date(anio, 12, 31)).values_list(
        'fecha', 'total_venta'
    )
    for fecha, total in filas:
        mes = timezone.localtime(fecha).month
        data[mes - 1] += float(total or 0)
        data_count[mes - 1] += 1

    meses_con_datos = [i for i, v in enumerate(data) if v > 0]

    idx_mejores, idx_peores = [], []
    if meses_con_datos:
        ordenados = sorted(meses_con_datos, key=lambda i: data[i], reverse=True)
        idx_mejores = ordenados[:3]
        idx_peores = [i for i in ordenados[-3:] if i not in idx_mejores]

    colores = []
    for i in range(12):
        if i in idx_mejores:
            colores.append('rgba(29,158,117,0.85)')
        elif i in idx_peores:
            colores.append('rgba(220,53,69,0.75)')
        else:
            colores.append('rgba(167,139,250,0.75)')

    return {
        'anio':        anio,
        'labels':      list(MESES),
        'data':        data,
        'data_count':  data_count,
        'colores':     colores,
        'idx_mejores': idx_mejores,
        'idx_peores':  idx_peores,
    }


def _resumen_meses(mensual):
    mejores = [(mensual['labels'][i], mensual['data'][i], mensual['data_count'][i])
               for i in mensual['idx_mejores']]
    peores = [(mensual['labels'][i], mensual['data'][i], mensual['data_count'][i])
              for i in mensual['idx_peores']]
    return mejores, peores


def _grupos_categorias():
    categorias = Categoria.objects.annotate(total=Count('productos')).order_by('nombre')
    grupos, actual = [], []
    for cat in categorias:
        actual.append(cat)
        if len(actual) == 6:
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    return grupos


# ════════════════════════════════════════
# VISTAS
# ════════════════════════════════════════

def principal(request):
    if not _autenticado(request):
        return redirect('login')

    semana = _datos_semana(offset=0)
    mensual = _datos_mensuales()
    mejores_meses, peores_meses = _resumen_meses(mensual)

    context = {
        'grupos_categorias': _grupos_categorias(),

        'anio':             mensual['anio'],
        'semana_label':     semana['semana_label'],
        'offset':           semana['offset'],
        'hoy_idx':          semana['hoy_idx'],
        'total_hoy':        semana['total_hoy'],
        'pendiente_hoy':    semana['pendiente_hoy'],
        'ventas_hoy_num':   semana['ventas_hoy_num'],
        'prom_diario':      semana['prom_diario'],
        'mejor_dia':        semana['mejor_dia'],
        'mejor_dia_val':    semana['mejor_dia_val'],

        # Para el HTML con el JS adentro (el que tienes ahora)
        'labels':     json.dumps(semana['labels'], ensure_ascii=False),
        'data':       json.dumps(semana['data']),
        'data_count': json.dumps(semana['data_count']),

        # Para el HTML sin JS (principal.js lo lee con json_script)
        'semana_inicial':   semana,

        'mejores_meses': mejores_meses,
        'peores_meses':  peores_meses,
    }
    return render(request, 'principal/principal.html', context)


def semana_json(request):
    if not _autenticado(request):
        return JsonResponse({'error': 'no autorizado'}, status=403)
    try:
        offset = int(request.GET.get('offset', 0))
    except (TypeError, ValueError):
        offset = 0
    return JsonResponse(_datos_semana(offset))


def meses_json(request):
    if not _autenticado(request):
        return JsonResponse({'error': 'no autorizado'}, status=403)
    return JsonResponse(_datos_mensuales())