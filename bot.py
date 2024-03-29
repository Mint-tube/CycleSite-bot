import os, discord, asyncio, sqlite3, sys, time, socket, requests, asyncio, warnings
from discord import app_commands, Color, ui, utils
from discord.ext import tasks, commands
from icecream import ic
from random import randint, choice
from humanfriendly import parse_timespan, InvalidTimespan
from datetime import datetime, timedelta
from openai import OpenAI
from discord_webhook import DiscordWebhook, DiscordEmbed

#Сегодня без монолита(
import data.config as config
from data.emojis import emojis
from data.ai_utils import api_status, fetch_models, generate_response
from data.tickets_utils import ticket_launcher, ticket_operator
from data.logging import *
from colorama import Fore, Back, Style, init
import data.levelling as levelling
import data.scp_sync as scp_sync

#Инициализация бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

active_model = 'gpt-3.5-turbo'
in_voice = {}


#Добавление автора к embed
def interaction_author(embed: discord.Embed, interaction: discord.Interaction):
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
    return embed

#Пересоздание таблицы
async def drop_table_confirmed(table, original_intrct, intrct):
    match table:
        case 'bans':
            connection = sqlite3.connect(f'data/databases/warns.db')
            cursor = connection.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS bans')
            cursor.execute(f'CREATE TABLE bans (id INTEGER PRIMARY KEY)')
            embed = discord.Embed(title=f'Баны успешно сброшены!', color=config.info)
            warning("Таблица банов была сброшена")
            interaction_author(embed, original_intrct)
            connection.commit()
            connection.close()

        case 'warns':
            connection = sqlite3.connect(f'data/databases/warns.db')
            cursor = connection.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS warns')
            cursor.execute(f'''CREATE TABLE warns (
                            warn_id INTEGER PRIMARY KEY, 
                            name TEXT NOT NULL, 
                            reason TEXT, 
                            message TEXT, 
                            lapse_time INTEGER
                            )''')
            embed = discord.Embed(title=f'Таблица варнов была успешно сброшена!', color=config.info)
            warning("Таблица варнов была сброшена")
            interaction_author(embed, original_intrct)
            connection.commit()
            connection.close()
            
        case 'levelling':
            connection = sqlite3.connect('data/databases/levelling.db')
            cursor = connection.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS levelling')
            cursor.execute(f'''CREATE TABLE levelling (
                            user_id INTEGER, 
                            evel INTEGER DEFAULT 1, 
                            xp INTEGER DEFAULT 0, 
                            voice_time REAL DEFAULT 0, 
                            pizza INTEGER DEFAULT 0, 
                            user_name TEXT
                            )''')
            embed = discord.Embed(title=f'Таблица опыта была успешно сброшена!', color=config.info)
            warning("Таблица опыта была сброшена")
            interaction_author(embed, original_intrct)
            connection.commit()
            connection.close()
    if not "embed" in locals():
        embed = discord.Embed(title=f'Таблицы не существует, и существовать не должно 😠', color=config.danger)
    await intrct.response.send_message(embed=embed)
    await original_intrct.delete_original_response()

#Перевод даты в unix (секунды)
def unix_datetime(source):
    return int(time.mktime(source.timetuple()))

#Мут. Жестоко и сердито.
async def mute(intrct, target, timespan):
    try:
        real_timespan = parse_timespan(timespan)
    except InvalidTimespan:
        print(f'Не удалось распарсить {timespan}')
        return
    
    #Корень зла
    try:
        await target.timeout(datetime.now().astimezone() + timedelta(seconds=real_timespan))
    except:
        embed = discord.Embed(title=f'Не удалось замутить пользователя😨', color=config.danger)
        await intrct.channel.send(embed = embed)
        return
    
    embed = discord.Embed(title=f'Пользователь был замьючен.', description=f'Он сможет снова говорить <t:{unix_datetime(datetime.now().astimezone() + timedelta(seconds=real_timespan))}:R>', color=config.warning)
    await intrct.channel.send(embed = embed)

async def check_ban(member: discord.Member):
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM bans WHERE id = ?', (member.id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return True
    else:
        return False

class drop_confirm(discord.ui.View):
    def __init__(self, table, intrct) -> None:
        self.table = table
        self.intrct = intrct
        super().__init__(timeout=None)

    @discord.ui.button(label="Жми! Жми! Жми!", style=discord.ButtonStyle.red, custom_id="drop_confirm")
    async def drop(self, interaction, button):
        await drop_table_confirmed(self.table, self.intrct, interaction)


#Изменение статуса
@tasks.loop(seconds = 60)
async def presence():
    emoji = choice(emojis)
    online_members = [member for member in client.get_guild(1122085072577757275).members if not member.bot and member.status == discord.Status.online]
    if online_members:
        activity_text = f'{choice(online_members).display_name} {emoji}'
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=activity_text))


