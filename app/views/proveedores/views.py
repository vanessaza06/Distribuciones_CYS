import json
import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Sum, Count, Q

from app.models import Proveedor, Compra

logger = logging.getLogger(__name__)


# ── LISTA PRINCIPAL DE PROVEEDORES ─────────────────────────────────────────────
#@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all().order_by('-fecha_registro')

    # Filtros de búsqueda
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    if q:
        proveedores = proveedores.filter(
            Q(nombre_empresa__icontains=q) |
            Q(correo__icontains=q) |
            Q(nit_proveedores__icontains=q)
        )

    if estado:
        proveedores = proveedores.filter(estado=estado)

    if tipo:
        proveedores = proveedores.filter(tipo_proveedor=tipo)

    # Calcular estadísticas de compras por proveedor
    for p in proveedores:
        compras_p = Compra.objects.filter(proveedor=p)
        p.total_compras = compras_p.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')
        p.total_ordenes = compras_p.count()
        # Aliases para el template HTML
        p.id = p.pk
        p.nit = p.nit_proveedores
        p.email = p.correo

    # Estadísticas generales (KPIs)
    total_proveedores = Proveedor.objects.count()
    proveedores_activos = Proveedor.objects.filter(estado='activo').count()
    proveedores_inactivos = Proveedor.objects.filter(estado='inactivo').count()
    proveedores_sancionados = Proveedor.objects.filter(estado='sancionado').count()
    porcentaje_activos = int((proveedores_activos / total_proveedores) * 100) if total_proveedores > 0 else 0

    # Normalización para barra de progreso
    max_compras = max([p.total_compras for p in proveedores], default=1) or 1
    for p in proveedores:
        p.bar_width = int((p.total_compras / max_compras) * 100) if p.total_compras > 0 else 1

    # Paginación
    paginator = Paginator(proveedores, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    # Top 5 gastos por proveedor para el gráfico (ORM nativo)
    gastos_qs = (
        Compra.objects.values('proveedor__nombre_empresa')
        .annotate(total=Sum('valor'))
        .order_by('-total')[:5]
    )
    gastos_labels = [g['proveedor__nombre_empresa'] for g in gastos_qs]
    gastos_data = [float(g['total'] or 0) for g in gastos_qs]
    gastos_total = sum(gastos_data) or 1
    gastos_porcentajes = [int((g / gastos_total) * 100) for g in gastos_data]

    context = {
        'proveedores': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_proveedores': total_proveedores,
        'proveedores_activos': proveedores_activos,
        'proveedores_inactivos': proveedores_inactivos,
        'proveedores_sancionados': proveedores_sancionados,
        'porcentaje_activos': porcentaje_activos,
        'max_compras': max_compras,
        'gastos_labels_json': json.dumps(gastos_labels),
        'gastos_data_json': json.dumps(gastos_data),
        'gastos_porcentajes_json': json.dumps(gastos_porcentajes),
        'breadcrumb_items': [{'nombre': 'Proveedores', 'url': None}],
    }
    return render(request, 'proveedores/proveedores.html', context)


# ── CRUD TRADICIONAL ──────────────────────────────────────────────────────────
#@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Obtenemos los campos soportando tanto 'nit' como 'nit_proveedores', y 'email' como 'correo'
        nit = request.POST.get('nit') or request.POST.get('nit_proveedores')
        nombre = request.POST.get('nombre_empresa')
        correo = request.POST.get('email') or request.POST.get('correo')
        telefono = request.POST.get('telefono', '')
        tipo = request.POST.get('tipo_proveedor', 'distribuidor')

        if not nit or not nombre or not correo:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'nombre_empresa': 'Complete los campos obligatorios.'}}, status=400)
            messages.error(request, 'NIT, Nombre y Correo son obligatorios.')
            return redirect('lista_proveedores')

        if Proveedor.objects.filter(pk=nit).exists():
            error_msg = f'El proveedor con NIT {nit} ya se encuentra registrado.'
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'nit': error_msg}}, status=400)
            messages.error(request, error_msg)
            return redirect('lista_proveedores')

        proveedor = Proveedor.objects.create(
            nit_proveedores=nit,
            nombre_empresa=nombre,
            correo=correo,
            telefono=telefono,
            tipo_proveedor=tipo,
            estado='activo',
        )

        if is_ajax:
            return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} registrado correctamente.'})
        
        messages.success(request, f'Proveedor {proveedor.nombre_empresa} registrado correctamente.')
        return redirect('lista_proveedores')

    return redirect('lista_proveedores')


