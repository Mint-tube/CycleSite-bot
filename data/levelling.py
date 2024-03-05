import os, sqlite3, discord, random
import data.config as config
from data.logging import debug, info, warning, error


async def get_member(id: int):
    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM levelling WHERE user_id = {id}")
    member = cursor.fetchone()
    return member

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

# async def add_level(member: discord.Member, delta: int):
#     connection = sqlite3.connect('data/databases/levelling.db')
#     cursor = connection.cursor()
#     cursor.execute(f'UPDATE levelling SET level = level + {delta} WHERE user_id = {member.id}')
#     connection.commit()
#     connection.close()

async def add_xp(member: discord.Member, delta: int):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()
    cursor.execute(f'UPDATE levelling SET xp = xp + {delta} WHERE user_id = {member.id}')
    connection.commit()
    connection.close()
    await update_level(member = member)




async def xp_on_message(message: discord.Message):
    member = message.author
    if member.bot == False and message.channel.category_id != 1133666070390132776:
        if await get_member(id = member.id) == None:
            connection = sqlite3.connect('data/databases/levelling.db')
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO levelling (user_id, level, xp, background) 
                            VALUES (?, 1, 0, ?)''', (message.author.id, config.bg_placeholder))
            connection.commit()
            connection.close()
        else:
            await add_xp(member = member, delta = random.randint(2, 10))