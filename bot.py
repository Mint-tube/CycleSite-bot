import os, discord, config, asyncio, sqlite3, sys
from discord import app_commands, Color
from discord.ext import commands
from icecream import ic
from random import randint, choice

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

# def tickets_counter_read():           ----- На всякий случай, потом вырежу -----
    # with open('data/tickets_counter.txt', 'r') as file:
    #     var = int(file.readline())
    # return var


class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None) 
    
    @discord.ui.button(label="Открыть тикет", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = await interaction.channel.create_thread(name=f"тикет-номер-{tickets_counter_add()}", auto_archive_duration=10080)
        embed = discord.Embed(title=f"Тикет открыт!", color=config.colors.info)
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
        embed = discord.Embed(title=f"Тикет номер {interaction.channel.name[-1]} закрыт!", color=config.colors.info)

        #БРО ДОДЕЛАЙ ЭТОТ EMBED
        await interaction.user.send(embed=embed)
        await interaction.response.send_message(embed=embed)
        await interaction.channel.edit(archived = True, locked = True)
        

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
    if randint(0, 10) == 1:
        await message.add_reaction(choice(message.guild.emojis))

@tree.command(name="тикет", description="Запускает систему тикетов в текущей категории!", guild=discord.Object(id=config.guild))
async def ticketing(intrct, title: str, description: str):
    if intrct.guild.get_role(config.admin_role) in intrct.user.roles:
        embed = discord.Embed(title=title, description=description, color=config.colors.info)
        client.add_view(ticket_launcher())
        await intrct.channel.send(embed=embed, view=ticket_launcher())
        await intrct.response.send_message("Система тикетов была успешно (или почти) запущена", ephemeral=True)
    else:
        await intrct.response.send_message(">У вас нет прав для запуска этой команды", ephemeral=True)


#Выебать бота (для МАО)
sex_variants = ['О, да, мао! Выеби меня полностью💕','Боже мой, как сильно...💘','Ещеее! Ещееееее!🥴']
@tree.command(name="выебать", description="Приветствие бота!", guild=discord.Object(id=config.guild))
async def on_sex(intrct):
    if intrct.user.id == 879679189425475594:
        embed = discord.Embed(title = choice(sex_variants),description='', color = config.colors.success)
        await intrct.response.send_message(embed = embed)
    else:
        await intrct.response.send_message("Ты не достоин ебать бота👿", ephemeral = True)

client.run(config.token)
