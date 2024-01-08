import os, discord, config, asyncio, sqlite3, sys
from discord import app_commands, Color
from discord.ext import commands
from dotenv import load_dotenv, dotenv_values
from icecream import ic
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
# conn = sqlite3.connect("CycleSite.db")
# cursor = conn.cursor()
# cursor.close()
# conn.commit()
# conn.close()

#Добавление автора к embed
def interaction_author(embed: discord.Embed, interaction: discord.Interaction):
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
    return embed

class ticket_launcher(discord.ui.View):

    def __init__(self) -> None:
        super().__init__(timeout=None) 
    
    @discord.ui.button(label="Открыть тикет", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.get_role(config.admin_role): discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        channel = await interaction.guild.create_text_channel(f"Тикет-для-{interaction.user.name}", overwrites=overwrites, category=interaction.channel.category)
        embed = discord.Embed(title=f"Тикет открыт!", color=config.colors.info)
        embed = interaction_author(embed, interaction)
        await channel.send(embed=embed, view = ticket_operator())
        await channel.send(interaction.guild.get_role(config.admin_role).mention)
        embed = discord.Embed(title="Тикет открыт", description=f"В канале {channel.mention}", color=config.colors.info)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ticket_operator(discord.ui.View):

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction, button):
        embed = discord.Embed(title="Вы уверены что хотите закрыть тикет?", description=f"Удаление автоматически отменится через {config.auto_cancel_time} секунд", color=config.colors.info)
        await interaction.response.send_message(embed = embed, view = confirm_deletion(), ephemeral = True, delete_after = config.auto_cancel_time)

class confirm_deletion(discord.ui.View):

    def __init__(self) -> None:
        super().__init__(timeout=config.auto_cancel_time)

    @discord.ui.button(label="Удалить", style=discord.ButtonStyle.red)
    async def delete(self, interaction, button):
        await interaction.channel.delete()
        

@client.event
async def setup_hook():
    global synced
    synced = False
    client.add_view(ticket_launcher())
    client.add_view(ticket_operator())

@client.event
async def on_ready():
    global synced
    print('')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='на тебя <3'))
    if not synced:
        await tree.sync(guild=discord.Object(id=guild))
        synced = True
    print(f'{client.user.name} подключён к серверу!    \n{round(client.latency * 1000)}ms')

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

@tree.command(name="тикет", description="Запускает систему тикетов в текущей категории!", guild=discord.Object(id=guild))
async def ticketing(intrct):
    embed = discord.Embed(title="PLACEHOLDER", description="PLACEHOLDER", color=config.colors.info)
    client.add_view(ticket_launcher())
    await intrct.channel.send(embed=embed, view=ticket_launcher())
    await intrct.response.send_message("Система тикетов была успешно (или почти) запущена", ephemeral=True)

@tree.command(name="добавить", description="Добавляет пользователя в тикет", guild=discord.Object(id=guild))
@app_commands.describe(user="Пользователь для добавления в тикет")
async def add_user(intrct, user: discord.User):
    if "тикет-для-" in intrct.channel.name:
        if intrct.user.roles and intrct.guild.get_role(config.admin_role) in intrct.user.roles:
            await intrct.channel.set_permissions(user, read_messages=True, send_messages=True, attach_files=True)
            embed = discord.Embed(title=f"Пользователь добавлен", description=f"{user.mention} был добавлен в тикет {intrct.user.mention}", color=config.colors.info)
            await intrct.response.send_message(embed=embed, ephemeral=False)
        else:
            await intrct.response.send_message("Вы не можете добавить пользователей в тикет", ephemeral=True)
    else:
        await intrct.response.send_message("Это не тикет!", ephemeral=True)

client.run(token)
