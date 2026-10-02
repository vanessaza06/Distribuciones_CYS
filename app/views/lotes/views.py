from decimal import Decimal, InvalidOperation
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from app.models import Producto, Lote, Bodega, PresentacionProducto
from app.forms import LoteForm

# Nombre del campo de fecha de ingreso en el modelo Lote.
# Si tu modelo lo llama distinto, cámbialo aquí.
CAMPO_FECHA_LOTE = 'fecha_ingreso'


def _stats_lotes(hoy):
    """Devuelve (unidades ingresadas hoy, lotes registrados en el mes)."""
    try:
        campo = Lote._meta.get_field(CAMPO_FECHA_LOTE)
    except FieldDoesNotExist:
        return 0, 0

    if isinstance(campo, models.DateTimeField):
        filtro_hoy = {f'{CAMPO_FECHA_LOTE}__date': hoy}
    else:
        filtro_hoy = {CAMPO_FECHA_LOTE: hoy}

    ingresos_hoy = (
        Lote.objects.filter(**filtro_hoy)
        .aggregate(total=Sum('cantidad_inicial'))['total'] or 0
    )
    lotes_mes = Lote.objects.filter(
        **{
            f'{CAMPO_FECHA_LOTE}__year': hoy.year,
            f'{CAMPO_FECHA_LOTE}__month': hoy.month,
        }
    ).count()
    return ingresos_hoy, lotes_mes


@login_required
def lote_list(request):
    """Página 'Lotes': formulario de registro + resumen.

    Si llega ?presentacion=<pk> (por ejemplo desde el botón "Crear Lote"
    de Bodega), esa presentación queda preseleccionada en el formulario.
    """
    hoy = timezone.localdate()

    # Si no hay ninguna bodega, se crea una por defecto para no bloquear el lote.
    if not Bodega.objects.exists():
        Bodega.objects.get_or_create(nombre='Bodega Principal')

    productos = Producto.objects.prefetch_related('presentaciones')
    bodegas = Bodega.objects.all()
    hay_presentaciones = PresentacionProducto.objects.exists()
    hay_bodegas = bodegas.exists()

    presentacion_preseleccionada = request.GET.get('presentacion', '')

    ingresos_hoy, ordenes_mes = _stats_lotes(hoy)

    top = (
        Lote.objects
        .values('presentacion__producto__nombre')
        .annotate(total=Sum('stock_actual'))
        .order_by('-total')[:5]
    )
    labels = [t['presentacion__producto__nombre'] for t in top]
    data = [int(t['total'] or 0) for t in top]

    context = {
        'productos': productos,
        'bodegas': bodegas,
        'hay_presentaciones': hay_presentaciones,
        'hay_bodegas': hay_bodegas,
        'presentacion_preseleccionada': presentacion_preseleccionada,
        'ingresos_hoy': ingresos_hoy,
        'ordenes_mes': ordenes_mes,
        'proveedores_labels': json.dumps(labels),
        'proveedores_data': json.dumps(data),
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Lotes', 'url': reverse('lote_list')},
        ],
    }
    return render(request, 'lotes/lotes.html', context)


@login_required
def gestion_stock(request):
    productos = Producto.objects.select_related('categoria').prefetch_related('presentaciones__lotes')
    lotes_activos = list(Lote.objects.select_related('presentacion__producto', 'bodega'))
    lotes_por_vencer = [l for l in lotes_activos if l.stock_actual > 0 and l.proximo_a_vencer]
    lotes_vencidos = [l for l in lotes_activos if l.stock_actual > 0 and l.esta_vencido]

    context = {
        'productos': productos,
        'lotes_activos': lotes_activos,
        'lotes_por_vencer': lotes_por_vencer,
        'lotes_vencidos': lotes_vencidos,
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Stock & Productos', 'url': reverse('gestion_stock')},
        ],
    }
    return render(request, 'lotes/gestion.html', context)


@login_required
def lote_create(request):
    if request.method == 'POST':
        datos = request.POST.copy()

        # Si no llegó bodega, se usa la primera disponible.
        if not datos.get('bodega'):
            bodega_default = Bodega.objects.first()
            if bodega_default:
                datos['bodega'] = bodega_default.pk

        form = LoteForm(datos, request.FILES)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.stock_actual = lote.cantidad_inicial
            lote.costo_total = lote.costo_unitario * lote.cantidad_inicial
            lote.save()
            messages.success(request, f'Lote {lote.numero_lote} registrado.')
        else:
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')
    return redirect('lote_list')


@login_required
def lote_update(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    cantidad_inicial_original = lote.cantidad_inicial

    if request.method == 'POST':
        form = LoteForm(request.POST, request.FILES, instance=lote)
        if form.is_valid():
            lote_actualizado = form.save(commit=False)
            # La cantidad inicial no se edita aquí: representa el ingreso
            # original del lote. Para cambiar el stock disponible se usa
            # "Ajustar stock".
            lote_actualizado.cantidad_inicial = cantidad_inicial_original
            lote_actualizado.costo_total = lote_actualizado.costo_unitario * cantidad_inicial_original
            lote_actualizado.save()
            messages.success(request, f'Lote {lote.numero_lote} actualizado.')
            return redirect('lote_list')
        else:
            for campo, errores in form.errors.items():
                for error in errores:
                    messages.error(request, f'{campo}: {error}')
    else:
        form = LoteForm(instance=lote)

    return render(request, 'lotes/lote_form.html', {'form': form, 'lote': lote})


@login_required
def lote_detail(request, numero_lote):
    """Reutiliza el mismo formulario de edición completa del lote."""
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    form = LoteForm(instance=lote)
    return render(request, 'lotes/lote_form.html', {'form': form, 'lote': lote})


@login_required
def lote_ajustar_stock(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)

    if request.method != 'POST':
        return redirect('gestion_stock')

    nuevo_stock_raw = request.POST.get('nuevo_stock', '').strip()
    costo_unitario_raw = request.POST.get('costo_unitario', '').strip()

    try:
        nuevo_stock = int(nuevo_stock_raw)
    except (TypeError, ValueError):
        messages.error(request, 'El nuevo stock debe ser un número entero.')
        return redirect('gestion_stock')

    if nuevo_stock < 0:
        messages.error(request, 'El stock no puede ser negativo.')
        return redirect('gestion_stock')

    lote.stock_actual = nuevo_stock

    if costo_unitario_raw:
        try:
            nuevo_costo = Decimal(costo_unitario_raw.replace(',', '.'))
        except (InvalidOperation, ValueError):
            messages.error(request, 'El costo unitario no es válido.')
            return redirect('gestion_stock')

        if nuevo_costo <= 0:
            messages.error(request, 'El costo unitario debe ser mayor a 0.')
            return redirect('gestion_stock')

        lote.costo_unitario = nuevo_costo
        # Se recalcula el costo total con la cantidad inicial del lote.
        lote.costo_total = nuevo_costo * lote.cantidad_inicial
        lote.save(update_fields=['stock_actual', 'costo_unitario', 'costo_total'])
    else:
        lote.save(update_fields=['stock_actual'])

    messages.success(request, 'Stock ajustado.')
    return redirect('gestion_stock')