import os, discord, asyncio, sqlite3, sys
from discord import app_commands, Color
from discord.ext import commands, tasks
from icecream import ic
from random import randint, choice
from data.emojis import emojis
import data.config as config

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

#Добавление автора к embed
def interaction_author(embed: discord.Embed, interaction: discord.Interaction):
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
    return embed

#Взаимодействие с tickets_counter.txt
def tickets_counter_add():
    with open('data/tickets_counter.txt', 'r') as file:
        var = int(file.readline())
    with open('data/tickets_counter.txt', 'w+') as file:
        file.write(str(var + 1))
    return var

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None) 
    
    @discord.ui.button(label="Открыть тикет", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = await interaction.channel.create_thread(name=f"тикет-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
        ticket_id = int(thread.name.split("-")[-1])
        embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.colors.info)
        embed = interaction_author(embed, interaction)
        await thread.send(embed=embed, view = ticket_operator())
        await thread.send(interaction.guild.get_role(config.admin_role).mention + ' ' + interaction.user.mention)
        embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ticket_operator(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction, button):
        embed = discord.Embed(title="Вы уверены что хотите закрыть тикет?", description=f"Удаление автоматически отменится через {config.auto_cancel_time} секунд", color=config.colors.info)
        await interaction.response.send_message(embed = embed, view = confirm_closing(), ephemeral = True, delete_after = config.auto_cancel_time)

class confirm_closing(discord.ui.View):

    def __init__(self) -> None:
        super().__init__(timeout=config.auto_cancel_time)

    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        ticket_number = int(interaction.channel.name.split("-")[-1])
        channel = interaction.channel
        async for first_message in channel.history(limit=1, oldest_first=True):
            embed = discord.Embed(title=f"Тикет номер {ticket_number} закрыт!", color=config.colors.info)
            embed.add_field(name='Время открытия:', value=first_message.created_at.date(), inline=True)
            embed.add_field(name='Открыл:', value=first_message.embeds[0].author.name, inline=True)
            embed.add_field(name='Время закрытия:', value=interaction.created_at.date(), inline=True)
            embed.add_field(name='Закрыл:', value=interaction.user, inline=True)
            embed.add_field(name='Перейти к тикету:', value=first_message.channel.jump_url, inline=False)
        await interaction.user.send(f"Тикет номер {ticket_number} закрыт!", embed=embed)
        await interaction.response.send_message(f"Тикет номер {ticket_number} закрыт!", embed=embed)
        await interaction.channel.edit(archived = True, locked = True)
        
@tasks.loop(seconds = 60) # repeat after every 10 seconds
async def presence():
    emoji = choice(emojis)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
    name = choice(client.get_guild(1122085072577757275).members).display_name +
    f' {emoji}'))

@client.event
async def setup_hook():
    global synced
    synced = False
    client.add_view(ticket_launcher())
    client.add_view(ticket_operator())

@client.event
async def on_ready():
    global synced
    presence.start()
    if not synced:
        await tree.sync(guild=discord.Object(id=config.guild))
        synced = True
    print(f'{client.user.name} подключён к серверу!    \n{round(client.latency * 1000)}ms')


#Пинг бота по slash-комманде ----------------
@tree.command(name="пинг", description="Пингани бота!", guild=discord.Object(id=config.guild))
async def on_ping(intrct):
    embed = discord.Embed(title="Понг!    ", description=f"{round(client.latency * 1000)}мс", color=config.colors.info)
    await intrct.response.send_message(embed=embed)

#Cлучайные реакции на сообщения ----------------
@client.event 
async def on_message(message):
    if message.author == client.user:
        return
    if randint(0, 15) == 1:
        if message.channel.category_id not in config.very_serious_categories:
            await message.add_reaction(choice(message.guild.emojis))

@tree.command(name="тикет", description="Запускает систему тикетов в текущей категории!", guild=discord.Object(id=config.guild))
async def ticketing(intrct, title: str, description: str):
    if intrct.user.id in config.bot_engineers:
        embed = discord.Embed(title=title, description=description, color=config.colors.info)
        client.add_view(ticket_launcher())
        await intrct.channel.send(embed=embed, view=ticket_launcher())
        await intrct.response.send_message("Система тикетов была успешно (или почти) запущена", ephemeral=True)
    else:
        await intrct.response.send_message("> У вас нет прав для запуска этой команды", ephemeral=True)


#Выебать бота (для МАО)
@tree.command(name="выебать", description="Приветствие бота!", guild=discord.Object(id=config.guild))
async def on_sex(intrct):
    sex_variants = [f'О, да, {intrct.user.display_name}! Выеби меня полностью, {intrct.user.display_name} 💕','Боже мой, как сильно... 💘','Ещеее! Ещееееее! 😍',f'{intrct.user.display_name}, я люблю тебя!']
    fucked = False
    if intrct.channel.is_nsfw():
        for role in intrct.user.roles:
            if role.id in config.can_sex:
                embed = discord.Embed(title = choice(sex_variants),description='', color = config.colors.info)
                await intrct.response.send_message(embed = embed)
                fucked = True
                break
        if not fucked:
            await intrct.response.send_message("> Ты не достоин ебать бота 👿", ephemeral = True)
    else:
        await intrct.response.send_message("> Это не NSFW канал!", ephemeral = True)

client.run(config.token)
