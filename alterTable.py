import sqlite3

co = sqlite3.connect('data/databases/levelling.db')
cu = co.cursor()
cu.execute('ALTER TABLE levelling ADD COLUMN voice_time REAL DEFAULT 0')
co.commit()
co.close()