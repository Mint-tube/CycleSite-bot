import sqlite3


connection = sqlite3.connect('data/databases/levelling.db')
cursor = connection.cursor()
cursor.execute('ALTER TABLE levelling DROP COLUMN background')
connection.commit()
connection.close()