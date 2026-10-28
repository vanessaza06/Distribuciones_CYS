import pymysql
from django.conf import settings
db = settings.DATABASES["default"]
conn = pymysql.connect(host=db["HOST"], port=int(db["PORT"]), user=db["USER"], password=db["PASSWORD"])
cur = conn.cursor()
for nombre in ("distribuciones_cys", "distribuiciones_cys", "licorera_cys"):
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s", (nombre,))
    print(nombre, "->", cur.fetchone()[0], "tablas")
conn.close()