#Удаление предупреждений
@tasks.loop(hours = 1)
async def lapse_of_warns():
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    cursor.execute('SELECT warn_id, lapse_time FROM warns')
    warns = cursor.fetchall()
    for warn in warns:
        if unix_datetime(datetime.now()) >= warn[1]:
            cursor.execute(f'DELETE FROM warns WHERE warn_id = {warn[0]}')
    connection.commit()
    connection.close()

@tasks.loop(hours = 24)
async def update_usernames():
    connection = sqlite3.connect('data/databases/levelling.db')
    cursor = connection.cursor()

    cursor.execute("SELECT user_id FROM levelling")
    ids = cursor.fetchall()

    for row in ids:
        member = await client.fetch_user(row[0])
        cursor.execute("UPDATE levelling SET user_name = ? WHERE user_id = ?", (member.display_name, member.id))

    connection.commit()
    connection.close()

    debug('Обновлены имёна в levelling.db')

#Подгрузка view с тикетами
@client.event
async def setup_hook():
    client.add_view(ticket_launcher.question())
    client.add_view(ticket_launcher.bug())
    client.add_view(ticket_launcher.report())
    client.add_view(ticket_launcher.application())
    client.add_view(ticket_operator())

#Запуск циклов и инфо о запуске
@client.event
async def on_ready():
    global guild
    guild = client.get_guild(config.guild)
    try:
        presence.start()
        lapse_of_warns.start()
        # update_usernames.start()
    except RuntimeError as exc:
        warning('Задача запущенна и не завершена! \n' + exc)
    await tree.sync(guild=discord.Object(id=config.guild))
    info(f'{Fore.CYAN}{client.user.name}{Style.RESET_ALL} подключён к серверу!')

#Пинг бота по slash-комманде
@tree.command(name="пинг", description="Пингани бота!", guild=discord.Object(id=config.guild))
async def on_ping(intrct):
    embed = discord.Embed(title="Понг!    ", description=f"{round(client.latency * 1000)}мс", color=config.info)
    await intrct.response.send_message(embed=embed)

@client.event 
async def on_message(message):
    #Проверка на адекватность
    if message.author == client.user or isinstance(message.channel, discord.DMChannel):
        return

    #Случайные реакции
    if randint(0, 20) == 1:
        if message.channel.category_id not in config.very_serious_categories:
            await message.add_reaction(choice(message.guild.emojis))

    #Чат гпт
    if message.mentions and int(client.user.mention.replace(f'<@{client.user.id}>', str(client.user.id))) == message.mentions[0].id and message.channel.id in config.ai_channels:
        if api_status.status_code != 200:
            await message.add_reaction("❎")
            embed = discord.Embed(title='Невозможно подключится к API', description=f'**{api_status.status_code}: {api_status.reason}**', color=config.warning)
            await message.channel.send(embed = embed, delete_after = 15)
        else:
            await message.add_reaction("☑")
            for mention in message.mentions:
                    message.content = message.content.replace(f'<@{mention.id}>', f'{mention.display_name}')
            async with message.channel.typing():
                response = generate_response(message.content, model=active_model)
                if type(response) == int:
                    await message.clear_reactions()
                    await message.add_reaction("⛔")
                    embed = discord.Embed(description=f'**Ошибка {response}**', color=config.danger)
                    await message.channel.send(embed = embed, delete_after = 60)
                else:
                    await message.channel.send(response)

    new_role = await levelling.xp_on_message(message)
    if new_role:
        roles_to_remove = [role for role in message.author.roles if role.id in config.levelling_roles]
        await message.author.remove_roles(*roles_to_remove)
        await message.author.add_roles(guild.get_role(int(new_role)))

#Выдача и удаление роли Меценат за буст
@client.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next(role for role in after.roles if role not in before.roles)
        if new_role.id == config.nitro_booster_id:
            await after.add_roles(client.get_guild(int(config.guild)).get_role(1138436827909455925))
    elif len(before.roles) > len(after.roles):
        old_role = next(role for role in before.roles if role not in after.roles)
        if old_role.id == config.nitro_booster_id:
            await after.remove_roles(client.get_guild(int(config.guild)).get_role(1138436827909455925))

