import os, sqlite3, discord, random, asyncio, datetime
from math import ceil

import data.config as config
from data.logging import *

#О нет, view(
class leaderboard_view(discord.ui.View):
    def __init__(self, original_intrct, dataframe, lb_type, page):
        self.original_intrct = original_intrct
        self.dataframe = dataframe
        self.lb_type = lb_type
        self.page = page
        super().__init__(timeout=600)


    @discord.ui.button(label="◀ Назад", style=discord.ButtonStyle.primary, custom_id="backward")
    async def backward(self, interaction, button):
        if self.page == 1:
            await interaction.response.send_message("Это начало рейтинга 😎", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.page -= 1
        embed = await dataframe_to_leaderboard(self.dataframe, self.lb_type, self.page)

        await self.original_intrct.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Вперёд ▶", style=discord.ButtonStyle.primary, custom_id="forward")
    async def forward(self, interaction, button):
        if len(self.dataframe)/10 <= self.page:
            await interaction.response.send_message("Это конец рейтинга 😓", ephemeral=True)
            return

        await interaction.response.defer()
        self.page += 1
        embed = await dataframe_to_leaderboard(self.dataframe, self.lb_type, self.page)

        await self.original_intrct.edit_original_response(embed=embed, view=self)

    async def on_timeout(self):
        self.clear_items()
        self.add_item(discord.ui.Button(label="Лидерборд устарел", custom_id="stopped", disabled=True))
        await self.original_intrct.edit_original_response(view=self)
        

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

    connection.close()

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

        return level_current
    else:
        connection.close()

        return None

async def add_xp(member: discord.Member, delta: int):
    await check_member(member = member)

    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    try:
        cursor.execute(f'UPDATE levelling SET xp = xp + {delta} WHERE user_id = {member.id}')
    except sqlite3.OperationalError:
        error("in add_xp():    sqlite3.OperationalError: database is locked")

    connection.commit()
    connection.close()

    return await update_level(member = member) 

async def update_role(lvl: int):
    connection = sqlite3.connect('data/databases/roles.db')
    cursor = connection.cursor()

    cursor.execute(f'SELECT level, role_id FROM roles')
    roles = cursor.fetchall()
    connection.close()

    if lvl == -1:
        return None

    for role in roles:
        if role[0] <= lvl:
            return role[1]

async def add_voice_time(member: discord.Member, delta: int):
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    try:
        cursor.execute(f'UPDATE levelling SET voice_time = voice_time + {"{:.2f}".format(round(delta/3600, 2))} WHERE user_id = {member.id}')
    except sqlite3.OperationalError:
        error("in add_voice_time():    sqlite3.OperationalError: database is locked")
    connection.commit()
    connection.close()

async def get_rank(member: discord.Member):
    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()

    cursor.execute(f'SELECT RANK () OVER (ORDER BY xp DESC) rank FROM levelling WHERE user_id = {member.id}')
    rank = cursor.fetchone()[0]

    connection.close()
    return rank

async def dataframe_to_leaderboard(dataframe: list, lb_type: str, page: int):
    embed = discord.Embed(title=f'Топ пользователей по  {lb_type.name} \nСтраница {page}/{ceil(len(dataframe)/10)}', color=config.info)
    for datatile in dataframe[page*10-10:page*10]:
        rank = dataframe.index(datatile)+1
        rank_emoji = config.rank_emojis[str(rank)] if rank <= 5 else ""
        embed.add_field(name=f'#{rank} {datatile[5]} {rank_emoji}', 
                        value=f'**{datatile[1]}** уровень | **{round(datatile[2], 2)}** опыта | **{round(datatile[3], 2)}** часов в войсе | **{datatile[4]}** 🍕', 
                        inline=False)
    return embed
#Функции для bot.py ------------

async def xp_on_message(message: discord.Message):
    member = message.author
    if member.bot == False and message.channel.id not in [1123192369630695475, 1122481071330689045] and message.channel.category_id not in [1132586162356244480, 1133666070390132776, 1195776029973819533]:
        delta = ceil(len(message.content) * config.xp_per_char)
        new_lvl = await add_xp(member = member, delta = delta if delta < config.max_xp_per_msg else config.max_xp_per_msg)
        #Эмбед при новом уровне
        if new_lvl != None:
            xp = await get_xp(member = member)
            xp_used = 0
            old_lvl = 1
            while old_lvl < new_lvl:
                xp_used += old_lvl * config.xp_per_lvl
                old_lvl += 1

            file = discord.File("data/images/cyclesite.png")
            embed = discord.Embed(title=f'**{member.display_name}** достиг уровня **{new_lvl}**!', color=config.info)
            embed.set_author(name=member.name, icon_url=member.display_avatar)
            embed.set_thumbnail(url='attachment://cyclesite.png')
            embed.add_field(name='Всего опыта:', value = await get_xp(member=member))
            embed.add_field(name='Прогресс до следующего уровня:', value = f'{xp - xp_used}/{new_lvl * config.xp_per_lvl}', inline = False)
            try:
                await message.channel.send(file=file, embed=embed, reference=message)
            except discord.errors.HTTPException as ex:
                if ex.status == 400:
                    pass
                else:
                    raise
            
            return await update_role(lvl = new_lvl)

async def xp_on_voice(member: discord.Member, timedelta: int):
    new_lvl = await add_xp(member = member, delta = int(timedelta/config.seconds_per_xp))
    await add_voice_time(member = member, delta = timedelta)
    if new_lvl:
        await update_role(lvl = new_lvl)

async def leaderboard(intrct, lb_type: str):
    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM levelling ORDER BY {lb_type.value} DESC")
    dataframe = cursor.fetchall()
    connection.close()
    await intrct.response.send_message(embed=await dataframe_to_leaderboard(dataframe=dataframe, lb_type=lb_type, page=1),
                              view=leaderboard_view(original_intrct=intrct, dataframe=dataframe, lb_type=lb_type, page=1))

async def user_profile(intrct, member: discord.Member):
    await check_member(member = member)

    connection = sqlite3.connect("data/databases/levelling.db")
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM (SELECT *, RANK () OVER (ORDER BY xp DESC) rank FROM levelling) WHERE user_id = {member.id}")
    data = cursor.fetchall()[0]
    connection.close()

    lvl, xp, voice_time, pizza = data[1], data[2], data[3], data[4]
    rank = data[-1]
    rank_emoji = config.rank_emojis[str(rank)] if rank <= 5 else ""

    xp_used = 0
    calc_lvl = 1
    while calc_lvl < lvl:
        xp_used += calc_lvl * config.xp_per_lvl
        calc_lvl += 1

    embed = discord.Embed(title=f'Статистика пользователя {member.display_name} \n———————————————————————————', color=config.info)
    embed.set_author(name=intrct.user.display_name, icon_url=intrct.user.display_avatar)
    embed.set_thumbnail(url=member.display_avatar)
    embed.add_field(name='Место в топе:', value = str(rank) + f' {rank_emoji}', inline=False)
    embed.add_field(name='Уровень:', value = lvl)
    embed.add_field(name='Всего опыта:', value = str(xp) + ' ✨')
    embed.add_field(name='Прогресс до уровня:', value = f'{xp - xp_used}/{lvl * config.xp_per_lvl} 📈')
    embed.add_field(name='Пиццы:', value = f'{pizza} 🍕')
    embed.add_field(name='Время в войсе:', value = str(round(voice_time, 2)) + ' часов')
    embed.add_field(name='', value = f'')
    await intrct.response.send_message(embed=embed)