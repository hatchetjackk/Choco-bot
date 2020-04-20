import asyncio
import inspect
import json
import discord
import util.tools as tools
import util.db as db
from discord.ext import commands

mae_banner = 'https://i.imgur.com/HffuudZ.jpg'
turnip = 'https://i.imgur.com/wl2MZIV.png'
_turnip_emoji = 694822764699320411
_confirm = ['y', 'yes']
_deny = ['n', 'no']
_quit = ['q', 'quit']

# where to send invite information
_dms_channel = 694015832728010762


class BetaFeatures(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def show_prefix(guild):
        prefix = db.get_prefix(guild)[0]
        return prefix

    async def show_menu(self, ctx):
        prefix = await self.show_prefix(ctx.guild)
        embed = discord.Embed(title='Daisy-Mae Session Queueing System', color=discord.Color.green())
        session_cmds = {
            'menu': 'This menu',
            'close': 'Close your session off from new guests. This does not end the session.',
            'open': 'Open your session back up to new guests.',
            'end': 'End your session. Any guests still in your queue will be notified.',
            'dodo `code`': 'Change your dodo code. This is helpful if your code has been leaked.',
            'show': 'Show your current group list.',

        }
        guest_cmds = {
            'guest_bans': 'Get a list of banned guests for your current session.',
            'guest_ban `@user`': 'Ban the mentioned guest from your current session. They will not be able to re-join '
                                 'even if you change your dodo code.',
            'guest_unban `@user`': 'Unban the mentioned user.',
            'guest_kick `@user`': 'Kick the mentioned user from your queue.'
        }
        messaging_cmds = {
            'notify `message`': 'Send a message to every guest in your queue.',
            'welcome `message`': 'Set or change your welcome message. Guests will see this when they join.'
        }
        embed.add_field(name='\u200b', value='```Session Management```', inline=False)
        for k, v in session_cmds.items():
            embed.add_field(name=f'> {prefix}{k}', value=v)
        embed.add_field(name='\u200b', value='```Guest Management```', inline=False)
        for k, v in guest_cmds.items():
            embed.add_field(name=f'> {prefix}{k}', value=v, inline=False)
        embed.add_field(name='\u200b', value='```Messaging```', inline=False)
        for k, v in messaging_cmds.items():
            embed.add_field(name=f'> {prefix}{k}', value=v)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role(701854792699347065)
    async def beta(self, ctx):
        options = f'Available options:\n' \
                  f'`bcreate`: start a new session'
        await ctx.send(embed=tools.single_embed(options, self.client.user.avatar_url))

    async def dms_embed(self, title, description):
        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)
        return embed

    @commands.command()
    @commands.has_role(701854792699347065)
    async def bcreate(self, ctx):
        """
        Create a DMS session and generate the wizard
        :param ctx:
        :return:
        """
        session_code = await tools.random_code()
        private_session = await tools.create_private_channel(ctx, ctx.author, session_code)
        if not private_session:
            msg = 'You already have an active Session Channel.'
            await ctx.send(embed=tools.single_embed_neg(msg))
            return
        msg = f'Your private Session Channel has been created: {private_session.mention}'
        notification = await ctx.send(embed=tools.single_embed(msg))

        msg = f'**Welcome to the Daisy-Mae Queue Wizard!**\n' \
              f':raccoon: Begin Turnip Session\n' \
              f':pig: Begin Daisy-Mae Session\n' \
              f':star: Begin Celeste Session\n\n' \
              f':x: Quit'
        msg = await private_session.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))

        await msg.add_reaction('🦝')
        await msg.add_reaction('🐷')
        await msg.add_reaction('⭐')
        await msg.add_reaction('❌')
        await asyncio.sleep(0)
        cache_msg = await private_session.fetch_message(msg.id)

        def check(react, user):
            return react.message.id == cache_msg.id and user.id == ctx.message.author.id

        while True:
            reaction, member = await self.client.wait_for('reaction_add', check=check)
            if reaction.emoji == '🦝':
                await msg.delete()
                await self.nook(ctx, private_session, session_code, notification)
            elif reaction.emoji == '🐷':
                await msg.delete()
                await self.daisymae(ctx, private_session, session_code, notification)
            elif reaction.emoji == '⭐':
                await msg.delete()
                await self.other_session(ctx, private_session, session_code, notification)
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

    async def nook(self, ctx, private_session, session_code, notification):
        """
        Create a nook session for turnip selling
        :param ctx:
        :param private_session: The host's private channel
        :param session_code: The host's randomly generated code
        :param notification: The notification message id and channel id
        :return:
        """
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        # get dodo code
        title = 'Turnip Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await prompt.delete()
        await msg.delete()

        # get nook buying price
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much are the Nooks buying for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        # get max groups
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f':exclamation: How many groups will you allow? *Note that more than 25 groups ' \
                      f'will only show the next 25 due to message length limitations.*'
        embed = await self.dms_embed(title + ' (3/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                max_groups = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        # get guests per group
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group?'
        embed = await self.dms_embed(title + ' (4/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                per_group = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        # get session instructions
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_message = msg.content
        await prompt.delete()
        await msg.delete()

        # grab an image
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Turnip sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)
        await prompt.delete()

        # prompt to post
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\nGuests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\nImage attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        prompt = await private_session.send(embed=embed)
        await prompt.add_reaction('✅')
        await asyncio.sleep(0)

        # sell channel usually timmy sell
        sell_channel = self.client.get_channel(694015832728010762)
        # sell_channel = self.client.get_channel(701258725385568307)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(1)
        while True:
            if reaction.emoji == '✅':
                msg = f'**{ctx.author.display_name}** has created a new **Turnip Session**!\n' \
                      f'Tap :raccoon: to join!\n\n' \
                      f'**Bell Price**: {turnip_price} bells\n'\
                      f'**Groups**: {max_groups}\n' \
                      f'**Players per Group**: {per_group}\n\n' \
                      f'**Message from the Host**: {session_message}'
                embed = discord.Embed(color=discord.Color.green(), description=msg)
                embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.set_image(url=img.url)
                posting = await sell_channel.send(embed=embed)
                await posting.add_reaction('🦝')
                await img_msg.delete()

                msg = f'Your session has been posted to {sell_channel.mention}'
                await private_session.send(embed=tools.single_embed(msg))
                break

        # write data
        session_file = 'sessions/nook.json'
        data = await tools.read_sessions(session_file)
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []

        data[session_code] = {
            "host": ctx.author.id,
            "session_notification": {
                "id": notification.id,
                "channel": notification.channel.id
            },
            "private_session": private_session.id,
            "ban_list": [],
            "message_id": posting.id,
            "queue_id": None,
            "dodo_code": dodo_code,
            "max_groups": max_groups,
            "members_per": per_group,
            "welcome": None,
            "groups": groups,
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=4)

        while True:
            await self.show_queue(host=ctx.author, session_file=session_file)

    async def daisymae(self, ctx, private_session, session_code, notification):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        title = 'Daisy-Mae Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much is Daisy selling for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f':exclamation:  How many groups will you allow? *Note that more than 25 groups ' \
                      f'will only show the next 25 due to message length limitations.*'
        embed = await self.dms_embed(title + ' (3/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                max_groups = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group?'
        embed = await self.dms_embed(title + ' (4/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                per_group = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_message = msg.content
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Daisy-Mae sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)
        await prompt.delete()

        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\nGuests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\nImage attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        prompt = await private_session.send(embed=embed)
        await prompt.add_reaction('✅')
        await asyncio.sleep(0)

        # daisy channel
        sell_channel = self.client.get_channel(694015696241164368)
        # sell_channel = self.client.get_channel(701258725385568307)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(1)
        posting = None
        if reaction.emoji == '✅':
            msg = f'**{ctx.author.display_name}** has created a new **Daisy-Mae Session**!\n' \
                  f'Tap :pig: to join!\n\n' \
                  f'**Daisy-Mae Price**: {turnip_price} bells\n' \
                  f'**Groups**: {max_groups}\n' \
                  f'**Players per Group**: {per_group}\n\n' \
                  f'**Message from the Host**: {session_message}'
            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_thumbnail(url=self.client.user.avatar_url)
            embed.set_image(url=img.url)
            posting = await sell_channel.send(embed=embed)
            await posting.add_reaction('🐷')
            await img_msg.delete()

            msg = f'Your session has been posted to {sell_channel.mention}'
            await private_session.send(embed=tools.single_embed(msg))

        # write data
        session_file = 'sessions/daisy.json'
        with open(session_file, 'r') as f:
            data = json.load(f)
        if posting is not None:
            posting = posting.id

        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []

        data[session_code] = {
            "host": ctx.author.id,
            "session_notification": {
                "id": notification.id,
                "channel": notification.channel.id
            },
            "private_session": private_session.id,
            "ban_list": [],
            "message_id": posting,
            "queue_id": None,
            "dodo_code": dodo_code,
            "max_groups": max_groups,
            "members_per": per_group,
            "welcome": None,
            "groups": groups,
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=4)

        while True:
            await self.show_queue(host=ctx.author, session_file=session_file)

    async def other_session(self, ctx, private_session, session_code, notification):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        title = 'Generic/Other Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: What kind of session is this? Some examples could be ' \
                      f'trading, Sahara, meteors, villagers, etc.'
        embed = await self.dms_embed(title + ' (2/6)', description)
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_type = int(msg.content)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{session_type}`\n' \
                      f':exclamation:  How many groups will you allow? *Note that more than 25 groups ' \
                      f'will only show the next 25 due to message length limitations.*'
        embed = await self.dms_embed(title + ' (3/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                max_groups = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{session_type}`\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group?'
        embed = await self.dms_embed(title + ' (4/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                per_group = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{session_type}`\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests. For generic sessions, this message is very important. Please be clear!'
        embed = await self.dms_embed(title + ' (5/6)', description)
        prompt = await private_session.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_message = msg.content
        await prompt.delete()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{session_type}`\n' \
                      f'Max Groups: `{max_groups}`\nGuests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture for your session.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        prompt = await private_session.send(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)
        await prompt.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{session_type}`\n' \
                      f'Max Groups: {max_groups}\nGuests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\nImage attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        prompt = await private_session.send(embed=embed)
        await prompt.add_reaction('✅')
        await asyncio.sleep(0)

        # sell channel
        # sell_channel = self.client.get_channel(694015696241164368)
        sell_channel = self.client.get_channel(701258725385568307)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(1)
        posting = None
        if reaction.emoji == '✅':
            msg = f'**{ctx.author.display_name}** has created a new generic session for **{session_type}**!\n' \
                  f'Tap :star: to join!\n\n' \
                  f'**Groups**: {max_groups}\n' \
                  f'**Players per Group**: {per_group}\n\n' \
                  f'**Message from the Host**: {session_message}'
            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_thumbnail(url=self.client.user.avatar_url)
            embed.set_image(url=img.url)
            posting = await sell_channel.send(embed=embed)
            await posting.add_reaction('⭐')
            await img_msg.delete()

            msg = f'Your session has been posted to {sell_channel.mention}'
            await private_session.send(embed=tools.single_embed(msg))

        # write data
        session_file = 'sessions/other.json'
        with open(session_file, 'r') as f:
            data = json.load(f)
        if posting is not None:
            posting = posting.id

        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []

        data[session_code] = {
            "host": ctx.author.id,
            "session_notification": {
                "id": notification.id,
                "channel": notification.channel.id
            },
            "private_session": private_session.id,
            "ban_list": [],
            "message_id": posting,
            "dodo_code": dodo_code,
            "max_groups": max_groups,
            "members_per": per_group,
            "welcome": None,
            "groups": groups,
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=4)

    # @commands.command()
    # async def bopen(self, ctx):
    #     """
    #     Open a closed session
    #     :param ctx:
    #     :return:
    #     """
    #     if not await self.is_host(ctx.author):
    #         msg = f'You cannot run this command if you are not hosting a Session.'
    #         await ctx.send(embed=tools.single_embed_neg(msg))
    #         return
    #
    #     data = await tools.read_sessions()
    #     session_code = await self.get_session_code(ctx.author)
    #     notification = data[session_code]['notification']
    #     data[session_code]['closed'] = False
    #     await tools.write_sessions(data)
    #
    #     channel = self.client.get_channel(data[session_code]['session'])
    #     await channel.send(embed=tools.single_embed(f'Your session has been **reopened** to new guests.'))
    #     msg = f'Private Session **closed**.'
    #     await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)
    #
    #     # edit sell embed if available
    #     msg = f'Session **{session_code}** has **reopened**.'
    #     await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)

    # @commands.command()
    # @commands.has_permissions(manage_channels=True)
    # async def badmin_end(self, ctx, session_code):
    #     """
    #     Close a session and prevent guests from joining
    #     :param ctx:
    #     :param session_code:
    #     :return:
    #     """
    #     data = await tools.read_sessions()
    #     try:
    #         data[session_code]
    #     except KeyError:
    #         await ctx.send(embed=tools.single_embed(f'That session does not exist.'))
    #         return
    #
    #     notification = data[session_code]['notification']
    #     data[session_code]['closed'] = True
    #     await tools.write_sessions(data)
    #
    #     channel = self.client.get_channel(data[session_code]['session'])
    #     await tools.close_private_channel(channel)
    #     msg = f'Private Session **ended**.'
    #     await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)
    #
    #     # edit sell embed if available
    #     try:
    #         msg = f'Session **{session_code}** has **ended**.'
    #         await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)
    #     except Exception as e:
    #         print(e, ' ending session ' + session_code)
    #
    #     del data[session_code]
    #     await tools.write_sessions(data)

    # @commands.command()
    # async def bclose(self, ctx):
    #     """
    #     Close a session and prevent guests from joining
    #     :param ctx:
    #     :return:
    #     """
    #     if not await self.is_host(ctx.author):
    #         await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
    #         return
    #
    #     data = await tools.read_sessions()
    #     session_code = await self.get_session_code(ctx.author)
    #     notification = data[session_code]['notification']
    #     data[session_code]['closed'] = True
    #     await tools.write_sessions(data)
    #
    #     channel = self.client.get_channel(data[session_code]['session'])
    #     await channel.send(embed=tools.single_embed(f'Your session has been **closed** to new guests.'))
    #     msg = f'Private Session **closed**.'
    #     await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)
    #
    #     # edit sell embed if available
    #     msg = f'Session **{session_code}** is currently **closed**.'
    #     await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)

    # @commands.command()
    async def bend(self, host, session_file):
        """
        End a session
        :param host: member object
        :param session_file:
        :return:
        """
        # if not await self.is_host(ctx.author):
        #     await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
        #     return
        print(type(host))
        print(inspect.stack()[1][3])
        print('bend')

        data = await tools.read_sessions(session_file)

        session_to_close = []
        for session_code, value in data.items():
            if value['host'] == host.id:
                session_to_close.append(session_code)
                channel = self.client.get_channel(value['private_session'])

                # edit private session notification if available
                msg = f'Private Session **closed**.'
                await tools.edit_msg(
                    self.client.get_channel(value['session_notification']['channel']),
                    value['session_notification']['id'],
                    msg, delete_after=30
                )
                if channel is not None:
                    await tools.close_private_channel(channel)

                # edit sell embed if available
                try:
                    msg = f'Session **{session_code}** has **ended**.'
                    await tools.edit_msg(
                        self.client.get_channel(_dms_channel),
                        value['message_id'],
                        msg, delete_after=30
                    )
                except KeyError:
                    pass

                try:
                    groups = data[session_code]['groups']
                    for place, member_list in groups.items():
                        for uid in member_list:
                            member = self.client.get_user(uid)
                            msg = f'Session **{session_code}** was **ended** by the host.'
                            await member.send(embed=tools.single_embed(msg))
                except KeyError:
                    pass

        print(session_to_close)
        for code in session_to_close:
            del data[code]
            await tools.write_sessions(data, session_file)

    async def get_session_channel(self, member, session_file):
        """

        :param member:
        :param session_file:
        :return:
        """
        data = await tools.read_sessions(session_file)
        for k, v in data.items():
            if v['host'] == member.id:
                return self.client.get_channel(v['private_session'])

    @staticmethod
    async def get_session_code(member, session_file):
        """
        :param member:  member object
        :param session_file:
        :return:
        """
        print(session_file)
        data = await tools.read_sessions(session_file)
        for session_code, values in data.items():
            if values['host'] == member.id:
                return session_code

    @staticmethod
    def to_upper(argument):
        return argument.upper()

    @commands.command()
    async def bleave(self, ctx, session_code):
        session_code = session_code.upper()
        session_files = ['sessions/nook.json',
                         'sessions/daisy.json']
        for session_file in session_files:
            data = await tools.read_sessions(session_file)
            for k, v in data.items():
                if k == session_code:
                    groups = data[session_code]['groups']
                    host = discord.utils.get(ctx.guild.members, id=v['host'])
                    private_channel = await self.get_session_channel(host, session_file)
                    for place, member_list in groups.items():
                        if ctx.author.id in member_list:
                            member_list.remove(ctx.author.id)
                            await ctx.author.send(embed=tools.single_embed(f'You have left **Session {session_code}**.'))
                            msg = f'{ctx.author.display_name} has **left** your queue.'
                            await private_channel.send(embed=tools.single_embed(msg), delete_after=5)
                            await tools.write_sessions(data, session_file)
                            await self.show_queue(host=host, session_file=session_file)
                            return

    async def bsend(self, host, session_file):
        """
        Send a dodo code to the next group in a DMS queue
        :param host: a member object
        :param session_file:
        :return:
        """
        print(inspect.stack()[1][3])
        print(type(host))
        data = await tools.read_sessions(session_file)
        session_code = await self.get_session_code(host, session_file)
        private_channel = await self.get_session_channel(host, session_file)

        # welcome = data[session_code]['welcome']
        groups = data[session_code]['groups']
        place = list(groups.keys())[0]
        msg = await private_channel.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'), delete_after=5)
        await private_channel.fetch_message(msg.id)

        if len(data[session_code]['groups'][place]) < 1:
            await private_channel.send(embed=tools.single_embed(f'**Group {place}** is empty.'), delete_after=5)
        else:
            for user in data[session_code]['groups'][place]:
                try:
                    member = self.client.get_user(int(user))
                    if member is None:
                        continue
                    msg = f'You have gotten your Session Code for **{host.display_name}\'s** Session!\n' \
                          f'Please do not forget to leave a review for your host when you finish.\n'\
                          f'**Dodo Code**: `{data[session_code]["dodo_code"]}`\n'
                    # if welcome is not None:
                    #     msg += f'\n\n**Your host left you a message!**\n"{welcome}"'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                    # await cache_msg.edit(embed=tools.single_embed(f'Dodo code sent to **Group {place}**'), delete_after=5)
                except Exception as e:
                    # await cache_msg.edit(embed=tools.single_embed(f'Dodo code could not be sent to **Group {place}**'), delete_after=30)
                    print(f'an error occurred when sending a dodo code: {e}')
            del data[session_code]['groups'][place]
            await tools.write_sessions(data=data, sessions=session_file)

            # notify groups that they have moved up
            for place, member_list in groups.items():
                for uid in member_list:
                    member = self.client.get_user(uid)
                    if member is None:
                        continue
                    position = list(groups.keys()).index(place) + 1
                    msg = f'Your group in **Session {session_code}** has moved up! \n' \
                          f'You are now in **Position** `{position}` of `{len(list(groups.keys()))}`.'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))

    async def show_queue(self, host, session_file):
        """
        Show current groups and guests. Usually called after a host action but can be triggered by
        join or leave which requires the host arg
        :param session_file: the session type
        :param host: a member object
        :return:
        """
        print(inspect.stack()[1][3])
        print(type(host))
        data = await tools.read_sessions(session_file)
        session_code = await self.get_session_code(host, session_file)
        if session_code is None:
            return
        private_channel = await self.get_session_channel(host, session_file)

        if data[session_code]['queue_id'] is None:
            pass
        else:
            print(data[session_code]['queue_id'])
            print('get cacge')
            print('priv channel', private_channel)
            queue_id = data[session_code]['queue_id']
            cache_msg = await private_channel.fetch_message(id=queue_id)
            print(cache_msg)
            await cache_msg.delete()
        while True:
            print(1)
            # grab session data
            data = await tools.read_sessions(session_file)
            session_code = await self.get_session_code(host, session_file)
            if session_code is None:
                return
            private_channel = await self.get_session_channel(host, session_file)

            groups = data[session_code]['groups']
            per_group = data[session_code]['members_per']

            print(1)
            if len(data[session_code]['groups'].keys()) < 1:
                msg = f'You are at the end of your groups. Consider starting a new session.'
                await private_channel.send(embed=tools.single_embed(msg))
                return

            embed = discord.Embed(title=f'Your Queue', color=discord.Color.green())
            embed.set_thumbnail(url=self.client.user.avatar_url)

            print(1)
            for place, group in groups.items():
                members = []
                if len(group) == 0:
                    group = None
                    place = f'Group {place} (0/{per_group})'
                else:
                    for uid in group:
                        member = discord.utils.get(host.guild.members, id=uid)
                        if member is None:
                            continue
                        else:
                            reviewer_rank = await tools.get_reviewer_rank(db.get_reviews_given(member))
                            members.append(f'{member.mention} (rank: *{reviewer_rank}*)')
                        # members.append(f'{member.mention}')
                if group is not None:
                    group = '\n'.join(members)
                    place = f'Group {place} ({len(members)}/{per_group})'
                embed.add_field(name=f'{place}', value=group)
                # embed.add_field(name=f'{place}', value=group, inline=False)

            # show options
            def check_react(react, user):
                return react.message.id == queue.id and user.id == host.id
            options = '```\nOptions```\n' \
                      '➡ Send Dodo code to the next group\n' \
                      '⏹ End session'
            embed.add_field(name='\u200b', value=options, inline=False)
            queue = await private_channel.send(embed=embed)

            # update queue id
            data[session_code]['queue_id'] = queue.id
            await tools.write_sessions(data, session_file)

            await queue.add_reaction('➡')
            # await queue.add_reaction('🔁')
            await queue.add_reaction('⏹')
            reaction, member = await self.client.wait_for('reaction_add', check=check_react)
            if reaction.emoji == '➡':
                await queue.delete()
                await self.bsend(host, session_file)
            if reaction.emoji == '🔁':
                await private_channel.send('auto on')
            if reaction.emoji == '⏹':
                confirm = await private_channel.send(embed=tools.single_embed('Are you sure you want to end your session?'))
                await asyncio.sleep(0)
                await confirm.add_reaction('🇾')
                await confirm.add_reaction('🇳')
                await asyncio.sleep(0)

                def check_react(react, user):
                    return react.message.id == confirm.id and user.id == host.id
                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                if reaction.emoji == '🇾':
                    await self.bend(host, session_file)
                if reaction.emoji == '🇳':
                    await confirm.delete()

    async def promote(self, session_code):
        """
        Notify groups in a queue that they have moved up one position
        :param session_code:
        :return:
        """
        data = await tools.read_sessions()
        groups = data[session_code]['groups']
        members_per_group = data[session_code]['members per group']
        not_filled = None
        user_to_move = None

        for place, member_list in groups.items():
            # find an unfilled list
            if len(member_list) < members_per_group and not_filled is None:
                not_filled = place
            # if a list isn't full, find the first member in the next list
            if not_filled is not None and len(member_list) > 0:
                user_to_move = member_list[0]
            if not_filled is not None and user_to_move is not None:
                data[session_code]['groups'][not_filled] = user_to_move
                member = self.client.get_user(user_to_move)
                await member.send(f'You have been moved up to **Group {not_filled}**!')
                await tools.write_sessions(data)

    async def is_host(self, member, session_file=None):
        print(member, session_file)
        session_code = await self.get_session_code(member, session_file)
        if session_code is not None:
            return True
        return False

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        reactions = ['🦝', '🐷', '⭐']

        # match raccoon
        if reaction.emoji == reactions[0]:
            session_file = 'sessions/nook.json'
            data = await tools.read_sessions(session_file)
            for session_code in data:
                if data[session_code]['message_id'] == reaction.message.id:
                    if await self.is_host(user, session_file=session_file):
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == data[session_code]['host']:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = data[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = data[session_code]['open']
                    if user.id != 193416878717140992:
                    # if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in data[session_code]['groups'].items():
                        if user.id in group:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = data[session_code]['members_per']
                    for place, group in data[session_code]['groups'].items():
                        if len(group) < members_per_group:
                            group.append(user.id)
                            prefix = await self.show_prefix(reaction)
                            msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                                  f'You can use `{prefix}leave {session_code}` at any time to leave this Session. Be ' \
                                  f'aware that the Session Code is not the host\'s Dodo code.'
                            await user.send(embed=tools.single_embed(msg))
                            msg = f'**{user.mention}** has joined **Group {place}**.'
                            dms = self.client.get_channel(data[session_code]['private_session'])
                            await dms.send(embed=tools.single_embed(msg), delete_after=5)
                            await tools.write_sessions(data, 'sessions/nook.json')
                            host = discord.utils.get(reaction.message.guild.members, id=data[session_code]['host'])
                            print('host', host)
                            await self.show_queue(host=host, session_file='sessions/nook.json')
                            return

                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))

        # match pig
        elif reaction.emoji == reactions[1]:
            session_file = 'sessions/daisy.json'
            data = await tools.read_sessions(session_file)
            for session_code in data:
                if data[session_code]['message_id'] == reaction.message.id:
                    if await self.is_host(user, session_file):
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == data[session_code]['host']:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = data[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = data[session_code]['open']
                    if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in data[session_code]['groups'].items():
                        if user.id in group:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = data[session_code]['members_per']
                    for place, group in data[session_code]['groups'].items():
                        if len(group) < members_per_group:
                            group.append(user.id)
                            prefix = await self.show_prefix(reaction)
                            msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                                  f'You can use `{prefix}leave {session_code}` at any time to leave this Session. Be ' \
                                  f'aware that the Session Code is not the host\'s Dodo code.'
                            await user.send(embed=tools.single_embed(msg))
                            msg = f'**{user.mention}** has joined **Group {place}**.'
                            dms = self.client.get_channel(data[session_code]['private_session'])
                            await dms.send(embed=tools.single_embed(msg), delete_after=5)
                            await tools.write_sessions(data, 'sessions/daisy.json')
                            host = discord.utils.get(reaction.message.guild.members, id=data[session_code]['host'])
                            await self.show_queue(host=host, session_file='sessions/daisy.json')
                            return

                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))

        # match star
        elif reaction.emoji == reactions[2]:
            return

    @commands.command()
    @commands.is_owner()
    async def supporter(self, ctx, member: discord.Member):
        mae_supporter = ctx.guild.get_role(701854792699347065)
        await member.add_roles(mae_supporter, reason='For donating and supporting Mae\'s ongoing development!')
        msg = f'You\'ve been give the role **{mae_supporter.name}** for supporting {self.client.user.display_name}\'s '\
              f'continued development. Thank you so much! You now have access to the Mae-Supporter channel!'
        await member.send(embed=tools.single_embed(msg, self.client.user.avatar_url))
        await ctx.send(embed=tools.single_embed('Message sent!'))



def setup(client):
    client.add_cog(BetaFeatures(client))
