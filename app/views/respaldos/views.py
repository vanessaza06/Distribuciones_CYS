import os
import re
import glob
import shutil
import subprocess
import unicodedata
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app.models import BackupRegistro

MAX_UPLOAD_MB = 500

_LETRAS_INICIO_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3}")
_NOMBRE_RESPALDO_RE = re.compile(
    r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3}[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 _.-]*$"
)
_SQL_DATA_RE = re.compile(
    r"\b(?:"
    r"INSERT\s+(?:LOW_PRIORITY\s+|DELAYED\s+|HIGH_PRIORITY\s+)?(?:IGNORE\s+)?INTO\s+[`\"'\w.]+"
    r"(?:\s*\([^)]*\))?\s+(?:(?:VALUES|VALUE)\s*\(\s*[^)\s]|SET\s+\S|SELECT\s+\S)"
    r"|REPLACE\s+(?:LOW_PRIORITY\s+|DELAYED\s+)?INTO\s+[`\"'\w.]+"
    r"(?:\s*\([^)]*\))?\s+(?:(?:VALUES|VALUE)\s*\(\s*[^)\s]|SET\s+\S|SELECT\s+\S)"
    r"|LOAD\s+DATA\s+(?:LOW_PRIORITY\s+|CONCURRENT\s+)?(?:LOCAL\s+)?INFILE\s+\S"
    r")",
    re.IGNORECASE,
)
_SQL_ESTRUCTURA_RE = re.compile(
    r"\b(?:CREATE|DROP|ALTER|TRUNCATE|LOCK|UNLOCK|SET|USE)\s+(?:TABLE|DATABASE|SCHEMA|VIEW|INDEX|TRIGGER|TABLES|NAMES)\b",
    re.IGNORECASE,
)


def _validar_nombre_respaldo(texto, obligatorio=False):
    """Valida que el nombre del respaldo inicie con 3 letras (sin números ni puntos al principio).

    Devuelve un mensaje de error o None si es válido.
    """
    raw = (texto or "").strip()
    if not raw:
        if obligatorio:
            return "El nombre de la copia de seguridad es obligatorio."
        return None

    if "/" in raw or "\\" in raw:
        return "El nombre no puede contener barras (/ o \\)."

    base = raw[:-4] if raw.lower().endswith(".sql") else raw

    if len(base) > 80:
        return "El nombre de la copia de seguridad no puede superar 80 caracteres."

    if not _LETRAS_INICIO_RE.match(base):
        return (
            "El nombre de la copia de seguridad debe comenzar con 3 letras "
            "(no se permiten números, puntos ni símbolos al principio)."
        )

    if ".." in base or base.endswith("."):
        return "El nombre no puede contener puntos seguidos (..) ni terminar en punto."

    if not _NOMBRE_RESPALDO_RE.fullmatch(base):
        return (
            "El nombre contiene caracteres no permitidos. "
            "Usa solo letras, números, espacios, puntos, guiones (-) o guion bajo (_)."
        )

    return None


def _quitar_comentarios_sql(texto, estado):
    """Elimina comentarios SQL (-- ..., # ..., /* ... */) preservando el estado entre fragmentos."""
    out = []
    i = 0
    n = len(texto)
    en_bloque = estado["en_bloque"]
    en_linea = estado["en_linea"]
    comilla = estado["comilla"]
    escape = estado["escape"]

    while i < n:
        ch = texto[i]

        if en_linea:
            if ch == "\n":
                en_linea = False
                out.append("\n")
            i += 1
            continue

        if en_bloque:
            if ch == "*" and i + 1 < n and texto[i + 1] == "/":
                en_bloque = False
                out.append(" ")
                i += 2
            elif ch == "*" and i + 1 == n:
                estado["pendiente"] = "*"
                i += 1
            else:
                i += 1
            continue

        if comilla:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == comilla:
                comilla = None
            i += 1
            continue

        if ch in ("'", '"'):
            comilla = ch
            out.append(ch)
            i += 1
            continue

        if ch == "#":
            en_linea = True
            out.append(" ")
            i += 1
            continue

        if ch == "-":
            if i + 1 < n:
                if texto[i + 1] == "-":
                    if i + 2 >= n or texto[i + 2] in (" ", "\t", "\r", "\n", "-"):
                        en_linea = True
                        out.append(" ")
                        i += 2
                        continue
            else:
                estado["pendiente"] = "-"
                i += 1
                continue

        if ch == "/":
            if i + 1 < n:
                if texto[i + 1] == "*":
                    en_bloque = True
                    out.append(" ")
                    i += 2
                    continue
            else:
                estado["pendiente"] = "/"
                i += 1
                continue

        out.append(ch)
        i += 1

    estado["en_bloque"] = en_bloque
    estado["en_linea"] = en_linea
    estado["comilla"] = comilla
    estado["escape"] = escape
    return "".join(out)


