from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from app.models import Producto
from app.forms import LoteForm
from app.models import Lote


@login_required
def gestion_stock(request):
    productos = Producto.objects.select_related('categoria').prefetch_related('presentaciones__lotes')
    lotes_activos = list(Lote.objects.select_related('presentacion__producto', 'bodega'))
    lotes_por_vencer = [l for l in lotes_activos if l.proximo_a_vencer]
    lotes_vencidos = [l for l in lotes_activos if l.esta_vencido]

    context = {
        'productos': productos,
        'lotes_activos': lotes_activos,
        'lotes_por_vencer': lotes_por_vencer,
        'lotes_vencidos': lotes_vencidos,
    }
    return render(request, 'lotes/gestion_stock.html', context)


@login_required
def lote_list(request):
    lotes = Lote.objects.select_related('presentacion__producto', 'bodega')
    hoy = timezone.now().date()
    ingresos_hoy = lotes.filter(fecha_registro__date=hoy).aggregate(total=Sum('stock_actual'))['total'] or 0
    lotes_mes = lotes.filter(fecha_registro__year=hoy.year, fecha_registro__month=hoy.month).count()
    top_productos = Producto.objects.annotate(
        stock_calculado=Sum('lotes__stock_actual')
    ).order_by('-stock_calculado')[:5]

    return render(request, 'lotes/lote_list.html', {
        'lotes': lotes,
        'ingresos_hoy': ingresos_hoy,
        'lotes_mes': lotes_mes,
        'top_productos': top_productos,
    })


@login_required
def lote_detail(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    return render(request, 'lotes/lote_detail.html', {'lote': lote})


@login_required
def lote_create(request):
    if request.method == 'POST':
        form = LoteForm(request.POST)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.stock_actual = lote.cantidad_inicial
            lote.costo_total = lote.costo_unitario * lote.cantidad_inicial
            lote.save()
            messages.success(request, f'Lote {lote.numero_lote} registrado.')
        else:
            messages.error(request, 'Error al registrar lote.')
    else:
        form = LoteForm()
    return render(request, 'lotes/lote_form.html', {'form': form})


@login_required
def lote_update(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lote {lote.numero_lote} actualizado.')
            return redirect('lotes:lote_list')
    else:
        form = LoteForm(instance=lote)
    return render(request, 'lotes/lote_form.html', {'form': form, 'lote': lote})


@login_required
def lote_ajustar_stock(request, numero_lote):
    lote = get_object_or_404(Lote, numero_lote=numero_lote)
    if request.method == 'POST':
        nuevo_stock = int(request.POST.get('nuevo_stock', 0))
        lote.stock_actual = nuevo_stock
        lote.save(update_fields=['stock_actual'])
        messages.success(request, 'Stock ajustado.')
    return redirect('lotes:gestion_stock')