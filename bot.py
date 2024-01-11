import os, discord, asyncio, sqlite3, sys
from discord import app_commands, Color, ui
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

class application_type_select(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Заявка на роль постоянного игрока (Канцелярия)', emoji='📋'),
            discord.SelectOption(label='Заявка на администратора сервера SCP:SL', emoji='👮🏻‍♂️'),
            discord.SelectOption(label='Заявка на модератора Discord', emoji='👾'),
            discord.SelectOption(label='Заявка на тех. администратора', emoji='💻'),
            discord.SelectOption(label='Заявка на ивентолога', emoji='🎈'),
            discord.SelectOption(label='Заявка на становление организацией', emoji='🎓')
        ]

        super().__init__(placeholder='На какую роль будете подавать?', min_values=1, max_values=1, options=options, custom_id='application_type')

    async def callback(self, interaction: discord.Interaction):
        match self.values[0]:
            case 'Заявка на роль постоянного игрока (Канцелярия)':
                await interaction.response.send_modal(modal.application.player_role())
            case 'Заявка на администратора сервера SCP:SL':
                await interaction.response.send_modal(modal.application.administrator_scp())
            case 'Заявка на модератора Discord':
                await interaction.response.send_modal(modal.application.administrator_discord())
            case 'Заявка на тех. администратора':
                await interaction.response.send_modal(modal.application.administrator_tech())
            case 'Заявка на ивентолога':
                await interaction.response.send_modal(modal.application.eventmaker())
            case 'Заявка на становление организацией':
                await interaction.response.send_modal(modal.application.organization())

class ticket_launcher():
    class question(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None) 
        
        @discord.ui.button(label="Задать вопрос", style=discord.ButtonStyle.green, custom_id="open_question")
        async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(modal.question())
            
    
    class bug(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None) 
        
        @discord.ui.button(label="Сообщить о баге", style=discord.ButtonStyle.green, custom_id="open_bug")
        async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(modal.bug())

    class report(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)

        @discord.ui.button(label="Подать жалобу", style=discord.ButtonStyle.green, custom_id="open_report")
        async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(modal.report())
    
    class application(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)
            self.add_item(application_type_select())

