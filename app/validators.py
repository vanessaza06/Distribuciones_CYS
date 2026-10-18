import re
import unicodedata

from django.core.exceptions import ValidationError

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