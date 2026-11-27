import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.models import (
    Usuario as AppUsuario,
    Bodega,
    Categoria,
    Producto,
    PresentacionProducto,
    Lote,
    Marca,
    DetalleProducto,
    Proveedor,
    Compra,
    DetalleCompra,
    DevolucionProveedores,
    Caja,
    AperturaCaja,
    CierreCaja,
    Venta,
    DetalleVenta,
    Devolucion,
    DetalleDevolucion,
    MetodoPago,
    AgendaInventario,
    Hallazgo,
    ConfiguracionEmpresa,
    BackupRegistro,
)

UserAuth = get_user_model()


class Command(BaseCommand):
    help = "Puebla datos masivos, coherentes y relacionales para todos los modulos del sistema Distribuciones CYS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina datos operacionales antes de repoblar (manteniendo usuarios base)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("==> Iniciando poblado masivo de datos para Distribuciones CYS..."))

        with transaction.atomic():
            # 1. Configuración de Empresa
            config, _ = ConfiguracionEmpresa.objects.get_or_create(
                pk=1,
                defaults={
                    "nombre_empresa": "Distribuciones CYS S.A.S.",
                    "nit": "901.458.789-2",
                    "direccion": "Calle 45 # 12-80, Tunja, Boyacá",
                    "telefono": "+57 (608) 742-9988",
                    "email": "contacto@distribucionescys.com",
                    "iva_porcentaje": Decimal("19.00"),
                    "moneda": "COP",
                    "unidades_medida": ["Unidad", "Botella", "Lata", "Sixpack", "Caja", "Canasta"],
                    "tema_predeterminado": "oscuro",
                },
            )
            self.stdout.write(self.style.SUCCESS("[OK] Módulo Empresa: Configuración empresarial lista."))

            # 2. Usuarios del sistema (Tanto Auth User como App Usuario para compatibilidad total)
            usuarios_data = [
                ("admin", "admin@cys.com", "Admin", "General", "1001", "admin", "administrador"),
                ("supervisor1", "supervisor@cys.com", "Carlos", "Ramírez", "1002", "admin", "administrador"),
                ("cajero1", "cajero1@cys.com", "Ana", "Gómez", "1003", "cajero", "cajero"),
                ("cajero2", "cajero2@cys.com", "Mateo", "Pérez", "1004", "cajero", "cajero"),
                ("bodeguero1", "bodega@cys.com", "Julián", "Torres", "1005", "admin", "administrador"),
            ]
            auth_users_dict = {}
            app_users_dict = {}

            for username, email, fn, ln, ident, auth_rol, app_rol in usuarios_data:
                # 2.1 Modelo Auth (usuarios.Usuario)
                u_auth = UserAuth.objects.filter(username=username).first() or UserAuth.objects.filter(identificacion=ident).first()
                if not u_auth:
                    u_auth = UserAuth.objects.create(
                        username=username,
                        email=email,
                        first_name=fn,
                        last_name=ln,
                        identificacion=ident,
                        rol=auth_rol,
                        is_staff=(auth_rol == "admin"),
                        is_superuser=(auth_rol == "admin"),
                    )
                    u_auth.set_password("Password123!")
                    u_auth.save()
                auth_users_dict[username] = u_auth

                # 2.2 Modelo Legacy App (app.Usuario)
                u_app = AppUsuario.objects.filter(documento=ident).first() or AppUsuario.objects.filter(correo=email).first()
                if not u_app:
                    u_app = AppUsuario.objects.create_user(
                        correo=email,
                        nombre=fn,
                        apellido=ln,
                        documento=ident,
                        password="Password123!",
                    )
                u_app.rol = app_rol
                u_app.tipo_identificacion = "CC"
                u_app.save()
                app_users_dict[ident] = u_app

            # Asignaciones clave:
            # - Auth User (para Venta.vendedor, AperturaCaja.usuario)
            auth_admin = auth_users_dict["admin"]
            auth_cajero = auth_users_dict["cajero1"]
            # - App User (para Caja.usuario, Compra.usuario, AgendaInventario.responsable)
            app_admin = app_users_dict["1001"]
            app_bodeguero = app_users_dict["1005"]

            self.stdout.write(self.style.SUCCESS(f"[OK] Módulo Usuarios: 5 usuarios creados en ambos modelos auth/app."))

            # 3. Bodegas
            bodegas_data = [
                ("Bodega Principal", "Centro logístico y despacho mayorista principal", "activa", 50000),
                ("Bodega Secundaria", "Almacenamiento de alta rotación y punto de venta directo", "activa", 25000),
                ("Bodega Refrigerada", "Cámara de frío para cervezas, vinos y lácteos", "activa", 10000),
            ]
            bodegas_objs = []
            for nom, desc, est, cap in bodegas_data:
                b, _ = Bodega.objects.get_or_create(
                    nombre=nom,
                    defaults={"descripcion": desc, "estado": est, "capacidad": cap},
                )
                bodegas_objs.append(b)
            self.stdout.write(self.style.SUCCESS(f"[OK] Módulo Bodegas: {len(bodegas_objs)} bodegas verificadas."))

            # 4. Categorías y Subcategorías
            cat_jerarquia = [
                ("CAT-LIC", "Licores y Destilados", [
                    ("SUB-AGU", "Aguardiente"),
                    ("SUB-RON", "Ron Añejo"),
                    ("SUB-WHI", "Whisky"),
                    ("SUB-VOD", "Vodka"),
                ]),
                ("CAT-CER", "Cervezas", [
                    ("SUB-CNAC", "Cervezas Nacionales"),
                    ("SUB-CIMP", "Cervezas Importadas"),
                    ("SUB-CART", "Cervezas Artesanales"),
                ]),
                ("CAT-VIN", "Vinos y Espumosos", [
                    ("SUB-VTIN", "Vinos Tintos"),
                    ("SUB-VBLA", "Vinos Blancos"),
                    ("SUB-VESP", "Espumosos y Champaña"),
                ]),
                ("CAT-BEB", "Bebidas no alcohólicas", [
                    ("SUB-GAS", "Gaseosas y Sodas"),
                    ("SUB-ENE", "Energizantes e Hidratantes"),
                    ("SUB-AGUAS", "Agua y Zumos"),
                ]),
                ("CAT-SNA", "Snacks y Pasabocas", [
                    ("SUB-SAL", "Pasabocas Salados"),
                    ("SUB-DUL", "Confitería y Chocolates"),
                ]),
            ]
            subcategorias_list = []
            for cod_padre, nom_padre, subs in cat_jerarquia:
                padre, _ = Categoria.objects.get_or_create(
                    codigo=cod_padre,
                    defaults={"nombre": nom_padre, "descripcion": f"Categoría de {nom_padre}", "activo": True},
                )
                for cod_sub, nom_sub in subs:
                    sub, _ = Categoria.objects.get_or_create(
                        codigo=cod_sub,
                        defaults={
                            "nombre": nom_sub,
                            "descripcion": f"Subcategoría de {nom_sub}",
                            "subcategoria": padre,
                            "activo": True,
                        },
                    )
                    subcategorias_list.append(sub)
            self.stdout.write(self.style.SUCCESS(f"[OK] Módulo Categorías: {len(subcategorias_list)} subcategorías creadas."))

            # 5. Marcas
            marcas_data = [
                ("MAR-BAV", "Bavaria S.A."),
                ("MAR-POS", "Postobón S.A."),
                ("MAR-DIA", "Diageo Colombia"),
                ("MAR-ILC", "Industria Licorera de Caldas"),
                ("MAR-FLA", "Frito-Lay Colombia"),
                ("MAR-KO", "The Coca-Cola Company"),
                ("MAR-RB", "Red Bull GmbH"),
                ("MAR-PR", "Pernod Ricard"),
            ]
            marcas_dict = {}
            for cod, nom in marcas_data:
                m, _ = Marca.objects.get_or_create(
                    nombre=nom,
                    defaults={"descripcion": f"Productos oficiales de {nom}", "estado": "activo"},
                )
                marcas_dict[cod] = m
            self.stdout.write(self.style.SUCCESS(f"[OK] Módulo Marcas: {len(marcas_dict)} marcas creadas."))

            # 6. Proveedores
            proveedores_data = [
                ("860005224-1", "Bavaria & Cía S.C.A.", "3104509988", "ventas@bavaria.co", "fabricante"),
                ("890903939-5", "Gaseosas Posada Tobón S.A.", "3118907654", "pedidos@postobon.com", "fabricante"),
                ("900123456-7", "Distribuidora Internacional Diageo", "3156781234", "comercial@diageo.co", "importador"),
                ("890801020-3", "Industria Licorera de Caldas E.I.C.E.", "3209876543", "licores@ilc.com.co", "fabricante"),
                ("860001001-9", "PepsiCo Alimentos Colombia / Frito Lay", "3145678901", "distribucion@pepsico.com", "distribuidor"),
                ("900987654-2", "Importadora de Vinos Andinos S.A.S.", "3187654321", "info@vinosandinos.com", "importador"),
            ]
            proveedores_list = []
            for nit, nombre, tel, email, tipo in proveedores_data:
                p, _ = Proveedor.objects.get_or_create(
                    nit_proveedores=nit,
                    defaults={
                        "nombre_empresa": nombre,
                        "telefono": tel,
                        "correo": email,
                        "tipo_proveedor": tipo,
                        "estado": "activo",
                        "observacion": "Proveedor estratégico con crédito a 30 días",
                    },
                )
                proveedores_list.append(p)
            self.stdout.write(self.style.SUCCESS(f"[OK] Módulo Proveedores: {len(proveedores_list)} proveedores verificados."))

            # 7. Productos, Presentaciones y Lotes
            productos_catalogo = [
                ("Cerveza Poker Lata 330ml", "SUB-CNAC", "MAR-BAV", "Cerveza rubia tradicional colombiana", [
                    ("Lata 330ml", 1, Decimal("2600"), Decimal("3500"), 450),
                    ("Sixpack Lata 330ml", 6, Decimal("15000"), Decimal("19500"), 120),
                    ("Canasta x24 Latas", 24, Decimal("58000"), Decimal("74000"), 40),
                ]),
                ("Cerveza Águila Original 330ml", "SUB-CNAC", "MAR-BAV", "Cerveza clara y refrescante", [
                    ("Lata 330ml", 1, Decimal("2500"), Decimal("3300"), 400),
                    ("Sixpack Lata 330ml", 6, Decimal("14500"), Decimal("18500"), 90),
                    ("Canasta x24 Latas", 24, Decimal("56000"), Decimal("71000"), 35),
                ]),
                ("Cerveza Corona Extra 355ml", "SUB-CIMP", "MAR-BAV", "Cerveza tipo pilsner de importación", [
                    ("Botella 355ml", 1, Decimal("4800"), Decimal("6500"), 300),
                    ("Sixpack Botella", 6, Decimal("27000"), Decimal("36000"), 80),
                    ("Caja x24 Botellas", 24, Decimal("105000"), Decimal("138000"), 25),
                ]),
                ("Aguardiente Antioqueño Azul 750ml", "SUB-AGU", "MAR-ILC", "Aguardiente sin azúcar tapa azul", [
                    ("Botella 750ml", 1, Decimal("32000"), Decimal("42000"), 85),
                    ("Media 375ml", 1, Decimal("18000"), Decimal("24000"), 110),
                    ("Caja x12 Botellas", 12, Decimal("370000"), Decimal("480000"), 15),
                ]),
                ("Ron Viejo de Caldas Juan de la Cruz 750ml", "SUB-RON", "MAR-ILC", "Ron añejo 5 años", [
                    ("Botella 750ml", 1, Decimal("38000"), Decimal("51000"), 70),
                    ("Media 375ml", 1, Decimal("21000"), Decimal("28500"), 95),
                ]),
                ("Whisky Johnnie Walker Black Label 750ml", "SUB-WHI", "MAR-DIA", "Whisky escocés 12 años", [
                    ("Botella 750ml", 1, Decimal("110000"), Decimal("145000"), 45),
                    ("Caja x12 Botellas", 12, Decimal("1280000"), Decimal("1650000"), 8),
                ]),
                ("Vino Tinto Casillero del Diablo Cabernet 750ml", "SUB-VTIN", "MAR-PR", "Vino chileno reserva valle central", [
                    ("Botella 750ml", 1, Decimal("36000"), Decimal("49000"), 60),
                    ("Caja x6 Botellas", 6, Decimal("210000"), Decimal("280000"), 18),
                ]),
                ("Gaseosa Colombiana 1.5L", "SUB-GAS", "MAR-POS", "Gaseosa tradicional sabor a Kola", [
                    ("Botella PET 1.5L", 1, Decimal("3800"), Decimal("5200"), 180),
                    ("Pack x6 Botellas", 6, Decimal("22000"), Decimal("29500"), 50),
                ]),
                ("Bebida Energizante Red Bull 250ml", "SUB-ENE", "MAR-RB", "Bebida funcional energizante", [
                    ("Lata 250ml", 1, Decimal("5500"), Decimal("7500"), 220),
                    ("Fourpack 250ml", 4, Decimal("21000"), Decimal("28000"), 65),
                ]),
                ("Papas Margarita Pollo 110g", "SUB-SAL", "MAR-FLA", "Papas fritas con sabor a pollo", [
                    ("Paquete 110g", 1, Decimal("3200"), Decimal("4500"), 250),
                    ("Tira x6 Paquetes", 6, Decimal("18500"), Decimal("25000"), 75),
                ]),
            ]

            hoy = timezone.now()
            fecha_venc_default = (hoy + timedelta(days=365)).date()
            productos_creados = 0
            presentaciones_creadas = 0
            lotes_creados = 0

            for prod_idx, (p_nom, sub_cod, mar_cod, p_desc, pres_list) in enumerate(productos_catalogo, start=1):
                subcat = Categoria.objects.filter(codigo=sub_cod).first() or subcategorias_list[0]
                marca = marcas_dict.get(mar_cod)

                prod, _ = Producto.objects.get_or_create(
                    nombre=p_nom,
                    defaults={
                        "categoria": subcat,
                        "descripcion": p_desc,
                        "fecha_vencimiento": fecha_venc_default,
                    },
                )
                productos_creados += 1

                # Detalle de producto (código de barras EAN-13)
                ean13 = f"770{prod_idx:04d}{random.randint(100000, 999999)}"[:13]
                DetalleProducto.objects.get_or_create(
                    producto=prod,
                    defaults={
                        "marca": marca,
                        "codigo_barras": ean13,
                        "fecha_vencimiento": fecha_venc_default,
                    },
                )

                # Presentaciones y lotes
                for pres_idx, (pres_nom, pres_cant, costo, pventa, stock_inicial) in enumerate(pres_list, start=1):
                    pres, _ = PresentacionProducto.objects.get_or_create(
                        producto=prod,
                        nombre=pres_nom,
                        defaults={
                            "cantidad": pres_cant,
                            "precio_venta": pventa,
                        },
                    )
                    presentaciones_creadas += 1

                    # Crear Lote para que conecte la base de datos con stock real
                    bodega_target = bodegas_objs[prod_idx % len(bodegas_objs)]
                    num_lote = f"LT-2026-{prod_idx:02d}-{pres_idx:02d}"
                    costo_tot = costo * stock_inicial
                    lote, _ = Lote.objects.get_or_create(
                        numero_lote=num_lote,
                        presentacion=pres,
                        defaults={
                            "producto": prod,
                            "bodega": bodega_target,
                            "cantidad_inicial": stock_inicial,
                            "stock_actual": stock_inicial,
                            "costo_unitario": costo,
                            "costo_total": costo_tot,
                        },
                    )
                    lotes_creados += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Módulo Productos e Inventario: {productos_creados} productos, "
                    f"{presentaciones_creadas} presentaciones y {lotes_creados} lotes con stock activo."
                )
            )

            # 8. Cajas y Sesiones de Turno (Apertura y Cierre)
            caja_abierta, _ = Caja.objects.get_or_create(
                codigo_caja=1,
                defaults={
                    "monto_base": Decimal("200000.00"),
                    "total_efectivo": Decimal("850000.00"),
                    "total_transferencias": Decimal("320000.00"),
                    "total_retirado": Decimal("0.00"),
                    "observacion": "Caja operativa 01 - Turno Mañana y Tarde",
                    "usuario": app_admin,
                },
            )

            apertura_hoy, _ = AperturaCaja.objects.get_or_create(
                fecha=hoy.date(),
                defaults={
                    "monto_base": Decimal("200000.00"),
                    "usuario": auth_cajero,
                    "observacion": "Apertura estándar con cambio inicial",
                    "denominaciones": {"50000": 2, "20000": 3, "10000": 4},
                },
            )

            ayer = hoy.date() - timedelta(days=1)
            apertura_ayer, _ = AperturaCaja.objects.get_or_create(
                fecha=ayer,
                defaults={
                    "monto_base": Decimal("200000.00"),
                    "usuario": auth_cajero,
                    "observacion": "Turno finalizado y cuadrado",
                },
            )
            cierre_ayer, _ = CierreCaja.objects.get_or_create(
                fecha=ayer,
                defaults={
                    "apertura": apertura_ayer,
                    "total_contado": Decimal("1450000.00"),
                    "monto_base_siguiente": Decimal("200000.00"),
                    "total_retirado": Decimal("1250000.00"),
                    "denominaciones": {"100000": 8, "50000": 11, "20000": 5},
                },
            )
            self.stdout.write(self.style.SUCCESS("[OK] Módulo Cajas: Aperturas y cierres operativos registrados."))

            # 9. Compras a Proveedores
            compras_data = [
                (proveedores_list[0], Decimal("2850000.00"), Decimal("0.00"), "recibida"),
                (proveedores_list[1], Decimal("1450000.00"), Decimal("0.00"), "recibida"),
                (proveedores_list[2], Decimal("3200000.00"), Decimal("1000000.00"), "confirmada"),
                (proveedores_list[3], Decimal("1980000.00"), Decimal("0.00"), "recibida"),
            ]
            for prov, val_total, saldo, est in compras_data:
                compra = Compra.objects.create(
                    usuario=app_admin,
                    proveedor=prov,
                    valor=val_total,
                    saldo=saldo,
                    estado=est,
                    fecha=hoy - timedelta(days=random.randint(2, 20)),
                )
                # Detalle de compra
                prod_muestra = Producto.objects.order_by("?").first()
                if prod_muestra:
                    DetalleCompra.objects.create(
                        compra=compra,
                        producto=prod_muestra,
                        cantidad=50,
                        precio_unitario=Decimal("25000.00"),
                        subtotal_compra=Decimal("1250000.00"),
                    )
                # Método de pago de la compra
                MetodoPago.objects.create(
                    compra=compra,
                    valor=val_total - saldo,
                    transaccion=val_total - saldo,
                    referencia="TRF-Bancolombia-2026",
                )
            self.stdout.write(self.style.SUCCESS("[OK] Módulo Compras: 4 órdenes de compra con detalles y pagos."))

            # 10. Ventas y Facturación
            presentaciones_disponibles = list(PresentacionProducto.objects.select_related("producto").all())
            ventas_registradas = 0
            for v_idx in range(1, 13):
                fecha_v = hoy - timedelta(days=random.randint(0, 7), hours=random.randint(1, 8))
                pres_sel = random.choice(presentaciones_disponibles)
                cant_v = random.randint(1, 5)
                subtot = pres_sel.precio_venta * cant_v
                lote_sel = Lote.objects.filter(presentacion=pres_sel).first()

                v = Venta.objects.create(
                    vendedor=auth_cajero,
                    caja=caja_abierta,
                    fecha=fecha_v,
                    cliente_nombre=f"Cliente Frecuente {v_idx}",
                    cliente_email=f"cliente{v_idx}@correo.com",
                    total_venta=subtot,
                    total_con_descuento=subtot,
                    pago_efectivo=subtot,
                    metodo_pago="efectivo",
                    saldo_pendiente=Decimal("0.00"),
                    observacion=f"Venta en mostrador factura #{v_idx:04d}",
                )

                det_v = DetalleVenta.objects.create(
                    venta=v,
                    producto=pres_sel.producto,
                    presentacion=pres_sel,
                    lote=lote_sel,
                    cantidad=cant_v,
                    precio_unitario=pres_sel.precio_venta,
                    subtotal_val=subtot,
                    total_val=subtot,
                )
                ventas_registradas += 1

                # 11. Devoluciones (Generar 2 devoluciones de muestra)
                if v_idx in (2, 5):
                    dev = Devolucion.objects.create(
                        venta=v,
                        detalle_venta=det_v,
                        fecha=fecha_v + timedelta(hours=2),
                        motivo="defectuoso",
                        observaciones="Empaque con abolladura reportado por el cliente",
                        restaurar_stock=False,
                        tiene_comprobante=True,
                        total_devuelto=pres_sel.precio_venta,
                        tipo_devolucion="devolucion",
                        estado="activo",
                    )
                    DetalleDevolucion.objects.create(
                        devolucion=dev,
                        producto=pres_sel.producto,
                        presentacion=pres_sel,
                        lote=lote_sel,
                        cantidad=1,
                        precio_unitario=pres_sel.precio_venta,
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Módulo Ventas y Devoluciones: {ventas_registradas} ventas completas con detalles "
                    f"y 2 devoluciones procesadas."
                )
            )

            # 12. Devoluciones a Proveedores
            if proveedores_list:
                DevolucionProveedores.objects.create(
                    proveedor=proveedores_list[0],
                    motivo="defectuoso",
                    estado="aprobada",
                    observaciones="Lote recibido con botella partida en transporte",
                )
                self.stdout.write(self.style.SUCCESS("[OK] Módulo Proveedores: Devolución a proveedor registrada."))

            # 13. Agenda de Inventario y Hallazgos
            agenda, _ = AgendaInventario.objects.get_or_create(
                titulo="Auditoría Física y Conteo Cíclico Semanal",
                defaults={
                    "descripcion": "Verificación física de stock en Bodega Principal vs Sistema",
                    "fecha": hoy,
                    "tipo": "conteo_ciclico",
                    "estado": "en_proceso",
                    "documento_usuario": app_admin,
                    "responsable": app_bodeguero,
                },
            )

            prod_hallazgo = Producto.objects.first()
            if prod_hallazgo:
                Hallazgo.objects.get_or_create(
                    agenda=agenda,
                    producto=prod_hallazgo,
                    defaults={
                        "cantidad_sistema": 120,
                        "cantidad_fisica": 120,
                        "diferencia": 0,
                        "sesion_conteo": "Sesion-A1",
                        "tipo_hallazgo": "exacto",
                        "resultado_inventario": "Conforme al 100%",
                        "observaciones": "Inventario cuadrado sin novedades",
                    },
                )
            self.stdout.write(self.style.SUCCESS("[OK] Módulo Auditoría: Agenda de inventario y hallazgos registrados."))

            # 14. Registro de Respaldo de Base de Datos
            BackupRegistro.objects.get_or_create(
                nombre="Respaldo_Automatico_Semanal_MySQL.sql",
                defaults={
                    "descripcion": "Respaldo íntegro y consistente de la base de datos distribuidora_cys",
                    "ruta": "backups/Respaldo_Automatico_Semanal_MySQL.sql",
                    "tamaño_mb": 14.85,
                },
            )
            self.stdout.write(self.style.SUCCESS("[OK] Módulo Backups: Registro histórico de respaldo confirmado."))

        self.stdout.write(self.style.SUCCESS("\n[ÉXITO TOTAL] Se poblaron exitosamente datos masivos en TODOS los 14 módulos."))
