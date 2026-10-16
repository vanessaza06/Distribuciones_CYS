"""Validaciones de servidor reutilizables (lista blanca de caracteres y números estrictos).

Nada de lo que llega del navegador se da por bueno: se normaliza, se acota y se
compara contra un patrón permitido antes de tocar la base de datos.
"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation

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