#@login_required
def editar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)

    if request.method == 'POST':
        proveedor.nombre_empresa = request.POST.get('nombre_empresa', proveedor.nombre_empresa)
        proveedor.correo = request.POST.get('email') or request.POST.get('correo', proveedor.correo)
        proveedor.telefono = request.POST.get('telefono', proveedor.telefono)
        proveedor.tipo_proveedor = request.POST.get('tipo_proveedor', proveedor.tipo_proveedor)
        proveedor.observacion = request.POST.get('observacion', proveedor.observacion)
        proveedor.save()

        messages.success(request, f'Proveedor {proveedor.nombre_empresa} actualizado con éxito.')
        return redirect('lista_proveedores')

    # Aliases para template
    proveedor.id = proveedor.pk
    proveedor.nit = proveedor.nit_proveedores
    proveedor.email = proveedor.correo

    context = {
        'proveedor': proveedor,
        'breadcrumb_items': [
            {'nombre': 'Proveedores', 'url': reverse('lista_proveedores')},
            {'nombre': f'Editar: {proveedor.nombre_empresa}', 'url': None},
        ],
    }
    return render(request, 'proveedores/editar_proveedor.html', context)


#@login_required
def detalle_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.id = proveedor.pk
    proveedor.nit = proveedor.nit_proveedores
    proveedor.email = proveedor.correo

    compras = Compra.objects.filter(proveedor=proveedor).order_by('-fecha')
    total_compras = compras.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

    context = {
        'proveedor': proveedor,
        'compras': compras,
        'total_compras': total_compras,
        'breadcrumb_items': [
            {'nombre': 'Proveedores', 'url': reverse('lista_proveedores')},
            {'nombre': proveedor.nombre_empresa, 'url': None},
        ],
    }
    return render(request, 'proveedores/detalle_proveedor.html', context)


#@login_required
def eliminar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    if request.method == 'POST':
        nombre = proveedor.nombre_empresa
        proveedor.delete()
        messages.success(request, f'Proveedor {nombre} eliminado correctamente.')
    return redirect('lista_proveedores')


#@login_required
def activar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.estado = 'activo'
    proveedor.save(update_fields=['estado'])
    messages.success(request, f'Proveedor {proveedor.nombre_empresa} activado.')
    return redirect('lista_proveedores')


#@login_required
def desactivar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    proveedor.estado = 'inactivo'
    proveedor.save(update_fields=['estado'])
    messages.success(request, f'Proveedor {proveedor.nombre_empresa} desactivado.')
    return redirect('lista_proveedores')


#@login_required
def sancionar_proveedor(request, id):
    proveedor = get_object_or_404(Proveedor, pk=id)
    if request.method == 'POST':
        observacion = request.POST.get('observacion', '').strip()
        if observacion:
            proveedor.estado = 'sancionado'
            proveedor.observacion = observacion
            proveedor.save(update_fields=['estado', 'observacion'])
            messages.success(request, f'Proveedor {proveedor.nombre_empresa} sancionado.')
        else:
            messages.error(request, 'Debe indicar el motivo de la sanción.')
    return redirect('lista_proveedores')


# ── VISTAS MODALES / AJAX (Usadas por proveedores.js) ─────────────────────────
#@login_required
def detalle_proveedor_modal(request, id):
    try:
        proveedor = get_object_or_404(Proveedor, pk=id)
        compras_p = Compra.objects.filter(proveedor=proveedor)
        total_gastado = compras_p.aggregate(s=Sum('valor'))['s'] or Decimal('0.00')

        data = {
            'success': True,
            'proveedor': {
                'id': proveedor.pk,
                'nombre_empresa': proveedor.nombre_empresa,
                'nit': proveedor.nit_proveedores,
                'email': proveedor.correo,
                'telefono': proveedor.telefono or '—',
                'tipo_proveedor': proveedor.get_tipo_proveedor_display(),
                'estado': proveedor.get_estado_display(),
                'estado_value': proveedor.estado,
                'observacion': proveedor.observacion or 'Sin observaciones',
                'fecha_registro': proveedor.fecha_registro.strftime('%d/%m/%Y'),
                'total_compras': compras_p.count(),
                'total_gastado': f'${total_gastado:,.2f}',
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


#@login_required
@csrf_exempt
def desactivar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'inactivo'
        proveedor.save(update_fields=['estado'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} desactivado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


#@login_required
@csrf_exempt
def reactivar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'activo'
        proveedor.save(update_fields=['estado'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} reactivado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


#@login_required
@csrf_exempt
def sancionar_proveedor_modal(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        observacion = request.POST.get('observacion', '').strip()
        if not observacion:
            return JsonResponse({'success': False, 'error': 'Debe indicar el motivo de la sanción.'}, status=400)
        proveedor.estado = 'sancionado'
        proveedor.observacion = observacion
        proveedor.save(update_fields=['estado', 'observacion'])
        return JsonResponse({'success': True, 'message': f'Proveedor {proveedor.nombre_empresa} sancionado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


#@login_required
@csrf_exempt
def levantar_sancion_proveedor(request, id):
    if request.method == 'POST':
        proveedor = get_object_or_404(Proveedor, pk=id)
        proveedor.estado = 'activo'
        proveedor.observacion = ''
        proveedor.save(update_fields=['estado', 'observacion'])
        return JsonResponse({'success': True, 'message': f'Sanción levantada para {proveedor.nombre_empresa}.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
