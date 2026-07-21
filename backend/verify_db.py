import sqlite3
conn = sqlite3.connect('app/data/construction.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
tables = cur.fetchall()
print(f"Total tables: {len(tables)}\n")
for (t,) in tables:
    count = cur.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
    print(f"  {t}: {count} rows")
    # Show 2 sample rows
    rows = cur.execute(f"SELECT * FROM [{t}] LIMIT 2").fetchall()
    cols = [d[0] for d in cur.description]
    print(f"    Columns: {', '.join(cols)}")
    for r in rows:
        print(f"    -> {dict(zip(cols, r))}")
    print()
conn.close()