def _validar_contenido_sql(archivo):
    """Verifica que el archivo .sql no esté vacío, sea texto válido y contenga datos SQL.

    Devuelve un mensaje de error o None si el archivo es válido.
    """
    if getattr(archivo, "size", 0) == 0:
        return "El archivo seleccionado está vacío."

    estado = {
        "en_bloque": False,
        "en_linea": False,
        "comilla": None,
        "escape": False,
        "pendiente": "",
    }
    tiene_contenido = False
    tiene_estructura = False
    tiene_datos = False
    ventana = ""
    es_primer_chunk = True

    try:
        archivo.seek(0)
        for chunk in archivo.chunks():
            if not chunk:
                continue

            if b"\x00" in chunk:
                return "El archivo no es un archivo .sql de texto válido."

            if tiene_datos:
                # Ya se encontraron datos válidos; solo seguimos verificando que no sea binario
                continue

            if es_primer_chunk:
                es_primer_chunk = False
                if chunk.startswith(b"\xef\xbb\xbf"):
                    chunk = chunk[3:]

            try:
                texto = chunk.decode("utf-8")
            except UnicodeDecodeError:
                texto = chunk.decode("latin-1", errors="ignore")

            if estado["pendiente"]:
                texto = estado["pendiente"] + texto
                estado["pendiente"] = ""

            limpio = _quitar_comentarios_sql(texto, estado)
            if limpio.strip():
                tiene_contenido = True

            ventana = (ventana + limpio)[-8192:]
            if _SQL_DATA_RE.search(ventana):
                tiene_datos = True
            elif not tiene_estructura and _SQL_ESTRUCTURA_RE.search(ventana):
                tiene_estructura = True

        if not tiene_datos and estado["pendiente"]:
            limpio = estado["pendiente"]
            if limpio.strip():
                tiene_contenido = True
            ventana = (ventana + limpio)[-8192:]
            if _SQL_DATA_RE.search(ventana):
                tiene_datos = True
    finally:
        try:
            archivo.seek(0)
        except Exception:
            pass

    if not tiene_contenido:
        return "El archivo .sql está vacío o solo contiene comentarios, sin datos."
    if not tiene_datos:
        if tiene_estructura:
            return "El archivo .sql solo contiene estructura y no tiene datos (registros INSERT) para restaurar."
        return "El archivo .sql no contiene datos ni sentencias SQL válidas para restaurar."
    return None


def _sanitizar_nombre(texto, fallback="backup_cys"):
    """Deja solo caracteres seguros para nombres de archivo (evita path traversal)."""
    base = os.path.basename((texto or "").strip())
    if base.lower().endswith(".sql"):
        base = base[:-4]
    base = unicodedata.normalize("NFKD", base)
    base = "".join(ch for ch in base if unicodedata.category(ch) != "Mn")
    limpio = re.sub(r"[^A-Za-z0-9._\- ]+", "", base).strip().replace(" ", "_")
    limpio = re.sub(r"_+", "_", limpio).strip("._-")
    return (limpio[:80] or fallback)


def _formatear_tamano(size_mb):
    """Formatea un tamaño en MB a KB o MB legible."""
    val = float(size_mb or 0)
    if val < 1 and val > 0:
        return f"{round(val * 1024, 1)} KB"
    return f"{val:.2f} MB"


def _ejecutar_mysqldump(bin_dump, db_info, dest_path):
    """Ejecuta mysqldump hacia dest_path. Devuelve (ok, error_msg)."""
    comando = [
        bin_dump,
        f"-u{db_info['usuario']}",
        f"-h{db_info['host']}",
        f"-P{db_info['puerto']}",
        "--default-character-set=utf8mb4",
        "--single-transaction",
        "--quick",
        db_info["nombre"],
    ]
    env = os.environ.copy()
    if db_info["password"]:
        env["MYSQL_PWD"] = db_info["password"]

    with open(dest_path, "wb") as f:
        res = subprocess.run(
            comando, stdout=f, stderr=subprocess.PIPE, env=env, check=False
        )

    if res.returncode != 0:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        err_msg = res.stderr.decode("utf-8", errors="ignore").strip() or "Error en mysqldump"
        return False, err_msg
    return True, ""



