import pymysql
from django.conf import settings

db = settings.DATABASES["default"]
conn = pymysql.connect(host=db["HOST"], port=int(db["PORT"]), user=db["USER"], password=db["PASSWORD"])
cur = conn.cursor()
cur.execute("SHOW DATABASES")
print("Bases de datos:", ", ".join(f[0] for f in cur.fetchall()))
conn.close()