@tree.command(name="тикет", description="Запускает систему тикетов в текущей категории!", guild=discord.Object(id=config.guild))
@app_commands.rename(type='тип')
@app_commands.describe(type='вопросы/баги/жалобы/заявки')
async def ticketing(intrct, type: str):
    match type.lower():
        case 'вопросы':
            embed = discord.Embed(title="Задайте свой вопрос!", description="Здесь вы можете создать тикет с вашим вопросом, на который ответит администрация сервера!", color=config.info)
            await intrct.channel.send(embed=embed, view=ticket_launcher.question())
            client.add_view(ticket_launcher.question())
        case 'баги':
            embed = discord.Embed(title="Пожаловаться на баг.", description="Здесь можно сообщить о баге.", color=config.danger)
            await intrct.channel.send(embed=embed, view=ticket_launcher.bug())
            client.add_view(ticket_launcher.bug())
        case 'жалобы':
            embed = discord.Embed(title="Подать жалобу/апелляцию.", description="Здесь можно написать жалобу на игрока/админа или написать апелляцию!", color=config.warning)
            await intrct.channel.send(embed=embed, view=ticket_launcher.report())
            client.add_view(ticket_launcher.report())
        case 'заявки':
            #пиздец олежа что ты сделал
            embed = discord.Embed(title="👥 Роли", description='''**Список ролей Discord сервера!** 
                            **Администрация:** 

                            > <@&1122089304290762773> - роль владельца сервера 
                            > <@&1134198325189562468> - роль большой шишки 
                            > <@&1210729205340311622> - роль высшего администратора 
                            > <@&1134810427889549383> - роль технического администратора 
                            > <@&1134183737400250468> - роль администратора FullRP 
                            > <@&1134177570770911373> - роль администратора классических серверов 
                            > <@&1177911300941164674> - роль модератора Discord 
                            > <@&1123307213000298627> - роль стажёра администрации 

                            **Люди заслужившие особое внимание:** 

                            > <@&1177515135280103504> - роль проводящего ивенты 
                            > <@&1174776209477996574> - роль доверенного администрации 
                            > <@&1122546899665293382> - роль начального игрока 
                            > <@&1179756967397425273> - роль среднего игрока 
                            > <@&1179757460492386355> - роль профессионального игрока 

                            **Донатеры:** 

                            > <@&1138445633519357954> - роль ультра щедрого человека 
                            > <@&1138443741699522571> - роль очень щедрого человека 
                            > <@&1138436827909455925> - роль щедрого человека 

                            **Роли за уровень:** 

                            > <@&1138456995498823781> - роль за 40 уровень Discord 
                            > <@&1138456798005842041> - роль за 30 уровень Discord 
                            > <@&1138456361202614302> - роль за 20 уровень discord 
                            > <@&1138455999993360444> - роль за 15 уровень Discord 
                            > <@&1138455214706393088> - роль за 10 уровень Discord 
                            > <@&1138454303409963088> - роль за 3 уровень Discord 



                            > **Есть роли, которые тут не написаны. Эти роли либо очень очевидные, по типу <@&1122932414923161660> или же объяснены в другом месте либо же секретные, о предназначении которых вам стоит догадаться самостоятельно!** 


                            > **Так же вы можете выбрать ниже интересующую вас заявку.**''', color=config.info)
            await intrct.channel.send(embed=embed, view=ticket_launcher.application())
            client.add_view(ticket_launcher.application())
    await intrct.response.defer()
    await intrct.delete_original_response()

@tree.command(name='сказать', description='Эмбед от имени бота', guild=discord.Object(id=config.guild))
@app_commands.rename(title='заголовок', description='описание', color='цвет')
@app_commands.describe(title='Заголовок', description='Описание', color='HEX цвет в формате 0x5c5eff')
async def say(intrct, title: str = None, description: str = None, color: str = '0x5c5eff'):
    if intrct.user.id in config.bot_engineers:
        if description != None or title != None:
            await intrct.response.defer()
            embed = discord.Embed(title=title, description=description, color=int(color, 16))
            await intrct.channel.send(embed=embed)
            await intrct.delete_original_response()
        else:
            await intrct.response.send_message('Необходимо указать заголовок или описание.', ephemeral=True)
    else:
        await intrct.response.send_message('У тебя нет прав.', ephemeral=True)