def _obtener_binario(nombre):
    """Localiza el binario de MySQL (mysqldump o mysql) en el sistema."""
    # 1. Probar en PATH del sistema
    en_path = shutil.which(nombre)
    if en_path:
        return en_path

    # 2. Rutas conocidas en Windows (MySQL 8 / XAMPP / MariaDB)
    exe_name = f"{nombre}.exe"
    rutas_candidatas = [
        os.path.join(r"C:\Program Files\MySQL\MySQL Server 8.0\bin", exe_name),
        os.path.join(r"C:\Program Files\MySQL\MySQL Server 8.4\bin", exe_name),
        os.path.join(r"C:\Program Files\MySQL\MySQL Server 8.1\bin", exe_name),
        os.path.join(r"C:\Program Files\MySQL\MySQL Server 8.2\bin", exe_name),
        os.path.join(r"C:\xampp\mysql\bin", exe_name),
        os.path.join(r"C:\wamp64\bin\mysql\mysql8.0.31\bin", exe_name),
    ]
    for ruta in rutas_candidatas:
        if os.path.exists(ruta):
            return ruta

    # 3. Buscar mediante glob en Program Files
    patron = os.path.join(r"C:\Program Files\MySQL", "*", "bin", exe_name)
    coincidencias = glob.glob(patron)
    if coincidencias:
        return coincidencias[0]

    return None


def _obtener_datos_db():
    """Extrae las credenciales de la base de datos MySQL configurada en settings."""
    db = settings.DATABASES.get("default", {})
    return {
        "nombre": db.get("NAME", "distribuidora_cys"),
        "usuario": db.get("USER", "root"),
        "password": db.get("PASSWORD", ""),
        "host": db.get("HOST") or "127.0.0.1",
        "puerto": str(db.get("PORT") or 3306),
    }


@login_required
def respaldos_index(request):
    """Vista principal del módulo Copia de Seguridad."""
    respaldos = list(BackupRegistro.objects.all().order_by("-fecha"))
    total_respaldos = len(respaldos)

    disponibles_count = 0
    total_mb = 0.0
    for r in respaldos:
        r.existe_en_disco = bool(r.ruta and os.path.exists(r.ruta))
        if r.existe_en_disco:
            disponibles_count += 1
            try:
                real_mb = round(os.path.getsize(r.ruta) / (1024 * 1024), 4)
                if abs(real_mb - float(r.tamaño_mb or 0)) > 0.01:
                    r.tamaño_mb = real_mb
                    r.save(update_fields=["tamaño_mb"])
            except OSError:
                pass
        r.tamano_legible = _formatear_tamano(r.tamaño_mb)
        total_mb += float(r.tamaño_mb or 0)

    ultimo_respaldo = respaldos[0] if respaldos else None
    db_info = _obtener_datos_db()
    mysqldump_disponible = bool(_obtener_binario("mysqldump"))

    contexto = {
        "respaldos": respaldos,
        "total_respaldos": total_respaldos,
        "disponibles_count": disponibles_count,
        "faltantes_count": total_respaldos - disponibles_count,
        "total_mb": round(total_mb, 2),
        "total_espacio_legible": _formatear_tamano(total_mb),
        "ultimo_respaldo": ultimo_respaldo,
        "db_name": db_info["nombre"],
        "db_host": db_info["host"],
        "db_port": db_info["puerto"],
        "mysqldump_disponible": mysqldump_disponible,
        "breadcrumb_items": [{"nombre": "Copia de Seguridad", "url": None}],
    }
    return render(request, "respaldos/respaldos.html", contexto)


