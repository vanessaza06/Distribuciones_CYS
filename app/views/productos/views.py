from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Prefetch
from django.urls import reverse
from app.models import Categoria
from app.models import PresentacionProducto
from app.models import Producto
from app.forms import ProductoRegistroForm

# ===============================
# LISTA / VISTA PRINCIPAL
# ===============================
@login_required
def lista_productos(request):
    productos_qs = Producto.objects.select_related('categoria').prefetch_related('presentaciones__lotes').all()

    categorias = Categoria.objects.filter(subcategoria__isnull=True).prefetch_related(
        Prefetch(
            'productos',
            queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria')
        ),
        Prefetch(
            'subcategorias',
            queryset=Categoria.objects.prefetch_related(
                Prefetch(
                    'productos',
                    queryset=Producto.objects.prefetch_related('presentaciones__lotes').select_related('categoria')
                )
            )
        ),
    )

    resumen_categorias = []
    for cat in Categoria.objects.filter(subcategoria__isnull=True):
        total  = Producto.objects.filter(categoria=cat).count()
        total += Producto.objects.filter(categoria__subcategoria=cat).count()
        resumen_categorias.append({'pk': cat.pk, 'nombre': cat.nombre, 'total': total})

    todas_cats = Categoria.objects.all()
    form       = ProductoRegistroForm()

    context = {
        'productos': productos_qs,
        'categorias': categorias,
        'todas_cats': todas_cats,
        'resumen_categorias': resumen_categorias,
        'form': form,
        'breadcrumb_items': [
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

    is_ajax  = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    next_url = request.POST.get('next') or request.GET.get('next') or 'lista_productos'

    nombre      = request.POST.get('nombre', '').strip()
    categoria   = request.POST.get('categoria')
    descripcion = request.POST.get('descripcion', '').strip()

    errores = {}
    if not nombre:
        errores['nombre'] = ['El nombre es obligatorio.']
    if not categoria:
        errores['categoria'] = ['La categoría es obligatoria.']

    if errores:
        if is_ajax:
            return JsonResponse({'ok': False, 'errores': errores}, status=400)
        messages.error(request, 'Corrige los errores del formulario.')
        return redirect('lista_productos')

    producto = Producto.objects.create(
        nombre=nombre,
        categoria_id=categoria,
        descripcion=descripcion,
    )

    messages.success(request, f'✅ Producto "{producto.nombre}" creado correctamente.')

    if is_ajax:
        return JsonResponse({'ok': True, 'pk': producto.pk, 'nombre': producto.nombre})

    return redirect(next_url)

# ===============================
# DETALLE PRODUCTO
# ===============================
@login_required
def producto_detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    lotes = producto.lotes.select_related('presentacion', 'bodega').order_by('-fecha_registro')
    context = {
        'producto': producto,
        'lotes': lotes,
        'breadcrumb_items': [
            {'nombre': 'Productos', 'url': reverse('lista_productos')},
            {'nombre': producto.nombre, 'url': None},
        ],
    }

    return render(request, 'productos/productos.html', context)

# ===============================
# EDITAR PRODUCTO
# ===============================
@login_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        cambios = []

        nombre       = request.POST.get('nombre', '').strip()
        descripcion  = request.POST.get('descripcion', '').strip()
        categoria_pk = request.POST.get('categoria')

        if nombre and nombre != producto.nombre:
            cambios.append(f'📝 Nombre: "{producto.nombre}" → "{nombre}"')
        if nombre:
            producto.nombre = nombre

        if descripcion != (producto.descripcion or ''):
            cambios.append('📄 Descripción actualizada')
        producto.descripcion = descripcion

        if categoria_pk:
            try:
                nueva_cat_id = int(categoria_pk)
                if nueva_cat_id != producto.categoria_id:
                    nueva_cat = Categoria.objects.get(pk=nueva_cat_id)
                    cambios.append(f'🏷️ Categoría: "{producto.categoria.nombre}" → "{nueva_cat.nombre}"')
                producto.categoria_id = nueva_cat_id
            except (ValueError, TypeError, Categoria.DoesNotExist):
                pass

        producto.save()

        # ── Presentaciones existentes ──────────────────────────────────
        for key, valor in request.POST.items():
            if key.startswith('pres_nombre_'):
                pres_id = key.replace('pres_nombre_', '')
                try:
                    pres         = PresentacionProducto.objects.get(pk=int(pres_id), producto=producto)
                    nuevo_nombre = valor.strip()
                    nueva_cant   = request.POST.get(f'pres_cantidad_{pres_id}', '').strip()
                    nuevo_precio = request.POST.get(f'pres_precio_{pres_id}', '').strip()

                    if nuevo_nombre and nuevo_nombre != pres.nombre:
                        cambios.append(f'📦 Presentación: "{pres.nombre}" → "{nuevo_nombre}"')
                        pres.nombre = nuevo_nombre

                    if nueva_cant:
                        try:
                            nc = max(1, int(nueva_cant))
                            if nc != pres.cantidad:
                                cambios.append(f'📦 Cantidad "{pres.nombre}": {pres.cantidad} → {nc}')
                                pres.cantidad = nc
                        except (ValueError, TypeError):
                            pass

                    if nuevo_precio:
                        try:
                            np_ = float(nuevo_precio)
                            if np_ != float(pres.precio_venta):
                                cambios.append(f'💲 Precio "{pres.nombre}": ${pres.precio_venta} → ${np_}')
                                pres.precio_venta = np_
                                pres.lotes.all().update(costo_unitario=np_)
                        except (ValueError, TypeError):
                            pass

                    pres.save()

                except PresentacionProducto.DoesNotExist:
                    pass

        # ── Nuevas presentaciones ──────────────────────────────────────
        nuevos_nombres = request.POST.getlist('nueva_pres_nombre[]')
        nuevas_cants   = request.POST.getlist('nueva_pres_cantidad[]')
        nuevos_precios = request.POST.getlist('nueva_pres_precio[]')

        for i, nombre_pres in enumerate(nuevos_nombres):
            nombre_pres = nombre_pres.strip()
            if not nombre_pres:
                continue

            try:
                cantidad_pres = max(1, int(nuevas_cants[i])) if i < len(nuevas_cants) else 1
            except (ValueError, TypeError, IndexError):
                cantidad_pres = 1

            try:
                precio_pres = float(nuevos_precios[i]) if i < len(nuevos_precios) and nuevos_precios[i].strip() else 0.0
            except (ValueError, TypeError):
                precio_pres = 0.0

            nueva_pres = PresentacionProducto.objects.create(
                producto=producto,
                nombre=nombre_pres,
                cantidad=cantidad_pres,
                precio_venta=precio_pres,
            )
            if precio_pres > 0:
                nueva_pres.lotes.all().update(costo_unitario=precio_pres)

            cambios.append(f'➕ Nueva presentación: "{nombre_pres}" · {cantidad_pres} uds')

        if cambios:
            messages.success(request, f"✅ Producto '{producto.nombre}' actualizado.")
        else:
            messages.info(request, 'ℹ️ No se detectaron cambios en el producto.')

    return redirect('lista_productos')

# ===============================
# REGISTRO PRODUCTO
# ===============================
@login_required
def producto_registro(request):
    form = ProductoRegistroForm()
    if request.method == 'POST':
        form = ProductoRegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Producto registrado correctamente.')
    context = {
        'form': form,
        'breadcrumb_items': [
            {'nombre': 'Productos', 'url': reverse('lista_productos')},
            {'nombre': 'Registrar Producto', 'url': None},
        ],
    }

    return render(request, 'productos/productos.html', context)

# ===============================
# STOCK STATUS
# ===============================
@login_required
def stock_status(request):
    """Sin propiedad stock_critico en el modelo: se calcula todo aquí,
    directo sobre Lote, con umbral fijo de 5."""
    criticos = []
    for producto in Producto.objects.filter(activo=True):
        total = Lote.objects.filter(producto=producto).aggregate(total=Sum('stock_actual'))['total'] or 0
        if total <= 5:
            criticos.append({'nombre': producto.nombre, 'total_stock': total})

    return JsonResponse({
        'criticos': criticos,
        'total_alertas': len(criticos),
    })

# ===============================
# BUSCAR PRODUCTO
# ===============================
@login_required
def buscar_producto(request):
    q    = request.GET.get('q', '').strip()
    modo = request.GET.get('modo', '')

    if not q:
        if modo == 'sugerencias':
            return JsonResponse({'resultados': []})
        return JsonResponse({'encontrado': False, 'mensaje': 'Escribe un nombre.'})

    if modo == 'sugerencias':
        productos = Producto.objects.filter(nombre__icontains=q).select_related('categoria')[:8]

        resultados = [{
            'pk':        p.pk,
            'nombre':    p.nombre,
            'categoria': p.categoria.nombre if p.categoria else '—',
        } for p in productos]

        return JsonResponse({'resultados': resultados})

    producto = Producto.objects.filter(nombre__icontains=q).first()

    if not producto:
        return JsonResponse({'encontrado': False, 'mensaje': f'No se encontró "{q}".'})

    stock_total = producto.presentaciones.aggregate(
        total=Sum('lotes__stock_actual')
    )['total'] or 0

    presentaciones = []
    for pres in producto.presentaciones.all():
        stock_pres = pres.lotes.aggregate(total=Sum('stock_actual'))['total'] or 0
        presentaciones.append({
            'id':           pres.id,
            'nombre':       pres.nombre,
            'cantidad':     pres.cantidad,
            'precio':       str(pres.precio_venta),
            'stock_actual': stock_pres,
        })

    return JsonResponse({
        'encontrado': True,
        'producto': {
            'pk':           producto.pk,
            'nombre':       producto.nombre,
            'categoria':    producto.categoria.nombre if producto.categoria else '—',
            'stock_total':  stock_total,
            'descripcion':  producto.descripcion or '',
            'presentaciones': presentaciones,
        }
    })