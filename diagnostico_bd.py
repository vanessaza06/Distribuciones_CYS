from django.apps import apps
from django.db import connection

problemas = 0

with connection.cursor() as cur:
    tablas_bd = set(connection.introspection.table_names())

    for modelo in apps.get_app_config('app').get_models():
        tabla = modelo._meta.db_table

        if tabla not in tablas_bd:
            print("FALTA TABLA:", tabla)
            problemas += 1
            continue

        cols_bd = {c.name for c in connection.introspection.get_table_description(cur, tabla)}
        cols_modelo = {f.column for f in modelo._meta.local_concrete_fields}

        for col in sorted(cols_modelo - cols_bd):
            print("FALTA COLUMNA:", tabla + "." + col)
            problemas += 1

        for col in sorted(cols_bd - cols_modelo):
            print("SOBRA EN BD (no esta en el modelo):", tabla + "." + col)
            problemas += 1

print("Problemas encontrados:", problemas)