@login_required
@require_POST
def respaldo_crear(request):
    """Genera un nuevo respaldo completo de la base de datos."""
    nombre_custom = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()[:500]

    err_nombre = _validar_nombre_respaldo(nombre_custom, obligatorio=False)
    if err_nombre:
        messages.error(request, err_nombre)
        return redirect("respaldos_index")

    try:
        bin_dump = _obtener_binario("mysqldump")
        if not bin_dump:
            messages.error(
                request,
                "No se encontró 'mysqldump' en el servidor. Verifica la instalación de MySQL.",
            )
            return redirect("respaldos_index")

        db_info = _obtener_datos_db()
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if nombre_custom:
            nombre_limpio = _sanitizar_nombre(nombre_custom, fallback="backup_cys")
            nombre_archivo = f"{nombre_limpio}_{timestamp}.sql"
        else:
            nombre_archivo = f"backup_cys_{timestamp}.sql"

        dest_path = os.path.join(backup_dir, nombre_archivo)

        ok, err_msg = _ejecutar_mysqldump(bin_dump, db_info, dest_path)
        if not ok:
            messages.error(request, f"Error al generar la copia de seguridad: {err_msg}")
            return redirect("respaldos_index")

        size_bytes = os.path.getsize(dest_path)
        size_mb = round(size_bytes / (1024 * 1024), 4)

        BackupRegistro.objects.create(
            nombre=nombre_archivo,
            descripcion=descripcion,
            ruta=dest_path,
            tamaño_mb=size_mb,
        )

        messages.success(
            request,
            f"¡Copia de seguridad '{nombre_archivo}' generada con éxito ({_formatear_tamano(size_mb)})!",
        )
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado al crear el respaldo: {e}")

    return redirect("respaldos_index")


@login_required
def respaldo_descargar(request, pk):
    """Descarga el archivo .sql del respaldo seleccionado."""
    registro = get_object_or_404(BackupRegistro, pk=pk)
    if not registro.ruta or not os.path.exists(registro.ruta):
        messages.error(
            request,
            f"El archivo de respaldo '{registro.nombre}' no se encuentra en el disco.",
        )
        return redirect("respaldos_index")

    response = FileResponse(
        open(registro.ruta, "rb"),
        as_attachment=True,
        filename=registro.nombre,
        content_type="application/sql",
    )
    return response


@login_required
@require_POST
def respaldo_editar(request, pk):
    """Edita el nombre y la descripción de una copia de seguridad."""
    registro = get_object_or_404(BackupRegistro, pk=pk)
    nuevo_nombre_raw = request.POST.get("nombre", "").strip()
    nueva_desc = request.POST.get("descripcion", "").strip()[:500]

    err_nombre = _validar_nombre_respaldo(nuevo_nombre_raw, obligatorio=True)
    if err_nombre:
        messages.error(request, err_nombre)
        return redirect("respaldos_index")

    base_segura = _sanitizar_nombre(nuevo_nombre_raw, fallback=f"backup_{registro.pk}")
    nuevo_nombre = f"{base_segura}.sql"

    if nuevo_nombre != registro.nombre and registro.ruta and os.path.exists(registro.ruta):
        backup_dir = os.path.dirname(registro.ruta)
        nueva_ruta = os.path.join(backup_dir, nuevo_nombre)
        if os.path.exists(nueva_ruta):
            messages.error(
                request,
                f"Ya existe un archivo llamado '{nuevo_nombre}'. Elige otro nombre.",
            )
            return redirect("respaldos_index")
        try:
            os.rename(registro.ruta, nueva_ruta)
            registro.ruta = nueva_ruta
        except Exception as e:
            messages.warning(
                request,
                f"Se actualizó el registro pero no se pudo renombrar en disco: {e}",
            )

    registro.nombre = nuevo_nombre
    registro.descripcion = nueva_desc
    registro.save()

    messages.success(request, f"Respaldo '{registro.nombre}' actualizado correctamente.")
    return redirect("respaldos_index")


@login_required
@require_POST
def respaldo_eliminar(request, pk):
    """Elimina la copia de seguridad de la base de datos y del disco."""
    registro = get_object_or_404(BackupRegistro, pk=pk)
    nombre = registro.nombre

    try:
        if registro.ruta and os.path.exists(registro.ruta):
            os.remove(registro.ruta)
        registro.delete()
        messages.success(request, f"La copia de seguridad '{nombre}' ha sido eliminada.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la copia de seguridad: {e}")

    return redirect("respaldos_index")


