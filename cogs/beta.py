import asyncio
import inspect
import json
import discord
import aiohttp
import util.tools as tools
import util.db as db
from discord.ext import commands, tasks

mae_banner = 'https://i.imgur.com/HffuudZ.jpg'
turnip = 'https://i.imgur.com/wl2MZIV.png'
_turnip_emoji = 694822764699320411


class BetaFeatures(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.sessions = {}
        with open('sessions/session.json', 'r') as f:
            self.sessions = json.load(f)
        # self.loop_file_write.start()

    @commands.command()
    @commands.is_owner()
    async def clean(self, ctx):
        self.sessions = {}
        with open('sessions/session.json', 'w') as f:
            json.dump(self.sessions, f, indent=4)
        print('sessions overwritten')

    @staticmethod
    async def show_prefix(guild):
        prefix = db.get_prefix(guild)[0]
        return prefix

    @commands.command()
    @commands.has_any_role('mae-supporters', 'ADMIN', 'Merch Dept.', 'TECHNICIAN')
    async def beta(self, ctx):
        options = f'Available options:\n' \
                  f'`bcreate`: start a new session\n' \
                  f'`bleave`: see what queues you are in and pick a reaction to leave \n' \
                  f'`ac` predict future Turnip prices (`ac mon_am_price mon_pm_price tues_am_price ...)`\n' \
                  f'`pfp @member` see a member\'s profile picture in all it\'s glory'
        await ctx.send(embed=tools.single_embed(options, self.client.user.avatar_url))

    async def dms_embed(self, title, description):
        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)
        return embed

    @staticmethod
    async def in_blacklist(guild, content):
        blacklist = db.get_blacklist(guild)
        offending_words = [i for i in content if i in blacklist]
        if len(offending_words) > 0:
            return offending_words
        else:
            return False

    @commands.command()
    @commands.has_any_role('mae-supporters', 'ADMIN', 'Merch Dept.', 'TECHNICIAN')
    async def pfp(self, ctx, member: discord.Member):
        embed = discord.Embed(title=f'{member.display_name}\'s Avatar', color=member.color)
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)

    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.text()

    @commands.command()
    @commands.has_any_role('mae-supporters', 'ADMIN', 'Merch Dept.', 'TECHNICIAN')
    async def ac(self, ctx, *args):
        async with aiohttp.ClientSession() as session:
            url = 'https://api.ac-turnip.com/data/?f='
            for a in args:
                url += f'{a}-'
            f = await self.fetch(session, url)
            values = json.loads(f)
            await ctx.send(values['preview'])

    @staticmethod
    async def create_private_channel(ctx, member):
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True)
        }

        channel_name = str(member.id) + '_session'
        # if discord.utils.get(ctx.guild.text_channels, name=channel_name) is not None:
        #     return False
        category = discord.utils.get(ctx.guild.channels, id=697086444082298911)
        private_channel = await ctx.guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)
        msg = f'Welcome, {member.mention}! This is your private Session.'
        await private_channel.send(embed=tools.single_embed(msg))
        return private_channel

    @commands.command()
    @commands.has_any_role(701854792699347065, 'ADMIN')
    async def bcreate(self, ctx):
        """
        Create a DMS session and generate the wizard
        :param ctx:
        :return:
        """
        # if ctx.author.id != 193416878717140992:
        #     await ctx.send(embed=tools.single_embed(f'Sorry, the beta is closed at the moment.'))
        # session_code = await tools.random_code()
        private_session = await self.create_private_channel(ctx, ctx.author)
        if not private_session:
            msg = 'You already have an active Session Channel.'
            await ctx.send(embed=tools.single_embed_neg(msg))
            return
        msg = f'Your private Session Channel has been created: {private_session.mention}'
        notification = await ctx.send(embed=tools.single_embed(msg))

        msg = f'**Welcome to the Daisy-Mae Queue Wizard!**\n' \
              f':raccoon: Create Turnip Session\n' \
              f':pig: Create Daisy-Mae Session\n' \
              f':star: Create Catalogue Session\n\n' \
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
                await msg.clear_reactions()
                await self.nook(ctx, private_session, notification, cache_msg)
            elif reaction.emoji == '🐷':
                await msg.clear_reactions()
                await self.daisymae(ctx, private_session, notification, cache_msg)
            elif reaction.emoji == '⭐':
                await msg.clear_reactions()
                await self.other_session(ctx, private_session, notification, cache_msg)
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

    async def nook(self, ctx, private_session, notification, prompt):
        """
        Create a nook session for turnip selling
        :param ctx:
        :param private_session: The host's private channel
        :param notification: The notification message id and channel id
        :param prompt:
        :return:
        """
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        # get dodo code
        title = 'Turnip Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content
        await msg.delete()

        # get nook buying price
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much are the Nooks buying for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f':exclamation: How much are the Nooks buying for?\n' \
                              f':exclamation: Positive integers only'
                embed = await self.dms_embed(title + ' (2/6)', description)
                await prompt.edit(embed=embed)
        await msg.delete()

        # get max groups
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    break
                else:
                    await msg.delete()
                    description = f'Dodo Code: `{dodo_code}`\n' \
                                  f'Turnip Price: `{turnip_price}` bells\n' \
                                  f':exclamation: How many groups will you allow? (max 20)\n' \
                                  f':exclamation: Enter positive integers only between 1 and 20.'
                    embed = await self.dms_embed(title + ' (3/6)', description)
                    await prompt.edit(embed=embed)
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Turnip Price: `{turnip_price}` bells\n' \
                              f':exclamation: How many groups will you allow? (max 20)\n' \
                              f':exclamation: Enter positive integers only between 1 and 20.'
                embed = await self.dms_embed(title + ' (3/6)', description)
                await prompt.edit(embed=embed)
        await msg.delete()

        # get guests per group
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    description = f'Dodo Code: `{dodo_code}`\n' \
                                  f'Turnip Price: `{turnip_price}` bells\n' \
                                  f'Max Groups: `{max_groups}`\n' \
                                  f':exclamation: How many guests per group? (max 7)' \
                                  f':exclamation: Enter positive integers only between 1 and 7.'
                    embed = await self.dms_embed(title + ' (3/6)', description)
                    await prompt.edit(embed=embed)
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Turnip Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f':exclamation: How many guests per group? (max 7)' \
                              f':exclamation: Enter positive integers only between 1 and 7.'
                embed = await self.dms_embed(title + ' (3/6)', description)
                await prompt.edit(embed=embed)

        # get session instructions
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.content) > 0:
                session_message = msg.content
                await msg.delete()
                break
            else:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Turnip Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f'Guests per Group: `{per_group}`\n' \
                              f':exclamation: Please enter a session message. Use this to give instructions to ' \
                              f'your guests.\n' \
                              f':exclamation: Session messages cannot be empty.'
                embed = await self.dms_embed(title + ' (5/6)', description)
                await prompt.edit(embed=embed)

        # grab an image
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Turnip sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        await prompt.edit(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Turnip Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f'Guests per Group: `{per_group}`\n' \
                              f'Session Message: `{session_message}`\n' \
                              f':exclamation: Please attach a picture of your Turnip sale price.\n' \
                              f':exclamation: Images only, please.'
                embed = await self.dms_embed(title + ' (6/6)', description)
                await prompt.edit(embed=embed)

        # prompt to post
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\n' \
                      f'Guests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\n' \
                      f'Image attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it or ❌ to cancel.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        await prompt.edit(embed=embed)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        await asyncio.sleep(0)

        # sell channel usually timmy sell
        sell_channel = self.client.get_channel(694015832728010762)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(0)
        while True:
            if reaction.emoji == '✅':
                msg = f'**{ctx.author.display_name}** has created a new **Turnip Session**!\n' \
                      f'Tap :raccoon: to join!\n' \
                      f'**Groups**: {max_groups}\n' \
                      f'**Players per Group**: {per_group}\n\n' \
                      f'**Message from the Host**: {session_message}'
                embed = discord.Embed(
                    title=f'**Turnip Sell Price**: {turnip_price} bells!',
                    color=discord.Color.green(),
                    description=msg)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_image(url=img.url)
                posting = await sell_channel.send(embed=embed)
                await posting.add_reaction('🦝')

                msg = f'Your session has been posted to {sell_channel.mention}'
                await private_session.send(embed=tools.single_embed(msg))
                await img_msg.delete()
                break
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        self.sessions[ctx.author.id] = {
            "type": "nook",
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
            "groups": groups,
            "open": True
        }

        # write to local  storage
        await self.write_session()
        await self.show_queue(host=ctx.author)

    async def daisymae(self, ctx, private_session, notification, prompt):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        title = 'Daisy-Mae Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content
        await msg.delete()

        # get sale price
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much is Daisy selling for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                await msg.delete()
                break
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f':exclamation: How much is Daisy selling for\n' \
                              f':exclamation: Positive integers only'
                embed = await self.dms_embed(title + ' (2/6)', description)
                await prompt.edit(embed=embed)
            await msg.delete()

        # get max groups
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    description = f'Dodo Code: `{dodo_code}`\n' \
                                  f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                                  f':exclamation: How many groups will you allow? (max 20)\n' \
                                  f':exclamation: Enter positive integers only between 1 and 20.'
                    embed = await self.dms_embed(title + ' (3/6)', description)
                    await prompt.edit(embed=embed)
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                              f':exclamation: How many groups will you allow? (max 20)\n' \
                              f':exclamation: Enter positive integers only between 1 and 20.'
                embed = await self.dms_embed(title + ' (3/6)', description)
                await prompt.edit(embed=embed)
        await msg.delete()

        # guests per group
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    description = f'Dodo Code: `{dodo_code}`\n' \
                                  f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                                  f'Max Groups: `{max_groups}`\n' \
                                  f':exclamation: How many guests per group? (max 7)\n' \
                                  f':exclamation: Enter positive integers only between 1 and 7.'
                    embed = await self.dms_embed(title + ' (3/6)', description)
                    await prompt.edit(embed=embed)
            except ValueError:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f':exclamation: How many guests per group? (max 7)\n' \
                              f':exclamation: Enter positive integers only between 1 and 7.'
                embed = await self.dms_embed(title + ' (3/6)', description)
                await prompt.edit(embed=embed)

        # get session instructions
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.content) > 0:
                session_message = msg.content
                await msg.delete()
                break
            else:
                await msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f'Guests per Group: `{per_group}`\n' \
                              f':exclamation: Please enter a session message. Use this to give instructions to ' \
                              f'your guests.\n' \
                              f':exclamation: Session messages cannot be empty.'
                embed = await self.dms_embed(title + ' (5/6)', description)
                await prompt.edit(embed=embed)

        # grab an image
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Daisy-Mae sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        await prompt.edit(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                description = f'Dodo Code: `{dodo_code}`\n' \
                              f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                              f'Max Groups: `{max_groups}`\n' \
                              f'Guests per Group: `{per_group}`\n' \
                              f'Session Message: `{session_message}`\n' \
                              f':exclamation: Please attach a picture of your Daisy-Mae sale price.\n' \
                              f':exclamation: Images only, please.'
                embed = await self.dms_embed(title + ' (6/6)', description)
                await prompt.edit(embed=embed)

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\n' \
                      f'Guests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\n' \
                      f'Image attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        prompt = await private_session.send(embed=embed)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        await asyncio.sleep(0)

        # daisy channel
        sell_channel = self.client.get_channel(694015696241164368)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(0)
        while True:
            if reaction.emoji == '✅':
                msg = f'**{ctx.author.display_name}** has created a new **Daisy-Mae Session**!\n' \
                      f'Tap :pig: to join!\n' \
                      f'**Groups**: {max_groups}\n' \
                      f'**Players per Group**: {per_group}\n\n' \
                      f'**Message from the Host**: {session_message}'
                embed = discord.Embed(title=f'**Turnip Buy Price**: {turnip_price} bells!',
                                      color=discord.Color.green(), description=msg)
                # embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_image(url=img.url)
                posting = await sell_channel.send(embed=embed)
                await posting.add_reaction('🐷')
                await img_msg.delete()

                msg = f'Your session has been posted to {sell_channel.mention}'
                await private_session.send(embed=tools.single_embed(msg))
                break
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        self.sessions[ctx.author.id] = {
            "type": "daisy",
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
            "open": True
        }

        # write to local  storage
        await self.write_session()
        await self.show_queue(host=ctx.author)

    async def other_session(self, ctx, private_session, notification, prompt):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        title = 'Catalogue'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: Enter a #channel where your session will be posted.'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.channel_mentions) > 0:
                posting_channel = msg.channel_mentions[0]
                if posting_channel.permissions_for(ctx.author).read_messages is True:
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    msg = f'You do not have permission to post in that channel'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=3)
            else:
                await msg.delete()
                msg = f'Please enter a valid channel mention.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=3)

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 20.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 20.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    await msg.delete()
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 7.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 7.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests. For generic sessions, this message is very important. Please be clear!'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_message = msg.content
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture for your session.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        await prompt.edit(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f'Image attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        await prompt.edit(embed=embed)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        await asyncio.sleep(0)

        # sell channel
        sell_channel = self.client.get_channel(posting_channel.id)
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        await asyncio.sleep(0)
        while True:
            if reaction.emoji == '✅':
                msg = f'**{ctx.author.display_name}** has created a new **Catalogue** session!\n' \
                      f'Tap :star: to join!\n\n' \
                      f'**Groups**: {max_groups}\n' \
                      f'**Players per Group**: {per_group}\n\n' \
                      f'**Message from the Host**: {session_message}'
                embed = discord.Embed(color=discord.Color.green(), description=msg)
                # embed.set_thumbnail(url=self.client.user.avatar_url)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_image(url=img.url)
                posting = await sell_channel.send(embed=embed)
                await posting.add_reaction('⭐')
                await img_msg.delete()

                msg = f'Your session has been posted to {sell_channel.mention}'
                await private_session.send(embed=tools.single_embed(msg))
                break
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        self.sessions[ctx.author.id] = {
            "type": "other",
            "session_notification": {
                "id": notification.id,
                "channel": notification.channel.id
            },
            "private_session": private_session.id,
            "ban_list": [],
            "message_id": posting.id,
            "sell_channel": sell_channel.id,
            "queue_id": None,
            "dodo_code": dodo_code,
            "max_groups": max_groups,
            "members_per": per_group,
            "welcome": None,
            "groups": groups,
            "open": True
        }

        await self.show_queue(host=ctx.author)

    async def bend(self, host):
        """
        End a session
        :param host: member object
        :return:
        """
        post_chans = {
            'nook': 694015832728010762,
            'daisy': 694015696241164368
            }
        session_to_close = None
        for session_code, value in self.sessions.items():
            if int(session_code) == host.id:
                session_to_close = session_code
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
                    if self.sessions[session_code]['type'] == 'other':
                        sell_channel = self.sessions[session_code]['sell_channel']
                    else:
                        sell_channel = post_chans.get(self.sessions[session_code]['type'])
                    await tools.edit_msg(
                        self.client.get_channel(sell_channel),
                        value['message_id'],
                        msg, delete_after=30
                    )
                except KeyError as e:
                    print(e)
                    pass

                groups = self.sessions[session_code]['groups']
                for place, member_list in groups.items():
                    for uid in member_list:
                        member = self.client.get_user(uid)
                        if member is None:
                            continue
                        try:
                            msg = f'Session **{session_code}** was **ended** by the host.'
                            await member.send(embed=tools.single_embed(msg))
                        except discord.Forbidden:
                            msg = f'Guest **{member.display_name}** could not be notified'
                            await host.send(embed=tools.single_embed(msg))
        self.sessions.pop(session_to_close, host.id)
        await self.write_session()

    async def get_session_channel(self, member):
        """

        :param member:
        :return:
        """
        print(inspect.stack()[0][3])
        for session_code, v in self.sessions.items():
            if int(session_code) == member.id:
                return self.client.get_channel(int(v['private_session']))

    async def get_session_code(self, member):
        """
        :param member:  member object
        :return:
        """
        print(inspect.stack()[0][3])

        for session_code, values in self.sessions.items():
            if int(session_code) == member.id:
                return session_code

    @staticmethod
    def to_upper(argument):
        return argument.upper()

    @commands.command()
    async def bleave(self, ctx):
        sessions_member_is_in = []
        for session_code, values in self.sessions.items():
            groups = self.sessions[session_code]['groups']
            _type = self.sessions[session_code]['type']
            for place, member_list in groups.items():
                if ctx.author.id in member_list:
                    host = discord.utils.get(ctx.guild.members, id=int(session_code))
                    sessions_member_is_in.append((_type, session_code, host))
        while True:
            if len(sessions_member_is_in) < 1:
                await ctx.send(embed=tools.single_embed('You are not in any sessions.'))
                return
            else:
                reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '⏩', '⏹']
                session_list = [f'{sessions_member_is_in.index(s)+1}. {s[0]} - {s[2].display_name}\'s session ({s[1]})' for s in sessions_member_is_in]
                title = 'Which session do you want to leave?'
                embed = discord.Embed(title=title, description='\n'.join(session_list), color=discord.Color.green())
                prompt = await ctx.send(embed=embed)
                for i in range(len(sessions_member_is_in)):
                    await prompt.add_reaction(reactions[i])
                await prompt.add_reaction('⏹')

                def check_react(react, user):
                    return react.message.id == prompt.id and user.id == ctx.author.id

                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                session_left = None
                if reaction.emoji == reactions[0]:
                    session_left = sessions_member_is_in[0][1]
                if reaction.emoji == reactions[1]:
                    session_left = sessions_member_is_in[1][1]
                if reaction.emoji == reactions[2]:
                    session_left = sessions_member_is_in[2][1]
                if reaction.emoji == reactions[3]:
                    session_left = sessions_member_is_in[3][1]
                if reaction.emoji == reactions[4]:
                    session_left = sessions_member_is_in[4][1]
                if reaction.emoji == reactions[5]:
                    session_left = sessions_member_is_in[5][1]
                if reaction.emoji == reactions[6]:
                    session_left = sessions_member_is_in[6][1]
                if reaction.emoji == reactions[7]:
                    session_left = sessions_member_is_in[7][1]
                if reaction.emoji == reactions[8]:
                    session_left = sessions_member_is_in[8][1]
                if reaction.emoji == reactions[9]:
                    session_left = sessions_member_is_in[9][1]
                if reaction.emoji == reactions[10]:
                    del sessions_member_is_in[:10]
                    await prompt.delete()
                    continue
                if reaction.emoji == '⏹':
                    await prompt.delete()
                    return

                for session_code, values in self.sessions.items():
                    if session_code == session_left:
                        for place, member_list in self.sessions[session_code]['groups'].items():
                            if ctx.author.id in member_list:
                                self.sessions[session_code]['groups'][place].remove(ctx.author.id)
                                msg = f'You have left Session {session_code}.'
                                await ctx.send(embed=tools.single_embed(msg), delete_after=5)
                                msg = f'**{ctx.author.mention}** has left your queue.'
                                # host = self.client.get_user(int(session_code))
                                host = discord.utils.get(ctx.guild.members, id=int(session_code))
                                private_channel = await self.get_session_channel(host)
                                await private_channel.send(embed=tools.single_embed_neg(msg), delete_after=5)
                                await prompt.delete()
                                await self.show_queue(host)
                                await self.write_session()
                                return
                await prompt.delete()

            # move everyone up in the queue

    async def bsend(self, host):
        """
        Send a dodo code to the next group in a DMS queue
        :param host: a member object
        :return:
        """
        session_code = await self.get_session_code(host)
        private_channel = await self.get_session_channel(host)

        groups = self.sessions[session_code]['groups']
        place = list(groups.keys())[0]
        msg = await private_channel.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'), delete_after=5)
        await private_channel.fetch_message(msg.id)

        if len(self.sessions[session_code]['groups'][place]) < 1:
            await private_channel.send(embed=tools.single_embed(f'**Group {place}** is empty.'), delete_after=5)
        else:
            for user in self.sessions[session_code]['groups'][place]:
                try:
                    member = self.client.get_user(int(user))
                    if member is None:
                        continue
                    msg = f'You have gotten your Session Code for **{host.display_name}\'s** Session!\n' \
                          f'Please do not forget to leave a review for your host when you finish.\n'\
                          f'**Dodo Code**: `{self.sessions[session_code]["dodo_code"]}`\n'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                except Exception as e:
                    print(f'an error occurred when sending a dodo code: {e}')
            del self.sessions[session_code]['groups'][place]

            # notify groups that they have moved up
            for place, member_list in groups.items():
                for uid in member_list:
                    member = self.client.get_user(uid)
                    if member is None:
                        continue
                    position = list(groups.keys()).index(place) + 1
                    msg = f'Your group in **Session {session_code}** has moved up! \n'
                    if int(position) == 1:
                        msg += f'You are next in line! Please wait for your Dodo Code.'
                    else:
                        msg += f'You are now in **Position** `{position}` of `{len(list(groups.keys()))}`.'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))

    async def show_queue(self, host, remove_reaction=None):
        """
        Show current groups and guests. Usually called after a host action but can be triggered by
        join or leave which requires the host arg
        :param host: a member object
        :param remove_reaction:
        :return:
        """
        # read to session_type
        session_code = await self.get_session_code(host)
        if session_code is None:
            return
        private_channel = await self.get_session_channel(host)
        print(private_channel)

        groups = self.sessions[session_code]['groups']
        per_group = self.sessions[session_code]['members_per']

        if len(self.sessions[session_code]['groups'].keys()) < 1:
            msg = f'You are at the end of your groups. Please end your session and consider starting a new session.'
            await private_channel.send(embed=tools.single_embed(msg))
            return

        dodo_code = self.sessions[session_code]['dodo_code']
        status = self.sessions[session_code]['open']
        if status is True:
            status = 'Open'
        else:
            status = 'Closed'
        description = f'Status: {status}\n Dodo Code: {dodo_code}'
        embed = discord.Embed(title=f'Your Queue', color=discord.Color.green(), description=description)
        # embed.set_thumbnail(url=self.client.user.avatar_url)

        for place, group in groups.items():
            members = []
            if len(group) == 0:
                group = None
                place = f'Group {place} (0/{per_group})'
            else:
                for uid in group:
                    member = discord.utils.get(host.guild.members, id=uid)
                    if member is None:
                        self.sessions[session_code]['groups'][place].remove(uid)
                        continue
                    else:
                        members.append(f'{member.mention}')

            if group is not None:
                group = '\n'.join(members)
                place = f'Group {place} ({len(members)}/{per_group})'
            embed.add_field(name=f'{place}', value=group)

        send = '➡ Send next group'
        end = '⏹ End session'
        kick = '🥾 Kick guest'
        ban = '🚫 Ban guest'
        dodo = '🔁 Change Dodo'
        notify = '💬 Notify Guests'
        addgroup = '➕ Add a group'
        close_open = '⏯ Close/Open queue'
        options1 = f'```\n' \
                   f'{send}\n' \
                   f'{end}\n' \
                   f'{close_open}\n' \
                   f'{dodo}\n' \
                   f'```'
        options2 = f'```\n' \
                   f'{kick}\n' \
                   f'{ban}\n' \
                   f'\n' \
                   f'```'
        options3 = f'```\n' \
                   f'{notify}\n' \
                   f'{addgroup}\n' \
                   f'\n' \
                   f'```'
        embed.add_field(name='\u200b', value='```\nHost Options```', inline=False)
        embed.add_field(name='\u200b', value=options1)
        embed.add_field(name='\u200b', value=options2)
        embed.add_field(name='\u200b', value=options3)

        # edit queue in place if not exists
        queue_id = self.sessions[session_code]['queue_id']
        if queue_id is None:
            print(2)
            queue = await private_channel.send(embed=embed)
            self.sessions[session_code]['queue_id'] = queue.id
        else:
            print(type(queue_id), queue_id)
            queue = await private_channel.fetch_message(id=queue_id)
            await queue.edit(embed=embed)
            if remove_reaction is not None:
                await queue.remove_reaction(remove_reaction, host)
            self.sessions[session_code]['queue_id'] = queue.id

        # update queue id
        self.sessions[session_code]['queue_id'] = queue.id

        reactions = [
            '➡', '⏹', '⏯', '🔁', '🥾', '🚫',
            # '🔠',
            '💬', '➕'
        ]
        for r in reactions:
            await queue.add_reaction(r)

        await self.write_session()

    async def pause(self, host):
        session_code = await self.get_session_code(host)
        status = self.sessions[session_code]['open']
        if status is True:
            self.sessions[session_code]['open'] = False
        else:
            self.sessions[session_code]['open'] = True

    async def add_group(self, host):
        session_code = await self.get_session_code(host)
        last_place = int(list(self.sessions[session_code]['groups'].keys())[-1])
        last_place += 1
        self.sessions[session_code]['groups'][last_place] = []

    async def notify_guests(self, host):
        def check_msg(m):
            return m.author == host and m.channel == private_channel

        session_code = await self.get_session_code(host)
        private_channel = await self.get_session_channel(host)

        embed = discord.Embed(title='What is your message?', color=discord.Color.green())
        prompt = await private_channel.send(embed=embed)
        notification = await self.client.wait_for('message', check=check_msg)
        await private_channel.purge(limit=1)
        await prompt.delete()

        groups = self.sessions[session_code]['groups']
        could_not_reach = []
        for place, member_list in groups.items():
            for uid in member_list:
                try:
                    member = self.client.get_user(uid)
                    msg = f'You\'ve received a message from your Session host **{host.display_name}**:\n' \
                          f'"{notification.content}"'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                except Exception as e:
                    could_not_reach.append(self.client.get_user(uid))
                    print(f'{host} could not send a message to {self.client.get_user(uid)}', e)
        msg = f'Your message has been sent.'
        delete_after = 5
        if len(could_not_reach) > 0:
            msg += f' Your message was not able to reach {", ".join([m.display_name for m in could_not_reach])}'
            delete_after = 10
        await private_channel.send(embed=tools.single_embed(msg), delete_after=delete_after)

    async def change_dodo(self, host):
        def check_msg(m):
            return m.author == host and m.channel == private_channel

        for session_code, value in self.sessions.items():
            if int(session_code) == host.id:
                private_channel = await self.get_session_channel(host)
                embed = discord.Embed(title='Please enter your new Dodo Code', color=discord.Color.green())
                prompt = await private_channel.send(embed=embed)
                msg = await self.client.wait_for('message', check=check_msg)
                self.sessions[session_code]['dodo_code'] = msg.content.upper()
                await private_channel.purge(limit=1)
                msg = f'Your code has been changed to **{self.sessions[session_code]["dodo_code"]}**'
                await prompt.edit(embed=tools.single_embed(msg), delete_after=5)

    async def guest_kick(self, host):
        """
        Kick a guest from a session
        :param host: member object
        :return:
        """

        session_code = await self.get_session_code(host)
        private_channel = await self.get_session_channel(host)
        to_kick = []

        for place, group in self.sessions[session_code]['groups'].items():
            if len(group) == 0:
                pass
            else:
                for uid in group:
                    member = discord.utils.get(host.guild.members, id=uid)
                    if member is None:
                        continue
                    else:
                        to_kick.append(member)

        while True:
            if len(to_kick) > 0:
                reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '⏩', '⏹']
                msg = '\n'.join(f'{to_kick.index(member) + 1}. {member.mention}' for member in to_kick[:10])
                embed = discord.Embed(title='Who do you want to kick?', description=msg, color=discord.Color.green())
                embed.set_thumbnail(url=self.client.user.avatar_url)
                prompt = await private_channel.send(embed=embed)
                for i in range(0, len(to_kick[:11])):
                    await prompt.add_reaction(reactions[i])
                await prompt.add_reaction('⏹')

                def check_react(react, user):
                    return react.message.id == prompt.id and user.id == host.id

                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                kicked_member = None
                if reaction.emoji == reactions[0]:
                    kicked_member = to_kick[0]
                if reaction.emoji == reactions[1]:
                    kicked_member = to_kick[1]
                if reaction.emoji == reactions[2]:
                    kicked_member = to_kick[2]
                if reaction.emoji == reactions[3]:
                    kicked_member = to_kick[3]
                if reaction.emoji == reactions[4]:
                    kicked_member = to_kick[4]
                if reaction.emoji == reactions[5]:
                    kicked_member = to_kick[5]
                if reaction.emoji == reactions[6]:
                    kicked_member = to_kick[6]
                if reaction.emoji == reactions[7]:
                    kicked_member = to_kick[7]
                if reaction.emoji == reactions[8]:
                    kicked_member = to_kick[8]
                if reaction.emoji == reactions[9]:
                    kicked_member = to_kick[9]
                if reaction.emoji == reactions[10]:
                    del to_kick[:10]
                    await prompt.delete()
                    continue
                if reaction.emoji == '⏹':
                    await prompt.delete()
                    return

                member_kick = None
                for place, member_list in self.sessions[session_code]['groups'].items():
                    for uid in member_list:
                        if self.client.get_user(uid) == kicked_member:
                            member_kick = kicked_member
                            try:
                                self.sessions[session_code]['groups'][place].remove(uid)
                                to_kick.remove(kicked_member)
                            except ValueError as e:
                                print(e)
                msg = f'Member **{member_kick.mention}** kicked from session.'
                await private_channel.send(embed=tools.single_embed(msg), delete_after=5)

                msg = f'You have been removed from **Session {session_code}**'
                await member_kick.send(embed=tools.single_embed_neg(msg))

                await prompt.delete()
                return
            else:
                embed = discord.Embed(title='Your queue is empty')
                await private_channel.send(embed=embed, delete_after=5)
                return

    async def guest_ban(self, host):
        """
        Kick a guest from a session
        :param host: member object
        :return:
        """

        session_code = await self.get_session_code(host)
        private_channel = await self.get_session_channel(host)
        to_ban = []

        for place, group in self.sessions[session_code]['groups'].items():
            if len(group) == 0:
                pass
            else:
                for uid in group:
                    member = discord.utils.get(host.guild.members, id=uid)
                    if member is None:
                        continue
                    else:
                        to_ban.append(member)

        while True:
            if len(to_ban) > 0:
                reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '⏩', '⏹']
                msg = '\n'.join(f'{to_ban.index(member) + 1}. {member.mention}' for member in to_ban[:10])
                embed = discord.Embed(title='Who do you want to ban?', description=msg, color=discord.Color.green())
                embed.set_thumbnail(url=self.client.user.avatar_url)
                prompt = await private_channel.send(embed=embed)
                for i in range(0, len(to_ban[:11])):
                    await prompt.add_reaction(reactions[i])
                await prompt.add_reaction('⏹')

                def check_react(react, user):
                    return react.message.id == prompt.id and user.id == host.id

                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                kicked_member = None
                if reaction.emoji == reactions[0]:
                    kicked_member = to_ban[0]
                if reaction.emoji == reactions[1]:
                    kicked_member = to_ban[1]
                if reaction.emoji == reactions[2]:
                    kicked_member = to_ban[2]
                if reaction.emoji == reactions[3]:
                    kicked_member = to_ban[3]
                if reaction.emoji == reactions[4]:
                    kicked_member = to_ban[4]
                if reaction.emoji == reactions[5]:
                    kicked_member = to_ban[5]
                if reaction.emoji == reactions[6]:
                    kicked_member = to_ban[6]
                if reaction.emoji == reactions[7]:
                    kicked_member = to_ban[7]
                if reaction.emoji == reactions[8]:
                    kicked_member = to_ban[8]
                if reaction.emoji == reactions[9]:
                    kicked_member = to_ban[9]
                if reaction.emoji == reactions[10]:
                    del to_ban[:10]
                    await prompt.delete()
                    continue
                if reaction.emoji == '⏹':
                    await prompt.delete()
                    return

                member_kick = None
                for place, member_list in self.sessions[session_code]['groups'].items():
                    for uid in member_list:
                        if self.client.get_user(uid) == kicked_member:
                            member_kick = kicked_member
                            try:
                                self.sessions[session_code]['groups'][place].remove(uid)
                                self.sessions[session_code]['ban_list'].append(uid)
                                to_ban.remove(kicked_member)
                            except ValueError as e:
                                print(e)
                msg = f'Member **{member_kick.mention}** banned from session.'
                await private_channel.send(embed=tools.single_embed(msg), delete_after=5)

                msg = f'You have been banned from **Session {session_code}**'
                await member_kick.send(embed=tools.single_embed_neg(msg))

                await prompt.delete()
                return
            else:
                embed = discord.Embed(title='Your queue is empty')
                await private_channel.send(embed=embed, delete_after=5)
                return

    async def promote(self, session_code):
        """
        Notify groups in a queue that they have moved up one position
        :param session_code:
        :return:
        """
        groups = self.sessions[session_code]['groups']
        members_per_group = self.sessions[session_code]['members per group']
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
                self.sessions[session_code]['groups'][not_filled] = user_to_move
                member = self.client.get_user(user_to_move)
                await member.send(f'You have been moved up to **Group {not_filled}**!')

    async def is_host(self, member):
        session_code = await self.get_session_code(member)
        if session_code is not None:
            return True
        return False

    @commands.Cog.listener()
    # async def on_reaction_add(self, reaction, user):
    async def on_raw_reaction_add(self, payload):
        # check queue reactions
        try:
            guild = self.client.get_guild(payload.guild_id)
            user = discord.utils.get(guild.members, id=payload.user_id)
            if user.bot or user is None:
                return
        except AttributeError as e:
            print('raw reaction error', e)
            return

        emoji = payload.emoji.name
        message = payload.message_id

        reactions = ['➡', '⏹', '⏯', '🔁', '🥾', '🚫', '💬', '➕']
        if emoji in reactions:
            try:
                # await self.get_session_code(user)
                if emoji == '➡':
                    await self.bsend(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[1]:
                    session_code = await self.get_session_code(user)
                    if message == self.sessions[session_code]['queue_id']:
                        private_channel = await self.get_session_channel(user)
                        msg = 'Are you sure you want to end your session?'
                        confirm = await private_channel.send(embed=tools.single_embed(msg))
                        await confirm.add_reaction('🇾')
                        await confirm.add_reaction('🇳')
                        await asyncio.sleep(0)

                        def check_react(react, actor):
                            return react.message.id == confirm.id and actor.id == user.id

                        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                        if reaction.emoji == '🇾':
                            await self.bend(user)
                            return
                        if reaction.emoji == '🇳':
                            await confirm.delete()

                if emoji == reactions[2]:
                    await self.pause(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[3]:
                    await self.change_dodo(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[4]:
                    await self.guest_kick(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[5]:
                    await self.guest_ban(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[6]:
                    await self.notify_guests(user)
                    await self.show_queue(user, emoji)

                if emoji == reactions[7]:
                    await self.add_group(user)
                    await self.show_queue(user, emoji)

            except KeyError as e:
                print('no session found', e)
            except discord.Forbidden as e:
                print(e)

        # check join reactions
        guild = self.client.get_guild(payload.guild_id)
        reactions = ['🦝', '🐷', '⭐']
        if emoji in reactions:
            for session_code in self.sessions:
                if self.sessions[session_code]['message_id'] == message:
                    if await self.is_host(user) and user.id != 193416878717140992:
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == self.sessions[session_code] and user.id != 193416878717140992:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = self.sessions[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = self.sessions[session_code]['open']
                    if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in self.sessions[session_code]['groups'].items():
                        if user.id in group and user.id != 193416878717140992:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = self.sessions[session_code]['members_per']
                    for place, group in self.sessions[session_code]['groups'].items():
                        try:
                            if len(group) < members_per_group:
                                group.append(user.id)
                                prefix = await self.show_prefix(guild)
                                msg = f'You have joined a BETA session\n' \
                                      f'**Group {place}** Session **{session_code}**\n' \
                                      f'~~You can use `{prefix}bleave {session_code}` (lol) at any time to leave this Session.~~\n\n' \
                                      f'You will receive the Host\'s Dodo Code when your group is called.'
                                await user.send(embed=tools.single_embed(msg))
                                msg = f'**{user.mention}** has joined **Group {place}**.'
                                dms = self.client.get_channel(self.sessions[session_code]['private_session'])
                                await dms.send(embed=tools.single_embed(msg), delete_after=5)
                                host = discord.utils.get(guild.members, id=int(session_code))
                                await self.show_queue(host)
                                return
                        except AttributeError as e:
                            print('More than one session found in the session file for this user', e)
                            return
                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))

    async def write_session(self):
        with open('sessions/session.json', 'w') as f:
            json.dump(self.sessions, f, indent=4)

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

