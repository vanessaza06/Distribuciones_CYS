import json
from datetime import date, datetime, time, timedelta

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Value, IntegerField
from django.db.models.functions import Coalesce

from app.models import Venta, Categoria, DetalleVenta, Producto, DetalleProducto

DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
MESES       = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
               'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
MESES_LABEL = ['ene', 'feb', 'mar', 'abr', 'may', 'jun',
               'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

# Umbrales del tablero (stock crítico igual que Producto.stock_critico)
STOCK_CRITICO_MAX = 5
DIAS_POR_VENCER   = 30
LIMITE_LISTA      = 5

# Medios digitales que se agrupan en "Transferencias"
# (clave, nombre visible, ícono Bootstrap)
MEDIOS_DIGITALES = [
    ('transferencia', 'Transferencia', 'bi-bank'),
    ('nequi',         'Nequi',         'bi-phone'),
    ('daviplata',     'Daviplata',     'bi-wallet2'),
    ('tarjeta',       'Tarjeta',       'bi-credit-card-2-front'),
    ('otro',          'Otros',         'bi-three-dots'),
]


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


def _plural(n, singular, plural):
    return singular if n == 1 else plural


def _pct(parte, total):
    return round(parte * 100 / total) if total else 0


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


# ── Pestaña 1: más vendidos de la semana ──
def _mas_vendidos(limite=LIMITE_LISTA):
    lunes = _lunes_de_semana(0)
    detalles = (
        DetalleVenta.objects.filter(
            venta__fecha__gte=_inicio_dia(lunes),
            venta__fecha__lt=_inicio_dia(lunes + timedelta(days=7)),
        )
        .select_related('producto', 'presentacion__producto')
    )

    acumulado = {}
    for d in detalles:
        prod = d.producto or (d.presentacion.producto if d.presentacion else None)
        nombre = prod.nombre if prod else 'Producto'
        fila = acumulado.setdefault(nombre, {'cantidad': 0, 'ingreso': 0.0})
        fila['cantidad'] += d.cantidad or 0
        fila['ingreso'] += float(d.subtotal or 0)

    total_unidades = sum(f['cantidad'] for f in acumulado.values())
    total_ingresos = sum(f['ingreso'] for f in acumulado.values())

    ranking = sorted(acumulado.items(), key=lambda kv: kv[1]['cantidad'], reverse=True)[:limite]
    maximo = ranking[0][1]['cantidad'] if ranking else 0

    lista = [
        {
            'nombre':   nombre,
            'cantidad': fila['cantidad'],
            'ingreso':  fila['ingreso'],
            'maximo':   maximo,
            'pct':      _pct(fila['cantidad'], total_unidades),
        }
        for nombre, fila in ranking
    ]
    return {
        'lista':     lista,
        'unidades':  total_unidades,
        'ingresos':  total_ingresos,
        'productos': len(acumulado),
    }


# ── Pestaña 2: stock bajo ──
def _stock_bajo(limite=LIMITE_LISTA):
    filas = list(
        Producto.objects.filter(activo=True)
        .select_related('categoria')
        .annotate(stock=Coalesce(Sum('lotes__stock_actual'), Value(0),
                                 output_field=IntegerField()))
        .filter(stock__lte=STOCK_CRITICO_MAX)
        .order_by('stock', 'nombre')
    )

    agotados = sum(1 for p in filas if p.stock <= 0)
    criticos = len(filas) - agotados

    lista = [
        {
            'nombre':    p.nombre,
            'categoria': p.categoria.nombre if p.categoria else 'Sin categoría',
            'stock':     p.stock,
            'nivel':     'agotado' if p.stock <= 0 else 'critico',
            # 5 segmentos: encendidos = unidades que quedan
            'segmentos': [i < p.stock for i in range(STOCK_CRITICO_MAX)],
        }
        for p in filas[:limite]
    ]
    return {
        'lista':    lista,
        'total':    len(filas),
        'extra':    max(0, len(filas) - limite),
        'agotados': agotados,
        'criticos': criticos,
        'umbral':   STOCK_CRITICO_MAX,
    }


# ── Pestaña 3: por vencer (solo productos que aún tienen stock) ──
def _detalles_con_stock():
    return (
        DetalleProducto.objects.filter(producto__activo=True)
        .select_related('producto')
        .annotate(stock=Coalesce(Sum('producto__lotes__stock_actual'), Value(0),
                                 output_field=IntegerField()))
        .filter(stock__gt=0)
    )


def _nivel_vencimiento(dias):
    if dias < 0:
        return 'vencido', f"Vencido hace {-dias} {_plural(-dias, 'día', 'días')}"
    if dias == 0:
        return 'urgente', 'Vence hoy'
    nivel = 'urgente' if dias <= 7 else 'proximo'
    return nivel, f"Vence en {dias} {_plural(dias, 'día', 'días')}"


def _por_vencer(limite=LIMITE_LISTA):
    hoy = timezone.localdate()
    fecha_tope = hoy + timedelta(days=DIAS_POR_VENCER)

    detalles = (
        _detalles_con_stock()
        .filter(fecha_vencimiento__lte=fecha_tope)
        .order_by('fecha_vencimiento')
    )

    vistos, filas = set(), []
    for d in detalles:
        if d.producto_id in vistos:      # un producto puede tener varios detalles
            continue
        vistos.add(d.producto_id)
        filas.append(d)

    vencidos = urgentes = proximos = 0
    lista = []
    for i, d in enumerate(filas):
        dias = (d.fecha_vencimiento - hoy).days
        nivel, texto = _nivel_vencimiento(dias)

        if nivel == 'vencido':
            vencidos += 1
        elif nivel == 'urgente':
            urgentes += 1
        else:
            proximos += 1

        if i < limite:
            lista.append({
                'nombre': d.producto.nombre,
                'fecha':  d.fecha_vencimiento,
                'stock':  d.stock,
                'texto':  texto,
                'nivel':  nivel,
            })

    # Para el estado vacío: el siguiente producto que vence después de la ventana
    siguiente = (
        _detalles_con_stock()
        .filter(fecha_vencimiento__gt=fecha_tope)
        .order_by('fecha_vencimiento')
        .first()
    )
    proximo = None
    if siguiente:
        dias = (siguiente.fecha_vencimiento - hoy).days
        proximo = {
            'nombre': siguiente.producto.nombre,
            'fecha':  siguiente.fecha_vencimiento,
            'texto':  f"en {dias} {_plural(dias, 'día', 'días')}",
        }

    return {
        'lista':    lista,
        'total':    len(filas),
        'extra':    max(0, len(filas) - limite),
        'vencidos': vencidos,
        'urgentes': urgentes,
        'proximos': proximos,
        'dias':     DIAS_POR_VENCER,
        'proximo':  proximo,
    }


# ── Tarjeta: métodos de pago de la semana ──
def _descuento_de_venta(total_venta, total_con_desc, pct):
    """
    Devuelve (descuento_en_pesos, bruto_de_la_venta).

    Cubre las formas en que puede estar guardada una venta:
      A) total_venta es el bruto y total_con_descuento el neto  → diferencia
      B) total_venta ya viene con el descuento aplicado         → se reconstruye
      C) solo existe el porcentaje                              → pct sobre total_venta
    """
    if 0 < total_con_desc < total_venta:                       # A
        return total_venta - total_con_desc, total_venta

    if pct > 0:
        if total_con_desc > 0 and pct < 100:                   # B
            desc = total_venta * pct / (100 - pct)
            return desc, total_venta + desc
        return total_venta * pct / 100, total_venta            # C

    return 0.0, total_venta


def _metodos_pago():
    lunes = _lunes_de_semana(0)
    domingo = lunes + timedelta(days=6)

    efectivo = 0.0
    digitales = {clave: 0.0 for clave, _, _ in MEDIOS_DIGITALES}

    pendiente_total = facturado_total = bruto_total = 0.0
    ventas_con_saldo = ventas_con_desc = 0
    descuento_total = suma_pct_desc = 0.0

    filas = _ventas_entre(lunes, domingo).values_list(
        'metodo_pago', 'total_venta', 'saldo_pendiente',
        'total_con_descuento', 'descuento_porcentaje',
        'pago_efectivo', 'pago_tarjeta', 'pago_transferencia',
        'pago_nequi', 'pago_daviplata',
    )
    n_ventas = 0
    for (metodo, total, saldo, con_desc, pct_desc,
         p_ef, p_ta, p_tr, p_ne, p_da) in filas:
        n_ventas += 1
        total = float(total or 0)
        saldo = float(saldo or 0)
        con_desc = float(con_desc or 0)
        pct_desc = float(pct_desc or 0)

        facturado_total += total

        # ── Saldo por cobrar ──
        if saldo > 0:
            pendiente_total += saldo
            ventas_con_saldo += 1

        # ── Descuentos ──
        desc, bruto = _descuento_de_venta(total, con_desc, pct_desc)
        bruto_total += bruto
        if desc > 0:
            descuento_total += desc
            ventas_con_desc += 1
            suma_pct_desc += pct_desc if pct_desc > 0 else (desc * 100 / bruto if bruto else 0)

        # ── Cobrado por medio de pago ──
        partes = {
            'efectivo':      float(p_ef or 0),
            'tarjeta':       float(p_ta or 0),
            'transferencia': float(p_tr or 0),
            'nequi':         float(p_ne or 0),
            'daviplata':     float(p_da or 0),
        }
        if sum(partes.values()) <= 0:
            # Venta sin desglose: se toma lo cobrado y el método guardado
            cobrado = max(0.0, total - saldo)
            clave = (metodo or '').strip().lower()
            if clave not in partes:
                clave = 'otro'
            partes = {clave: cobrado}

        efectivo += partes.pop('efectivo', 0.0)
        for clave, valor in partes.items():
            digitales[clave] += valor

    digital_total = sum(digitales.values())
    cobrado_total = efectivo + digital_total

    desglose = [
        {'nombre': nombre, 'icono': icono, 'monto': digitales[clave]}
        for clave, nombre, icono in MEDIOS_DIGITALES
        if digitales[clave] > 0
    ]
    desglose.sort(key=lambda m: m['monto'], reverse=True)

    return {
        'total':  cobrado_total,
        'ventas': n_ventas,

        'efectivo': {
            'monto': efectivo,
            'pct':   _pct(efectivo, cobrado_total),
        },
        'digital': {
            'monto':    digital_total,
            'pct':      _pct(digital_total, cobrado_total),
            'desglose': desglose,
        },
        'descuentos': {
            'monto':    descuento_total,
            'ventas':   ventas_con_desc,
            'promedio': round(suma_pct_desc / ventas_con_desc) if ventas_con_desc else 0,
            'pct':      _pct(descuento_total, bruto_total),
        },
        'pendiente': {
            'monto':  pendiente_total,
            'ventas': ventas_con_saldo,
            'pct':    _pct(pendiente_total, facturado_total),
        },
    }


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
        'vendidos':          _mas_vendidos(),
        'stock_bajo':        _stock_bajo(),
        'por_vencer':        _por_vencer(),
        'metodos_pago':      _metodos_pago(),

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