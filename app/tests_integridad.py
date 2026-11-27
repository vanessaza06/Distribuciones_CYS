"""
Pruebas unitarias de integridad referencial de base de datos y coherencia
de patrones de diseño para Distribuciones CYS.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, IntegrityError, models, transaction
from django.test import TestCase

from app.models import (
    Bodega, Categoria, Marca, Producto, DetalleProducto,
    PresentacionProducto, Lote, Proveedor, Compra, DetalleCompra,
    Caja, AperturaCaja, CierreCaja, Venta, DetalleVenta, PagoVenta,
    Devolucion, MetodoPago, BackupRegistro, ConfiguracionEmpresa
)

Usuario = get_user_model()


class IntegridadReferencialTablasTest(TestCase):
    """
    Verifica que todas las tablas de los modelos del sistema existan,
    tengan claves primarias válidas, relaciones de clave foránea coherentes
    y reglas de integridad referencial (CASCADE, PROTECT, SET_NULL).
    """

    def setUp(self):
        self.user = Usuario.objects.create_user(
            username='qa_integrity_user',
            identificacion='1098765432',
            first_name='Auditor',
            last_name='QA',
            email='qa@cys.com',
            password='Password123!',
            rol='admin'
        )

    def test_todas_las_tablas_existen_en_la_base_de_datos(self):
        """Cada modelo en 'app' y 'usuarios' debe tener su tabla física creada en la BD."""
        tablas_bd = connection.introspection.table_names()
        modelos = [
            m for m in apps.get_models()
            if m._meta.app_label in ('app', 'usuarios')
        ]
        self.assertGreater(len(modelos), 0)

        faltantes = []
        for modelo in modelos:
            tabla = modelo._meta.db_table
            if tabla not in tablas_bd:
                faltantes.append(f"{modelo._meta.app_label}.{modelo.__name__} (tabla: {tabla})")

        self.assertEqual(
            faltantes, [],
            f"Existen modelos sin tabla física en la base de datos: {faltantes}"
        )

    def test_todas_las_claves_foraneas_tienen_regla_on_delete_valida(self):
        """Todas las relaciones ForeignKey deben especificar explícitamente on_delete."""
        reglas_validas = {models.CASCADE, models.PROTECT, models.SET_NULL, models.DO_NOTHING, models.RESTRICT}
        for modelo in apps.get_models():
            if modelo._meta.app_label in ('app', 'usuarios'):
                for campo in modelo._meta.fields:
                    if campo.is_relation and campo.many_to_one:
                        on_delete = campo.remote_field.on_delete
                        self.assertIn(
                            on_delete, reglas_validas,
                            f"El campo {modelo.__name__}.{campo.name} no tiene una regla on_delete válida."
                        )

    def test_integridad_cascada_producto_presentacion_lote(self):
        """
        Integridad Referencial:
        - Borrar un Producto debe eliminar en CASCADA sus Presentaciones y Lotes.
        - Borrar una Bodega debe colocar en SET_NULL la referencia en Lote sin borrar el Lote.
        """
        cat = Categoria.objects.create(codigo='CAT-TEST', nombre='Bebidas Test')
        prod = Producto.objects.create(nombre='Cerveza Test', descripcion='Test', categoria=cat)
        pres = PresentacionProducto.objects.create(producto=prod, nombre='Unidad 330ml', precio_venta=Decimal('4500'), cantidad=1)
        bodega = Bodega.objects.create(nombre='Bodega Central Test', estado='activo')

        lote = Lote.objects.create(
            numero_lote='LOT-TEST-001',
            producto=prod,
            presentacion=pres,
            bodega=bodega,
            cantidad_inicial=100,
            stock_actual=100,
            costo_unitario=Decimal('2500'),
            costo_total=Decimal('250000')
        )

        self.assertEqual(Lote.objects.filter(pk=lote.pk).count(), 1)
        self.assertEqual(lote.bodega, bodega)

        # Probar SET_NULL en Bodega
        bodega.delete()
        lote.refresh_from_db()
        self.assertIsNone(lote.bodega, "Al borrar Bodega, lote.bodega debe quedar en NULL (SET_NULL).")

        # Probar CASCADE en Producto -> Presentacion y Lote
        prod.delete()
        self.assertEqual(PresentacionProducto.objects.filter(pk=pres.pk).count(), 0)
        self.assertEqual(Lote.objects.filter(pk=lote.pk).count(), 0)

    def test_integridad_proteccion_venta_vendedor_y_caja(self):
        """
        Integridad Referencial:
        - Venta tiene ForeignKey PROTECT con Usuario (vendedor) y Caja.
        - No debe permitirse borrar el Usuario vendedor si tiene ventas asociadas.
        """
        caja = Caja.objects.create(
            monto_base=Decimal('100000'),
            total_efectivo=Decimal('50000'),
            total_transferencias=Decimal('0'),
            total_retirado=Decimal('0')
        )
        venta = Venta.objects.create(
            vendedor=self.user,
            caja=caja,
            total_venta=Decimal('50000'),
            pago_efectivo=Decimal('50000'),
            metodo_pago='efectivo'
        )

        with self.assertRaises(models.ProtectedError):
            self.user.delete()

    def test_integridad_cascada_venta_detalle(self):
        """
        Integridad Referencial:
        - Al eliminar una Venta, sus detalles (DetalleVenta) deben eliminarse en CASCADA.
        """
        cat = Categoria.objects.create(codigo='CAT-V', nombre='Categoria V')
        prod = Producto.objects.create(nombre='Prod Venta', categoria=cat)
        pres = PresentacionProducto.objects.create(producto=prod, nombre='Caja x12', precio_venta=Decimal('30000'), cantidad=12)
        caja = Caja.objects.create(
            monto_base=Decimal('50000'),
            total_efectivo=Decimal('30000'),
            total_transferencias=Decimal('0'),
            total_retirado=Decimal('0')
        )

        venta = Venta.objects.create(
            vendedor=self.user,
            caja=caja,
            total_venta=Decimal('30000'),
            pago_efectivo=Decimal('30000'),
            metodo_pago='efectivo'
        )

        det = DetalleVenta.objects.create(
            venta=venta,
            producto=prod,
            presentacion=pres,
            cantidad=1,
            precio_unitario=Decimal('30000'),
            subtotal_val=Decimal('30000')
        )

        det_pk = det.pk
        venta.delete()
        self.assertFalse(DetalleVenta.objects.filter(pk=det_pk).exists())

    def test_restriccion_unicidad_categoria_codigo(self):
        """El código de categoría debe ser único en base de datos."""
        Categoria.objects.create(codigo='CAT-U1', nombre='Cat 1')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Categoria.objects.create(codigo='CAT-U1', nombre='Cat Duplicada')

    def test_restriccion_unicidad_lote_numero(self):
        """El número de lote debe ser único en base de datos."""
        cat = Categoria.objects.create(codigo='CAT-LOT', nombre='Cat Lot')
        prod = Producto.objects.create(nombre='Prod Lote Unico', categoria=cat)
        pres = PresentacionProducto.objects.create(producto=prod, nombre='Unidad', precio_venta=Decimal('1000'), cantidad=1)

        Lote.objects.create(
            numero_lote='LOT-EXCLUSIVO-99',
            producto=prod,
            presentacion=pres,
            cantidad_inicial=10,
            stock_actual=10,
            costo_unitario=Decimal('500'),
            costo_total=Decimal('5000')
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lote.objects.create(
                    numero_lote='LOT-EXCLUSIVO-99',
                    producto=prod,
                    presentacion=pres,
                    cantidad_inicial=5,
                    stock_actual=5,
                    costo_unitario=Decimal('500'),
                    costo_total=Decimal('2500')
                )


class CoexistenciaPatronDisenoTest(TestCase):
    """
    Verifica que todos los módulos del proyecto coexistan bajo el mismo
    patrón arquitectónico:
    - Organización por módulos funcionales (FBVs estandarizadas con decorators).
    - Protección de rutas con control de sesión (login_required).
    - Estandarización de contexto para plantillas (breadcrumb, tema, títulos).
    """

    def test_coherencia_modulos_vistas(self):
        """Todos los submódulos de vistas deben exponer funciones estándar y ser importables."""
        modulos_esperados = [
            'categorias', 'proveedores', 'marcas', 'productos', 'presentaciones',
            'lotes', 'detalle_producto', 'compra', 'devoluciones', 'bodega',
            'principal', 'ventas', 'reportes', 'configuracion', 'metodo_de_pago',
            'ayuda', 'respaldos'
        ]
        import importlib
        for mod in modulos_esperados:
            try:
                modulo = importlib.import_module(f"app.views.{mod}.views")
                self.assertIsNotNone(modulo, f"El módulo app.views.{mod}.views debe ser importable.")
            except ImportError as e:
                self.fail(f"Fallo al importar submódulo app.views.{mod}.views: {e}")

    def test_estandarizacion_rutas_y_seguridad_vistas(self):
        """Las vistas críticas no públicas deben redirigir a login para usuarios no autenticados."""
        rutas_protegidas = [
            'lista_productos',
            'categorias_lista',
            'lista_proveedores',
            'lista_marcas',
            'presentacion_lista',
            'lote_list',
            'gestion_stock',
            'bodega_home',
            'lista_compras',
            'ventas',
            'reportes',
            'respaldos_index',
            'configuracion_index',
        ]
        from django.urls import reverse
        for ruta in rutas_protegidas:
            url = reverse(ruta)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 302,
                f"La ruta '{ruta}' ({url}) debe requerir autenticación y responder 302 hacia login."
            )
