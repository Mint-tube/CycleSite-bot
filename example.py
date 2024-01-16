    @commands.command(
        name='warn',
        description='The famous warn command',
        usage='<@offender> called my mommy a fat :((((((( cri'
    )
    @has_permissions(manage_messages=True)
    async def warn_command(self, ctx, user:discord.Member, *, reason:str):
        if user.id == self.bot.user.id:
            # User tried to warn this exact bot.
            await ctx.send("Oh, REALLY now, huh? I do my best at maintaining this server and THIS is how you treat me? Screw this..")
            return
        if user.bot == 1:
            # User tried to warn a bot.
            await ctx.send("It's useless to warn a bot. Why would you even try.")
            return
        if user == ctx.author:
            # User tried to warn themselves.
            await ctx.send("Why the heck would you warn yourself? You hate yourself THAT much?")
            return
        if user.guild_permissions.manage_messages == True:
            # User mentioned another user who had the permission "Manage Messages"
            await ctx.send("The specified user has the \"Manage Messages\" permission (or higher) inside the guild/server.")
            return
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if not os.path.exists("data/warns/" + str(ctx.guild.id) + "/"):
            os.makedirs("data/warns/" + str(ctx.guild.id) + "/")
            # Checks if the folder for the guild exists. If it doesn't, create it.
        try:
            with open(f"data/warns/{str(ctx.guild.id)}/{str(user.id)}.json") as f:
                data = json.load(f)
            # See if the user has been warned
        except FileNotFoundError:
            # User has not been warned yet
            with open(f"data/warns/{str(ctx.guild.id)}/{str(user.id)}.json", "w") as f:
                data = ({
                    'offender_name':user.name,
                    'warns':1,
                    1:({
                        'warner':ctx.author.id,
                        'warner_name':ctx.author.name,
                        'reason':reason,
                        'channel':str(ctx.channel.id),
                        'datetime':dt_string
                    })
                }) # Creates the initial dictionary, which will then be dumped into a JSON file.
                json.dump(data, f)
            embed = discord.Embed(
                title=f"{user.name}'s new warn",
                color=random.choice(color_list)
            )
            embed.set_author(
                name=ctx.message.author.name,
                icon_url=ctx.message.author.avatar_url,
                url=f"https://discord.com/users/{ctx.message.author.id}/"
            )
            embed.add_field(
                name="Warn 1",
                value=f"Warner: {ctx.author.name} (<@{ctx.author.id}>)\nReason: {reason}\nChannel: <#{str(ctx.channel.id)}>\nDate and Time: {dt_string}",
                inline=True
            )
            await ctx.send(
                content="Successfully added new warn.",
                embed=embed
            )
            # Creates and sends embed, showing that the user has been warned successfully.
            return
            # using "return" so that it doesn't continue along the script

        # If the script made it this far, then the user has already been warned at least once.
        warn_amount = data.get("warns")
        new_warn_amount = warn_amount + 1
        data["warns"]=new_warn_amount
        data["offender_name"]=user.name
        new_warn = ({
            'warner':ctx.author.id,
            'warner_name':ctx.author.name,
            'reason':reason,
            'channel':str(ctx.channel.id),
            'datetime':dt_string
        })
        data[new_warn_amount]=new_warn
        json.dump(data, open(f"data/warns/{str(ctx.guild.id)}/{str(user.id)}.json", "a"))
        # Appends to dictionary, which will then be written inside the JSON.

        embed = discord.Embed(
            title=f"{user.name}'s new warn",
            color=random.choice(color_list)
        )
        embed.set_author(
            name=ctx.message.author.name,
            icon_url=ctx.message.author.avatar_url,
            url=f"https://discord.com/users/{ctx.message.author.id}/"
        )
        embed.add_field(
            name=f"Warn {new_warn_amount}",
            value=f"Warner: {ctx.author.name} (<@{ctx.author.id}>)\nReason: {reason}\nChannel: <#{str(ctx.channel.id)}>\nDate and Time: {dt_string}",
            inline=True
        )
        await ctx.send(
            content="Successfully added new warn.",
            embed=embed
        )
        # Creates and sends embed
    @warn_command.error
    async def warn_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            # Author is missing permissions
            await ctx.send('{0.author.name}, you do not have the correct permissions to do so. *(commands.MissingPermissions error, action cancelled)*'.format(ctx))
            return
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'user':
                # Author did not specify the user to warn
                await ctx.send("{0.author.name}, you forgot to specify a user to warn. *(commands.MissingRequiredArgument error, action cancelled)*".format(ctx))
                return
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'reason':
                # Author did not specify the reason
                await ctx.send("{0.author.name}, you forgot to specify a reason. *(commands.MissingRequiredArgument error, action cancelled)*".format(ctx))
                return
        print(error)
        await ctx.send(error)

    @commands.command(
        name='warns',
        description='See all the warns a user has',
        usage='<@offender>',
        aliases=['warnings']
    )
    async def warns_command(self, ctx, user:discord.Member):
        try:
            with open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "r") as f:
                data = json.load(f)
            # See if the user has been warned
        except FileNotFoundError:
            # User does not have any warns.
            await ctx.send(f"{ctx.author.name}, user [{user.name} ({user.id})] does not have any warns.")
            return

        # If the script made it this far, then the user has warns.
        warn_amount = data.get("warns")
        last_noted_name = data.get("offender_name")
        if warn_amount == 1:
            warns_word = "warn"
        else:
            warns_word = "warns"
        # Dumb thing to complain about, but if the user has 1 warn, then set the word as "warn". Otherwise, set the word as "warns".
        # I dunno, I might just be a perfectionnist and want my bot to have only the b e s t grammar or something. But hey, little detail is better than none!

        try:
            username = user.name
        except:
            # User may have left the server
            username = last_noted_name


        embed = discord.Embed(
            title=f"{username}'s warns",
            description=f"They have {warn_amount} {warns_word}.",
            color=random.choice(color_list)
        )
        embed.set_author(
            name=ctx.message.author.name,
            icon_url=ctx.message.author.avatar_url,
            url=f"https://discord.com/users/{ctx.message.author.id}/"
        )
        for x in range (1,warn_amount+1):
            with open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "r") as f:
                data = json.load(f)

            warn_dict = data.get(str(x))
            warner_id = warn_dict.get('warner')
            try:
                warner_name = self.bot.get_user(id=warner_id)
            except:
                # User probably left
                warner_name = warn_dict.get('warner_name')

            warn_reason = warn_dict.get('reason')
            warn_channel = warn_dict.get('channel')
            warn_datetime = warn_dict.get('datetime')

            embed.add_field(
                name=f"Warn {x}",
                value=f"Warner: {warner_name} (<@{warner_id}>)\nReason: {warn_reason}\nChannel: <#{warn_channel}>\nDate and Time: {warn_datetime}",
                inline=True
            )
            # For every warn between 1 and warn_amount+1, get the info of that warn and put it inside an embed field.
        await ctx.send(
            content=None,
            embed=embed
        )
        # Send embed.
    @warns_command.error
    async def warns_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'user':
                # Author did not specify user
                await ctx.send("Please mention someone to verify their warns.")
                return
        await ctx.send(error)

    @commands.command(
        name='remove_warn',
        description='Removes a specific warn from a specific user.',
        usage='@user 2',
        aliases=['removewarn','clearwarn']
    )
    @has_permissions(manage_messages=True)
    async def remove_warn_command(self, ctx, user:discord.Member, *, warn:str):
        try:
            with open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "r") as f:
                data = json.load(f)
            # See if the user has been warned
        except FileNotFoundError:
            # User does not have any warns.
            await ctx.send(f"[{ctx.author.name}], user [{user.name} ({user.id})] does not have any warns.")
            return
        warn_amount = data.get('warns')
        specified_warn = data.get(warn)
        warn_warner = specified_warn.get('warner')
        warn_reason = specified_warn.get('reason')
        warn_channel = specified_warn.get('channel')
        warn_datetime = specified_warn.get('datetime')
        try:
            warn_warner_name = self.bot.get_user(id=warn_warner)
        except:
            # User probably left
            warn_warner_name = specified_warn.get('warner_name')

        confirmation_embed = discord.Embed(
            title=f'{user.name}\'s warn number {warn}',
            description=f'Warner: {warn_warner_name}\nReason: {warn_reason}\nChannel: <#{warn_channel}>\nDate and Time: {warn_datetime}',
            color=random.choice(color_list),
        )
        confirmation_embed.set_author(
            name=ctx.message.author.name,
            icon_url=ctx.message.author.avatar_url,
            url=f"https://discord.com/users/{ctx.message.author.id}/"
        )
        def check(ms):
            # Look for the message sent in the same channel where the command was used
            # As well as by the user who used the command.
            return ms.channel == ctx.message.channel and ms.author == ctx.message.author

        await ctx.send(content='Are you sure you want to remove this warn? (Reply with y or n)', embed=confirmation_embed)
        msg = await self.bot.wait_for('message', check=check)
        reply = msg.content.lower() # Set the reply into a string
        if reply in ('y', 'yes', 'confirm'):
            # do the whole removing process.
            if warn_amount == 1: # Check if the user only has one warn.
                os.remove("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json") # Removes the JSON containing their only warn.
                await ctx.send(f"[{ctx.author.name}], user [{user.name} ({user.id})] has gotten their warn removed.")
                return
            # User does not have only one warn.
            if warn != warn_amount: # Check if the warn to remove was not the last warn.
                for x in range(int(warn),int(warn_amount)):
                    data[str(x)] = data[str(x+1)]
                    del data[str(x+1)]
                    # Puts all warns with a value higher than the current specified warn back by one (I suck at explaining)
            else:
                del data[warn]
                # It was their last warn.
            data['warns']=warn_amount - 1
            json.dump(data,open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "w"))
            await ctx.send(f"[{ctx.author.name}], user [{user.name} ({user.id})] has gotten their warn removed.")
            return
        elif reply in ('n', 'no', 'cancel'):
            await ctx.send("Alright, action cancelled.")
            return
        else:
            await ctx.send("I have no idea what you want me to do. Action cancelled.")
    @remove_warn_command.error
    async def remove_warn_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'user':
                # Author did not specify a user
                await ctx.send("Please mention someone to remove their warns.")
                return
            if error.param.name == 'warn':
                # Author did not specify a warn ID
                await ctx.send("You did not specify a warn ID to remove.")
                return
        if isinstance(error, commands.CommandInvokeError):
            # Author probably specified an invalid ID.
            await ctx.send("You specified an invalid ID.")
            return
        await ctx.send(error)

    @commands.command(
        name='edit_warn',
        description='Edits a specific warn from a specific user.',
        usage='@user 2',
        aliases=['editwarn','changewarn']
    )
    @has_permissions(manage_messages=True)
    async def edit_warn_command(self, ctx, user:discord.Member, *, warn:str):
        try:
            with open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "r") as f:
                data = json.load(f)
            # See if the user has been warned
        except FileNotFoundError:
            # User does not have any warns.
            await ctx.send(f"[{ctx.author.name}], user [{user.name} ({user.id})] does not have any warns.")
            return


        def check(ms):
            # Look for the message sent in the same channel where the command was used
            # As well as by the user who used the command.
            return ms.channel == ctx.message.channel and ms.author == ctx.message.author

        await ctx.send(content='What would you like to change the warn\'s reason to?')
        msg = await self.bot.wait_for('message', check=check) # Pause the ongoing script to wait for the user to send a message.
        warn_new_reason = msg.content.lower()

        specified_warn = data.get(warn)
        warn_warner = specified_warn.get('warner')
        warn_channel = specified_warn.get('channel')
        warn_datetime = specified_warn.get('datetime')
        try:
            warn_warner_name = self.bot.get_user(id=warn_warner)
        except:
            # User probably left
            warn_warner_name = specified_warn.get('warner_name')

        confirmation_embed = discord.Embed(
            title=f'{user.name}\'s warn number {warn}',
            description=f'Warner: {warn_warner_name}\nReason: {warn_new_reason}\nChannel: <#{warn_channel}>\nDate and Time: {warn_datetime}',
            color=random.choice(color_list),
        )
        confirmation_embed.set_author(
            name=ctx.message.author.name,
            icon_url=ctx.message.author.avatar_url,
            url=f"https://discord.com/users/{ctx.message.author.id}/"
        )

        await ctx.send(content='Are you sure you want to edit this warn like this? (Reply with y/yes or n/no)', embed=confirmation_embed)

        msg = await self.bot.wait_for('message', check=check)
        reply = msg.content.lower() # Set the title
        if reply in ('y', 'yes', 'confirm'):
            specified_warn['reason']=warn_new_reason
            json.dump(data,open("data/warns/" + str(ctx.guild.id) + "/" + str(user.id) + ".json", "w"))
            await ctx.send(f"[{ctx.author.name}], user [{user.name} ({user.id})] has gotten their warn edited.")
            return
        elif reply in ('n', 'no', 'cancel', 'flanksteak'):
            # dont ask me why i decided to put flanksteak
            await ctx.send("Alright, action cancelled.")
            return
        else:
            await ctx.send("I have no idea what you want me to do. Action cancelled.")
    @edit_warn_command.error
    async def edit_warn_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'user':
                # Author did not specify a user
                await ctx.send("Please mention someone to remove their warns.")
                return
            if error.param.name == 'warn':
                # Author did not specify a warn ID
                await ctx.send("You did not specify a warn ID to remove.")
                return
        if isinstance(error, commands.CommandInvokeError):
            # Author probably specified an invalid ID.
            await ctx.send("You specified an invalid ID.")
            return
        await ctx.send(error)



def setup(bot):
    bot.add_cog(Warn(bot))