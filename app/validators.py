"""Validaciones de servidor reutilizables (lista blanca de caracteres y números estrictos).

Nada de lo que llega del navegador se da por bueno: se normaliza, se acota y se
compara contra un patrón permitido antes de tocar la base de datos.
"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

# Texto libre (observaciones, motivos, referencias): letras, números, espacios y
# . , : ! ? ¿ ¡ ( ) ' " % / + # @ & -   →  se rechazan < > { } [ ] = ; $ | \ `
TEXTO_RE = re.compile(r"[\w\s.,:!?¿¡()'\"%/+#@&\-]*", re.UNICODE)
# Referencia / N° de factura: sin espacios raros ni símbolos de inyección
REFERENCIA_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._/\-#]{0,99}")

CARACTERES_PROHIBIDOS = '< > { } [ ] = ; $ | \\ `'


def limpiar_texto(valor):
    """Normaliza a NFC, quita caracteres de control y espacios sobrantes."""
    valor = unicodedata.normalize('NFC', str(valor if valor is not None else ''))
    valor = ''.join(ch for ch in valor if ch == '\n' or unicodedata.category(ch)[0] != 'C')
    return re.sub(r'[ \t]+', ' ', valor).strip()


def validar_texto_libre(texto, maximo=500):
    """Devuelve un mensaje de error, o None si el texto es seguro."""
    if len(texto) > maximo:
        return f'No puede superar {maximo} caracteres.'
    if not TEXTO_RE.fullmatch(texto):
        return f'Contiene caracteres no permitidos ({CARACTERES_PROHIBIDOS}).'
    return None


def validar_referencia(texto):
    """N° de factura o referencia de pago. Vacío es válido. Devuelve error o None."""
    if not texto:
        return None
    if not REFERENCIA_RE.fullmatch(texto):
        return 'La referencia solo admite letras, números, espacios y . _ / - #'
    return None


MSG_SOLO_DIGITOS = 'Solo se permiten números enteros: sin punto, coma, signo menos, letras ni espacios.'


def entero_estricto(raw, *, minimo=1, maximo=1_000_000):
    """Entero que contiene SOLO dígitos 0-9 (ni . , - + ni notación científica).
    Lanza ValueError con un mensaje claro si no cumple."""
    texto = str(raw if raw is not None else '').strip()
    if not re.fullmatch(r'[0-9]{1,12}', texto):
        raise ValueError(MSG_SOLO_DIGITOS)
    numero = int(texto)
    if numero < minimo:
        raise ValueError(f'Debe ser mayor o igual a {minimo}.')
    if numero > maximo:
        raise ValueError('No puede superar ' + f'{maximo:,}'.replace(',', '.') + '.')
    return numero


def decimal_estricto(raw, *, minimo=Decimal('1'), maximo=Decimal('9999999999'), decimales=0):
    """Valor en pesos como número entero (solo dígitos). Devuelve Decimal."""
    return Decimal(entero_estricto(raw, minimo=int(minimo), maximo=int(maximo)))


def solo_digitos(raw, *, vacio_ok=False):
    """True si el texto son solo dígitos (o vacío cuando vacio_ok)."""
    texto = str(raw if raw is not None else '').strip()
    if not texto:
        return vacio_ok
    return bool(re.fullmatch(r'[0-9]+', texto))


# -------------------------------------------------------------------------
# Validaciones de nombres y lotes
# -------------------------------------------------------------------------

SIMBOLOS_PERMITIDOS = " .-*/&'()"   # además de letras y números

_SIMBOLOS_SIN_ESPACIO = SIMBOLOS_PERMITIDOS.replace(" ", "")
_SIMBOLOS_SEGUIDOS = re.compile("[" + re.escape(_SIMBOLOS_SIN_ESPACIO) + "]{2,}")


def normalizar_nombre(valor):
    """Quita espacios al inicio/fin y deja un solo espacio entre palabras."""
    texto = unicodedata.normalize("NFC", valor or "")
    return re.sub(r"\s+", " ", texto).strip()


def validar_nombre(valor, etiqueta="El nombre", minimo=3, maximo=150, minimo_letras=2):
    """Devuelve el nombre limpio o lanza ValidationError con el motivo."""
    nombre = normalizar_nombre(valor)

    if not nombre:
        raise ValidationError(f"{etiqueta} es obligatorio; no puede estar vacío ni tener solo espacios.")
    if len(nombre) < minimo:
        raise ValidationError(f"{etiqueta} debe tener al menos {minimo} caracteres.")
    if len(nombre) > maximo:
        raise ValidationError(f"{etiqueta} no puede superar {maximo} caracteres.")
    if not nombre[0].isalnum():
        raise ValidationError(f"{etiqueta} debe empezar con una letra o un número.")

    invalidos = sorted({c for c in nombre if not (c.isalnum() or c in SIMBOLOS_PERMITIDOS)})
    if invalidos:
        raise ValidationError(f"{etiqueta} tiene caracteres no permitidos: " + " ".join(invalidos))

    if sum(1 for c in nombre if c.isalpha()) < minimo_letras:
        raise ValidationError(f"{etiqueta} debe tener al menos {minimo_letras} letras.")
    if _SIMBOLOS_SEGUIDOS.search(nombre):
        raise ValidationError(f'{etiqueta} no puede tener dos símbolos seguidos (por ejemplo "..").')

    return nombre


def validar_nombre_producto(valor):
    return validar_nombre(valor, "El nombre", maximo=150)


def validar_nombre_presentacion(valor):
    # max_length de PresentacionProducto.nombre = 100
    return validar_nombre(valor, "El nombre de la presentación", maximo=100)


SIMBOLOS_LOTE = "-_./"
_SIMBOLOS_LOTE_SEGUIDOS = re.compile("[" + re.escape(SIMBOLOS_LOTE) + "]{2,}")


def validar_numero_lote(valor, minimo=3, maximo=100):
    """Devuelve el número de lote limpio o lanza ValidationError con el motivo."""
    codigo = unicodedata.normalize("NFC", valor or "").strip()

    if not codigo:
        raise ValidationError("El número de lote es obligatorio; no puede estar vacío ni tener solo espacios.")
    if re.search(r"\s", codigo):
        raise ValidationError("El número de lote no puede contener espacios.")
    if len(codigo) < minimo:
        raise ValidationError(f"El número de lote debe tener al menos {minimo} caracteres.")
    if len(codigo) > maximo:
        raise ValidationError(f"El número de lote no puede superar {maximo} caracteres.")
    if not codigo[0].isalnum():
        raise ValidationError("El número de lote debe empezar con una letra o un número.")
    if not codigo[-1].isalnum():
        raise ValidationError("El número de lote debe terminar con una letra o un número.")

    invalidos = sorted({c for c in codigo if not (c.isalnum() or c in SIMBOLOS_LOTE)})
    if invalidos:
        raise ValidationError("El número de lote tiene caracteres no permitidos: " + " ".join(invalidos))
    if _SIMBOLOS_LOTE_SEGUIDOS.search(codigo):
        raise ValidationError('El número de lote no puede tener dos símbolos seguidos (por ejemplo "..").')

    return codigo