@tree.command(name='правила', guild=discord.Object(id=config.guild))
async def rules(intrct):
    embed = discord.Embed(title='📑 Правила сервера Discord', description=str(
        '1. Запрещено оскорбительное поведение, задевание за живое участников, а также унижение их чести и достоинства, проявление нетерпимости по отношению к тем или иным группам лиц и подогрев конфликтов или участие в них. Это правило не работает в <#1122481071330689045>. При нарушении выдаётся варн.\n\n'+
        '2. Запрещено размещать сообщения, которые не соответствуют тематике канала, нарушают его локальные правила или неоднократно повторяющиеся или бессмысленные. Это правило не работает в <#1122481071330689045> при условии, что флуд не массовый. При нарушении выдаётся варн.\n\n'+
        '3. Запрещено пингование других пользователей с целью раздражения. При нарушении выдаётся варн.\n\n'+
        '4. Запрещено мешать общению в голосовых каналах. К такому относится:\n\n'+
        '> 4.1 Некачественный звук микрофона, посторонние звуки в фоне, громкая музыка или звуки из других программ мешающие общению. При нарушении сначала будет выдано устное предупреждение, а если человек не слушается, то будет выдан варн.\n'+
        '> \n'+
        '> 4.2 Постоянный вход и выход из голосового канала, создающий помехи для других участников. При нарушении сначала будет выдано устное предупреждение, а если человек не слушается, то будет выдан варн.\n\n'+
        '5. Запрещено размещать контент, который может быть шокирующим, отвратительным, непристойным или опасным для других людей. К такому контенту относятся:\n\n'+
        '> 5.1 Изображения или видео сексуального характера, а также ролевые игры с сексуальными элементами. Это правило не касается шуток, цитат и выражений, которые имеют другой смысл. При нарушении выдаётся варн.\n'+ 
        '> \n'+
        '> 5.2 Политические обсуждения и высказывания ведущие к конфликту и обсуждение современных конфликтов и политик государств или личностей. Так же это касается шовинизма, фашизма и нацизма. При нарушении выдаётся варн.\n'+
        '> \n'+
        '> 5.3 Изображения или видео с кровью, мясом, жестокостью или другими отталкивающими сценами. При нарушении выдаётся варн.\n'+
        '> \n'+
        '> 5.4 Видео с яркими вспышками, громкими звуками или другими эффектами, которые могут вызвать негативную реакцию у чувствительных людей. При нарушении выдаётся варн.\n'+
        '> \n'+
        '> 5.5 Любые материалы, которые подстрекают к незаконным действиям, экстремизму или нанесению вреда себе или другим. При нарушении выдаётся варн.\n\n'+
        '6. Запрещено размещать сообщения или статус профиля или блоки "Обо мне", которые в каком-либо виде и форме имеют в себе рекламный или агитационный характер с целью привлечь пользователей на посторонние проекты и услуги, а так же товары. При нарушении сначала будет выдано устное предупреждение, если человек не убрал, то будет выдан кик, а если повторится, то бан.\n\n'+
        '7. Запрещено использование уязвимостей Discord’a и ботов нашего сервера. При нарушении выдаётся варн.\n\n'+
        '8. Запрещено распространять ложную или ошибочную информацию о проекте с целью оскорбления, провокации или введения в заблуждение других пользователей. При нарушении выдаётся варн.\n\n'+
        '9. Запрещено выкладывать личную информацию участников сервера без их согласия. При нарушении выдаётся варн.\n\n'+
        '10. Запрещено вынуждать людей нарушить правила или сливать любую информацию. Правило так же работает в ЛС. При нарушении выдаётся варн.\n\n'+
        '11. Запрещено участие в нанесении различного рода вреда или ущерба серверу или участникам сервера, а также его организация. При нарушении будет выдан бан навсегда.\n\n'+
        '12. Запрещено обходить наказание. Это означает, что нельзя создавать новые аккаунты для этой цели или использовать другие способы, чтобы избежать варна, мута, бана или кика. За избегание бана будет выдан бан навсегда, а за избегание варна будет выдан ещё один варн.\n\n'+
        '**Дополнение: Правила 1, 3, 4, 5 не работают если никто не против их нарушения.** \n\n'+
        'Наказания за определённое количество варнов:\n'+
        '> 2 Предупреждение - мут на 1 день\n'+ 
        '> 3 Предупреждение - мут на 2 дня\n'+ 
        '> 4 Предупреждение - мут на 7 дней\n'+ 
        '> 5 и последующее предупреждение - мут на 14 дней\n\n'+
        'Варны имеют срок в один месяц'), color=config.info)
    links = discord.Embed(title = '🔬 Правила на GitBook', description = str(
        '[Правила Classic & Events](https://cyclesite.gitbook.io/wiki/pravila/pravila-classic-and-events)\n'+
        '[Правила Администрации](https://cyclesite.gitbook.io/wiki/pravila/pravila-administracii)'), color = config.info)
    await intrct.response.defer()
    await intrct.channel.send(embeds = [embed, links])
    await intrct.delete_original_response()
    
