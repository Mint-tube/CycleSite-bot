import sqlite3
import data.levelling as levelling


connection = sqlite3.connect("data/databases/levelling.db")
cursor = connection.cursor()

cursor.execute('ALTER TABLE levelling ADD COLUMN user_name TEXT')

connection.commit()
connection.close()