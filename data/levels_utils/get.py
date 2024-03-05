import os, sqlite3, discord
import data.config as config


class response_object():

    def __init__(self, status: str, content = None):
        self.status = status
        self.content = content


def xp(user: discord.Member = None, guild: discord.Guild = None):

    connection = sqlite3.connect("data/levelling.db")
    cursor = connection.cursor()

    cursor.execute("SELECT xp FROM levelling WHERE user_id = ?", (user.id,))
    xp = cursor.fetchone()

    if xp != None:
        response = response_object(status = 'OK', content = xp[0])
    else:
        response = response_object(status = 'Not Found')

    cursor.close()

    return response