@tree.command(name='кпп', guild=discord.Object(id=config.guild))
async def rules(intrct):
    embed = discord.Embed(title=':wave: Добро пожаловать', description=str(
        'Привет, новый участник, добро пожаловать на наш проект! Я тебе посоветую сперва ознакомиться с <#1180963320820412476> и ознакомиться с <#1136346930285400154> , а так же пообщаться с другими участниками в <#1122085072577757278>.\n'+
        '\n'+
        'Вот объяснение что можно делать в некоторых местах:\n'+
        '<#1122085072577757278> - здесь можно общаться\n'+
        '<#1132404679880478751> - здесь можно общаться об играх\n'+
        '<#1172156034660446248> - здесь можно отсылать сообщения только раз в 6 часов\n'+
        '<#1122481071330689045> - здесь можно дурачиться и сраться\n'+
        '<#1130041299693748224> - здесь можно скидывать и смеяться над мемами\n'+
        '<#1172161486630686751> - здесь можно общаться с ИИ\n'+
        '<#1123192369630695475> - здесь можно отсылать команды ботам\n'+
        '<#1172159065040887888> - здесь можно отсылать свои шикарные цитаты\n'+
        '\n'+
        'Приятного тебе прибывания на нашем проекте!'), color=config.info)
    links = discord.Embed(title = '💵 Поддержка проекта', description = str(
        'При поддержке проекта от:\n'+
        '> 200 руб. даётся роль <@&1138436827909455925>\n'+
        '> 500 руб. даётся роль <@&1138443741699522571>\n'+
        '> 1000 руб. даётся роль <@&1138445633519357954>\n'+
        '\n'+
        'Роль даётся на срок выдачи привилегий. Подробно о донате вы можете узнать на самой странице в Boosty. Так же не забывайте указывать ваш Discord в сообщение к пожертвованию.\n'+
        '\n'+
        'За любое количество бустов Discord сервера даётся роль <@&1122867829662814279> и одна привилегия на SCP:SL сервере на выбор. Она даётся на срок буста.(По этому поводу обращайтесь в <#1132616103877673050>)'), color = config.info)
    await intrct.response.defer()
    await intrct.channel.send(embeds = [embed, links])
    await intrct.delete_original_response()
    
@tree.command(name='дроп', description='Сбросить таблицу', guild=discord.Object(id=config.guild))
@app_commands.rename(table='таблица')
async def drop(intrct, table: str):
    if intrct.user.id not in config.bot_engineers:
        await intrct.response.send_message('У тебя нет прав.', ephemeral=True)
        return
    embed = discord.Embed(title="Ты точно хочешь сбросить таблицу?", description=f"Будет сброшена таблица {table} у {socket.gethostname()}", color=config.danger)
    await intrct.response.send_message(embed = embed, view = drop_confirm(table, intrct), ephemeral = True, delete_after = 15)
    
@tree.command(name="варн", description="Выдача предупреждения", guild=discord.Object(id=config.guild))
@app_commands.rename(user='пользователь', reason='причина')
async def warn(intrct, user: discord.Member, reason: str):
    #Проверка на адекватность
    if user.id == client.user.id:
        await intrct.response.send_message("Нет.", ephemeral=True)
        return
    if user.bot:
        await intrct.response.send_message("Ты не можешь выдать предупреждение боту.", ephemeral=True)
        return
    if user == intrct.user:
        await intrct.response.send_message("Попроси кого-нибудь другого.", ephemeral=True)
        return

    await levelling.add_xp(member = user, delta = -1500)
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cursor.execute('SELECT max(warn_id) FROM warns')
    case_id = cursor.fetchone()[0]
    case_id = 1 if case_id == None else case_id + 1
    embed = discord.Embed(
            title=f"Выдано предупреждение!",
            description=f'Пользователь {user.mention} получил предупреждение \nШтраф опыта: **-1500xp** \nID: **{case_id}**',
            color=config.info
        )
    interaction_author(embed, intrct)
    embed.add_field(
            name="Причина:",
            value=reason,
            inline=False
        )
    embed.add_field(
            name="Истекает:",
            value=f"<t:{unix_datetime(datetime.now() + timedelta(days=30))}:f>",
        )
    await intrct.response.send_message(embed=embed)
    await intrct.guild.get_channel(config.warns_log_channel).send(embed = embed)
    response = await intrct.original_response()
    cursor.execute('INSERT INTO warns (name, reason, message, lapse_time) VALUES (?, ?, ?, ?)', (user.mention, reason, response.jump_url, unix_datetime(datetime.now() + timedelta(days=30))))
    cursor.execute('SELECT * FROM warns WHERE name = ?', (user.mention,))
    players_warns = len(cursor.fetchall())
    match players_warns:
        case 2:
            await mute(intrct, user, '1d')
        case 3:
            await mute(intrct, user, '2d')
        case 4:
            await mute(intrct, user, '7d')
    if players_warns >= 5:
        await mute(intrct, user, '14d')
    await intrct.channel.send(user.mention)

    connection.commit()
    connection.close()

