
from decimal import Decimal, InvalidOperation
from itertools import zip_longest

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from app.forms import ProductoRegistroForm
from app.models import Categoria, PresentacionProducto, Producto

UMBRAL_STOCK_CRITICO = 5


# ===============================
# HELPERS
# ===============================
def _es_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _destino_seguro(request, destino):
    """Evita open redirect: solo acepta rutas del mismo sitio."""
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return reverse('lista_productos')


def _entero_positivo(valor):
    """Devuelve un entero >= 1, o None si no es válido."""
    try:
        n = int(str(valor).strip())
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def _decimal_positivo(valor):
    """Devuelve un Decimal > 0 con 2 decimales, o None si no es válido."""
    try:
        d = Decimal(str(valor).strip().replace(',', '.'))
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if not d.is_finite() or d <= 0:
        return None
    return d.quantize(Decimal('0.01'))


# ===============================
# LISTA / VISTA PRINCIPAL
# ===============================
@login_required
def lista_productos(request):
    productos_qs = (
        Producto.objects.select_related('categoria')
        .prefetch_related('presentaciones__lotes', 'detalles')
        .all()
    )

    categorias = Categoria.objects.filter(subcategoria__isnull=True).prefetch_related(
        Prefetch(
            'productos',
            queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria'),
        ),
        Prefetch(
            'subcategorias',
            queryset=Categoria.objects.prefetch_related(
                Prefetch(
                    'productos',
                    queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria'),
                )
            ),
        ),
    )

    resumen_categorias = []
    for cat in Categoria.objects.filter(subcategoria__isnull=True):
        total = Producto.objects.filter(categoria=cat).count()
        total += Producto.objects.filter(categoria__subcategoria=cat).count()
        resumen_categorias.append({'pk': cat.pk, 'nombre': cat.nombre, 'total': total})

    context = {
        'productos': productos_qs,
        'categorias': categorias,
        'todas_cats': Categoria.objects.all(),
        'resumen_categorias': resumen_categorias,
        'form': ProductoRegistroForm(),
        'breadcrumb_items': [
            {'nombre': 'Inventario', 'url': None},
            {'nombre': 'Productos', 'url': None},
        ],
    }
    return render(request, 'productos/productos.html', context)


