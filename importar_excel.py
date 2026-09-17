"""
importar_excel.py
=================
Importa datos del archivo "FEB 2026 (2).xlsx" a la base de datos SQLite
del proyecto Django Distribuciones CYS.

Tablas que se poblan (en orden por dependencias):
  1. categoria
  2. producto
  3. presentacion_producto
  4. lote  (requiere bodega - se crea una bodega dummy si no existe)

Uso:
  python importar_excel.py            # DRY-RUN (no toca la BD)
  python importar_excel.py --real     # Aplica cambios reales
  python importar_excel.py --real --upsert   # Actualiza precios si ya existen
  python importar_excel.py --real --no-lote  # Solo categoria + producto + presentacion
"""

import sys
import os
import shutil
import sqlite3
import warnings
from datetime import date, datetime
from decimal import Decimal

import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "FEB 2026 (2).xlsx")
DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
BACKUP_PATH = os.path.join(BASE_DIR, "db.sqlite3.backup")

HOJAS_INVENTARIO = {
    "PLAZA": date(2026, 2, 1),
    "3 FEB": date(2026, 2, 3),
    "5 FEB": date(2026, 2, 5),
    "6 feb": date(2026, 2, 6),
    "8 FEB": date(2026, 2, 8),
    "9 FEB": date(2026, 2, 9),
    "17 FEB": date(2026, 2, 17),
}

FECHA_VENCIMIENTO_DUMMY = date(2099, 12, 31)
BODEGA_DUMMY_NOMBRE = "Principal"

DRY_RUN = "--real" not in sys.argv
UPSERT = "--upsert" in sys.argv
WITH_LOTE = "--no-lote" not in sys.argv

stats = {
    "categorias_nuevas": 0,
    "categorias_existentes": 0,
    "productos_nuevos": 0,
    "productos_existentes": 0,
    "presentaciones_nuevas": 0,
    "presentaciones_existentes": 0,
    "lotes_nuevos": 0,
    "rechazados": [],
}


