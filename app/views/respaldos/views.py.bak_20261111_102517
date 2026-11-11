import os
import glob
import shutil
import subprocess
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from app.models import BackupRegistro


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
    respaldos = BackupRegistro.objects.all().order_by("-fecha")
    total_respaldos = respaldos.count()

    total_mb = sum(r.tamaño_mb for r in respaldos)
    ultimo_respaldo = respaldos.first()
    db_info = _obtener_datos_db()

    # Comprobar que los archivos físicos existan en disco
    for r in respaldos:
        r.existe_en_disco = os.path.exists(r.ruta) if r.ruta else False

    contexto = {
        "respaldos": respaldos,
        "total_respaldos": total_respaldos,
        "total_mb": round(total_mb, 2),
        "ultimo_respaldo": ultimo_respaldo,
        "db_name": db_info["nombre"],
        "db_host": db_info["host"],
        "db_port": db_info["puerto"],
    }
    return render(request, "respaldos/respaldos.html", contexto)


@login_required
@require_POST
def respaldo_crear(request):
    """Genera un nuevo respaldo completo de la base de datos."""
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

        nombre_custom = request.POST.get("nombre", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if nombre_custom:
            # Limpiar caracteres inválidos
            nombre_limpio = "".join(
                c for c in nombre_custom if c.isalnum() or c in ("-", "_", " ")
            ).strip()
            nombre_archivo = f"{nombre_limpio}_{timestamp}.sql"
        else:
            nombre_archivo = f"backup_cys_{timestamp}.sql"

        dest_path = os.path.join(backup_dir, nombre_archivo)

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
            err_msg = res.stderr.decode("utf-8", errors="ignore") or "Error en mysqldump"
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
            f"¡Copia de seguridad '{nombre_archivo}' generada con éxito ({size_mb:.2f} MB)!",
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
    nuevo_nombre = request.POST.get("nombre", "").strip()
    nueva_desc = request.POST.get("descripcion", "").strip()

    if nuevo_nombre:
        if not nuevo_nombre.endswith(".sql"):
            nuevo_nombre = f"{nuevo_nombre}.sql"

        # Si el nombre físico cambia, renombrar el archivo en disco si existe
        if nuevo_nombre != registro.nombre and registro.ruta and os.path.exists(registro.ruta):
            backup_dir = os.path.dirname(registro.ruta)
            nueva_ruta = os.path.join(backup_dir, nuevo_nombre)
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
                f"¡Base de datos restaurada exitosamente desde '{registro.nombre}'!",
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

    try:
        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_base = os.path.splitext(archivo.name)[0]
        nombre_final = f"{nombre_base}_subido_{timestamp}.sql"
        dest_path = os.path.join(backup_dir, nombre_final)

        with open(dest_path, "wb+") as destination:
            for chunk in archivo.chunks():
                destination.write(chunk)

        size_bytes = os.path.getsize(dest_path)
        size_mb = round(size_bytes / (1024 * 1024), 4)

        desc = request.POST.get("descripcion", "").strip() or "Copia de seguridad subida manualmente"

        BackupRegistro.objects.create(
            nombre=nombre_final,
            descripcion=desc,
            ruta=dest_path,
            tamaño_mb=size_mb,
        )

        messages.success(
            request,
            f"¡Archivo '{nombre_final}' subido y registrado exitosamente ({size_mb:.2f} MB)!",
        )
    except Exception as e:
        messages.error(request, f"Error al subir el archivo: {e}")

    return redirect("respaldos_index")
