import asyncio
import inspect
import json
import discord
# import queue
import requests
import aiohttp
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

nook_sessions = {}
daisy_sessions = {}
other_sessions = {}


class Alpha(commands.Cog):
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

    async def dms_embed(self, title, description):
        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)
        return embed

    @commands.command()
    @commands.is_owner()
    async def acreate(self, ctx):
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
              f':raccoon: Create Turnip Session\n' \
              f':pig: Create Daisy-Mae Session\n' \
              f':star: Create Catalogue Session\n\n' \
              f':x: Quit'
        prompt = await private_session.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))

        await prompt.add_reaction('🦝')
        await prompt.add_reaction('🐷')
        await prompt.add_reaction('⭐')
        await prompt.add_reaction('❌')
        await asyncio.sleep(0)
        cache_msg = await private_session.fetch_message(prompt.id)

        def check(react, user):
            return react.message.id == cache_msg.id and user.id == ctx.message.author.id

        while True:
            reaction, member = await self.client.wait_for('reaction_add', check=check)
            if reaction.emoji == '🦝':
                await prompt.clear_reactions()
                await self.nook(ctx, private_session, session_code, notification, cache_msg)
            elif reaction.emoji == '🐷':
                await prompt.clear_reactions()
                await self.daisymae(ctx, private_session, session_code, notification, cache_msg)
            elif reaction.emoji == '⭐':
                await prompt.clear_reactions()
                await self.other_session(ctx, private_session, session_code, notification, cache_msg)
            elif reaction.emoji == '❌':
                await private_session.send(embed=tools.single_embed('Quitting'))
                await private_session.delete()
                return

    async def nook(self, ctx, private_session, session_code, notification, nook_prompt):
        """
        Create a nook session for turnip selling
        :param ctx:
        :param private_session: The host's private channel
        :param session_code: The host's randomly generated code
        :param notification: The notification message id and channel id
        :param creation_prompt:
        :return:
        """
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])

        print(nook_prompt)

        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == nook_prompt.id and user.id == ctx.message.author.id

        # get dodo code
        title = 'Turnip Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await nook_prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await msg.delete()

        # get nook buying price
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much are the Nooks buying for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await nook_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        # get max groups
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await nook_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 20.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 20.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        # get guests per group
        description = f'Dodo Code: `{dodo_code}`\nTurnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await nook_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 7.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 7.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        # get session instructions
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await nook_prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        session_message = msg.content
        await msg.delete()

        # grab an image
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Turnip sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        await nook_prompt.edit(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)

        # prompt to post
        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\n' \
                      f'Guests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\n' \
                      f'Image attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        await nook_prompt.edit(embed=embed)
        await nook_prompt.add_reaction('✅')
        await nook_prompt.add_reaction('❌')
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
                embed = discord.Embed(title=f'**Turnip Sell Price**: {turnip_price} bells!',
                                      color=discord.Color.green(), description=msg)
                embed.set_thumbnail(url=ctx.author.avatar_url)
                embed.set_image(url=img.url)
                posting = await sell_channel.send(embed=embed)
                await posting.add_reaction('🦝')
                await img_msg.delete()

                msg = f'Your session has been posted to {sell_channel.mention}'
                await private_session.send(embed=tools.single_embed(msg))
                await nook_prompt.delete()
                break
            elif reaction.emoji == '❌':
                await self.bend(ctx.author, nook_sessions)

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        nook_sessions[session_code] = {
            "host": ctx.author.id,
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
            "welcome": None,
            "groups": groups,
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }

        await self.show_queue(host=ctx.author, session_type=nook_sessions)

    async def daisymae(self, ctx, private_session, session_code, notification, daisy_prompt):
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])

        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == daisy_prompt.id and user.id == ctx.message.author.id

        title = 'Daisy-Mae Session'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await daisy_prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: How much is Daisy selling for?'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await daisy_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                turnip_price = int(msg.content)
                break
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await daisy_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 20.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 20.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nDaisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await daisy_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 7.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 7.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests.'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await daisy_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            session_message = msg.content
            if session_message == '':
                await private_session.send(embed=tools.single_embed(f'Please enter a session message.'), delete_after=3)
            else:
                break
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Daisey-Mae Price: `{turnip_price}` bells\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f'Session Message: `{session_message}`\n' \
                      f':exclamation: Please attach a picture of your Daisy-Mae sale price.'
        embed = await self.dms_embed(title + ' (6/6)', description)
        await daisy_prompt.edit(embed=embed)
        while True:
            img_msg = await self.client.wait_for('message', check=check_msg)
            if len(img_msg.attachments) > 0:
                img = img_msg.attachments[0]
                break
            else:
                await img_msg.delete()
                await private_session.send(embed=tools.single_embed_neg('Please upload an image'), delete_after=5)

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Turnip Price: {turnip_price}\n' \
                      f'Max Groups: {max_groups}\n' \
                      f'Guests per Group: {per_group}\n' \
                      f'Session Message: {session_message}\n' \
                      f'Image attached.\n' \
                      f':exclamation: Your session is ready! Click ✅ to post it.'
        embed = await self.dms_embed(title, description)
        embed.set_image(url=img.url)
        await daisy_prompt.edit(embed=embed)
        await daisy_prompt.add_reaction('✅')
        await daisy_prompt.add_reaction('❌')
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
                await daisy_prompt.delete()
                break
            elif reaction.emoji == '❌':
                await self.bend(ctx.author, daisy_sessions)

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        daisy_sessions[session_code] = {
            "host": ctx.author.id,
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
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }

        await self.show_queue(host=ctx.author, session_type=daisy_sessions)

    async def other_session(self, ctx, private_session, session_code, notification, other_prompt):
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])

        def check_msg(m):
            return m.author == ctx.message.author and m.channel == private_session

        def check_react(react, user):
            return react.message.id == other_prompt.id and user.id == ctx.message.author.id

        title = 'Catalogue'
        embed = await self.dms_embed(title + ' (1/6)', ':exclamation: Enter your Dodo code')
        await other_prompt.edit(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        dodo_code = msg.content.upper()
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f':exclamation: Enter a #channel where your session will be posted.'
        embed = await self.dms_embed(title + ' (2/6)', description)
        await other_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.channel_mentions) > 0:
                posting_channel = msg.channel_mentions[0]
                if posting_channel.permissions_for(ctx.author).read_messages is True:
                    break
                else:
                    await msg.delete()
                    msg = f'You do not have permission to post in that channel'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=3)
            else:
                await msg.delete()
                msg = f'Please enter a valid channel mention.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=3)
        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\nSession Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f':exclamation: How many groups will you allow? (max 20)'
        embed = await self.dms_embed(title + ' (3/6)', description)
        await other_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 20:
                    max_groups = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 20.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 20.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)

        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f':exclamation: How many guests per group? (max 7)'
        embed = await self.dms_embed(title + ' (4/6)', description)
        await other_prompt.edit(embed=embed)
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            try:
                if 1 <= int(msg.content) <= 7:
                    per_group = int(msg.content)
                    break
                else:
                    await msg.delete()
                    msg = 'Enter positive integers only between 1 and 7.'
                    await private_session.send(embed=tools.single_embed(msg), delete_after=5)
            except ValueError:
                await msg.delete()
                msg = 'Enter positive integers only between 1 and 7.'
                await private_session.send(embed=tools.single_embed(msg), delete_after=5)

        await msg.delete()

        description = f'Dodo Code: `{dodo_code}`\n' \
                      f'Session Type: `{title}`\n' \
                      f'Channel: {posting_channel.mention}\n' \
                      f'Max Groups: `{max_groups}`\n' \
                      f'Guests per Group: `{per_group}`\n' \
                      f':exclamation: Please enter a session message. Use this to give instructions to ' \
                      f'your guests. For generic sessions, this message is very important. Please be clear!'
        embed = await self.dms_embed(title + ' (5/6)', description)
        await other_prompt.edit(embed=embed)
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
        await other_prompt.edit(embed=embed)
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
        await other_prompt.edit(embed=embed)
        await other_prompt.add_reaction('✅')
        await other_prompt.add_reaction('❌')
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
                await other_prompt.delete()
                break
            elif reaction.emoji == '❌':
                await self.bend(ctx.author, other_sessions)

        # write data
        groups = {}
        for i in range(max_groups):
            groups[i + 1] = []
        other_sessions[session_code] = {
            "host": ctx.author.id,
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
            "auto": {'active': False, 'minutes': 0},
            "open": True
        }

        await self.show_queue(host=ctx.author, session_type=other_sessions)

    async def bend(self, host, session_type):
        """
        End a session
        :param host: member object
        :param session_type:
        :return:
        """
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])
        post_chans = {
            'nook': 694015832728010762,
            'daisy': 694015696241164368
            }
        session_to_close = []
        for session_code, value in session_type.items():
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
                    if session_type[session_code]['type'] == 'other':
                        sell_channel = session_type[session_code]['sell_channel']
                    else:
                        sell_channel = post_chans.get(session_type[session_code]['type'])
                    await tools.edit_msg(
                        self.client.get_channel(sell_channel),
                        value['message_id'],
                        msg, delete_after=30
                    )
                except KeyError as e:
                    print(e)
                    pass

                groups = session_type[session_code]['groups']
                for place, member_list in groups.items():
                    for uid in member_list:
                        member = self.client.get_user(uid)
                        if member is None:
                            continue
                        msg = f'Session **{session_code}** was **ended** by the host.'
                        await member.send(embed=tools.single_embed(msg))

        for code in session_to_close:
            del session_type[code]
        return

    async def get_session_channel(self, member, session_type):
        """

        :param member:
        :param session_type:
        :return:
        """
        # data = await tools.read_sessions(session_type)
        for k, v in session_type.items():
            if v['host'] == member.id:
                return self.client.get_channel(v['private_session'])

    @staticmethod
    async def get_session_code(member, session_type):
        """
        :param member:  member object
        :param session_type:
        :return:
        """
        # data = await tools.read_sessions(session_file)
        print(inspect.stack()[0][3], ' -> ', inspect.stack()[1][3])
        for session_code, values in session_type.items():
            if values['host'] == member.id:
                return session_code

    @staticmethod
    def to_upper(argument):
        return argument.upper()

    @commands.command()
    async def aleave(self, ctx):
        # session_code = session_code.upper()
        session_types = [nook_sessions,
                         daisy_sessions,
                         other_sessions]
        sessions_member_is_in = []
        for session_type in session_types:
            for session_code, values in session_type.items():
                groups = session_type[session_code]['groups']
                for place, member_list in groups.items():
                    if ctx.author.id in member_list:
                        host = discord.utils.get(ctx.guild.members, id=session_type[session_code]['host'])
                        sessions_member_is_in.append((session_code, host))
        while True:
            if len(sessions_member_is_in) < 1:
                await ctx.send(embed=tools.single_embed('You are not in any sessions.'))
                return
            else:
                reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '⏩', '⏹']
                sessions = [f'{sessions_member_is_in.index(s)+1}. {s[0]} ({s[1].display_name}\'s session)' for s in sessions_member_is_in]
                title = 'Which session do you want to leave?'
                embed = discord.Embed(title=title, description='\n'.join(sessions), color=discord.Color.green())
                prompt = await ctx.send(embed=embed)
                for i in range(len(sessions_member_is_in)):
                    await prompt.add_reaction(reactions[i])
                await prompt.add_reaction('⏹')

                def check_react(react, user):
                    return react.message.id == prompt.id and user.id == ctx.author.id

                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                session_left = None
                if reaction.emoji == reactions[0]:
                    session_left = sessions_member_is_in[0][0]
                if reaction.emoji == reactions[1]:
                    session_left = sessions_member_is_in[1][0]
                if reaction.emoji == reactions[2]:
                    session_left = sessions_member_is_in[2][0]
                if reaction.emoji == reactions[3]:
                    session_left = sessions_member_is_in[3][0]
                if reaction.emoji == reactions[4]:
                    session_left = sessions_member_is_in[4][0]
                if reaction.emoji == reactions[5]:
                    session_left = sessions_member_is_in[5][0]
                if reaction.emoji == reactions[6]:
                    session_left = sessions_member_is_in[6][0]
                if reaction.emoji == reactions[7]:
                    session_left = sessions_member_is_in[7][0]
                if reaction.emoji == reactions[8]:
                    session_left = sessions_member_is_in[8][0]
                if reaction.emoji == reactions[9]:
                    session_left = sessions_member_is_in[9][0]
                if reaction.emoji == reactions[10]:
                    del sessions_member_is_in[:10]
                    await prompt.delete()
                    continue
                if reaction.emoji == '⏹':
                    await prompt.delete()
                    return

                for session_type in session_types:
                    for session_code, values in session_type.items():
                        if session_code == session_left:
                            for place, member_list in session_type[session_code]['groups'].items():
                                if ctx.author.id in member_list:
                                    session_type[session_code]['groups'][place].remove(ctx.author.id)

                                    msg = f'You have left Session {session_code}.'
                                    await ctx.send(embed=tools.single_embed(msg), delete_after=5)

                                    msg = f'**{ctx.author.mention}** has left your queue.'
                                    host = self.client.get_user(session_type[session_code]['host'])
                                    private_channel = await self.get_session_channel(host, session_type)
                                    await private_channel.send(embed=tools.single_embed_neg(msg), delete_after=5)
                                    await prompt.delete()
                                    await self.show_queue(host, session_type)
                await prompt.delete()
                return

    async def bsend(self, host, session_type):
        """
        Send a dodo code to the next group in a DMS queue
        :param host: a member object
        :param session_type:
        :return:
        """
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])
        session_code = await self.get_session_code(host, session_type)
        private_channel = await self.get_session_channel(host, session_type)

        groups = session_type[session_code]['groups']
        place = list(groups.keys())[0]
        msg = await private_channel.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'), delete_after=5)
        await private_channel.fetch_message(msg.id)

        if len(session_type[session_code]['groups'][place]) < 1:
            await private_channel.send(embed=tools.single_embed(f'**Group {place}** is empty.'), delete_after=5)
        else:
            for user in session_type[session_code]['groups'][place]:
                try:
                    member = self.client.get_user(int(user))
                    if member is None:
                        continue
                    msg = f'You have gotten your Session Code for **{host.display_name}\'s** Session!\n' \
                          f'Please do not forget to leave a review for your host when you finish.\n'\
                          f'**Dodo Code**: `{session_type[session_code]["dodo_code"]}`\n'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                except Exception as e:
                    print(f'an error occurred when sending a dodo code: {e}')
            del session_type[session_code]['groups'][place]

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

    async def show_queue(self, host, session_type):
        """
        Show current groups and guests. Usually called after a host action but can be triggered by
        join or leave which requires the host arg
        :param session_type: the session type
        :param host: a member object
        :return:
        """
        print(inspect.stack()[1][3], ' -> ', inspect.stack()[0][3])
        session_code = await self.get_session_code(host, session_type)
        if session_code is None:
            return
        private_channel = await self.get_session_channel(host, session_type)

        while True:
            groups = session_type[session_code]['groups']
            per_group = session_type[session_code]['members_per']

            if len(session_type[session_code]['groups'].keys()) < 1:
                msg = f'You are at the end of your groups. Please end your session and consider starting a new session.'
                await private_channel.send(embed=tools.single_embed(msg))
                return

            dodo_code = session_type[session_code]['dodo_code']
            status = session_type[session_code]['open']
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
                            session_type[session_code]['groups'][place].remove(uid)
                            continue
                        else:
                            members.append(f'{member.mention}')
                            # reviewer_rank = await tools.get_reviewer_rank(db.get_reviews_given(member))
                            # members.append(f'{member.mention} (rank: *{reviewer_rank}*)')

                if group is not None:
                    group = '\n'.join(members)
                    place = f'Group {place} ({len(members)}/{per_group})'
                embed.add_field(name=f'{place}', value=group)

            # show options
            def check_react(react, user):
                return react.message.id == queue.id and user.id == host.id

            send = '➡ Send next group'
            end = '⏹ End session'
            kick = '🥾 Kick guest'
            ban = '🚫 Ban guest'
            dodo = '🔁 Change Dodo'
            notify = '💬 Notify Guests'
            addgroup = '➕ Add a group'
            close_open = '⏯ Close/Open your queue'
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

            queue_id = session_type[session_code]['queue_id']

            if queue_id is None:
                queue = await private_channel.send(embed=embed)
                session_type[session_code]['queue_id'] = queue.id
            else:
                queue = await private_channel.fetch_message(id=queue_id)
                await queue.edit(embed=embed)
                await queue.clear_reactions()
                session_type[session_code]['queue_id'] = queue.id

            try:
                await queue.add_reaction('➡')
                await queue.add_reaction('⏹')
                await queue.add_reaction('⏯')
                await queue.add_reaction('🔁')
                await queue.add_reaction('🥾')
                await queue.add_reaction('🚫')
                await queue.add_reaction('💬')
                await queue.add_reaction('➕')

            except Exception as e:
                print(e)
                pass
            reaction, member = await self.client.wait_for('reaction_add', check=check_react)

            if reaction.emoji == '➡':
                # await queue.delete()
                await self.bsend(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '🔁':
                # await queue.delete()
                await self.change_dodo(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '⏹':
                msg = 'Are you sure you want to end your session?'
                confirm = await private_channel.send(embed=tools.single_embed(msg))
                await confirm.add_reaction('🇾')
                await confirm.add_reaction('🇳')
                await asyncio.sleep(0)

                def check_react(react, user):
                    return react.message.id == confirm.id and user.id == host.id

                reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                if reaction.emoji == '🇾':
                    await self.bend(host, session_type)
                    return
                if reaction.emoji == '🇳':
                    await confirm.delete()

            if reaction.emoji == '⏯':
                # await queue.delete()
                await self.pause(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '🥾':
                # await queue.delete()
                await self.guest_kick(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '🚫':
                # await queue.delete()
                await self.guest_ban(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '💬':
                # await queue.delete()
                await self.notify_guests(host, session_type)
                # await self.show_queue(host, session_type)

            if reaction.emoji == '➕':
                # await queue.delete()
                await self.add_group(host, session_type)
                # await self.show_queue(host, session_type)

    async def pause(self, host, session_type):
        session_code = await self.get_session_code(host, session_type)
        status = session_type[session_code]['open']
        if status is True:
            session_type[session_code]['open'] = False
        else:
            session_type[session_code]['open'] = True

    async def add_group(self, host, session_type):
        session_code = await self.get_session_code(host, session_type)
        last_place = list(session_type[session_code]['groups'].keys())[-1]
        last_place += 1
        session_type[session_code]['groups'][last_place] = []

    async def notify_guests(self, host, session_type):
        def check_msg(m):
            return m.author == host and m.channel == private_channel

        session_code = await self.get_session_code(host, session_type)
        private_channel = await self.get_session_channel(host, session_type)

        embed = discord.Embed(title='What is your message?', color=discord.Color.green())
        prompt = await private_channel.send(embed=embed)
        msg = await self.client.wait_for('message', check=check_msg)
        await private_channel.purge(limit=1)
        await prompt.delete()

        groups = session_type[session_code]['groups']
        for place, member_list in groups.items():
            for uid in member_list:
                member = self.client.get_user(uid)
                if member is not None:
                    msg = f'You\'ve received a message from your Session host **{host.display_name}**:\n' \
                          f'"{msg.content}"'
                    await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        await private_channel.send(embed=tools.single_embed(f'Your message has been sent.'), delete_after=3)

    async def change_dodo(self, host, session_type):
        def check_msg(m):
            return m.author == host and m.channel == private_channel

        for session_code, value in session_type.items():
            if value['host'] == host.id:
                private_channel = await self.get_session_channel(host, session_type)
                embed = discord.Embed(title='Please enter your new Dodo Code', color=discord.Color.green())
                prompt = await private_channel.send(embed=embed)
                msg = await self.client.wait_for('message', check=check_msg)
                session_type[session_code]['dodo_code'] = msg.content.upper()
                await private_channel.purge(limit=1)
                msg = f'Your code has been changed to **{session_type[session_code]["dodo_code"]}**'
                await prompt.edit(embed=tools.single_embed(msg), delete_after=5)

    async def guest_kick(self, host, session_type):
        """
        Kick a guest from a session
        :param host: member object
        :param session_type:
        :return:
        """

        session_code = await self.get_session_code(host, session_type)
        private_channel = await self.get_session_channel(host, session_type)
        to_kick = []

        for place, group in session_type[session_code]['groups'].items():
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
                # embed.set_thumbnail(url=self.client.user.avatar_url)
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
                for place, member_list in session_type[session_code]['groups'].items():
                    for uid in member_list:
                        if self.client.get_user(uid) == kicked_member:
                            member_kick = kicked_member
                            try:
                                session_type[session_code]['groups'][place].remove(uid)
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

    async def guest_ban(self, host, session_type):
        """
        Kick a guest from a session
        :param host: member object
        :param session_type:
        :return:
        """

        session_code = await self.get_session_code(host, session_type)
        private_channel = await self.get_session_channel(host, session_type)
        to_ban = []

        for place, group in session_type[session_code]['groups'].items():
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
                for place, member_list in session_type[session_code]['groups'].items():
                    for uid in member_list:
                        if self.client.get_user(uid) == kicked_member:
                            member_kick = kicked_member
                            try:
                                session_type[session_code]['groups'][place].remove(uid)
                                session_type[session_code]['ban_list'].append(uid)
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
        session_code = await self.get_session_code(member, session_file)
        if session_code is not None:
            return True
        return False

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        reactions = ['🦝', '🐷', '⭐']

        # match raccoon
        if reaction.emoji == reactions[0]:
            for session_code in nook_sessions:
                if nook_sessions[session_code]['message_id'] == reaction.message.id:
                    if await self.is_host(user, nook_sessions):
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == nook_sessions[session_code]['host']:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = nook_sessions[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = nook_sessions[session_code]['open']
                    if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in nook_sessions[session_code]['groups'].items():
                        if user.id in group and user.id != 193416878717140992:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = nook_sessions[session_code]['members_per']
                    for place, group in nook_sessions[session_code]['groups'].items():
                        try:
                            if len(group) < members_per_group:
                                group.append(user.id)
                                prefix = await self.show_prefix(reaction.message.guild)
                                msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                                      f'You can use `{prefix}leave {session_code}` at any time to leave this Session. Be ' \
                                      f'aware that the Session Code is not the host\'s Dodo code.\n\n' \
                                      f'You will receive the Host\'s Dodo Code when your group is called.'
                                await user.send(embed=tools.single_embed(msg))
                                msg = f'**{user.mention}** has joined **Group {place}**.'
                                dms = self.client.get_channel(nook_sessions[session_code]['private_session'])
                                await dms.send(embed=tools.single_embed(msg), delete_after=5)
                                # await tools.write_sessions(data, 'sessions/nook.json')
                                host = discord.utils.get(reaction.message.guild.members, id=nook_sessions[session_code]['host'])
                                print('host', host)
                                await self.show_queue(host=host, session_type=nook_sessions)
                                return
                        except AttributeError as e:
                            print('More than one session found in the session file for this user', e)
                            pass
                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))

        # match pig
        elif reaction.emoji == reactions[1]:
            for session_code in daisy_sessions:
                if daisy_sessions[session_code]['message_id'] == reaction.message.id:
                    if await self.is_host(user, daisy_sessions):
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == daisy_sessions[session_code]['host']:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = daisy_sessions[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = daisy_sessions[session_code]['open']
                    if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in daisy_sessions[session_code]['groups'].items():
                        if user.id in group and user.id != 193416878717140992:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = daisy_sessions[session_code]['members_per']
                    for place, group in daisy_sessions[session_code]['groups'].items():
                        try:
                            if len(group) < members_per_group:
                                group.append(user.id)
                                prefix = await self.show_prefix(reaction.message.guild)
                                msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                                      f'You can use `{prefix}leave {session_code}` at any time to leave this Session. Be ' \
                                      f'aware that the Session Code is not the host\'s Dodo code.\n\n' \
                                      f'You will receive the Host\'s Dodo Code when your group is called.'
                                await user.send(embed=tools.single_embed(msg))
                                msg = f'**{user.mention}** has joined **Group {place}**.'
                                private_channel = self.client.get_channel(daisy_sessions[session_code]['private_session'])
                                await private_channel.send(embed=tools.single_embed(msg), delete_after=5)
                                host = discord.utils.get(reaction.message.guild.members,
                                                         id=daisy_sessions[session_code]['host'])
                                await self.show_queue(host=host, session_type=daisy_sessions)
                                return
                        except AttributeError as e:
                            print('More than one session found in the session file for this user', e)
                            pass

                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))

        # match star
        elif reaction.emoji == reactions[2]:
            for session_code in other_sessions:
                if other_sessions[session_code]['message_id'] == reaction.message.id:
                    if await self.is_host(user, other_sessions) and user.id != 193416878717140992:
                        msg = f'You cannot **join** a session if you are **Hosting**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    if user.id == other_sessions[session_code]['host'] and user.id != 193416878717140992:
                        await user.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                        return

                    ban_list = other_sessions[session_code]['ban_list']
                    if user.id in ban_list:
                        msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                        await user.send(embed=tools.single_embed_neg(msg))
                        return

                    _open = other_sessions[session_code]['open']
                    if not _open:
                        await user.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                        return

                    for place, group in other_sessions[session_code]['groups'].items():
                        if user.id in group and user.id != 193416878717140992:
                            msg = f'You have already joined Session **{session_code}**.'
                            await user.send(embed=tools.single_embed(msg))
                            return

                    members_per_group = other_sessions[session_code]['members_per']
                    for place, group in other_sessions[session_code]['groups'].items():
                        try:
                            if len(group) < members_per_group:
                                group.append(user.id)
                                prefix = await self.show_prefix(reaction.message.guild)
                                msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                                      f'You can use `{prefix}leave {session_code}` at any time to leave this Session. Be ' \
                                      f'aware that the Session Code is not the host\'s Dodo code.\n\n' \
                                      f'You will receive the Host\'s Dodo Code when your group is called.'
                                await user.send(embed=tools.single_embed(msg))
                                msg = f'**{user.mention}** has joined **Group {place}**.'
                                private_channel = self.client.get_channel(
                                    other_sessions[session_code]['private_session'])
                                await private_channel.send(embed=tools.single_embed(msg), delete_after=5)
                                host = discord.utils.get(reaction.message.guild.members,
                                                         id=other_sessions[session_code]['host'])
                                await self.show_queue(host=host, session_type=other_sessions)
                                return
                        except AttributeError as e:
                            print('More than one session found in the session file for this user', e)
                            pass

                    await user.send(embed=tools.single_embed(f'Sorry, the Session you are trying to join is full.'))


def setup(client):
    client.add_cog(Alpha(client))