@tree.command(name="список_варнов", description="Помощь", guild=discord.Object(id=config.guild))
@app_commands.rename(user='пользователь')
async def warns_list(intrct, user: discord.Member = None):
    if not user:
        user = intrct.user
    if user == client.user:
        await intrct.response.send_message("Ты не поверишь!", ephemeral=True)
        return
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    cursor.execute('SELECT warn_id, reason, message, lapse_time FROM warns WHERE name = ?', (user.mention,))
    warns = cursor.fetchall()
    if warns:
        embed = discord.Embed(title=f'Предупреждения пользователя {user.display_name}:', color=config.warning)
        interaction_author(embed, intrct)
        for warn in warns:
            embed.add_field(
                name=f'Предупреждение {warn[0]}',
                value=f'Причина: {warn[1]}  \nСсылка: {warn[2]}   \nИстекает: <t:{warn[3]}:R>',
                inline=False
            )
        await intrct.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f'Предупреждения пользователя {user.display_name}:', description='Предупреждений нет, но это всегда можно исправить!', color=config.info)
        interaction_author(embed, intrct)
        await intrct.response.send_message(embed=embed)
    connection.commit()
    connection.close()

@tree.command(name='снять_варн', description='Досрочно снять варн', guild=discord.Object(id=config.guild))
@app_commands.rename(warn_id='id')
async def warn_del(intrct, warn_id: int):
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM warns WHERE warn_id = ?', (warn_id,))
    connection.commit()
    connection.close()

    embed = discord.Embed(title=f'Варн {warn_id} был успешно снят.', color=config.info)
    interaction_author(embed, intrct)
    await intrct.response.send_message(embed=embed)
    
@tree.command(name='аватар', description='Аватар пользователя', guild=discord.Object(id=config.guild))
@app_commands.rename(user='пользователь')
async def avatar(intrct, user: discord.Member = None):
    if user:
        embed = discord.Embed(title=f'Аватар пользователя {user.display_name}:', color=config.info)
        embed.set_image(url=user.display_avatar.url)
        await intrct.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f'Аватар пользователя {intrct.user.display_name}:', color=config.info)
        embed.set_image(url=intrct.user.display_avatar.url)
        await intrct.response.send_message(embed=embed)

@tree.command(name='сменить_ии', description='Сменить модель ИИ', guild=discord.Object(id=config.guild))
@app_commands.rename(model='модель')
async def change_gpt_model(intrct, model: str):
    if model in fetch_models():
        global active_model
        active_model = model
        embed = discord.Embed(description=f'**ИИ был успешно изменен на {model}.**', color=config.info)
        await intrct.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title='Список доступных моделей:', description='\n'.join(fetch_models()), color=config.info)
        await intrct.response.send_message(embed=embed, ephemeral=True)

@tree.command(name='бан', description='Унижение человека', guild=discord.Object(id=config.guild))
@app_commands.rename(user='пользователь')
async def ban(intrct, user: discord.User):
    if guild.get_member(user.id):
        try:
            await user.remove_roles(*user.roles, atomic=False)
            await user.add_roles(intrct.guild.get_role(config.banned_role))
        except discord.app_commands.errors.CommandInvokeError as ex:
            await intrct.response.send_message(f'**Почему?**', ephemeral=True)

    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()
    cursor.execute(f'DELETE FROM bans WHERE id = {user.id}')
    cursor.execute(f'INSERT INTO bans (id) VALUES ({user.id})')
    connection.commit()
    connection.close()

    await intrct.response.send_message(f'**Пользователь был добавлен в чёрный список ✅**', ephemeral=True)

    embed = discord.Embed(description=f'**📕 {user.mention} забанен XD**', color=config.danger)
    await intrct.guild.get_channel(config.logs_channels.main).send(embed = embed)

@tree.command(name='пардон', description='Унижение человека, но обратно', guild=discord.Object(id=config.guild))
@app_commands.rename(user='пользователь')
async def pardon(intrct, user: discord.Member):
    connection = sqlite3.connect('data/databases/warns.db')
    cursor = connection.cursor()

    cursor.execute(f'SELECT * FROM bans WHERE id = {user.id}')

    if cursor.fetchone():
        if guild.get_member(user.id): 
            await user.remove_roles(intrct.guild.get_role(config.banned_role))
        cursor.execute(f'DELETE FROM bans WHERE id = {user.id}')
        embed = discord.Embed(description=f'**📗 {user.mention} разбанен <3**', color=config.success)
        await intrct.guild.get_channel(config.logs_channels.main).send(embed = embed)
        await intrct.response.send_message(f'{user.mention} был разбанен.', ephemeral=True)
    else:
        await intrct.response.send_message('Этот пользователь не забанен.', ephemeral=True)

    connection.commit()
    connection.close()

@tree.command(name='профиль', description='Профиль', guild=discord.Object(id=config.guild))
@app_commands.rename(member='пользователь')
async def user_profile(intrct, member: discord.Member = None):
    await levelling.user_profile(intrct, member = member if not member == None else intrct.user)

