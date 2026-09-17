from django.test import TestCase
from django.db import IntegrityError
from decimal import Decimal
from app.models import Categoria, Producto, PresentacionProducto, Lote, Bodega
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse

from app.models import Categoria, Producto, Marca, DetalleProducto

Usuario = get_user_model()

# ─────────────────────────────────────────────
#  TESTS: Categoria
# ─────────────────────────────────────────────
class CategoriaModelTest(TestCase):

    def test_str_sin_subcategoria(self):
        """Una categoría raíz muestra solo su nombre."""
        cat = Categoria.objects.create(codigo='C01', nombre='Medicamentos')
        self.assertEqual(str(cat), 'Medicamentos')

    def test_str_con_subcategoria(self):
        """Una sub-categoría muestra sub → nombre."""
        principal = Categoria.objects.create(codigo='C01', nombre='Medicamentos')
        hijo = Categoria.objects.create(
            codigo='C02', nombre='Analgésicos', subcategoria=principal
        )
        self.assertEqual(str(hijo), 'Medicamentos → Analgésicos')

    def test_codigo_es_unico(self):
        """No se permiten dos categorías con el mismo código."""
        Categoria.objects.create(codigo='C01', nombre='Medicamentos')
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(codigo='C01', nombre='Otra')

    def test_subcategoria_puede_ser_nula(self):
        """Una categoría raíz no necesita subcategoria."""
        cat = Categoria.objects.create(codigo='C01', nombre='Raíz')
        self.assertIsNone(cat.subcategoria)

    def test_subcategorias_related_name(self):
        """Se puede acceder a las sub-categorías desde la principal."""
        principal = Categoria.objects.create(codigo='C01', nombre='Medicamentos')
        hijo = Categoria.objects.create(
            codigo='C02', nombre='Analgésicos', subcategoria=principal
        )
        self.assertIn(hijo, principal.subcategorias.all())

    def test_ordering_por_nombre(self):
        """Las categorías se ordenan alfabéticamente por nombre."""
        Categoria.objects.create(codigo='C02', nombre='Vitaminas')
        Categoria.objects.create(codigo='C01', nombre='Antibióticos')
        primera = Categoria.objects.first()
        self.assertEqual(primera.nombre, 'Antibióticos')

    def test_activo_por_defecto_true(self):
        cat = Categoria.objects.create(codigo='C01', nombre='Medicamentos')
        self.assertTrue(cat.activo)