@login_required
@require_POST
def respaldo_restaurar(request, pk):
    """Restaura la base de datos MySQL a partir de un archivo .sql de respaldo."""
    registro = get_object_or_404(BackupRegistro, pk=pk)

    if not registro.ruta or not os.path.exists(registro.ruta):
        messages.error(
            request,
            f"El archivo '{registro.nombre}' no existe en el disco y no se puede restaurar.",
        )
        return redirect("respaldos_index")

    bin_mysql = _obtener_binario("mysql")
    if not bin_mysql:
        messages.error(
            request,
            "No se encontró el ejecutable 'mysql' para restaurar. Verifica la instalación.",
        )
        return redirect("respaldos_index")

    db_info = _obtener_datos_db()

    # Respaldo automático previo de seguridad (si el usuario lo dejó activo)
    nota_previo = ""
    if request.POST.get("crear_previo") == "1":
        bin_dump = _obtener_binario("mysqldump")
        if bin_dump:
            backup_dir = os.path.join(settings.BASE_DIR, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_previo = f"auto_pre_restauracion_{ts}.sql"
            ruta_previo = os.path.join(backup_dir, nombre_previo)
            ok_prev, _ = _ejecutar_mysqldump(bin_dump, db_info, ruta_previo)
            if ok_prev:
                size_mb_prev = round(os.path.getsize(ruta_previo) / (1024 * 1024), 4)
                BackupRegistro.objects.create(
                    nombre=nombre_previo,
                    descripcion=f"Respaldo automático previo a restaurar '{registro.nombre}'",
                    ruta=ruta_previo,
                    tamaño_mb=size_mb_prev,
                )
                nota_previo = f" Se guardó un respaldo previo automático ({nombre_previo})."

    comando = [
        bin_mysql,
        f"-u{db_info['usuario']}",
        f"-h{db_info['host']}",
        f"-P{db_info['puerto']}",
        "--default-character-set=utf8mb4",
        db_info["nombre"],
    ]

    env = os.environ.copy()
    if db_info["password"]:
        env["MYSQL_PWD"] = db_info["password"]

    try:
        with open(registro.ruta, "rb") as f:
            res = subprocess.run(
                comando, stdin=f, stderr=subprocess.PIPE, env=env, check=False
            )

        if res.returncode == 0:
            messages.success(
                request,
                f"¡Base de datos restaurada exitosamente desde '{registro.nombre}'!{nota_previo}",
            )
        else:
            err = res.stderr.decode("utf-8", errors="ignore") or "Error en mysql"
            messages.error(request, f"Error al restaurar la base de datos: {err}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado al restaurar: {e}")

    return redirect("respaldos_index")


@login_required
@require_POST
def respaldo_subir(request):
    """Permite subir un archivo .sql externo como respaldo registrado."""
    archivo = request.FILES.get("archivo_sql")
    if not archivo:
        messages.error(request, "Por favor selecciona un archivo .sql válido.")
        return redirect("respaldos_index")

    if not archivo.name.lower().endswith(".sql"):
        messages.error(request, "El archivo debe tener extensión .sql")
        return redirect("respaldos_index")

    err_nombre = _validar_nombre_respaldo(os.path.basename(archivo.name), obligatorio=True)
    if err_nombre:
        messages.error(request, err_nombre)
        return redirect("respaldos_index")

    if archivo.size == 0:
        messages.error(request, "El archivo seleccionado está vacío.")
        return redirect("respaldos_index")

    if archivo.size > MAX_UPLOAD_MB * 1024 * 1024:
        messages.error(request, f"El archivo supera el límite permitido de {MAX_UPLOAD_MB} MB.")
        return redirect("respaldos_index")

    err_contenido = _validar_contenido_sql(archivo)
    if err_contenido:
        messages.error(request, err_contenido)
        return redirect("respaldos_index")

    try:
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_base = _sanitizar_nombre(os.path.splitext(archivo.name)[0], fallback="respaldo")
        nombre_final = f"{nombre_base}_subido_{timestamp}.sql"
        dest_path = os.path.join(backup_dir, nombre_final)

        with open(dest_path, "wb+") as destination:
            for chunk in archivo.chunks():
                destination.write(chunk)

        size_bytes = os.path.getsize(dest_path)
        size_mb = round(size_bytes / (1024 * 1024), 4)

        desc = request.POST.get("descripcion", "").strip()[:500] or "Copia de seguridad subida manualmente"

        BackupRegistro.objects.create(
            nombre=nombre_final,
            descripcion=desc,
            ruta=dest_path,
            tamaño_mb=size_mb,
        )

        messages.success(
            request,
            f"¡Archivo '{nombre_final}' subido y registrado exitosamente ({_formatear_tamano(size_mb)})!",
        )
    except Exception as e:
        messages.error(request, f"Error al subir el archivo: {e}")

    return redirect("respaldos_index")
