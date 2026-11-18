import json
import os
from pathlib import Path

from django.conf import settings

TEMAS_VALIDOS = ('oscuro', 'claro', 'alto-contraste', 'basecys', 'sepia')
TEMA_POR_DEFECTO = 'oscuro'


def _ruta():
    return Path(settings.BASE_DIR) / 'config_sistema.json'


def _leer_archivo():
    try:
        return json.loads(_ruta().read_text(encoding='utf-8'))
    except Exception:
        return {}


def leer_config():
    """Configuración global guardada en archivo (sin base de datos)."""
    tema = _leer_archivo().get('tema_predeterminado')
    if tema not in TEMAS_VALIDOS:
        tema = TEMA_POR_DEFECTO
    return {'tema_predeterminado': tema}


def guardar_tema(tema):
    if tema not in TEMAS_VALIDOS:
        raise ValueError('Tema no válido')
    data = _leer_archivo()
    data['tema_predeterminado'] = tema
    ruta = _ruta()
    tmp = ruta.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, ruta)