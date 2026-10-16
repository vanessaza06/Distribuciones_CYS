"""chatbot.py — Botellín para CYS Ltda (sin API externa, 100% gratis)."""
import json
import re
import unicodedata

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

MAX_MENSAJE = 500
LIMITE_POR_MINUTO = 15

PENDIENTE = ("Esa guía todavía no está disponible 🙏 Revisa las **Guías rápidas** "
             "o escribe en el formulario de soporte de la página de Ayuda.")

# Cada entrada: (lista de patrones, respuesta).
# Un patrón es una tupla de fragmentos: TODOS deben aparecer en el mensaje.
# Ej: ("producto", "cre") coincide con "cómo creo un producto".
RESPUESTAS = [
    ([("hola",), ("buenas",), ("buenos dias",), ("buenas tardes",)],
     "¡Hola! Soy **Botellín** 🍺 Pregúntame cómo usar el sistema: ventas, devoluciones, caja, compras, inventario…"),
    ([("gracias",)],
     "¡Con gusto! Aquí estoy si necesitas algo más del sistema 😊"),

    ([("usuario", "cre"), ("usuario", "agreg"), ("usuario", "nuev"), ("usuario", "registr")], PENDIENTE),
    ([("producto", "cre"), ("producto", "agreg"), ("producto", "nuev"), ("producto", "registr")], PENDIENTE),
    ([("lote", "cre"), ("lote", "registr"), ("lote", "agreg"), ("lote", "nuev")], PENDIENTE),

    ([("venta",), ("vender",), ("pos",), ("cobrar",), ("consumidor final",), ("factura",)],
     "Para registrar una venta:\n"
     "1. Ve a **Ventas** en el menú principal.\n"
     "2. Elige un cliente registrado o deja **Consumidor Final**.\n"
     "3. Agrega productos desde el buscador o el catálogo.\n"
     "4. Ingresa el desglose de pago (Efectivo, Nequi, Daviplata, Tarjeta o Transferencia).\n"
     "5. Clic en **Confirmar Venta** para registrar e imprimir el comprobante."),
    ([("devolucion",), ("devolver",), ("reembolso",)],
     "Para hacer una devolución:\n"
     "1. Ve a **Devoluciones**.\n"
     "2. Selecciona la venta original o busca el código de factura.\n"
     "3. Elige el ítem y la cantidad, e indica el motivo.\n"
     "4. Elige si se restaura el stock y el método de reembolso.\n"
     "5. Confirma; el saldo y el reporte del día se actualizan solos."),
    ([("caja",), ("arqueo",), ("apertura",), ("cierre",), ("turno",), ("hora pico",)],
     "En **Caja** haces la **Apertura de Turno** con el desglose de billetes y monedas iniciales. "
     "Ahí también ves las ventas por franjas horarias y la hora pico. Al terminar la jornada haces el "
     "**Cierre de Caja** con el conteo final para comparar el efectivo real contra el sistema."),
    ([("metodo de pago",), ("metodos de pago",), ("nequi",), ("daviplata",), ("efectivo",),
      ("abono",), ("recaudo",)],
     "En **Métodos de Pago** ves el consolidado diario del recaudo en efectivo y transferencias. "
     "También puedes registrar pagos independientes o abonos a órdenes de compra."),
    ([("inventario",), ("stock",), ("existencias",), ("minimo",)],
     "En **Inventario** consultas el stock por producto y presentación, los lotes activos y las alertas "
     "de stock mínimo. Las existencias se recalculan al registrar ventas o devoluciones. "
     "Los productos no se borran: se activan o desactivan."),
    ([("compra",), ("proveedor",)],
     "Para registrar una compra:\n"
     "1. Ve a **Compras** y elige el proveedor.\n"
     "2. Agrega los artículos comprados y el valor o saldo.\n"
     "3. Al confirmar la recepción, el inventario aumenta con la nueva mercancía."),
    ([("anul",)],
     "Anular una venta o un pago requiere permisos de administrador o supervisor, y se hace desde la "
     "tabla de detalle de la venta o del pago."),
]

FALLBACK = ("No encontré eso en mi guía 🤔 Solo puedo ayudarte con el sistema de CYS: ventas, "
            "devoluciones, caja, métodos de pago, inventario y compras. También puedes revisar "
            "las **Guías rápidas** o escribir a soporte.")


def _norm(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texto)


def _responder(mensaje):
    t = " " + _norm(mensaje) + " "
    mejor, puntaje = None, 0
    for patrones, respuesta in RESPUESTAS:
        score = sum(len(p) for p in patrones if all(f in t for f in p))
        if score > puntaje:
            mejor, puntaje = respuesta, score
    return mejor or FALLBACK


def _excede_limite(user_id):
    clave = f"botellin_rate_{user_id}"
    cache.add(clave, 0, timeout=60)
    try:
        return cache.incr(clave) > LIMITE_POR_MINUTO
    except ValueError:
        return False


@login_required
@require_POST
def chatbot_responder(request):
    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"respuesta": "No entendí tu mensaje. Intenta de nuevo."}, status=400)

    mensaje = str(datos.get("mensaje", "")).strip()[:MAX_MENSAJE]
    if not mensaje:
        return JsonResponse({"respuesta": "Escríbeme tu duda y te ayudo 😊"}, status=400)

    if _excede_limite(request.user.pk):
        return JsonResponse({"respuesta": "Vas muy rápido 😅 Espera un momentico."}, status=429)

    return JsonResponse({"respuesta": _responder(mensaje)})