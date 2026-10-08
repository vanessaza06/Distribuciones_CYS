from decimal import Decimal

from django.core.management.base import BaseCommand

from app.models import Categoria, PresentacionProducto, Producto  # type: ignore

# (producto/marca, presentación, contenido, empaque)
CERVEZAS = [
    ("Águila", "Botella", "1.000 ml", "x13"),
    ("Águila", "Botella", "750 ml", None),
    ("Águila", "Lata", "269 ml", "x6"),
    ("Águila", "Lata", "473 ml", "x6"),
    ("Águila Light", "Lata", "269 ml", None),
    ("Águila Light", "Lata", "473 ml", "x6"),
    ("Águila Zero", "Lata", "269 ml", None),
    ("Club Colombia", "Botella", "850 ml", "x13"),
    ("Club Colombia", "Botella", "473 ml", None),
    ("Club Colombia Trigo", "Botella", "330 ml", None),
    ("Club Colombia", "Lata", "473 ml", None),
    ("Club Colombia", "Lata", "330 ml", "x6"),
    ("Club Roja", "Lata", "330 ml", "x6"),
    ("Club Negra", "Lata", "330 ml", "x6"),
    ("Corona", "Botella", "330 ml", "x6"),
    ("Corona", "Lata", "269 ml", "x6"),
    ("Corona", "Lata", "473 ml", None),
    ("Corona Cero", "Lata", None, "x24"),
    ("Coronita", "Botella", "210 ml", "x6"),
    ("Costeña", "Botella", "750 ml", "x16"),
    ("Poker", "Botella", "1.000 ml", "x13"),
    ("Poker", "Botella", "750 ml", None),
    ("Poker", "Lata", "330 ml", "x6"),
    ("Poker", "Lata", "473 ml", None),
    ("Heineken", "Lata", "269 ml", None),
    ("Heineken", "Lata", "310 ml", None),
    ("Heineken", "Botella", "330 ml", "x24"),
    ("Heineken", "Botella", "250 ml", "x30"),
    ("Heineken", "Botella", "250 ml", "x24"),
    ("Sol", "Botella", "250 ml", "x24"),
    ("Sol", "Lata", "310 ml", None),
    ("Tecate", "Botella", "330 ml", None),
    ("Tecate", "Botella", "750 ml", "x16"),
    ("Tecate", "Lata", None, None),
]

LICORES_NACIONALES = [
    ("Líder", "Botella", None, None),
    ("Líder", "Garrafa", None, None),
    ("Líder", "Media", None, None),
    ("Líder", "Botella PET", "750 ml", None),
    ("Líder", "Botella PET", "2 L", None),
    ("Líder", "Cuarto", None, None),
    ("Líder Verde", "Botella", None, None),
    ("Líder Verde", "Media", None, None),
    ("Líder Verde", "Garrafa", "2 L", None),
    ("Onix", "Botella", None, None),
    ("Onix", "Media", None, None),
    ("Onix", "Garrafa", None, None),
    ("Onix", "Cuarto", None, None),
    ("Onix Sin Azúcar", "Botella", "750 ml", None),
    ("Onix Sin Azúcar", "Botella", "375 ml", None),
    ("Onix Sin Azúcar", "Botella", "175 ml", None),
    ("Ron Boyacá", "Botella", None, None),
    ("Ron Boyacá", "Media", None, None),
    ("Ron Boyacá", "Cuarto", None, None),
    ("Ron Caldas", "Botella", None, None),
    ("Ron Caldas", "Media", None, None),
    ("Ron Caldas", "Cuarto", None, None),
    ("Ron Caldas", "Botella", "1.000 ml", None),
    ("Ron Caldas 5 años", "Botella", None, None),
    ("Ron Caldas 5 años", "Media", None, None),
    ("Ron Caldas 8 años", "Botella", None, None),
    ("Ron Caldas 8 años", "Media", None, None),
    ("Ron Caldas", "Licor", "750 ml", None),
    ("Ron Caldas", "Licor", "375 ml", None),
    ("Antioqueño", "Botella", "750 ml", None),
    ("Antioqueño", "Botella", "375 ml", None),
    ("Antioqueño Verde", "Botella", "750 ml", None),
    ("Antioqueño Verde", "Botella", "375 ml", None),
]

# (código, nombre de la categoría, filas)
GRUPOS = [
    ("CERV", "Cervezas", CERVEZAS),
    ("LICN", "Licores nacionales", LICORES_NACIONALES),
]


class Command(BaseCommand):
    help = "Carga las presentaciones iniciales (cervezas y licores nacionales) (sin duplicar)."

    def handle(self, *args, **options):
        productos_nuevos = pres_nuevas = 0

        for codigo, nombre_cat, filas in GRUPOS:
            categoria, _ = Categoria.objects.get_or_create(
                codigo=codigo, defaults={"nombre": nombre_cat}
            )
            for marca, tipo, contenido, empaque in filas:
                producto = Producto.objects.filter(nombre__iexact=marca).first()
                if producto is None:
                    producto = Producto.objects.create(
                        nombre=marca, descripcion=nombre_cat, categoria=categoria
                    )
                    productos_nuevos += 1

                nombre = " ".join(p for p in (tipo, contenido, empaque) if p)
                cantidad = int(empaque[1:]) if empaque else 1

                _, creada = PresentacionProducto.objects.get_or_create(
                    producto=producto,
                    nombre=nombre,
                    defaults={"cantidad": cantidad, "precio_venta": Decimal("0")},
                )
                pres_nuevas += creada

        self.stdout.write(self.style.SUCCESS(
            f"Productos creados: {productos_nuevos}. Presentaciones creadas: {pres_nuevas}. "
            f"Total presentaciones en BD: {PresentacionProducto.objects.count()}"
        ))