# ─────────────────────────────────────────────
#  TESTS: Producto
# ─────────────────────────────────────────────
class ProductoModelTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            codigo='CAT01', nombre='Medicamentos'
        )
        self.producto = Producto.objects.create(
            nombre='Ibuprofeno',
            descripcion='Analgésico',
            fecha_vencimiento='2027-01-01',
            categoria=self.categoria,
        )

    def test_str_es_el_nombre(self):
        """__str__ solo devuelve el nombre (no hay campo código en Producto)."""
        self.assertEqual(str(self.producto), 'Ibuprofeno')

    def test_activo_por_defecto_true(self):
        self.assertTrue(self.producto.activo)

    def test_categoria_puede_ser_nula(self):
        """categoria usa SET_NULL, así que puede quedar sin categoría."""
        producto = Producto.objects.create(
            nombre='Sin categoría',
            descripcion='—',
            fecha_vencimiento='2027-01-01',
        )
        self.assertIsNone(producto.categoria)

    def test_categoria_se_pone_null_al_borrar_categoria(self):
        """Al borrar la categoría, el producto no se borra: categoria queda en null."""
        self.categoria.delete()
        self.producto.refresh_from_db()
        self.assertIsNone(self.producto.categoria)

    def test_stock_critico_cuando_stock_es_cinco_o_menos(self):
        """stock_critico debe ser True cuando el stock total es 5 o menos."""
        pres = PresentacionProducto.objects.create(
            producto=self.producto, nombre='Caja x10', cantidad=10, precio_venta=Decimal('15000.00')
        )
        bodega = Bodega.objects.create(nombre='Principal', estado='activo')
        Lote.objects.create(
            numero_lote='LOT-01', producto=self.producto, presentacion=pres, bodega=bodega,
            cantidad_inicial=5, stock_actual=5,
            costo_unitario=Decimal('1000.00'), costo_total=Decimal('5000.00'),
        )
        self.assertTrue(self.producto.stock_critico)

    def test_stock_critico_falso_cuando_stock_es_mayor_a_cinco(self):
        pres = PresentacionProducto.objects.create(
            producto=self.producto, nombre='Caja x10', cantidad=10, precio_venta=Decimal('15000.00')
        )
        bodega = Bodega.objects.create(nombre='Principal', estado='activo')
        Lote.objects.create(
            numero_lote='LOT-01', producto=self.producto, presentacion=pres, bodega=bodega,
            cantidad_inicial=6, stock_actual=6,
            costo_unitario=Decimal('1000.00'), costo_total=Decimal('6000.00'),
        )
        self.assertFalse(self.producto.stock_critico)

    def test_stock_total_sin_lotes_retorna_cero(self):
        """Sin lotes asociados el stock total debe ser 0."""
        self.assertEqual(self.producto.stock_total, 0)

    def test_precio_base_retorna_precio_menor_presentacion(self):
        """precio_base retorna el precio_venta de la presentación con precio_venta más bajo."""
        PresentacionProducto.objects.create(
            producto=self.producto, nombre='Caja x10', cantidad=10, precio_venta=Decimal('15000.00')
        )
        PresentacionProducto.objects.create(
            producto=self.producto, nombre='Unidad', cantidad=1, precio_venta=Decimal('1500.00')
        )
        self.assertEqual(self.producto.precio_base(), Decimal('1500.00'))

    def test_precio_base_sin_presentaciones_retorna_none(self):
        """Sin presentaciones, precio_base debe retornar None."""
        self.assertIsNone(self.producto.precio_base())

# ─────────────────────────────────────────────
#  TESTS: PresentacionProducto (modelo)
# ─────────────────────────────────────────────
class PresentacionProductoModelTest(TestCase):

    def setUp(self):
        self.categoria = Categoria.objects.create(
            codigo='CAT01', nombre='Medicamentos'
        )
        self.producto = Producto.objects.create(
            nombre='Ibuprofeno',
            descripcion='Analgésico',
            fecha_vencimiento='2027-01-01',
            categoria=self.categoria,
        )
        self.presentacion = PresentacionProducto.objects.create(
            producto=self.producto,
            nombre='Caja x10',
            cantidad=10,
            precio_venta=Decimal('15000.00')
        )

    def test_str_incluye_producto_nombre_y_cantidad(self):
        """__str__ debe mostrar producto y cantidad."""
        resultado = str(self.presentacion)
        self.assertIn('Ibuprofeno', resultado)
        self.assertIn('10', resultado)

    def test_activo_por_defecto_true(self):
        self.assertTrue(self.presentacion.activo)

    def test_stock_real_sin_lotes_es_cero(self):
        """Sin lotes, el stock real debe ser 0."""
        self.assertEqual(self.presentacion.stock_real, 0)

    def test_stock_real_suma_lotes(self):
        """stock_real suma el stock_actual de todos sus lotes."""
        bodega = Bodega.objects.create(nombre='Principal', estado='activo')
        Lote.objects.create(
            numero_lote='LOT-01', producto=self.producto, presentacion=self.presentacion, bodega=bodega,
            cantidad_inicial=10, stock_actual=10,
            costo_unitario=Decimal('1000.00'), costo_total=Decimal('10000.00'),
        )
        Lote.objects.create(
            numero_lote='LOT-02', producto=self.producto, presentacion=self.presentacion, bodega=bodega,
            cantidad_inicial=5, stock_actual=5,
            costo_unitario=Decimal('1000.00'), costo_total=Decimal('5000.00'),
        )
        self.assertEqual(self.presentacion.stock_real, 15)

    def test_presentaciones_related_name_desde_producto(self):
        """Se accede a presentaciones desde el producto con .presentaciones."""
        self.assertIn(
            self.presentacion,
            self.producto.presentaciones.all()
        )


