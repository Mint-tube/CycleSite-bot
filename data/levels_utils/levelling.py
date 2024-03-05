import os, sqlite3, discord, random
import data.config as config
from data.logging import debug, info, warning, error
import data.levels_utils.add as add
import data.levels_utils.get as get

class response_object():
    def __init__(self, status: str, content = None):
        self.status = status
        self.content = content

def xp_on_message(message: discord.Message):
    if not message.author.id == config.client_id:
        user_check = get.xp(user = message.author)
        if user_check.status == 'Not Found':
            connection = sqlite3.connect('data/levelling.db')
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO levelling (user_id, level, xp, background) 
                            VALUES (?, ?, ?, ?)''',
                            (message.author.id, 1, 0, config.bg_placeholder))
            connection.commit()
            connection.close()
        elif user_check.status == 'OK':
            xp_delta = random.randint(5, 25)
            #Добавление опыта в таблицу