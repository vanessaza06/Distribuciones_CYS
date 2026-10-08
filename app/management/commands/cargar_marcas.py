from django.core.management.base import BaseCommand

from app.models import Marca  # type: ignore

# Categoría -> marcas. La categoría se guarda como descripción de la marca.
MARCAS = {
    "Cervezas": [
        "Águila", "Águila Imperial", "Águila Light", "Águila Zero", "Andina",
        "Andina Light", "Andina Refajo", "Bacana", "Budweiser", "Club Colombia",
        "Club Dorada", "Club Negra", "Club Roja", "Club Trigo", "Cola y Pola",
        "Corona", "Corona Cero", "Coronita", "Costeña", "Heineken",
        "Heineken 0.0", "Kaufmann", "Modelo", "Miller Lite", "Poker", "Redd’s",
        "Sol", "Stella Artois", "Tecate", "Tres Cordilleras",
    ],
    "Licores nacionales": [
        "Líder", "Onix", "Ron Boyacá", "Amarillo", "Ron Caldas",
        "Ron Crema Caldas", "Molendero", "Cóctel Caldas", "Ginebra Bosque de Indias",
        "Aguardiente Antioqueño", "Aguardiente Blanco",
    ],
    "Maltas y bebidas": ["NatuMalta", "Pony", "Zalva"],
    "Aguas, energizantes y bebidas": [
        "Pool", "Agua Vida", "Zend", "Cifrut", "Pulp", "Néctar", "Saviloe",
        "Sporade", "Vive 100", "Electrolit", "Hidralite", "Amper", "Red Bull", "Speed",
    ],
    "Gaseosas y refrescos": [
        "Brisa", "Coca-Cola", "Coca-Cola Zero", "Fuze Tea", "Kola Román",
        "Manantial", "Monster", "Powerade", "Quatro", "Schweppes", "Sprite",
        "Valle", "Big Cola", "Postobón", "Pepsi", "Mr. Tea", "Acqua", "Bretaña",
        "Canadá Dry", "Cristal", "Hatsu", "Hit", "H2O", "Duos", "EconoLitro",
        "Squash", "Tropicola", "Tutti Frutti", "Gatorade",
    ],
    "Cigarrillos y encendedores": [
        "Mustang", "Mustang Blanco", "Mustang Foresta", "Lucki", "L&M",
        "Marlboro", "Caribe", "Piel Roja", "Yama", "BIC",
    ],
    "Whisky": [
        "Buchanan's", "Old Parr", "Johnnie Walker", "Chivas Regal",
        "Clan MacGregor", "Glenlivet", "Dewar's", "Jack Daniel's", "Ballantine's",
        "Black & White", "Something Special", "Passport", "VAT 69", "John Thomas",
        "Jameson", "Sir Edwards", "Harry", "Grants", "Singleton", "Grands",
        "Haward", "Black Jack", "Castle House", "Jägermeister",
    ],
    "Vodka": ["Smirnoff", "Absolut", "Tropcaya", "Stalinaya"],
    "Tequila": [
        "El Jimador", "Newton", "Puerta Negra", "Don Julio", "José Cuervo",
        "Tres Caballos", "Olmeca", "1800", "Los Cuates", "Patrón", "Altos",
    ],
    "Ron": ["Bacardí", "Ron Trópico", "Ron Santero"],
    "Cremas de whisky": [
        "Baileys", "Copacabana", "Castel Hause", "Black Jack", "Savors",
        "Whisleys", "Coloma", "Brymor", "Excelso", "Surtilégio",
    ],
    "Champañas y espumantes": [
        "Majestic", "Gran Brindis", "Peterlongo", "Casanova", "Alejandría",
        "Monserrate", "Frizzantino", "Gran Celebración", "Piccini", "Alteza",
        "Lambrusco", "JP Chenet", "Porttuse",
    ],
    "Vinos": [
        "Grajales", "Waltier", "Moscato Passito", "Embajador", "Casillero del Diablo",
        "Dubonet", "Mani Shewtiz", "Frontera", "Gato Negro", "Sangre de Boe",
        "Liebfraumilch", "Sanzón", "Cariñoso", "Moscatel", "Cinzano",
        "Dulce Amador", "Closs", "La Feria", "Tocornal", "Pazzito", "Polero",
        "Tres Medallas", "Rosaleda", "La Merced", "Viña Maipo", "Viña Piña",
        "Covier", "Arizo",
    ],
    "Ginebra": ["London", "Gordon's", "Sterling", "Haward"],
    "Otros licores y cócteles": [
        "Piña Colada Reagee", "Piña Colada Mavi", "Manzanilla Poderosa",
        "Piña Colada Isleña", "Paris Ice", "Sabajón", "Sabajón Apolo",
        "Piña Colada Tahití", "Brandy Domeco", "Brandy Cinco Estrellas",
        "Brandy Grajales", "Brandy Gran Brindis", "Four Loko",
    ],
}


class Command(BaseCommand):
    help = "Carga las marcas iniciales (sin duplicar las ya existentes)."

    def handle(self, *args, **options):
        existentes = {m.nombre.strip().lower(): m for m in Marca.objects.all()}
        creadas = actualizadas = 0

        for categoria, nombres in MARCAS.items():
            for nombre in nombres:
                clave = nombre.strip().lower()
                marca = existentes.get(clave)
                if marca is None:
                    existentes[clave] = Marca.objects.create(
                        nombre=nombre, descripcion=categoria, estado="activo"
                    )
                    creadas += 1
                elif not marca.descripcion:
                    marca.nombre = marca.nombre.strip()
                    marca.descripcion = categoria
                    marca.save()
                    actualizadas += 1
                elif categoria not in marca.descripcion.split(" / "):
                    # Marca repetida en varias categorías (ej. Haward, Black Jack)
                    marca.descripcion += f" / {categoria}"
                    marca.save()

        self.stdout.write(self.style.SUCCESS(
            f"Marcas creadas: {creadas}. Existentes completadas: {actualizadas}. "
            f"Total en BD: {Marca.objects.count()}"
        ))