# ─────────────────────────────────────────────
#  TESTS: Vistas de PresentacionProducto
# ─────────────────────────────────────────────
class PresentacionViewsTest(TestCase):

    def setUp(self):
        Usuario = get_user_model()
        self.user = Usuario.objects.create_user(
            correo='test@cys.com', nombre='Test', apellido='User',
            documento='123', password='clave123'
        )
        self.client.force_login(self.user)

        self.categoria = Categoria.objects.create(codigo='CAT01', nombre='Medicamentos')
        self.producto = Producto.objects.create(
            nombre='Ibuprofeno', descripcion='Analgésico',
            fecha_vencimiento='2027-01-01', categoria=self.categoria,
        )
        self.presentacion = PresentacionProducto.objects.create(
            producto=self.producto, nombre='Caja x10',
            cantidad=10, precio_venta=Decimal('15000.00')
        )

    def test_lista_requiere_login(self):
        """Sin login, redirige (no da 200 directo)."""
        self.client.logout()
        resp = self.client.get(reverse('presentacion_lista'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lista_devuelve_200(self):
        resp = self.client.get(reverse('presentacion_lista'))
        self.assertEqual(resp.status_code, 200)

    def test_lista_incluye_presentaciones_en_contexto(self):
        resp = self.client.get(reverse('presentacion_lista'))
        self.assertIn(self.presentacion, resp.context['presentaciones'])

    def test_crear_presentacion_valida(self):
        resp = self.client.post(
            reverse('presentacion_crear', args=[self.producto.pk]),
            {'nombre': 'Six-pack', 'cantidad': '6', 'precio_venta': '9000', 'observaciones': ''}
        )
        self.assertRedirects(resp, reverse('presentacion_lista'))
        self.assertTrue(
            PresentacionProducto.objects.filter(producto=self.producto, nombre='Six-pack').exists()
        )

    def test_crear_presentacion_sin_nombre_no_crea(self):
        total_antes = PresentacionProducto.objects.count()
        self.client.post(
            reverse('presentacion_crear', args=[self.producto.pk]),
            {'nombre': '', 'cantidad': '6', 'precio_venta': '9000'}
        )
        self.assertEqual(PresentacionProducto.objects.count(), total_antes)

    def test_editar_presentacion_actualiza_campos(self):
        resp = self.client.post(
            reverse('presentacion_editar', args=[self.presentacion.pk]),
            {'nombre': 'Caja x20', 'cantidad': '20', 'precio_venta': '25000', 'observaciones': 'nota'}
        )
        self.assertRedirects(resp, reverse('presentacion_lista'))
        self.presentacion.refresh_from_db()
        self.assertEqual(self.presentacion.nombre, 'Caja x20')
        self.assertEqual(self.presentacion.cantidad, 20)
        self.assertEqual(self.presentacion.precio_venta, Decimal('25000.00'))

    def test_editar_actualiza_costo_unitario_de_lotes(self):
        """Al cambiar el precio_venta, sus lotes deben actualizar costo_unitario."""
        bodega = Bodega.objects.create(nombre='Principal', estado='activo')
        lote = Lote.objects.create(
            numero_lote='LOT-01', producto=self.producto, presentacion=self.presentacion, bodega=bodega,
            cantidad_inicial=10, stock_actual=10,
            costo_unitario=Decimal('1000.00'), costo_total=Decimal('10000.00'),
        )
        self.client.post(
            reverse('presentacion_editar', args=[self.presentacion.pk]),
            {'nombre': 'Caja x10', 'cantidad': '10', 'precio_venta': '30000'}
        )
        lote.refresh_from_db()
        self.assertEqual(lote.costo_unitario, Decimal('30000.00'))

    def test_toggle_activo_desactiva(self):
        self.assertTrue(self.presentacion.activo)
        self.client.post(reverse('presentacion_toggle_activo', args=[self.presentacion.pk]))
        self.presentacion.refresh_from_db()
        self.assertFalse(self.presentacion.activo)

    def test_toggle_activo_reactiva(self):
        self.presentacion.activo = False
        self.presentacion.save()
        self.client.post(reverse('presentacion_toggle_activo', args=[self.presentacion.pk]))
        self.presentacion.refresh_from_db()
        self.assertTrue(self.presentacion.activo)
# ─────────────────────────────────────────────
#  DATOS BASE COMPARTIDOS (setUp)
# ─────────────────────────────────────────────
class BaseTestCase(TestCase):
    """Crea los objetos mínimos que los tests de Lote necesitan."""

    def setUp(self):
        # Usuario es un modelo custom (AbstractBaseUser), no el User estándar de Django.
        # Su manager exige correo, nombre, apellido y documento (documento es la PK).
        self.usuario = Usuario.objects.create_user(
            correo='test@correo.com',
            nombre='Test',
            apellido='User',
            documento='1234567890',
            password='testpass123'
        )

        self.categoria = Categoria.objects.create(
            codigo='CAT01',
            nombre='Medicamentos'
        )

        # fecha_vencimiento ahora es obligatoria en Producto (antes ni existía aquí).
        # Ya no existe el campo 'codigo' en Producto.
        self.producto = Producto.objects.create(
            nombre='Ibuprofeno',
            descripcion='Analgésico de prueba',
            fecha_vencimiento=date.today() + timedelta(days=365),
            categoria=self.categoria
        )

        # 'unidades' no existe en PresentacionProducto; 'precio' ahora es 'precio_venta'.
        self.presentacion = PresentacionProducto.objects.create(
            producto=self.producto,
            nombre='Caja x10',
            cantidad=10,
            precio_venta=Decimal('15000.00')
        )

        # Bodega es obligatoria para crear un Lote ahora.
        self.bodega = Bodega.objects.create(
            nombre='Bodega Principal',
            descripcion='Bodega de prueba',
            estado='activo',
            capacidad=500
        )

        # 'registrado_por' y 'fecha_vencimiento' ya no existen en Lote.
        # 'producto', 'presentacion', 'bodega' y 'costo_total' ahora son obligatorios.
        self.lote = Lote.objects.create(
            numero_lote='LOTE-001',
            producto=self.producto,
            presentacion=self.presentacion,
            bodega=self.bodega,
            costo_unitario=Decimal('1200.00'),
            costo_total=Decimal('120000.00'),
            cantidad_inicial=100,
            stock_actual=100
        )


# ─────────────────────────────────────────────
#  TESTS: Lote
# ─────────────────────────────────────────────
class LoteModelTest(BaseTestCase):

    def test_str_retorna_numero_lote_y_presentacion(self):
        """__str__ debe mostrar número de lote y presentación."""
        esperado = f"{self.lote.numero_lote} - {self.presentacion}"
        self.assertEqual(str(self.lote), esperado)

    def test_numero_lote_es_unico(self):
        """No se pueden crear dos lotes con el mismo número."""
        with self.assertRaises(IntegrityError):
            Lote.objects.create(
                numero_lote='LOTE-001',  # duplicado
                producto=self.producto,
                presentacion=self.presentacion,
                bodega=self.bodega,
                stock_actual=50,
                costo_unitario=Decimal('1000.00'),
                costo_total=Decimal('50000.00')
            )

    # NOTA: se eliminó test_dias_para_vencer_sin_fecha y
    # test_proximo_a_vencer_falso_sin_fecha — ya no aplican porque
    # Producto.fecha_vencimiento es obligatoria (no acepta NULL), así
    # que ya no existe el escenario "sin fecha".

    def test_dias_para_vencer_con_fecha_futura(self):
        """Debe retornar número positivo si el producto vence en el futuro."""
        self.producto.fecha_vencimiento = date.today() + timedelta(days=10)
        self.producto.save()
        self.assertEqual(self.lote.dias_para_vencer, 10)

    def test_esta_vencido_con_fecha_pasada(self):
        """Debe retornar True si la fecha de vencimiento del producto ya pasó."""
        self.producto.fecha_vencimiento = date.today() - timedelta(days=1)
        self.producto.save()
        self.assertTrue(self.lote.esta_vencido)

    def test_esta_vencido_con_fecha_futura(self):
        """Debe retornar False si el producto aún no ha vencido."""
        self.producto.fecha_vencimiento = date.today() + timedelta(days=5)
        self.producto.save()
        self.assertFalse(self.lote.esta_vencido)

    def test_proximo_a_vencer_dentro_de_30_dias(self):
        """Debe retornar True si el producto vence en 0 a 30 días."""
        self.producto.fecha_vencimiento = date.today() + timedelta(days=20)
        self.producto.save()
        self.assertTrue(self.lote.proximo_a_vencer)

    def test_proximo_a_vencer_falso_si_vence_despues_de_30_dias(self):
        """Debe retornar False si el producto vence en más de 30 días."""
        self.producto.fecha_vencimiento = date.today() + timedelta(days=31)
        self.producto.save()
        self.assertFalse(self.lote.proximo_a_vencer)

    def test_stock_actual_no_puede_ser_negativo(self):
        """PositiveIntegerField rechaza valores negativos."""
        lote = Lote(
            numero_lote='LOTE-NEG',
            producto=self.producto,
            presentacion=self.presentacion,
            bodega=self.bodega,
            stock_actual=-1,
            costo_unitario=Decimal('1000.00'),
            costo_total=Decimal('50000.00')
        )
        with self.assertRaises(Exception):
            lote.full_clean()

    def test_ordering_por_fecha_registro_descendente(self):
        """Los lotes más recientes deben aparecer primero."""
        lote2 = Lote.objects.create(
            numero_lote='LOTE-002',
            producto=self.producto,
            presentacion=self.presentacion,
            bodega=self.bodega,
            stock_actual=50,
            costo_unitario=Decimal('1000.00'),
            costo_total=Decimal('50000.00')
        )
        primero = Lote.objects.first()
        self.assertEqual(primero, lote2)
        
        # app/tests.py — DetalleProducto (modelo + vistas)


class BaseDetalleProductoTestCase(TestCase):
    """Objetos mínimos que los tests de DetalleProducto necesitan."""

    def setUp(self):
        self.categoria = Categoria.objects.create(
            codigo='CAT01',
            nombre='Licores'
        )

        self.producto = Producto.objects.create(
            nombre='Ron Viejo de Caldas',
            descripcion='Ron añejo',
            fecha_vencimiento=date.today() + timedelta(days=365),
            categoria=self.categoria
        )

        # Marca no tiene null=True/blank=True en ningún campo salvo el default de PK,
        # así que nombre, descripcion y estado son obligatorios al crearla.
        self.marca = Marca.objects.create(
            nombre='Ron Caldas',
            descripcion='Marca de prueba',
            estado='activo'
        )

        self.detalle = DetalleProducto.objects.create(
            codigo_barras='7701234567890',
            fecha_vencimiento=date.today() + timedelta(days=180),
            descripcion='Botella 750ml',
            marca=self.marca,
            producto=self.producto
        )


class DetalleProductoModelTest(BaseDetalleProductoTestCase):

    def test_str_retorna_codigo_barras_y_nombre_producto(self):
        """__str__ debe mostrar código de barras y nombre del producto."""
        esperado = f"{self.detalle.codigo_barras} - {self.producto.nombre}"
        self.assertEqual(str(self.detalle), esperado)

    def test_codigo_barras_es_unico(self):
        """No se pueden crear dos detalles con el mismo código de barras."""
        with self.assertRaises(IntegrityError):
            DetalleProducto.objects.create(
                codigo_barras='7701234567890',  # duplicado
                fecha_vencimiento=date.today() + timedelta(days=90),
                marca=self.marca,
                producto=self.producto
            )

    def test_descripcion_puede_ser_nula(self):
        """descripcion tiene blank=True, null=True — es opcional."""
        detalle = DetalleProducto.objects.create(
            codigo_barras='7709999999999',
            fecha_vencimiento=date.today() + timedelta(days=90),
            marca=self.marca,
            producto=self.producto
        )
        self.assertIsNone(detalle.descripcion)

    def test_fecha_vencimiento_es_obligatoria(self):
        """fecha_vencimiento no tiene null=True — omitirla debe fallar."""
        with self.assertRaises(IntegrityError):
            DetalleProducto.objects.create(
                codigo_barras='7708888888888',
                marca=self.marca,
                producto=self.producto
            )

    def test_marca_es_obligatoria(self):
        """marca no acepta null — omitirla debe fallar."""
        with self.assertRaises(IntegrityError):
            DetalleProducto.objects.create(
                codigo_barras='7707777777777',
                fecha_vencimiento=date.today() + timedelta(days=90),
                producto=self.producto
            )

    def test_producto_es_obligatorio(self):
        """producto no acepta null — omitirlo debe fallar."""
        with self.assertRaises(IntegrityError):
            DetalleProducto.objects.create(
                codigo_barras='7706666666666',
                fecha_vencimiento=date.today() + timedelta(days=90),
                marca=self.marca
            )

    def test_relacion_con_producto_related_name(self):
        """related_name='detalles' debe permitir producto.detalles.all()."""
        self.assertIn(self.detalle, self.producto.detalles.all())

    def test_relacion_con_marca_related_name(self):
        """related_name='productos' en Marca debe exponer los detalles asociados."""
        self.assertIn(self.detalle, self.marca.productos.all())

    def test_eliminar_producto_elimina_detalle_en_cascada(self):
        """on_delete=CASCADE: borrar el producto borra su(s) detalle(s)."""
        detalle_pk = self.detalle.pk
        self.producto.delete()
        self.assertFalse(DetalleProducto.objects.filter(pk=detalle_pk).exists())

    def test_eliminar_marca_elimina_detalle_en_cascada(self):
        """on_delete=CASCADE: borrar la marca borra el detalle asociado."""
        detalle_pk = self.detalle.pk
        self.marca.delete()
        self.assertFalse(DetalleProducto.objects.filter(pk=detalle_pk).exists())


# ─────────────────────────────────────────────
#  TESTS: Vistas de DetalleProducto
# ─────────────────────────────────────────────
class DetalleProductoViewsTest(BaseDetalleProductoTestCase):

    def setUp(self):
        super().setUp()
        self.usuario_login = Usuario.objects.create_user(
            correo='login@correo.com',
            nombre='Login',
            apellido='Test',
            documento='9999999999',
            password='testpass123'
        )

    # ── lista ──
    def test_lista_requiere_login(self):
        """Usuario anónimo debe ser redirigido (login_required)."""
        response = self.client.get(reverse('detalle_producto_lista'))
        self.assertEqual(response.status_code, 302)

    def test_lista_ok_autenticado(self):
        self.client.login(correo='login@correo.com', password='testpass123')
        response = self.client.get(reverse('detalle_producto_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.detalle, response.context['detalles'])

    # ── crear ──
    def test_crear_get_no_crea_nada(self):
        """La vista solo procesa datos en POST; un GET no debe crear registros."""
        self.client.login(correo='login@correo.com', password='testpass123')
        antes = DetalleProducto.objects.count()
        self.client.get(reverse('detalle_producto_crear', args=[self.producto.pk]))
        self.assertEqual(DetalleProducto.objects.count(), antes)

    def test_crear_post_valido_crea_detalle(self):
        self.client.login(correo='login@correo.com', password='testpass123')
        antes = DetalleProducto.objects.count()

        response = self.client.post(
            reverse('detalle_producto_crear', args=[self.producto.pk]),
            {
                'codigo_barras': '7701111111111',
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=90)).isoformat(),
                'descripcion': 'Nuevo detalle de prueba',
            }
        )

        self.assertEqual(DetalleProducto.objects.count(), antes + 1)
        nuevo = DetalleProducto.objects.get(codigo_barras='7701111111111')
        self.assertEqual(nuevo.producto, self.producto)
        self.assertRedirects(response, reverse('producto_detalle', args=[self.producto.pk]))

    def test_crear_post_invalido_no_crea_detalle(self):
        """codigo_barras vacío debe fallar la validación del form (es obligatorio)."""
        self.client.login(correo='login@correo.com', password='testpass123')
        antes = DetalleProducto.objects.count()

        self.client.post(
            reverse('detalle_producto_crear', args=[self.producto.pk]),
            {
                'codigo_barras': '',
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=90)).isoformat(),
            }
        )
        self.assertEqual(DetalleProducto.objects.count(), antes)

    def test_crear_post_codigo_duplicado_no_crea_detalle(self):
        """codigo_barras es unique — reusar uno existente debe fallar la validación."""
        self.client.login(correo='login@correo.com', password='testpass123')
        antes = DetalleProducto.objects.count()

        self.client.post(
            reverse('detalle_producto_crear', args=[self.producto.pk]),
            {
                'codigo_barras': self.detalle.codigo_barras,  # duplicado
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=90)).isoformat(),
            }
        )
        self.assertEqual(DetalleProducto.objects.count(), antes)

    # ── editar ──
    def test_editar_post_valido_actualiza_detalle(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.post(
            reverse('detalle_producto_editar', args=[self.detalle.pk]),
            {
                'codigo_barras': self.detalle.codigo_barras,
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=200)).isoformat(),
                'descripcion': 'Descripción actualizada',
            }
        )

        self.detalle.refresh_from_db()
        self.assertEqual(self.detalle.descripcion, 'Descripción actualizada')
        self.assertRedirects(response, reverse('detalle_producto_lista'))

    def test_editar_post_ajax_valido_retorna_json_ok(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.post(
            reverse('detalle_producto_editar', args=[self.detalle.pk]),
            {
                'codigo_barras': self.detalle.codigo_barras,
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=200)).isoformat(),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})

    def test_editar_post_ajax_invalido_retorna_json_400(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.post(
            reverse('detalle_producto_editar', args=[self.detalle.pk]),
            {
                'codigo_barras': '',  # inválido: obligatorio
                'marca': self.marca.pk,
                'fecha_vencimiento': (date.today() + timedelta(days=200)).isoformat(),
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])
        self.assertIn('codigo_barras', response.json()['errores'])

    # ── guardar_codigo ──
    def test_guardar_codigo_post_valido(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.post(
            reverse('guardar_codigo', args=[self.detalle.pk]),
            {'codigo_barras': '7702222222222'}
        )

        self.detalle.refresh_from_db()
        self.assertEqual(self.detalle.codigo_barras, '7702222222222')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])

    def test_guardar_codigo_vacio_retorna_error(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.post(
            reverse('guardar_codigo', args=[self.detalle.pk]),
            {'codigo_barras': ''}
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_guardar_codigo_duplicado_retorna_error(self):
        """No debe permitir un código de barras que ya existe en OTRO detalle."""
        self.client.login(correo='login@correo.com', password='testpass123')

        otro_detalle = DetalleProducto.objects.create(
            codigo_barras='7703333333333',
            fecha_vencimiento=date.today() + timedelta(days=90),
            marca=self.marca,
            producto=self.producto
        )

        response = self.client.post(
            reverse('guardar_codigo', args=[otro_detalle.pk]),
            {'codigo_barras': self.detalle.codigo_barras}  # ya usado por self.detalle
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_guardar_codigo_get_no_permitido(self):
        self.client.login(correo='login@correo.com', password='testpass123')

        response = self.client.get(reverse('guardar_codigo', args=[self.detalle.pk]))
        self.assertEqual(response.status_code, 405)

