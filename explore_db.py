import sqlite3

db_path = r'c:\Users\Asus\Documentos\Distribuciones_CYS\db.sqlite3'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('=== TABLAS ===')
print(tables)
print()

for t in tables:
    cur.execute(f'PRAGMA table_info("{t}")')
    cols = cur.fetchall()
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    count = cur.fetchone()[0]
    print(f'--- {t} ({count} registros) ---')
    for c in cols:
        print(f'  cid={c[0]} name={c[1]} type={c[2]} notnull={c[3]} dflt={c[4]} pk={c[5]}')

    # FK
    cur.execute(f'PRAGMA foreign_key_list("{t}")')
    fks = cur.fetchall()
    if fks:
        print('  FOREIGN KEYS:')
        for fk in fks:
            print(f'    {fk}')
    print()

conn.close()
