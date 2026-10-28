"""chatbot.py — Botellín para CYS Ltda (sin API externa, 100% gratis).

CÓMO AGREGAR UNA GUÍA NUEVA
  1. Añade una entrada a RESPUESTAS:  ([patrones], "respuesta").
  2. Un patrón es una tupla de fragmentos: TODOS deben aparecer en el mensaje
     (se compara en minúscula y sin tildes). Ej: ("producto", "cre") coincide
     con "cómo creo un producto".
  3. Gana la entrada con más fragmentos coincidentes. Si empatan, gana la que
     está primero. Por eso las guías ESPECÍFICAS van antes que las GENERALES.
"""
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

RESPUESTAS = [

    # ══════════ 1. CUENTA Y USUARIOS (guías específicas) ══════════
    ([("usuario", "cre"), ("usuario", "agreg"), ("usuario", "nuev"), ("usuario", "registr"),
      ("usuario", "anad"), ("cuenta", "cre"), ("cuenta", "nuev"), ("registrarme",), ("registrarse",)],
     "Hay dos formas de crear un usuario.\n"
     "**Si eres administrador (dentro del sistema):**\n"
     "1. Ve a **Lista de Usuarios** (arriba en el menú lateral).\n"
     "2. Clic en **Nuevo Usuario**.\n"
     "3. Completa **Nombres**, **Apellidos**, **Tipo de ID** e **Identificación** (el **Correo** es opcional).\n"
     "4. Escribe la **Contraseña** (mínimo 6 caracteres, 2 números y 1 mayúscula) y repítela en **Confirmar contraseña**.\n"
     "5. Marca la casilla de **Términos y Condiciones** y pulsa **Crear Usuario**.\n"
     "Siempre se crea como **Empleado**; el rol se cambia después desde la lista.\n"
     "**Si aún no tienes cuenta:** en el inicio de sesión pulsa **Crear usuario**, completa los datos, "
     "**Continuar**, confirma la contraseña, acepta los términos y pulsa **Crear Cuenta**. "
     "Para entrar la primera vez, tu usuario es tu número de documento."),

    ([("usuario", "edit"), ("usuario", "modific"), ("usuario", "actualiz"), ("usuario", "contrasen"),
      ("usuario", "correo")],
     "Para editar un usuario (solo Administrador):\n"
     "1. Ve a **Lista de Usuarios**.\n"
     "2. En la tarjeta del usuario, clic en **Editar**.\n"
     "3. Cambia **Nombres**, **Apellidos**, **Correo** o **Rol** (Cajero o Empleado).\n"
     "4. Si quieres cambiarle la contraseña, escríbela en **Nueva Contraseña** (opcional: mínimo 6 caracteres, 2 números y 1 mayúscula).\n"
     "5. Clic en **Guardar Cambios**."),

    ([(" rol ", "cambi"), (" rol ", "asign"), (" rol ", "modific"), (" rol ", "edit"),
      ("cambiar", "permiso"), ("hacer", "cajero")],
     "Para cambiar el rol de un usuario (solo Administrador):\n"
     "1. Ve a **Lista de Usuarios**.\n"
     "2. Clic en la etiqueta del rol del usuario (tiene un lápiz).\n"
     "3. Elige **Cajero** o **Empleado**.\n"
     "4. Confirma con la palomita ✓ (o cancela con la ✗).\n"
     "El rol **Administrador** no se puede cambiar desde ahí."),

    ([("usuario", "desactiv"), ("usuario", "activar"), ("usuario", "elimin"), ("usuario", "borrar"),
      ("usuario", "bloque"), ("usuario", "inactiv")],
     "Para activar, desactivar o eliminar un usuario (solo Administrador):\n"
     "1. Ve a **Lista de Usuarios**.\n"
     "2. En su tarjeta pulsa **Desactivar** (o **Activar** si ya está inactivo).\n"
     "3. El botón **Eliminar** solo aparece cuando el usuario está inactivo, así que primero hay que desactivarlo."),

    ([("lista", "usuario"), ("buscar", "usuario"), ("ver", "usuarios"), ("usuarios registrados",)],
     "En **Lista de Usuarios** ves una tarjeta por usuario con su nombre, identificación, correo, fecha de "
     "registro, estado y rol. Puedes buscar con la barra de arriba. A la derecha ves el total de usuarios y el "
     "porcentaje de activos, y los botones **Ver Estadísticas Detalladas** y **Ver Registros Recientes**.\n"
     "La ven el Administrador y el Cajero, pero solo el Administrador puede crear, editar, activar o desactivar, "
     "eliminar usuarios y cambiar roles. Tu propio usuario no aparece ahí: está en **Mi perfil**."),

    ([("iniciar sesion",), ("login",), ("ingresar al sistema",), ("no puedo entrar",), ("entrar al sistema",)],
     "En la pantalla de acceso escribe tu **Usuario** (tu identificación o tu nombre de usuario) y tu "
     "**Contraseña**, y pulsa **Iniciar Sesión**. Si no recuerdas la contraseña, usa **Olvidé mi contraseña**."),

    ([("olvide",), ("recuperar",), ("restablecer",), ("contrasena", "perd")],
     "Si olvidaste tu contraseña, en el inicio de sesión haz clic en **Olvidé mi contraseña** y elige cómo recuperarla:\n"
     "- **Enlace por correo**: te llega un enlace para crear una nueva contraseña.\n"
     "- **Código por correo**: te llega un código de 6 dígitos que vence en 10 minutos.\n"
     "Escribe tu correo y sigue las instrucciones."),

    ([("cerrar sesion",), ("cierro", "sesion"), ("cerrar", "sesion"), ("salir del sistema",),
      ("salir",), ("logout",)],
     "Para salir usa **Cerrar Sesión**, la última opción del menú lateral."),

    # ══════════ 2. INVENTARIO (guías específicas) ══════════
    ([("primeros pasos",), ("por donde empiezo",), ("como empiezo",), ("empezar",), ("desde cero",),
      ("orden", "crear"), ("que debo crear primero",)],
     "Para dejar listo el inventario, este es el orden:\n"
     "1. **Categorías**: crea al menos una.\n"
     "2. **Marcas**: crea las marcas que vayas a usar.\n"
     "3. **Productos**: crea el producto (nombre, categoría y fecha de vencimiento).\n"
     "4. **Presentaciones**: crea las presentaciones del producto.\n"
     "5. **Detalle de Producto**: registra su código de barras y su marca.\n"
     "6. **Lotes**: registra el lote con su presentación, cantidad y costo.\n"
     "Con eso el producto queda completo y con stock."),

    ([("producto", "cre"), ("producto", "agreg"), ("producto", "nuev"), ("producto", "registr"),
      ("producto", "anad")],
     "Para crear un producto:\n"
     "1. Ve a **Inventario → Productos**.\n"
     "2. Clic en **Nuevo Producto** (arriba a la derecha).\n"
     "3. Escribe el **Nombre** y elige la **Categoría** (principal o subcategoría). Si no hay categorías, "
     "primero crea una en **Categorías**.\n"
     "4. Si quieres, agrega una **Descripción**.\n"
     "5. Elige la **Fecha de vencimiento**.\n"
     "6. Clic en **Guardar Producto**.\n"
     "Después créale sus **Presentaciones** y registra su **Lote** para que tenga stock."),

    ([("lote", "cre"), ("lote", "registr"), ("lote", "agreg"), ("lote", "nuev"), ("lote", "anad")],
     "Para registrar un lote:\n"
     "1. Ve a **Inventario → Lotes**.\n"
     "2. (Opcional) Sube una imagen del producto: arrástrala o haz clic en el recuadro.\n"
     "3. Elige la **Presentación** (puedes buscarla por producto o presentación). Si no aparece ninguna, "
     "primero crea una en **Presentaciones**.\n"
     "4. Elige la **Bodega** (si solo hay una, ya viene seleccionada).\n"
     "5. Escribe el **Nº de Lote** y la **Cantidad inicial** (mínimo 1).\n"
     "6. Escribe el **Precio de Costo** por unidad; se actualiza en la presentación.\n"
     "7. Clic en **Nuevo Lote**."),

    ([("ajust", "stock"), ("ajust", "lote"), ("edit", "lote"), ("modific", "lote"), ("correg", "stock"),
      ("cambi", "stock"), ("actualiz", "stock"), ("costo", "lote")],
     "Para ajustar el stock o el costo de un lote:\n"
     "1. Ve a **Inventario → Stock & Productos**.\n"
     "2. En la tabla **Stock por Lote**, busca el lote (con el buscador o el filtro de estado).\n"
     "3. Clic en el lápiz de la columna **Acciones**.\n"
     "4. Cambia el **Stock de este lote** y/o el **Costo unitario**. Si quieres, anota un **Motivo** "
     "(conteo físico, corrección de error…).\n"
     "5. Clic en **Guardar**."),

    ([("categoria", "cre"), ("categoria", "nuev"), ("categoria", "agreg"), ("categoria", "registr"),
      ("subcategoria", "cre"), ("subcategoria", "nuev")], PENDIENTE),

    ([("presentacion", "cre"), ("presentacion", "nuev"), ("presentacion", "agreg"),
      ("presentacion", "registr")], PENDIENTE),

    ([(" marca ", "cre"), (" marca ", "nuev"), (" marca ", "agreg"), (" marca ", "registr")], PENDIENTE),

    ([("detalle", "cre"), ("detalle", "nuev"), ("detalle", "agreg"), ("detalle", "registr")], PENDIENTE),

    ([("proveedor", "cre"), ("proveedor", "nuev"), ("proveedor", "agreg"), ("proveedor", "registr"),
      ("proveedor", "edit"), ("proveedor", "modific")], PENDIENTE),

    ([("agenda", "cre"), ("agenda", "nuev"), ("agenda", "agreg"), ("agenda", "program")], PENDIENTE),

    ([("barras",)],
     "El **código de barras** se registra en **Inventario → Detalle de Producto**, junto con la marca y la "
     "fecha de vencimiento. Cada código debe ser único."),

    ([("stock", "critico"), ("stock", "minimo"), ("por reponer",), ("poco stock",), ("reponer",)],
     "Un producto queda en **stock crítico** cuando le quedan **5 unidades o menos** en total (la suma de "
     "todos sus lotes). Lo ves en la **campana** (pestaña **Stock**) y en el bloque **Resumen** del menú lateral."),

    ([("venc",), ("caduc",), ("expir",)],
     "La fecha de vencimiento se registra en **Inventario → Detalle de Producto** (y al crear el producto). "
     "Un lote se considera **por vencer** cuando faltan 30 días o menos, y **vencido** cuando la fecha ya pasó. "
     "Lo ves en **Stock & Productos**, en la columna **Estado**, y puedes filtrar por **Por vencer** o **Vencido**."),

    ([("devol", "motivo")],
     "Los motivos de una devolución de venta son: **Producto defectuoso**, **Producto equivocado**, "
     "**Cliente insatisfecho** y **Otro**."),

    ([("estado", "compra"), ("pago", "compra"), ("pagar", "compra"), ("abon",), ("recib", "compra"),
      ("cancel", "compra"), ("confirm", "compra"), ("anul", "compra"), ("detalle", "compra"),
      ("pagar", "proveedor"), ("pago", "proveedor")],
     "Una compra pasa por estos estados: **Pendiente** → **Confirmada** → **Recibida**. Desde Pendiente o "
     "Confirmada también se puede **Cancelar**; una compra Recibida o Cancelada ya no cambia. Al marcarla "
     "**Recibida**, la mercancía entra al stock (los ítems que tienen lote).\n"
     "Los pagos se registran como abonos: deben ser mayores a cero, no pueden superar el saldo pendiente y "
     "no se permiten en compras canceladas. Medios de pago: efectivo, Nequi, Daviplata, Bancolombia o Bre-B. "
     "El **Detalle Compra** (menú Compras) abre la última compra registrada."),

    ([("anul",), ("anul", "venta"), ("anul", "pago")],
     "Anular una venta o un pago requiere permisos de administrador o supervisor, y se hace desde la "
     "tabla de detalle de la venta o del pago."),

    ([("stock", "lote"), ("stock", "producto"), ("gestion", "stock"), ("lotes activos",), ("tabla", "stock")],
     "En **Inventario → Stock & Productos** ves cuatro indicadores (**Productos**, **Lotes activos**, "
     "**Por vencer** y **Vencidos**) y la tabla **Stock por Lote**, con producto, número de lote, stock, "
     "vencimiento, estado (**OK**, **Por vencer** o **Vencido**), costo unitario y valor total. Puedes "
     "buscar y filtrar por **Todos**, **En orden**, **Por vencer** o **Vencido**."),

    # ══════════ 3. MÓDULOS (guías generales) ══════════
    ([("venta",), ("vender",), (" pos ",), ("cobrar",), ("consumidor final",), ("factura",)],
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
     "**Cierre de Caja** con el conteo final para comparar el efectivo real contra el sistema. "
     "Solo se permite una apertura y un cierre por día."),

    ([("metodo de pago",), ("metodos de pago",), ("nequi",), ("daviplata",), ("efectivo",),
      ("abono",), ("recaudo",)],
     "En **Métodos de Pago** ves el consolidado diario del recaudo en efectivo y transferencias. "
     "También puedes registrar pagos independientes o abonos a órdenes de compra."),

    ([("inventario",), ("stock",), ("existencias",), ("minimo",)],
     "En **Inventario** consultas el stock por producto y presentación, los lotes activos y las alertas "
     "de stock mínimo. Las existencias se recalculan al registrar ventas o devoluciones. "
     "Los productos no se borran: se activan o desactivan."),

    ([("compra",)],
     "Para registrar una compra:\n"
     "1. Ve a **Compras** y elige el proveedor.\n"
     "2. Agrega los artículos comprados y el valor o saldo.\n"
     "3. Al confirmar la recepción, el inventario aumenta con la nueva mercancía."),

    ([("tablero",), ("pantalla principal",), ("pagina principal",)],
     "El **Tablero** es la pantalla principal: muestra indicadores del negocio y un resumen de los tipos "
     "de producto por categoría. Entras desde **Tablero** en el menú lateral."),

    ([("perfil",), ("mi cuenta",), ("nombre de usuario",)],
     "Arriba en el menú lateral aparece tu usuario y tu rol. Al hacer clic en él se abre **Mi perfil**, "
     "donde puedes personalizar tu nombre de usuario."),

    ([("campana",), ("notificacion",), ("alerta",)],
     "La **campana** de la barra superior tiene tres pestañas: **Stock** (productos con stock crítico, con "
     "el enlace **Ver stock completo**), **Compras** (compras pendientes, con acceso a Gestión de Compras) "
     "e **Historial**."),

    ([("compacto",), ("aside",), ("barra lateral",)],
     "En el encabezado del menú lateral hay un botón con flechas dobles (**Modo compacto**) que reduce el "
     "menú a solo íconos, y otro con una **X** para cerrarlo. Al pasar el mouse por un ícono ves su nombre."),

    ([("producto",)],
     "En **Inventario → Productos** ves la gráfica **Por categoría**, los **Últimos agregados**, el buscador, "
     "la lista de **Categorías** a la izquierda y, al elegir una, la tabla con sus productos (nombre, código y "
     "presentaciones). El botón **Detalles de productos** lleva a la gestión de cada uno. Los productos no se "
     "borran: se activan o desactivan."),

    ([("presentacion",)],
     "En **Inventario → Presentaciones** ves las presentaciones de cada producto. Se pueden crear para un "
     "producto, editar y activar o desactivar."),

    ([("categoria",)],
     "En **Inventario → Categorías** ves las categorías de productos. Puedes crear una nueva, editarla y "
     "activarla o desactivarla. En el **Resumen** del menú lateral ves cuántas hay activas."),

    ([(" marca ",), (" marcas ",)],
     "En **Inventario → Marcas** ves la lista de marcas. Puedes crear una marca, editarla y cambiar su "
     "estado (activa o inactiva)."),

    ([("detalle de producto",), ("detalle producto",)],
     "En **Inventario → Detalle de Producto** ves el detalle de cada producto (código de barras, marca y "
     "fecha de vencimiento) y puedes crearlo, editarlo y guardar su código."),

    ([("lote",)],
     "En **Inventario → Lotes** está el formulario para registrar lotes y, a la derecha, **Ingresos Hoy**, "
     "**Lotes del Mes** y el top 5 de productos en stock. La lista de lotes con su stock, vencimiento y estado "
     "está en **Stock & Productos**; ahí también puedes editar un lote y ajustar su stock."),

    ([("bodega",), ("agenda",), ("hallazgo",), ("conteo",)],
     "En **Inventario → Bodega** está el inicio de bodega y su **agenda**, donde se programan tareas de "
     "inventario (por ejemplo, conteos) con fecha y responsable. Cada tarea pasa por **Pendiente**, "
     "**En proceso**, **Completada** o **Cancelada**. Al contar se registran los **hallazgos**: faltante, "
     "sobrante o exacto. Desde bodega también se puede ajustar el stock de un producto."),

    ([("proveedor",), ("sancion",)],
     "En **Proveedores** ves la lista y el detalle de cada proveedor. Cada uno tiene un tipo "
     "(**Distribuidor**, **Fabricante**, **Importador** u **Otro**) y un estado (**Activo**, **Inactivo** o "
     "**Sancionado**). Puedes crear, editar, activar o desactivar un proveedor, y también **sancionarlo** "
     "(el motivo es obligatorio) o levantarle la sanción."),

    ([("reporte",), ("informe",), ("export",), ("excel",), ("pdf",), ("descargar",)],
     "Los reportes están en **Reportes** (menú lateral). Para sacar el listado de ventas, desde **Ventas** "
     "puedes exportarlo a **Excel** o **PDF**."),

    ([("configuracion",), ("empresa",), ("impuesto",), (" iva ",), ("backup",), ("copia de seguridad",)],
     "En **Configuración** (menú lateral) están los datos de la **empresa** (nombre, NIT, dirección, teléfono "
     "y correo), los **impuestos** (porcentaje de IVA) y la **copia de seguridad (backup)**. Los datos de la "
     "empresa se protegen con una clave: hay que verificarla para editarlos y luego se pueden volver a bloquear."),

    ([("ayuda",), ("soporte",), ("guias",)],
     "En **Ayuda** (menú lateral) encuentras las **Guías rápidas** y las preguntas frecuentes, y un "
     "formulario de soporte para escribirle al equipo."),

    ([("usuario",), (" rol ",), (" roles ",), ("permiso",), ("administrador",), ("cajero",), ("empleado",)],
     "El sistema maneja tres roles: **Administrador**, **Cajero** y **Empleado**. **Lista de Usuarios** la ven "
     "el Administrador y el Cajero; solo el Administrador puede crear, editar, activar o desactivar y eliminar "
     "usuarios, y cambiar roles."),

    # ══════════ 4. GENERALES (déjalas SIEMPRE al final) ══════════
    ([("menu",), ("modulos",), ("donde",), ("opciones",)],
     "En el menú lateral encuentras: **Tablero**, **Ventas** (con Caja y Métodos de Pago), **Devoluciones**, "
     "**Reportes**, **Inventario** (Productos, Presentaciones, Stock & Productos, Categorías, Detalle de "
     "Producto, Marcas, Bodega y Lotes), **Proveedores**, **Compras**, **Ayuda**, **Configuración** y "
     "**Cerrar Sesión**. ¿Cuál te interesa?"),

    ([("quien eres",), ("que eres",), ("que haces",), ("que puedes",), ("para que sirves",), ("como te llamas",)],
     "Soy **Botellín** 🍺, el asistente de CYS. Te explico cómo usar el sistema: usuarios, productos, lotes, "
     "ventas, devoluciones, caja, compras, inventario y más. ¡Pregúntame!"),

    ([("hola",), ("buenas",), ("buenos dias",), ("saludos",)],
     "¡Hola! Soy **Botellín** 🍺 Pregúntame cómo usar el sistema: ventas, devoluciones, caja, compras, inventario…"),

    ([("gracias",)],
     "¡Con gusto! Aquí estoy si necesitas algo más del sistema 😊"),
]

FALLBACK = ("No encontré eso en mi guía 🤔 Solo puedo ayudarte con el sistema de CYS: usuarios, productos, "
            "lotes, ventas, devoluciones, caja, métodos de pago, inventario y compras. También puedes revisar "
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