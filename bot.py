import os, discord, config, asyncio, sqlite3, sys
from discord import app_commands, Color
from discord.ext import commands
from dotenv import load_dotenv, dotenv_values
from icecream import ic
from config import colors
from random import randint, choice

#Загрузка переменных окружения из файла .env
load_dotenv()
token = os.getenv('TOKEN')
guild = os.getenv('GUILD')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#Подключение к базе данных
conn = sqlite3.connect("CycleSite.db")
cursor = conn.cursor()
cursor.close()
conn.commit()
conn.close()

@client.event
async def on_ready():
    print(f'{client.user.name} подключён к серверу!    \n{round(client.latency * 1000)}ms')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='на тебя <3'))

#Синхронизация дерева комманд. Можно сделать тоже самое в on_ready ----------------
@tree.command(name="синхронизация", description="Только для инженеров", guild=discord.Object(id=guild))
async def sync(intrct):
    if intrct.user.id in config.bot_engineers:
        await tree.sync(guild=discord.Object(id=guild))
        embed = discord.Embed(title="Комманды синхронизированы!", color=config.colors.success)
        embed.set_author(name=intrct.user.display_name, icon_url=intrct.user.display_avatar)
        await intrct.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Эта комманда не для тебя", color=config.colors.danger)
        await intrct.response.send_message(embed=embed)

#Пинг бота по slash-комманде ----------------
@tree.command(name="пинг", description="Пингани бота!", guild=discord.Object(id=guild))
async def on_ping(intrct):
    embed = discord.Embed(title="Понг!    ", description=f"{round(client.latency * 1000)}мс", color=config.colors.info)
    await intrct.response.send_message(embed=embed)

#Cлучайные реакции на сообщения ----------------
@client.event 
async def on_message(message):
    if message.author == client.user:
        return
    if randint(0, 5) == 1:
        await message.add_reaction(choice(message.guild.emojis))

#Безопасное выключение бота ----------------
@tree.command(name="выключение", description="Только для инженеров", guild=discord.Object(id=guild))
async def shutdown(intrct):
    if intrct.user.id in config.bot_engineers:
        embed = discord.Embed(title="Бот выключается...", color=config.colors.warning)
        embed.set_author(name=intrct.user.display_name, icon_url=intrct.user.display_avatar)
        await intrct.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Эта комманда не для тебя", color=config.colors.danger)
        await intrct.response.send_message(embed=embed)



client.run(token)