class modal():
    class question(ui.Modal, title='Вопрос'):
        question_object = ui.TextInput(label='Тема вопроса:', style=discord.TextStyle.short)
        question = ui.TextInput(label='Вопрос:', style=discord.TextStyle.long)

        async def on_submit(self, interaction: discord.Interaction):
            thread = await interaction.channel.create_thread(name=f"вопрос-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
            ticket_id = int(thread.name.split("-")[-1])
            open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.colors.info)
            open_embed = interaction_author(open_embed, interaction)
            modal_params = discord.Embed(color=config.colors.info)
            modal_params.add_field(name="**Тема вопроса:**", value='>>> ' + self.question_object.value, inline=False)
            modal_params.add_field(name="**Вопрос:**", value='>>> ' + self.question.value, inline=False)
            await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
            await thread.send(interaction.user.mention)
            await thread.send(interaction.guild.get_role(config.admin_role).mention)
            embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class bug(ui.Modal, title='Баг'):
        bug_type = ui.TextInput(label='Тип бага (бот, сервер и т.п.):', style=discord.TextStyle.short)
        steps = ui.TextInput(label='Шаги воспроизведения:', style=discord.TextStyle.long)
        expected = ui.TextInput(label='Ожидаемый результат:', style=discord.TextStyle.short)
        actual = ui.TextInput(label='Фактический результат:', style=discord.TextStyle.short)

        async def on_submit(self, interaction: discord.Interaction):
            thread = await interaction.channel.create_thread(name=f"баг-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
            ticket_id = int(thread.name.split("-")[-1])
            open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.colors.info)
            open_embed = interaction_author(open_embed, interaction)
            modal_params = discord.Embed(color=config.colors.info)
            modal_params.add_field(name="**Тип бага:**", value='>>> ' + self.bug_type.value, inline=False)
            modal_params.add_field(name="**Шаги воспроизведения:**", value='>>> ' + self.steps.value, inline=False)
            modal_params.add_field(name="**Ожидаемый результат:**", value='>>> ' + self.expected.value, inline=False)
            modal_params.add_field(name="**Фактический результат:**", value='>>> ' + self.actual.value, inline=False)
            await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
            await thread.send(interaction.user.mention)
            await thread.send(interaction.guild.get_role(config.admin_role).mention)
            embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class report(ui.Modal, title='Жалоба'):
        place = ui.TextInput(label='Место нарушения:', style=discord.TextStyle.short)
        troublemaker = ui.TextInput(label='Нарушитель:', style=discord.TextStyle.short)
        trouble = ui.TextInput(label='Нарушение:', style=discord.TextStyle.long)

        async def on_submit(self, interaction: discord.Interaction):
            thread = await interaction.channel.create_thread(name=f"жалоба-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
            ticket_id = int(thread.name.split("-")[-1])
            open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.colors.info)
            open_embed = interaction_author(open_embed, interaction)
            modal_params = discord.Embed(color=config.colors.info)
            modal_params.add_field(name="**Место нарушения:**", value='>>> ' + self.place.value, inline=False)
            modal_params.add_field(name="**Нарушитель:**", value='>>> ' + self.troublemaker.value, inline=False)
            modal_params.add_field(name="**Нарушение:**", value='>>> ' + self.trouble.value, inline=False)
            await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
            await thread.send(interaction.user.mention)
            await thread.send(interaction.guild.get_role(config.admin_role).mention)
            embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class application():
        class player_role(ui.Modal, title='Заявка на постоянного игрока (Канцелярия)'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            exp = ui.TextInput(label='Сколько уже играете на нашем сервере:', style=discord.TextStyle.short)
            familiar = ui.TextInput(label='Кто из администрации может знать вас:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Время собеседования или гс:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.familiar.label, value='>>> ' + self.familiar.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        class administrator_scp(ui.Modal, title='Заявка на администратора сервера SCP'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            steam = ui.TextInput(label='Cсылка на профиль Steam:', style=discord.TextStyle.short)
            exp = ui.TextInput(label='Ваш опыт в администрировании:', style=discord.TextStyle.short)
            activity =ui.TextInput(label='Сколько времени можете уделять проекту:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.steam.label, value='>>> ' + self.steam.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        class administrator_discord(ui.Modal, title='Заявка на модератора Discord'): 
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            exp = ui.TextInput(label='Ваш опыт в модерации:', style=discord.TextStyle.short)
            activity = ui.TextInput(label='Сколько можете уделять времени проекту:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        class administrator_tech(ui.Modal, title='Заявка на тех. админа'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            skills = ui.TextInput(label='Умения, знания и опыт в программировании:', style=discord.TextStyle.short)
            activity = ui.TextInput(label='Сколько можете уделять времени проекту:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.skills.label, value='>>> ' + self.skills.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        class eventmaker(ui.Modal, title='Заявка на ивентолога:'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            events = ui.TextInput(label='Какие ивенты будете проводить:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.events.label, value='>>> ' + self.events.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.colors.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        class organization(ui.Modal, title='Заявка на становление организацией:'):
            name = ui.TextInput(label='Название организации (Из лора SCP):', style=discord.TextStyle.short)
            activity = ui.TextInput(label='Ваш род деятельности:', style=discord.TextStyle.short)
            members = ui.TextInput(label='Перечислите членов организации и её лидеров:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда можете пройти собеседование:', style=discord.TextStyle.short)

            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Вопрос номер {ticket_id} открыт!", color=config.colors.info)
                open_embed = interaction_author(open_embed, interaction)
                modal_params = discord.Embed(color=config.colors.info)
                modal_params.add_field(name=self.name.label, value='>>> ' + self.name.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.members.label, value='>>> ' + self.members.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.applications_admin_role).mention)
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
        embed = discord.Embed(title=f"Тикет номер {ticket_number} закрыт!", color=config.colors.info)
        is_first = True
        async for message in channel.history(limit=2, oldest_first=True):
            if is_first:
                is_first = False       
                embed.add_field(name='Время открытия:', value=message.created_at.date(), inline=True)
                continue     
            embed.add_field(name='Открыл:', value=message.content, inline=True)
        embed.add_field(name='Время закрытия:', value=interaction.created_at.date(), inline=True)
        embed.add_field(name='Закрыл:', value=interaction.user.mention, inline=True)
        embed.add_field(name='Перейти к тикету:', value=interaction.channel.jump_url, inline=False)
        await interaction.user.send(embed = embed)
        await interaction.guild.get_channel(config.tickets_log_channel).send(embed = embed)
        await interaction.response.send_message(embed = embed)
        await interaction.channel.edit(archived = True, locked = True)
        
@tasks.loop(seconds = 60) # repeat after every 10 seconds
async def presence():
    emoji = choice(emojis)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
    name = choice(client.get_guild(1122085072577757275).members).display_name +
    f' {emoji}'))

def add_views():
    client.add_view(ticket_launcher.question())
    client.add_view(ticket_launcher.bug())
    client.add_view(ticket_launcher.report())
    client.add_view(ticket_launcher.application())
    client.add_view(ticket_operator())

@client.event
async def setup_hook():
    # await tree.sync(guild=discord.Object(id=config.guild))
    add_views()

@client.event
async def on_ready():
    presence.start()
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
async def ticketing(intrct, title: str, description: str, type: str):
    if intrct.user.id in config.bot_engineers:
        match type:
            case 'Вопрос':
                embed = discord.Embed(title=title, description=description, color=config.colors.info)
                await intrct.channel.send(embed=embed, view=ticket_launcher.question())
                client.add_view(ticket_launcher.question())
            case 'Баг':
                embed = discord.Embed(title=title, description=description, color=config.colors.danger)
                await intrct.channel.send(embed=embed, view=ticket_launcher.bug())
                client.add_view(ticket_launcher.bug())
            case 'Жалоба':
                embed = discord.Embed(title=title, description=description, color=config.colors.warning)
                await intrct.channel.send(embed=embed, view=ticket_launcher.report())
                client.add_view(ticket_launcher.report())
            case 'Заявка':
                embed = discord.Embed(title=title, description=description, color=config.colors.info)
                await intrct.channel.send(embed=embed, view=ticket_launcher.application())
                client.add_view(ticket_launcher.application())
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
