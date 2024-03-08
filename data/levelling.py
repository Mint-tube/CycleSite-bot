import os, sqlite3, discord, random
import data.config as config
from data.logging import debug, info, warning, error

#Вспомогательные функции ------------

async def check_member(member: discord.Member):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute(f'SELECT * FROM levelling WHERE user_id = {member.id}')
    if cursor.fetchone() == None:
        cursor.execute(f'INSERT INTO levelling (user_id) VALUES ({member.id})')
    connection.commit()
    connection.close()

async def get_xp(member: discord.Member):
    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()

    cursor.execute("SELECT xp FROM levelling WHERE user_id = ?", (member.id,))
    xp = cursor.fetchone()

    cursor.close()

    if xp != None:
        return xp[0]
    else:
        return None

async def get_level(member: discord.Member):
    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()
    cursor.execute("SELECT level FROM levelling WHERE user_id = ?", (member.id,))
    level = cursor.fetchone()
    if level != None:
        return level[0]
    else:
        return None

async def update_level(member: discord.Member):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute(f'SELECT xp, level FROM levelling WHERE user_id = {member.id}')
    fetched = cursor.fetchone()
    xp = fetched[0]
    level_cached = fetched[1]
    level_current = 1
    while xp >= level_current * config.xp_per_lvl:
        xp -= level_current * config.xp_per_lvl
        level_current += 1
    if level_cached != level_current:
        cursor.execute(f'UPDATE levelling SET level = {level_current} WHERE user_id = {member.id}')

        connection.commit()
    connection.close()

async def set_bg(member: discord.Member, url: str):
    await check_member(member = member)

    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute(f'UPDATE levelling set background = ? WHERE user_id = ?', (url, member.id))

    connection.commit()
    connection.close()

async def add_xp(member: discord.Member, delta: int):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute(f'UPDATE levelling SET xp = xp + {delta} WHERE user_id = {member.id}')

    connection.commit()
    connection.close()

    await update_level(member = member)

async def add_voice_time(member: discord.Member, delta: int):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute(f'UPDATE levelling SET voice_time = voice_time + {round(delta/3600, 2)} WHERE user_id = {member.id}')

    connection.commit()
    connection.close()

#Функции для bot.py ------------

async def xp_on_message(message: discord.Message):
    if message.author.bot == False and message.channel.id not in [1123192369630695475, 1122481071330689045]:
        await check_member(member = message.author)
        await add_xp(member = message.author, delta = random.randint(2, 10))

async def xp_on_voice(member: discord.Member, timedelta: int):
    await check_member(member = member)
    await add_xp(member = member, delta = int(timedelta/config.voice_seconds_per_xp))
    await add_voice_time(member = member, delta = timedelta)

# async def leaderboard(intrct):
#     connection = sqlite3.connect("data/databases/levelling.db")
#     cursor = connection.cursor()

#     cursor.execute("SELECT * FROM levelling ORDER BY xp DESC")
#     dataframe = cursor.fetchall()

#     connection.commit()
#     connection.close()

# async def user_profile(intrct, member: discord.Member):
#     connection = sqlite3.connect("data/databases/levelling.db")
#     cursor = connection.cursor()

#     cursor.execute("SELECT * FROM levelling ORDER BY xp DESC")
#     dataframe = cursor.fetchall()

#     connection.commit()
#     connection.close()