@tree.command(name='лидерборд', description='Топ по активности', guild=discord.Object(id=config.guild))
@app_commands.rename(lb_type='сортировать_по')
@app_commands.choices(lb_type=[
        app_commands.Choice(name="✨ Опыту дискорда", value="xp"),
        app_commands.Choice(name="🎤 Времени в войсе", value="voice_time"),
        app_commands.Choice(name="🍕 Пицца", value="pizza"),
        # app_commands.Choice(name="🎮 Опыту SCP", value="scp"),
        ])
async def leaderboard(intrct, lb_type: app_commands.Choice[str]):
    await levelling.leaderboard(intrct, lb_type = lb_type)

@tree.command(name='опыт', description='Снять/начислить опыт', guild=discord.Object(id=config.guild))
@app_commands.rename(member='пользователь', delta='дельта')
async def change_xp(intrct, member: discord.Member, delta: int):
    new_lvl = await levelling.add_xp(member = member, delta = delta)
    if new_lvl:
        new_role = await levelling.update_role(lvl = new_lvl)
        roles_to_remove = [role for role in member.roles if role.id in config.levelling_roles]
        await member.remove_roles(*roles_to_remove)
        await member.add_roles(guild.get_role(new_role)) if new_role else None
    
    embed = interaction_author(discord.Embed(description=f'Опыт {member.mention} был изменён на {str(delta)}', color=config.info), intrct)
    await intrct.response.send_message(embed = embed)

@tree.command(name='steam', description='Синхронизация Steam с Discord (0 для десинхронизации)', guild=discord.Object(id=config.guild))
async def steam_sync(intrct, steam_id: str):
    response = await scp_sync.steam_sync(discord_id=intrct.user.id, steam_id=int(steam_id))
    match response[0]:
        case 200:
            embed = discord.Embed(title="Привязанный Steam был изменён ✅", color=config.success)
            embed.add_field(name="Discord", value=str(intrct.user.mention), inline=True)
            embed.add_field(name="Steam", value=steam_id, inline=True)
        case 201:
            embed = discord.Embed(title="Steam привязан к Discord ✅", color=config.success)
            embed.add_field(name="Discord", value=str(intrct.user.mention), inline=True)
            embed.add_field(name="Steam", value=steam_id, inline=True)
        case 204:
            embed = discord.Embed(title="Соединение разорвано ⚠", color=config.warning)
            embed.add_field(name="Discord", value=str(intrct.user.mention), inline=True)
            embed.add_field(name="Steam", value="Не привязан", inline=True)
        case 304:
            embed = discord.Embed(title="Steam уже привязан к этому Discord 🆗", color=config.info)
            embed.add_field(name="Discord", value=str(intrct.user.mention), inline=True)
            embed.add_field(name="Steam", value=steam_id, inline=True)
        case 409:
            embed = discord.Embed(title="Steam уже привязан к чужому Discord ❌", description=f"Вы можете обратиться к пользователю или администрации,\nесли это ваш аккаунт", color=config.danger)
            embed.add_field(name="Discord", value=f'<@{response[1]}>', inline=True)
            embed.add_field(name="Steam", value=steam_id, inline=True)
        case 500:
            embed = discord.Embed(title="⚠ Произошла ошибка", color=config.warning)
    await intrct.response.send_message(embed = embed)

@tree.command(name='steam_forced', description='Насильно привязать Steam к аккаунту Discord', guild=discord.Object(id=config.guild))
async def steam_sync_forced(intrct, discord_id: str, steam_id: str):
    await scp_sync.steam_sync_forced(discord_id=int(discord_id), steam_id=int(steam_id))
    await intrct.response.send_message(embed = discord.Embed(title="Аккаунты синхронизированы успешно 🌐", color=config.info))


#События

@client.event
async def on_message_delete(message):

    if message.author.bot:
        return

    attachments = ''

    if message.attachments:
        attachments_temp = []
        for attachment in message.attachments:
            attachments_temp.append(attachment.url)
        attachments = '\n'.join(attachments_temp)

    embed = discord.Embed(title="🗑️ Сообщение Удалено", color=config.info)
    embed.set_author(name=str(message.author), icon_url=str(message.author.display_avatar))
    embed.add_field(name="Отправитель", value=str(message.author.mention), inline=False)
    if message.content != '':
        if len(message.content) > 1024:
            embed.add_field(name="Сообщение", value=str(f"```{message.content[:1010]}...```" + attachments), inline=False)
        else:
            embed.add_field(name="Сообщение", value=str(f"```{message.content}```" + attachments), inline=False)
    elif attachments != '':
        embed.add_field(name="Вложения", value=str(attachments), inline=False)
    embed.add_field(name="Канал", value=str(message.channel.mention), inline=False)

    if message.channel.category_id in config.very_secret_categories:
        await guild.get_channel(config.logs_channels.private).send(embed = embed)
    else:
        await guild.get_channel(config.logs_channels.main).send(embed = embed)