def leer_hoja(xl, nombre_hoja):
    df = pd.read_excel(xl, sheet_name=nombre_hoja, header=0)

    rename_map = {
        df.columns[0]: "categoria",
        df.columns[1]: "producto",
        "INICIAL": "inicial",
        "INGRESO": "ingreso",
        "SALIDA": "salida",
        "CANTIDAD TOTAL": "cantidad_total",
        "COSTO CANASTA": "costo_canasta",
        "VENTA CANASTA": "venta_canasta",
        "CAJAS VENDIDAS": "cajas_vendidas",
        "TOTAL VENTA FINAL DIA": "total_venta_dia",
        "UTILIDAD": "utilidad",
        "VALOR PRODUCTO": "valor_producto",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    cols_keep = [c for c in [
        "categoria", "producto", "inicial", "ingreso", "salida",
        "cantidad_total", "costo_canasta", "venta_canasta",
        "cajas_vendidas", "utilidad", "valor_producto"
    ] if c in df.columns]
    df = df[cols_keep].copy()

    df["categoria"] = df["categoria"].replace("", pd.NA).ffill()
    df = df[df["producto"].notna() & (df["producto"].astype(str).str.strip() != "")]
    df = df[~df["producto"].astype(str).str.upper().str.contains(
        r"^(PRODUCTO|NOMBRE|ITEM|DESCRIPCION)", na=False, regex=True
    )]
    df = df[df["categoria"].notna()]

    df["categoria"] = df["categoria"].astype(str).str.strip().str.upper()
    df["producto"] = df["producto"].astype(str).str.strip().str.upper()

    df = df[~df["categoria"].str.contains(
        r"^(NAN|NONE|TOTAL|SUBTOTAL|SUMA|#)", na=False, regex=True
    )]
    df = df[~df["producto"].str.contains(
        r"^(NAN|NONE|TOTAL|SUBTOTAL|SUMA|#)", na=False, regex=True
    )]

    num_cols = ["inicial", "ingreso", "salida", "cantidad_total",
                "costo_canasta", "venta_canasta", "cajas_vendidas", "utilidad", "valor_producto"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates(subset=["categoria", "producto"], keep="first")
    df = df.reset_index(drop=True)
    return df


def consolidar_todas_las_hojas(xl):
    frames = []
    for nombre_hoja, fecha_hoja in HOJAS_INVENTARIO.items():
        try:
            df = leer_hoja(xl, nombre_hoja)
            df["fecha_hoja"] = fecha_hoja
            frames.append(df)
            print(f"  OK Hoja '{nombre_hoja}': {len(df)} filas validas")
        except Exception as e:
            print(f"  ERROR Hoja '{nombre_hoja}': {e}")

    if not frames:
        raise RuntimeError("No se pudo leer ninguna hoja del Excel.")

    todo = pd.concat(frames, ignore_index=True)
    todo = todo.sort_values("fecha_hoja")
    todo = todo.drop_duplicates(subset=["categoria", "producto"], keep="last")
    todo = todo.reset_index(drop=True)
    return todo


def validar_fila(row):
    if not row.get("producto") or str(row.get("producto", "")).strip() == "":
        return False, "nombre de producto vacio"
    if not row.get("categoria") or str(row.get("categoria", "")).strip() == "":
        return False, "categoria vacia"
    venta = row.get("venta_canasta")
    if pd.isna(venta) or venta is None:
        return False, "precio de venta nulo"
    try:
        v = float(venta)
        if v <= 0:
            return False, f"precio de venta invalido ({v})"
    except (TypeError, ValueError):
        return False, f"precio de venta no numerico ({venta})"
    return True, None


def get_or_create_categoria(cur, nombre, upsert=False):
    cur.execute("SELECT codigo_categoria FROM categoria WHERE nombre = ?", (nombre,))
    row = cur.fetchone()
    if row:
        return row[0], False
    codigo_base = nombre[:4].upper().replace(" ", "_")
    cur.execute("SELECT COUNT(*) FROM categoria WHERE codigo LIKE ?", (f"{codigo_base}%",))
    count = cur.fetchone()[0]
    codigo = f"{codigo_base}{count + 1:02d}"
    cur.execute(
        "INSERT INTO categoria (codigo, nombre, descripcion, activo) VALUES (?, ?, ?, ?)",
        (codigo, nombre, "Importado desde Excel FEB 2026", 1),
    )
    return cur.lastrowid, True


def get_or_create_producto(cur, nombre, codigo_categoria, upsert=False):
    cur.execute("SELECT codigo_producto FROM producto WHERE nombre = ?", (nombre,))
    row = cur.fetchone()
    if row:
        if upsert:
            cur.execute(
                "UPDATE producto SET codigo_categoria = ? WHERE codigo_producto = ?",
                (codigo_categoria, row[0]),
            )
        return row[0], False
    cur.execute(
        "INSERT INTO producto (nombre, descripcion, fecha_vencimiento, codigo_categoria, activo) VALUES (?, ?, ?, ?, ?)",
        (nombre, "Importado desde Excel FEB 2026", FECHA_VENCIMIENTO_DUMMY.isoformat(), codigo_categoria, 1),
    )
    return cur.lastrowid, True


def get_or_create_presentacion(cur, codigo_producto, precio_venta, cantidad, upsert=False):
    cur.execute(
        "SELECT codigo_presentacion, precio_venta FROM presentacion_producto WHERE codigo_producto = ?",
        (codigo_producto,),
    )
    row = cur.fetchone()
    if row:
        if upsert and float(row[1]) != float(precio_venta):
            cur.execute(
                "UPDATE presentacion_producto SET precio_venta = ? WHERE codigo_presentacion = ?",
                (str(precio_venta), row[0]),
            )
        return row[0], False
    cant = max(1, int(cantidad) if not pd.isna(cantidad) else 1)
    cur.execute(
        "INSERT INTO presentacion_producto (nombre, precio_venta, cantidad, observaciones, activo, codigo_producto) VALUES (?, ?, ?, ?, ?, ?)",
        ("Caja", str(precio_venta), cant, "Importado desde Excel FEB 2026", 1, codigo_producto),
    )
    return cur.lastrowid, True


def get_or_create_bodega(cur):
    cur.execute("SELECT codigo_bodega FROM bodega WHERE nombre = ?", (BODEGA_DUMMY_NOMBRE,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO bodega (nombre, descripcion, estado, capacidad) VALUES (?, ?, ?, ?)",
        (BODEGA_DUMMY_NOMBRE, "Bodega creada por importacion automatica", "activo", None),
    )
    return cur.lastrowid


def crear_lote(cur, codigo_producto, codigo_presentacion, codigo_bodega, costo_unitario, cantidad_inicial, fecha_registro):
    numero_lote = f"FEB2026-{codigo_producto}-{fecha_registro.strftime('%Y%m%d')}"
    cur.execute("SELECT codigo_lote FROM lote WHERE numero_lote = ?", (numero_lote,))
    if cur.fetchone():
        return None, False
    costo_unit = Decimal(str(float(costo_unitario))) if not pd.isna(costo_unitario) else Decimal("0")
    cant = int(cantidad_inicial) if not pd.isna(cantidad_inicial) and float(cantidad_inicial) > 0 else 0
    costo_total = costo_unit * cant
    cur.execute(
        "INSERT INTO lote (numero_lote, costo_unitario, costo_total, cantidad_inicial, stock_actual, fecha_registro, codigo_producto, codigo_presentacion, codigo_bodega) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (numero_lote, str(costo_unit), str(costo_total), cant, cant,
         datetime.combine(fecha_registro, datetime.min.time()).isoformat(),
         codigo_producto, codigo_presentacion, codigo_bodega),
    )
    return cur.lastrowid, True


def hacer_backup():
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"  Backup creado en: {BACKUP_PATH}")


def main():
    print("=" * 60)
    print("  IMPORTADOR EXCEL -> SQLite  |  Distribuciones CYS")
    print(f"  Modo: {'DRY-RUN (sin cambios)' if DRY_RUN else '*** REAL ***'}")
    print(f"  UPSERT: {'SI' if UPSERT else 'NO (INSERT solo si no existe)'}")
    print(f"  Lotes: {'SI' if WITH_LOTE else 'NO'}")
    print("=" * 60)

    print("\n[1/4] Leyendo Excel...")
    xl = pd.ExcelFile(EXCEL_PATH)
    df = consolidar_todas_las_hojas(xl)
    print(f"  Total filas consolidadas: {len(df)}")

    print("\n[2/4] Validando filas...")
    filas_validas = []
    for idx, row in df.iterrows():
        ok, motivo = validar_fila(row)
        if ok:
            filas_validas.append(row)
        else:
            stats["rechazados"].append({
                "fila": idx,
                "producto": row.get("producto", "?"),
                "categoria": row.get("categoria", "?"),
                "motivo": motivo,
            })
    print(f"  Validas: {len(filas_validas)}")
    print(f"  Rechazadas: {len(stats['rechazados'])}")

    if DRY_RUN:
        print("\n[3/4] DRY-RUN: simulando inserciones...")
    else:
        print("\n[3/4] Aplicando cambios reales...")
        hacer_backup()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    codigo_bodega = None
    if WITH_LOTE and not DRY_RUN:
        codigo_bodega = get_or_create_bodega(cur)
    elif WITH_LOTE and DRY_RUN:
        cur.execute("SELECT codigo_bodega FROM bodega WHERE nombre = ?", (BODEGA_DUMMY_NOMBRE,))
        r = cur.fetchone()
        codigo_bodega = r[0] if r else -1

    for row in filas_validas:
        nombre_cat = str(row["categoria"]).strip()
        nombre_prod = str(row["producto"]).strip()
        precio_venta = Decimal(str(float(row["venta_canasta"])))
        costo = row.get("costo_canasta", 0)
        cantidad = row.get("cantidad_total", 0)
        fecha_hoja = row.get("fecha_hoja", date(2026, 2, 1))

        try:
            if DRY_RUN:
                cur.execute("SELECT codigo_categoria FROM categoria WHERE nombre = ?", (nombre_cat,))
                cat_row = cur.fetchone()
                if cat_row:
                    stats["categorias_existentes"] += 1
                    cod_prod_sim = -1
                    cur.execute("SELECT codigo_producto FROM producto WHERE nombre = ?", (nombre_prod,))
                    prod_row = cur.fetchone()
                    if prod_row:
                        stats["productos_existentes"] += 1
                        cod_prod_sim = prod_row[0]
                    else:
                        stats["productos_nuevos"] += 1
                else:
                    stats["categorias_nuevas"] += 1
                    stats["productos_nuevos"] += 1
                    cod_prod_sim = -1

                cur.execute(
                    "SELECT codigo_presentacion FROM presentacion_producto WHERE codigo_producto = ?",
                    (cod_prod_sim,)
                )
                if cur.fetchone():
                    stats["presentaciones_existentes"] += 1
                else:
                    stats["presentaciones_nuevas"] += 1

                if WITH_LOTE:
                    stats["lotes_nuevos"] += 1

            else:
                cod_cat, cat_creada = get_or_create_categoria(cur, nombre_cat, UPSERT)
                if cat_creada:
                    stats["categorias_nuevas"] += 1
                else:
                    stats["categorias_existentes"] += 1

                cod_prod, prod_creado = get_or_create_producto(cur, nombre_prod, cod_cat, UPSERT)
                if prod_creado:
                    stats["productos_nuevos"] += 1
                else:
                    stats["productos_existentes"] += 1

                cod_pres, pres_creada = get_or_create_presentacion(
                    cur, cod_prod, precio_venta, cantidad, UPSERT
                )
                if pres_creada:
                    stats["presentaciones_nuevas"] += 1
                else:
                    stats["presentaciones_existentes"] += 1

                if WITH_LOTE and codigo_bodega and cod_prod > 0:
                    lote_id, lote_creado = crear_lote(
                        cur, cod_prod, cod_pres, codigo_bodega,
                        costo, cantidad, fecha_hoja
                    )
                    if lote_creado:
                        stats["lotes_nuevos"] += 1

        except Exception as e:
            stats["rechazados"].append({
                "fila": "runtime",
                "producto": nombre_prod,
                "categoria": nombre_cat,
                "motivo": str(e),
            })
            continue

    if not DRY_RUN:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        print("  Cambios confirmados (COMMIT)")
    else:
        conn.rollback()

    conn.close()

    print("\n[4/4] Resumen")
    print("-" * 60)
    print(f"  Categorias nuevas:       {stats['categorias_nuevas']}")
    print(f"  Categorias existentes:   {stats['categorias_existentes']}")
    print(f"  Productos nuevos:        {stats['productos_nuevos']}")
    print(f"  Productos existentes:    {stats['productos_existentes']}")
    print(f"  Presentaciones nuevas:   {stats['presentaciones_nuevas']}")
    print(f"  Presentaciones exist.:   {stats['presentaciones_existentes']}")
    if WITH_LOTE:
        print(f"  Lotes nuevos:            {stats['lotes_nuevos']}")
    print(f"  Filas rechazadas:        {len(stats['rechazados'])}")

    if stats["rechazados"]:
        print("\n  Detalle de rechazados:")
        for r in stats["rechazados"][:20]:
            print(f"    * [{r['categoria']}] {r['producto']} -> {r['motivo']}")
        if len(stats["rechazados"]) > 20:
            print(f"    ... y {len(stats['rechazados']) - 20} mas")

    if DRY_RUN:
        print("\n" + "=" * 60)
        print("  Este fue un DRY-RUN. Ningun dato fue modificado.")
        print("  Para aplicar los cambios reales, ejecuta:")
        print("    python importar_excel.py --real")
        print("  Para tambien actualizar precios existentes:")
        print("    python importar_excel.py --real --upsert")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  Importacion completada.")
        print(f"  Backup disponible en: {BACKUP_PATH}")
        print("  Para revertir los cambios ejecuta:")
        print(f"    copy db.sqlite3.backup db.sqlite3")
        print("=" * 60)


if __name__ == "__main__":
    main()
