import discord, asyncio
from discord import ui
import data.config as config
from time import mktime

def tickets_counter_add():
    with open('data/counter.txt', 'r') as file:
        var = int(file.readline())
    with open('data/counter.txt', 'w+') as file:
        file.write(str(var + 1))
    return var

def interaction_author(embed: discord.Embed, interaction: discord.Interaction):
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)
    return embed

def unix_datetime(source):
    return int(mktime(source.timetuple()))


class ticket_operator(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction, button):
        embed = discord.Embed(title="Вы уверены что хотите закрыть тикет?", description=f"Удаление автоматически отменится через {config.auto_cancel_time} секунд", color=config.info)
        await interaction.response.send_message(embed = embed, view = confirm_closing(), ephemeral = True, delete_after = config.auto_cancel_time)

class confirm_closing(discord.ui.View):

    def __init__(self) -> None:
        super().__init__(timeout=config.auto_cancel_time)

    @discord.ui.button(label="Закрыть", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):
        ticket_number = int(interaction.channel.name.split("-")[-1])
        channel = interaction.channel
        embed = discord.Embed(title=f"Тикет номер {ticket_number} закрыт!", color=config.info)
        is_first = True
        async for message in channel.history(limit=2, oldest_first=True):
            if is_first:
                is_first = False       
                embed.add_field(name='Время открытия:', value=f'<t:{unix_datetime(message.created_at)}>', inline=True)
                continue     
            embed.add_field(name='Открыл:', value=message.content, inline=True)
        embed.add_field(name='Перейти к тикету:', value=interaction.channel.jump_url, inline=False)
        embed.add_field(name='Время закрытия:', value=f'<t:{unix_datetime(interaction.created_at)}>', inline=True)
        embed.add_field(name='Закрыл:', value=interaction.user.mention, inline=True)
        try:
            await interaction.user.send(embed = embed)
        except discord.errors.Forbidden:
            pass
        await interaction.guild.get_channel(config.logs_channels.tickets).send(embed = embed)
        await interaction.response.send_message(embed = embed)
        await interaction.channel.edit(archived = True, locked = True)