@client.event
async def on_message_edit(message_before, message_after):

    if str(message_before.content) != str(message_after.content) and str(message_after.content) != '':      
        embed = discord.Embed(title='✏️ Сообщение Отредактировано', color=config.info)
        embed.set_author(name=str(message_before.author), icon_url=str(message_before.author.display_avatar))
        embed.add_field(name="Отправитель", value=str(message_before.author.mention), inline=False)
        if len(message_before.content) > 1024:
            embed.add_field(name="До", value=str(f"```{message_after.content[:1010]}...```"), inline=False)
        else:
            embed.add_field(name="До", value=str(f"```{message_before.content}```"), inline=False)
        if len(message_after.content) > 1024:
            embed.add_field(name="После", value=str(f"```{message_after.content[:1010]}...```"), inline=False)
        else:
            embed.add_field(name="После", value=str(f"```{message_after.content}```"), inline=False)
        embed.add_field(name="Канал", value=str(message_after.channel.mention), inline=False)

        if message_after.channel.category_id in config.very_secret_categories:
            await guild.get_channel(config.logs_channels.private).send(embed = embed)
        else:
            await guild.get_channel(config.logs_channels.main).send(embed = embed)

@client.event
async def on_voice_state_update(member, state_before, state_after):
    #Логи
    voice_channel_before = state_before.channel
    voice_channel_after = state_after.channel
    
    if voice_channel_before == None:
        embed = discord.Embed(description=f'{member.mention} **присоединился к {voice_channel_after.mention}**', color=config.info)
        embed.set_author(name=member.display_name, icon_url=str(member.display_avatar))
        await guild.get_channel(config.logs_channels.voice).send(embed = embed)

        if not state_after.self_mute: 
            in_voice.update({member: datetime.now()})

    elif voice_channel_after == None:
        embed = discord.Embed(description=f'{member.mention} **вышел из {voice_channel_before.mention}**', color=config.info)
        embed.set_author(name=member.display_name, icon_url=str(member.display_avatar))
        await guild.get_channel(config.logs_channels.voice).send(embed = embed)

        if in_voice.get(member) != None and not state_before.self_mute and voice_channel_before.id != 1132601091238924349:
            timedelta = (datetime.now() - in_voice.get(member)).total_seconds()
            new_role = await levelling.xp_on_voice(member, timedelta)
            if new_role:
                    roles_to_remove = [role for role in member.roles if role.id in config.levelling_roles]
                    await member.remove_roles(*roles_to_remove)
                    await member.add_roles(guild.get_role(int(new_role)))
    
    elif voice_channel_after != voice_channel_before:
        embed = discord.Embed(description=f'{member.mention} **перешел из {voice_channel_before.mention} в {voice_channel_after.mention}**', color=config.info)
        embed.set_author(name=member.display_name, icon_url=str(member.display_avatar))
        await guild.get_channel(config.logs_channels.voice).send(embed = embed)
        
    elif state_after.self_mute and not state_before.self_mute and in_voice.get(member) != None:
        timedelta = (datetime.now() - in_voice.get(member)).total_seconds()
        new_role = await levelling.xp_on_voice(member, timedelta)
        if new_role:
                roles_to_remove = [role for role in member.roles if role.id in config.levelling_roles]
                await member.remove_roles(*roles_to_remove)
                await member.add_roles(guild.get_role(int(new_role)))
    
    elif state_before.self_mute and not state_after.self_mute:
        in_voice.update({member: datetime.now()})

@client.event
async def on_member_join(member):
        embed = discord.Embed(description=f'**✔ {member.mention} присоединился к серверу**', color=config.success)
        embed.add_field(name="Дата регистрации", value=f'<t:{unix_datetime(member.created_at)}:f>', inline=False)
        embed.set_thumbnail(url = str(member.display_avatar))
        
        await guild.get_channel(config.logs_channels.main).send(embed = embed)

        if await check_ban(member):
            await member.add_roles(member.guild.get_role(config.banned_role))
            embed = discord.Embed(title=f'**📕 {member.mention} забанен нахуй**', color=config.danger)
            await guild.get_channel(config.logs_channels.main).send(embed = embed)

@client.event
async def on_member_remove(member):
        embed = discord.Embed(description=f'**🔻 {member.mention} покинул сервер**', color=config.danger)
        embed.add_field(name="Дата присоединения", value=f'<t:{unix_datetime(member.joined_at)}:f>', inline=False)
        embed.set_thumbnail(url = str(member.display_avatar))

        await guild.get_channel(config.logs_channels.main).send(embed = embed)

client.run(config.token)