# ===============================
# CREAR PRODUCTO
# ===============================
@login_required
def crear_producto(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido.'}, status=405)

    ajax = _es_ajax(request)
    destino = _destino_seguro(request, request.POST.get('next') or request.GET.get('next'))

    nombre = request.POST.get('nombre', '').strip()
    categoria_pk = request.POST.get('categoria', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()

    errores = {}
    if not nombre:
        errores['nombre'] = ['El nombre es obligatorio.']

    categoria = None
    if not categoria_pk:
        errores['categoria'] = ['La categoría es obligatoria.']
    elif not categoria_pk.isdigit():
        errores['categoria'] = ['Categoría no válida.']
    else:
        categoria = Categoria.objects.filter(pk=int(categoria_pk), activo=True).first()
        if categoria is None:
            errores['categoria'] = ['La categoría no existe o está desactivada.']

    if errores:
        if ajax:
            return JsonResponse({'ok': False, 'errores': errores}, status=400)
        messages.error(request, 'Corrige los errores del formulario.')
        return redirect(destino)

    # La fecha de vencimiento se registra después, en Detalle de Producto.
    producto = Producto.objects.create(
        nombre=nombre,
        categoria=categoria,
        descripcion=descripcion,
    )

    messages.success(request, f'✅ Producto "{producto.nombre}" creado correctamente.')

    if ajax:
        return JsonResponse({'ok': True, 'pk': producto.pk, 'nombre': producto.nombre})
    return redirect(destino)


# ===============================
# DETALLE PRODUCTO
# ===============================
@login_required
def producto_detalle(request, pk):
    """
    Antes renderizaba productos.html sin contexto (página vacía).
    Ahora vuelve a la lista; ?producto=<pk> queda disponible para que el
    frontend resalte o abra ese producto.
    """
    get_object_or_404(Producto, pk=pk)
    return redirect(f"{reverse('lista_productos')}?producto={pk}")


# ===============================
# EDITAR PRODUCTO
# ===============================
@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method != 'POST':
        return redirect('lista_productos')

    cambios = []
    avisos = []

    with transaction.atomic():
        # ── Datos básicos ──
        nombre = request.POST.get('nombre', '').strip()
        if nombre and nombre != producto.nombre:
            producto.nombre = nombre
            cambios.append('nombre')

        descripcion = request.POST.get('descripcion')
        if descripcion is not None:
            descripcion = descripcion.strip()
            if descripcion != (producto.descripcion or ''):
                producto.descripcion = descripcion
                cambios.append('descripción')

        categoria_pk = request.POST.get('categoria', '').strip()
        if categoria_pk.isdigit() and int(categoria_pk) != producto.categoria_id:
            nueva_cat = Categoria.objects.filter(pk=int(categoria_pk)).first()
            if nueva_cat:
                producto.categoria = nueva_cat
                cambios.append('categoría')
            else:
                avisos.append('La categoría elegida no existe.')

        if cambios:
            producto.save()

        # ── Presentaciones existentes ──
        # OJO: ya NO se copia el precio de venta al costo de los lotes.
        for key, valor in request.POST.items():
            if not key.startswith('pres_nombre_'):
                continue
            pres_id = key.replace('pres_nombre_', '')
            if not pres_id.isdigit():
                continue
            pres = PresentacionProducto.objects.filter(pk=int(pres_id), producto=producto).first()
            if pres is None:
                continue

            modificado = False

            nuevo_nombre = valor.strip()
            if nuevo_nombre and nuevo_nombre != pres.nombre:
                pres.nombre = nuevo_nombre
                modificado = True

            cant_raw = request.POST.get(f'pres_cantidad_{pres_id}', '').strip()
            if cant_raw:
                nueva_cant = _entero_positivo(cant_raw)
                if nueva_cant is None:
                    avisos.append(f'Cantidad inválida en "{pres.nombre}" (debe ser 1 o más).')
                elif nueva_cant != pres.cantidad:
                    pres.cantidad = nueva_cant
                    modificado = True

            precio_raw = request.POST.get(f'pres_precio_{pres_id}', '').strip()
            if precio_raw:
                nuevo_precio = _decimal_positivo(precio_raw)
                if nuevo_precio is None:
                    avisos.append(f'Precio inválido en "{pres.nombre}" (debe ser mayor a 0).')
                elif nuevo_precio != pres.precio_venta:
                    pres.precio_venta = nuevo_precio
                    modificado = True

            if modificado:
                pres.save()
                cambios.append(f'presentación "{pres.nombre}"')

        # ── Nuevas presentaciones ──
        nombres = request.POST.getlist('nueva_pres_nombre[]')
        cantidades = request.POST.getlist('nueva_pres_cantidad[]')
        precios = request.POST.getlist('nueva_pres_precio[]')

        for nombre_pres, cant_raw, precio_raw in zip_longest(nombres, cantidades, precios, fillvalue=''):
            nombre_pres = nombre_pres.strip()
            if not nombre_pres:
                continue

            cantidad_pres = _entero_positivo(cant_raw)
            precio_pres = _decimal_positivo(precio_raw)
            if cantidad_pres is None or precio_pres is None:
                avisos.append(
                    f'Presentación "{nombre_pres}" no creada: cantidad y precio deben ser mayores a 0.'
                )
                continue

            if producto.presentaciones.filter(nombre__iexact=nombre_pres).exists():
                avisos.append(f'Presentación "{nombre_pres}" no creada: ya existe en este producto.')
                continue

            PresentacionProducto.objects.create(
                producto=producto,
                nombre=nombre_pres,
                cantidad=cantidad_pres,
                precio_venta=precio_pres,
            )
            cambios.append(f'nueva presentación "{nombre_pres}"')

    for aviso in avisos:
        messages.warning(request, f'⚠️ {aviso}')

    if cambios:
        messages.success(request, f"✅ Producto '{producto.nombre}' actualizado.")
    elif not avisos:
        messages.info(request, 'ℹ️ No se detectaron cambios en el producto.')

    return redirect('lista_productos')


# ===============================
# REGISTRO PRODUCTO
# ===============================
@login_required
def producto_registro(request):
    """Antes renderizaba productos.html sin contexto. Ahora guarda y vuelve a la lista."""
    if request.method == 'POST':
        form = ProductoRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Producto registrado correctamente.')
        else:
            for campo, errs in form.errors.items():
                messages.error(request, f'{campo}: {", ".join(errs)}')
    return redirect('lista_productos')


# ===============================
# STOCK STATUS
# ===============================
@login_required
def stock_status(request):
    """Una sola consulta; el umbral está en UMBRAL_STOCK_CRITICO."""
    productos = Producto.objects.filter(activo=True).annotate(total=Sum('lotes__stock_actual'))

    criticos = [
        {'nombre': p.nombre, 'total_stock': p.total or 0}
        for p in productos
        if (p.total or 0) <= UMBRAL_STOCK_CRITICO
    ]

    return JsonResponse({
        'criticos': criticos,
        'total_alertas': len(criticos),
    })


# ===============================
# BUSCAR PRODUCTO
# ===============================
@login_required
def buscar_producto(request):
    q = request.GET.get('q', '').strip()
    modo = request.GET.get('modo', '')

    if not q:
        if modo == 'sugerencias':
            return JsonResponse({'resultados': []})
        return JsonResponse({'encontrado': False, 'mensaje': 'Escribe un nombre.'})

    if modo == 'sugerencias':
        productos = Producto.objects.filter(nombre__icontains=q).select_related('categoria')[:8]
        resultados = [{
            'pk': p.pk,
            'nombre': p.nombre,
            'categoria': p.categoria.nombre if p.categoria else '—',
        } for p in productos]
        return JsonResponse({'resultados': resultados})

    producto = Producto.objects.filter(nombre__icontains=q).order_by('nombre').first()

    if not producto:
        return JsonResponse({'encontrado': False, 'mensaje': f'No se encontró "{q}".'})

    stock_total = producto.presentaciones.aggregate(
        total=Sum('lotes__stock_actual')
    )['total'] or 0

    presentaciones = []
    for pres in producto.presentaciones.all():
        stock_pres = pres.lotes.aggregate(total=Sum('stock_actual'))['total'] or 0
        presentaciones.append({
            'id': pres.pk,
            'nombre': pres.nombre,
            'cantidad': pres.cantidad,
            'precio': str(pres.precio_venta),
            'stock_actual': stock_pres,
        })

    return JsonResponse({
        'encontrado': True,
        'producto': {
            'pk': producto.pk,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre if producto.categoria else '—',
            'stock_total': stock_total,
            'descripcion': producto.descripcion or '',
            'presentaciones': presentaciones,
        },
    })


# ===============================
# ACTIVAR / DESACTIVAR
# ===============================
@login_required
def producto_toggle_activo(request, pk):
    # TODO: pasar a @require_POST cuando el template/JS envíe POST con CSRF.
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = not producto.activo
    producto.save(update_fields=['activo'])
    estado = 'activado' if producto.activo else 'desactivado'
    if _es_ajax(request):
        return JsonResponse({'ok': True, 'nombre': producto.nombre, 'activo': producto.activo})
    messages.success(request, f'Producto "{producto.nombre}" {estado}.')
    return redirect('lista_productos')