class modal():

    class question(ui.Modal, title='Вопрос'):
        question_object = ui.TextInput(label='Тема вопроса:', style=discord.TextStyle.short)
        question = ui.TextInput(label='Вопрос:', style=discord.TextStyle.long)
        async def on_submit(self, interaction: discord.Interaction):
            thread = await interaction.channel.create_thread(name=f"вопрос-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
            ticket_id = int(thread.name.split("-")[-1])
            open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.info)
            open_embed = interaction_author(open_embed, interaction)
            modal_params = discord.Embed(color=config.info)
            modal_params.add_field(name="**Тема вопроса:**", value='>>> ' + self.question_object.value, inline=False)
            modal_params.add_field(name="**Вопрос:**", value='>>> ' + self.question.value, inline=False)
            await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
            await thread.send(interaction.user.mention)
            await thread.send(interaction.guild.get_role(config.admin_role).mention)
            embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class bug(ui.Modal, title='Баг'):
        bug_type = ui.TextInput(label='Тип бага (бот, сервер и т.п.):', style=discord.TextStyle.short)
        steps = ui.TextInput(label='Шаги воспроизведения:', style=discord.TextStyle.long)
        expected = ui.TextInput(label='Ожидаемый результат:', style=discord.TextStyle.short)
        actual = ui.TextInput(label='Фактический результат:', style=discord.TextStyle.short)
        async def on_submit(self, interaction: discord.Interaction):
            thread = await interaction.channel.create_thread(name=f"баг-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
            ticket_id = int(thread.name.split("-")[-1])
            open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.info)
            open_embed = interaction_author(open_embed, interaction)
            modal_params = discord.Embed(color=config.info)
            modal_params.add_field(name="**Тип бага:**", value='>>> ' + self.bug_type.value, inline=False)
            modal_params.add_field(name="**Шаги воспроизведения:**", value='>>> ' + self.steps.value, inline=False)
            modal_params.add_field(name="**Ожидаемый результат:**", value='>>> ' + self.expected.value, inline=False)
            modal_params.add_field(name="**Фактический результат:**", value='>>> ' + self.actual.value, inline=False)
            await thread.send(embeds=[open_embed, modal_params], view = ticket_operator())
            await thread.send(interaction.user.mention)
            await thread.send(interaction.guild.get_role(config.admin_role).mention)
            embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    class report():

        class player(ui.Modal, title='Жалоба на игрока'):
            place = ui.TextInput(label='Место нарушения:', style=discord.TextStyle.short)
            troublemaker = ui.TextInput(label='Нарушитель:', style=discord.TextStyle.short)
            trouble = ui.TextInput(label='Нарушение:', style=discord.TextStyle.long)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"жалоба-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Жалоба на игрока', color=config.danger)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name="**Место нарушения:**", value='>>> ' + self.place.value, inline=False)
                modal_params.add_field(name="**Нарушитель:**", value='>>> ' + self.troublemaker.value, inline=False)
                modal_params.add_field(name="**Нарушение:**", value='>>> ' + self.trouble.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class administrator(ui.Modal, title='Жалоба на администратора'):
            place = ui.TextInput(label='Место нарушения:', style=discord.TextStyle.short)
            troublemaker = ui.TextInput(label='Нарушитель:', style=discord.TextStyle.short)
            trouble = ui.TextInput(label='Нарушение:', style=discord.TextStyle.long)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"жалоба-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Жалоба на администратора', color=config.danger)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name="**Место нарушения:**", value='>>> ' + self.place.value, inline=False)
                modal_params.add_field(name="**Нарушитель:**", value='>>> ' + self.troublemaker.value, inline=False)
                modal_params.add_field(name="**Нарушение:**", value='>>> ' + self.trouble.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class appeal(ui.Modal, title='Аппеляция наказания'):
            trouble = ui.TextInput(label='Нарушение:', style=discord.TextStyle.short)
            punishment = ui.TextInput(label='Наказание:', style=discord.TextStyle.short)
            appeal_reason = ui.TextInput(label='Почему наказание должно быть снято:', style=discord.TextStyle.long)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"жалоба-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Тикет номер {ticket_id} открыт!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Аппеляция наказания', color=config.warning)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name="**Нарушение:**", value='>>> ' + self.trouble.value, inline=False)
                modal_params.add_field(name="**Наказание:**", value='>>> ' + self.punishment.value, inline=False)
                modal_params.add_field(name="**Почему наказание должно быть снято::**", value='>>> ' + self.appeal_reason.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.admin_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

    class application():
        
        class player_role(ui.Modal, title='Заявка на партнёрку'):
            age = ui.TextInput(label='Ссылка на ваш сервер:', style=discord.TextStyle.short)
            exp = ui.TextInput(label='Ссылка на ваш сервер:', style=discord.TextStyle.short)
            familiar = ui.TextInput(label='Откуда узнали о нашем сервере:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Есть ли дополнительные просьбы:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Заявка на партнёрку', color=config.info)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.familiar.label, value='>>> ' + self.familiar.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
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
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Заявка на администратора сервера SCP', color=config.info)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.steam.label, value='>>> ' + self.steam.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class administrator_discord(ui.Modal, title='Заявка на модератора Discord'): 
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            exp = ui.TextInput(label='Ваш опыт в модерации:', style=discord.TextStyle.short)
            activity = ui.TextInput(label='Сколько можете уделять времени проекту:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Заявка на модератора Discord', color=config.info)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.exp.label, value='>>> ' + self.exp.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class administrator_tech(ui.Modal, title='Заявка на тех. админа'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            skills = ui.TextInput(label='Умения, знания и опыт в программировании:', style=discord.TextStyle.short)
            activity = ui.TextInput(label='Сколько можете уделять времени проекту:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Заявка на тех. админа', color=config.info)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.skills.label, value='>>> ' + self.skills.value, inline=False)
                modal_params.add_field(name=self.activity.label, value='>>> ' + self.activity.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)

        class eventmaker(ui.Modal, title='Заявка на ивентолога:'):
            age = ui.TextInput(label='Ваш возраст:', style=discord.TextStyle.short)
            events = ui.TextInput(label='Какие ивенты будете проводить:', style=discord.TextStyle.short)
            interview = ui.TextInput(label='Когда сможете пройти собеседование:', style=discord.TextStyle.short)
            async def on_submit(self, interaction: discord.Interaction):
                thread = await interaction.channel.create_thread(name=f"заявка-номер-{tickets_counter_add()}", auto_archive_duration=10080, invitable=False)
                ticket_id = int(thread.name.split("-")[-1])
                open_embed = discord.Embed(title=f"Заявка номер {ticket_id} открыта!", color=config.info)
                open_embed = interaction_author(open_embed, interaction)
                ticket_type = discord.Embed(title='Заявка на ивентолога', color=config.info)
                modal_params = discord.Embed(color=config.info)
                modal_params.add_field(name=self.age.label, value='>>> ' + self.age.value, inline=False)
                modal_params.add_field(name=self.events.label, value='>>> ' + self.events.value, inline=False)
                modal_params.add_field(name=self.interview.label, value='>>> ' + self.interview.value, inline=False)
                await thread.send(embeds=[open_embed, ticket_type, modal_params], view = ticket_operator())
                await thread.send(interaction.user.mention)
                await thread.send(interaction.guild.get_role(config.secretary_role).mention)
                embed = discord.Embed(title="Тикет открыт", description=f"В канале {thread.mention}", color=config.info)
                await interaction.response.send_message(embed=embed, ephemeral=True)


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

class report_type_select(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Подать жалобу на игрока', emoji='✍🏻'),
            discord.SelectOption(label='Подать жалобу на администратора', emoji='💥'),
            discord.SelectOption(label='Подать апелляцию', emoji='🗯'),
        ]

        super().__init__(placeholder='Что будете подавать?', min_values=1, max_values=1, options=options, custom_id='report_type')

    async def callback(self, interaction: discord.Interaction):
        match self.values[0]:
            case 'Подать жалобу на игрока':
                await interaction.response.send_modal(modal.report.player())
            case 'Подать жалобу на администратора':
                await interaction.response.send_modal(modal.report.administrator())
            case 'Подать апелляцию':
                await interaction.response.send_modal(modal.report.appeal())

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
            self.add_item(report_type_select())
    
    class application(discord.ui.View):
        def __init__(self) -> None:
            super().__init__(timeout=None)
            self.add_item(application_type_select())
