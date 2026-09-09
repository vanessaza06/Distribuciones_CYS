from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    cursor.execute("SHOW TABLES;")
    tablas = cursor.fetchall()
    for (tabla,) in tablas:
        print(f"Borrando tabla: {tabla}")
        cursor.execute(f"DROP TABLE `{tabla}`;")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

print("Listo. Todas las tablas fueron eliminadas.")
