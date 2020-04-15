import asyncio

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


class DMS(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def show_prefix(guild):
        prefix = db.get_prefix(guild)[0]
        return prefix

    @commands.command()
    async def dms(self, ctx):
        prefix = await self.show_prefix(ctx.guild)
        host_help = f'**Getting Started with Daisy-Mae Sessions (DMS)!**\n' \
                    f'`{prefix}create` Create a DMS\n' \
                    f'`{prefix}menu` Get a list of available commands when hosting a DMS\n' \
                    f'`{prefix}end` End your DMS session\n' \
                    f'`{prefix}join session_code` Join a DMS (if the DMS is public just click the turnip reaction!)\n' \
                    f'`{prefix}leave session_code` Leave a DMS session'
        await ctx.send(embed=tools.single_embed(host_help))

    @commands.command()
    async def create(self, ctx):
        prefix = await self.show_prefix(ctx.guild)
        session_code = await tools.random_code()
        dms = await tools.create_private_channel(ctx, ctx.author, session_code)
        if not dms:
            msg = 'You already have an active Session Channel.'
            await ctx.send(embed=tools.single_embed_neg(msg))
            return
        msg = f'Your private Session Channel has been created: {dms.mention}'
        notification = await ctx.send(embed=tools.single_embed(msg))

        data = await tools.read_sessions()
        data[session_code] = {
            "host": ctx.author.id,
            "notification": [notification.id, ctx.channel.id],
            "session": dms.id,
            "ban list": []
        }
        await tools.write_sessions(data)
        await self.wizard(ctx, dms, session_code)

        host_menu = f'**Daisy-Mae Session Commands**\n\n' \
                    f'`{prefix}send` to send out codes to the next group in the queue\n' \
                    f'`{prefix}close` to close the session off from new guests (sessions is still active)\n' \
                    f'`{prefix}end` to end the session.\n' \
                    f'`{prefix}dodo code` change your dodo `code`. ex: `{prefix}dodo ABCDEF`\n' \
                    f'`{prefix}show` to show the current queue\n' \
                    f'`{prefix}notify message` send `message` to everyone in your queue\n' \
                    f'`{prefix}welcome message` set a `message` for your guests\n\n' \
                    f'`{prefix}kick member` to kick `member` from the queue.\n' \
                    f'`{prefix}bans` show current list of banned members\n' \
                    f'`{prefix}ban member` ban a `member` and prevent them from joining again \n' \
                    f'`{prefix}unban member` unban a `member`\n\n' \
                    f'`{prefix}menu` to see these options again'

        await dms.send(embed=tools.single_embed(host_menu, avatar=self.client.user.avatar_url))

    async def wizard(self, ctx, dms, session_code):
        prefix = await self.show_prefix(ctx.guild)
        msg = '**Welcome to the Daisy-Mae Queue Wizard!**\n' \
              'If you\'d like to create a queue, please enter `y` or enter `q` to quit. You can enter `q` at any time to ' \
              'quit the wizard. Keep in mind you can only have one open session at a time, and you cannot host while ' \
              'waiting in another Session.\n\n' \
              f'If you experience problems, please report it using `{prefix}bug message` and attach a picture of the issue.'
        await dms.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))

        def check(m):
            return m.author == ctx.message.author and m.channel == dms

        while True:
            msg = await self.client.wait_for('message', check=check)
            if any(item.lower() == msg.content.lower() for item in _confirm):
                break
            elif any(item.lower() == msg.content.lower() for item in _quit):
                await dms.send(embed=tools.single_embed('Wizard cancelled'))
                await tools.close_private_channel(dms)
                return
            else:
                msg = 'I\'m sorry. Please answer with either `y` or `n`.'
                await dms.send(embed=tools.single_embed_neg(msg))

        # get dodo code
        msg = 'Please enter your Dodo code.'
        await dms.send(embed=tools.single_embed(msg))
        msg = await self.client.wait_for('message', check=check)
        dodo = msg.content

        # set turnip prices
        msg = '**Turnip Price**\nPlease enter the **Turnip sell** price on your island. Number values greater than `0` only.'
        await dms.send(embed=tools.single_embed(msg))
        while True:
            while True:
                msg = await self.client.wait_for('message', check=check)
                if msg.content == 'q':
                    await dms.send(embed=tools.single_embed('Quitting'))
                try:
                    bell_value = int(msg.content)
                    if not 0 < bell_value:
                        msg = 'Please enter a valid positive integer.'
                        await dms.send(embed=tools.single_embed_neg(msg))
                    else:
                        break
                except ValueError:
                    msg = 'Please enter a valid integer.'
                    await dms.send(embed=tools.single_embed_neg(msg))
            break

        # get max entries
        msg = '**Max Participants**\nPlease enter the maximum number of entrants you will accept between `1` and `100`.'
        await dms.send(embed=tools.single_embed(msg))
        while True:
            while True:
                msg = await self.client.wait_for('message', check=check)
                if msg.content == 'q':
                    await dms.send(embed=tools.single_embed('Quitting'))
                try:
                    max_entries = int(msg.content)
                    if not 1 <= max_entries <= 100:
                        msg = 'Please enter a number between `1` and `100`.'
                        await dms.send(embed=tools.single_embed_neg(msg))
                    else:
                        break
                except ValueError:
                    msg = 'Please enter a valid integer.'
                    await dms.send(embed=tools.single_embed_neg(msg))
            break

        # entries per group
        msg = '**Players per Group**\nPlease enter the maximum number of entries per group between `1` and `7`. ' \
              'This can help you manage how many players are on your island at any given time.'
        await dms.send(embed=tools.single_embed(msg))
        while True:
            while True:
                msg = await self.client.wait_for('message', check=check)
                if msg.content == 'q':
                    await dms.send(embed=tools.single_embed('Quitting'))
                    return
                try:
                    per_group = int(msg.content)
                    if not 1 <= per_group <= 7:
                        await dms.send(embed=tools.single_embed_neg('Please enter a number between `1` and `7`.'))
                    else:
                        break
                except ValueError:
                    await dms.send(embed=tools.single_embed_neg('Please enter a valid integer.'))
            break

        # set message
        msg = '**Session Post Message**\nYou can post an optional message with your Session to give your guests ' \
              'additional details about your Session. Enter `n` to skip.'
        await dms.send(embed=tools.single_embed(msg))
        while True:
            msg = await self.client.wait_for('message', check=check)
            if any(item.lower() == msg.content.lower() for item in _deny):
                welcome = None
                await dms.send(embed=tools.single_embed('Skipping Session Message.'))
            else:
                welcome = msg.content
            break

        # get image
        msg = '**Upload Image**\nWe encourage hosts to post images of their turnip sell price. You can upload your ' \
              'picture now or enter `n` to pass.'
        await dms.send(embed=tools.single_embed(msg))
        img = None
        while True:
            while True:
                msg = await self.client.wait_for('message', check=check)
                if any(item.lower() == msg.content.lower() for item in _deny):
                    await dms.send(embed=tools.single_embed('Skipping image upload.'))
                    break
                elif len(msg.attachments) > 0:
                    img = msg.attachments[0]
                    await dms.send(embed=tools.single_embed('Image found.'))
                    break
                elif any(item.lower() == msg.content.lower() for item in _quit):
                    await dms.send(embed=tools.single_embed('Quitting.'))
                    return
                else:
                    await dms.send(embed=tools.single_embed('A problem occurred. Skipping image upload.'))
                    break
            break

        event = f'**Bell Price**: {bell_value}\n'\
                f'**Max Entries**: {max_entries}\n' \
                f'**Players per Group**: {per_group}\n'
        if welcome is not None:
            event += '\n' + f'**Message from the Host**: {welcome}'

        await dms.send(embed=tools.single_embed(f'__Your Info__\n{event}', avatar=self.client.user.avatar_url))

        # get max entries
        msg = '**We\'re Ready!**\nWould you like to auto post this to the Sell Channel? Please enter `y` or `n`.'
        await dms.send(embed=tools.single_embed(msg))
        session_message = None
        while True:
            msg = await self.client.wait_for('message', check=check)
            if msg.content == 'q':
                await dms.send(embed=tools.single_embed('Quitting'))
                await tools.close_private_channel(dms)
            elif any(item.lower() == msg.content.lower() for item in _confirm):

                # generate the invite session embed
                notification_channel = self.client.get_channel(_dms_channel)
                embed = discord.Embed(color=discord.Color.green(),
                                      description=f'**{ctx.author.display_name}** has created a new Daisy-Mae session!\n'
                                                  f'To join just tap the `turnip` reaction\n\n{event}')
                if img is not None:
                    embed.set_image(url=img.url)
                embed.set_thumbnail(url=turnip)
                session_message = await notification_channel.send(embed=embed)
                await session_message.add_reaction(self.client.get_emoji(694822764699320411))

                session_message = session_message.id
                msg = f'Your Session invite has been sent to {notification_channel.mention}!'
                await dms.send(embed=tools.single_embed(msg))
                break
            elif any(item.lower() == msg.content.lower() for item in _deny):
                msg = f'OK! Your session is still open and your code is valid until you close the session.\n' \
                      f'You can invite guests to join with `{prefix}join {session_code}`.'
                await dms.send(embed=tools.single_embed(msg))
                break
            else:
                msg = 'I\'m sorry. Please answer with either `y` or `n`.'
                await dms.send(embed=tools.single_embed_neg(msg))
        msg = f'You can add a `welcome` message for guests by using the '\
              f'`{prefix}welcome message` command. This way you can let them know if they ' \
              f'should leave via the airport or wait to get kicked!'
        await dms.send(embed=tools.single_embed(msg))

        data = await tools.read_sessions()

        # create groups based on num of users
        groups = {}
        remainder = max_entries % per_group
        max_groups = int(max_entries / per_group)
        if remainder != 0:
            max_groups += 1

        for i in range(max_groups):
            groups[i + 1] = []

        new_data = {
            "message id": session_message,
            "dodo code": dodo.upper(),
            "max entries": max_entries,
            "members per group": per_group,
            "welcome": welcome,
            "groups": groups,
            "afk": {'active': False, 'minutes': 0}
        }

        for k, v in new_data.items():
            data[session_code][k] = v

        await tools.write_sessions(data)
        return session_code

    @commands.command()
    async def close(self, ctx):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)

        # data = await tools.read_sessions()
        # session_code = await self.get_dms_session(ctx.author)
        # dms = await self.get_session(ctx.author)
        channel = self.client.get_channel(session)
        await channel.send(embed=tools.single_embed(f'Your session has been **closed** to new guests.'))
        msg = f'Private Session **closed**.'
        await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg, delete_after=30)

        # edit sell embed if available
        msg = f'Session **{session_code}** is now **closed**.'
        await tools.edit_msg(self.client.get_channel(_dms_channel), message_id, msg, delete_after=30)

    @commands.command()
    async def end(self, ctx):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()

        session_to_close = []
        for session_code, value in data.items():
            if value['host'] == ctx.author.id:
                session_to_close.append(session_code)
                channel = self.client.get_channel(value['session'])

                # edit private session notification if available
                msg = f'Private Session **closed**.'
                await tools.edit_msg(
                    self.client.get_channel(value['notification'][1]),
                    value['notification'][0],
                    msg, delete_after=30
                )
                if channel is not None:
                    await tools.close_private_channel(channel)

                # edit sell embed if available
                try:
                    msg = f'Session **{session_code}** is now **closed**.'
                    await tools.edit_msg(
                        self.client.get_channel(_dms_channel),
                        value['message id'],
                        msg, delete_after=30
                    )
                except KeyError:
                    pass

                try:
                    groups = data[session_code]['groups']
                    for place, member_list in groups.items():
                        for uid in member_list:
                            member = self.client.get_user(uid)
                            msg = f'Session **{session_code}** was **closed** by the host.'
                            await member.send(embed=tools.single_embed(msg))
                except KeyError:
                    pass

        for code in session_to_close:
            del data[code]
            await tools.write_sessions(data)

    @commands.command()
    async def dodo(self, ctx, *, dodo):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        for session_code, value in data.items():
            if value['host'] == ctx.author.id:
                value['dodo code'] = dodo.upper()
                await ctx.send(embed=tools.single_embed(f'Your Dodo code has been changed to **{dodo.upper()}**'))
        await tools.write_sessions(data)

    @commands.command()
    async def welcome(self, ctx, *, message):
        prefix = await self.show_prefix(ctx.guild)
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)
        # session_code = await self.get_session_code(ctx.author)
        data[session_code]['welcome'] = message
        await tools.write_sessions(data)
        await ctx.send(embed=tools.single_embed(f'Your **welcome** message has been set to:\n'
                                                f'"{message}"\n'
                                                f'Members will receive it when you use the `{prefix}send` command.'))

    @commands.command()
    async def menu(self, ctx):
        prefix = await self.show_prefix(ctx.guild)
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        dms = await self.get_session(ctx.author)
        host_menu = f'**Daisy-Mae Session Commands**\n\n' \
                    f'`{prefix}send` to send out codes to the next group in the queue\n' \
                    f'`{prefix}close` to close the session off to **new** guests\n' \
                    f'`{prefix}end` to end the session.\n' \
                    f'`{prefix}dodo code` change your dodo `code`. ex: `{prefix}dodo ABCDEF`\n' \
                    f'`{prefix}show` to show the current queue\n' \
                    f'`{prefix}notify message` send a message to everyone in your queue\n' \
                    f'`{prefix}welcome message` set a message for your guests\n\n' \
                    f'`{prefix}kick member` to kick `member` from the queue.\n' \
                    f'`{prefix}bans` show current list of banned members\n' \
                    f'`{prefix}ban member` ban a `member` and prevent them from joining again \n' \
                    f'`{prefix}unban member` unban a `member`\n\n' \
                    f'`{prefix}menu` to see these options again\n' \
                    f'`{prefix}afk num` set an AFK timer that sends the next group every `num` minutes.\n'\
                    f'`{prefix}afk stop` stop an AFK timer.'
        await dms.send(embed=tools.single_embed(host_menu, avatar=self.client.user.avatar_url))

    @commands.command()
    async def afk(self, ctx, minutes):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        prefix = await self.show_prefix(ctx.guild)

        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome_message, groups, afk, default_minutes) = await self.get_dms_session(ctx.author)
        if minutes.lower() == 'stop':
            data = await tools.read_sessions()
            data[session_code]['afk']['active'] = False
            await tools.write_sessions(data)
            await ctx.send(embed=tools.single_embed_neg(f'Your afk session was ended.'))
            members_to_notify = []
            for place, member_list in groups.items():
                for uid in member_list:
                    members_to_notify.append(uid)

            for uid in members_to_notify:
                member = self.client.get_user(uid)
                msg = f'Your host for session **{session_code}** has turned off their **AFK** timer.'
                await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
            return
        else:
            try:
                minutes = int(minutes)
                if minutes < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Please choose an integer greater than `0`.'))
                    return
            except Exception as e:
                print(e)
                await ctx.send(embed=tools.single_embed_neg(f'Minutes must be an integer.'))
                return

            msg = f'Your AFK timer is set to {minutes} minutes. Every {minutes} minutes, a group will be sent ' \
                  f'until you run out of groups or you enter `{prefix}afk stop`.'
            await ctx.send(embed=tools.single_embed(msg))
            (session_code, host, notification, session, ban_list, message_id,
             dodo_code, max_entries, per_group, welcome_message, groups, afk, default_minutes) = await self.get_dms_session(ctx.author)
            data = await tools.read_sessions()
            data[session_code]['afk']['active'] = True
            data[session_code]['afk']['minutes'] = minutes
            await tools.write_sessions(data)
            while True:
                (session_code, host, notification, session, ban_list, message_id,
                 dodo_code, max_entries, per_group, welcome_message, groups, afk, default_minutes) = await self.get_dms_session(ctx.author)
                if afk is False:
                    return
                dms = self.client.get_channel(session)
                data = await tools.read_sessions()
                if len(groups) >= 1:
                    host = discord.utils.get(ctx.guild.members, id=host)
                    place = list(groups.keys())[0]
                    await dms.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'))

                    for user in data[session_code]['groups'][place]:
                        member = self.client.get_user(int(user))
                        msg = f'You have gotten your Session Code for **{host.display_name}\'s** Session!\n' \
                              f'Please do not forget to leave a review for your host when you finish.\n' \
                              f'**Dodo Code**: `{dodo_code}`\n'
                        if welcome_message is not None:
                            msg += f'\n\n**Your host left you a message!**\n"{welcome_message}"'
                        if member is not None:
                            await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                    del data[session_code]['groups'][place]
                    await tools.write_sessions(data)

                    # notify groups that they have moved up
                    for place, member_list in data[session_code]['groups'].items():
                        for uid in member_list:
                            member = self.client.get_user(uid)
                            position = list(groups.keys()).index(place) + 1
                            msg = f'Your group in **Session {session_code}** has moved up! \n' \
                                  f'You are now in **Position** `{position}` of `{len(list(groups.keys()))}`.\n' \
                                  f'**note**: Your host is using an AFK timer. Dodo codes will be sent every {minutes} ' \
                                  f'minute(s). \n__Please conduct your business as quickly as possible__.'
                            await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
                    try:
                        await self.reshow(ctx)
                    except Exception as e:
                        print(e)
                    await asyncio.sleep(60 * default_minutes)
                else:
                    await dms.send(embed=tools.single_embed(f'Your AFK session has ended.'))
                    return

    @commands.command()
    async def show(self, ctx):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        # data = await tools.read_sessions()
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)
        # per_group = data[session_code]['members per group']

        # groups = data[session_code]['groups']
        embed = discord.Embed(title=f'Groups in Queue for Session {session_code}',
                              color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)

        for place, group in groups.items():
            members = []
            if len(group) == 0:
                group = None
                place = f'Group {place} (0/{per_group})'
            else:
                for uid in group:
                    member = discord.utils.get(ctx.guild.members, id=uid)
                    reviewer_rank = await tools.get_reviewer_rank(db.get_reviews_given(member))
                    members.append(f'{member.display_name} (rank: *{reviewer_rank}*)')
            if group is not None:
                group = '\n'.join(members)
                place = f'Group {place} ({len(members)}/{per_group})'
            embed.add_field(name=f'{place}', value=group, inline=False)
        dms = await self.get_session(ctx.author)
        await dms.send(embed=embed)

    async def get_session(self, author):
        data = await tools.read_sessions()
        for k, v in data.items():
            if v['host'] == author.id:
                return self.client.get_channel(v['session'])

    @staticmethod
    async def get_dms_session(author):
        data = await tools.read_sessions()
        for session_code, values in data.items():
            if values['host'] == author.id:
                host = values['host']
                notification = values.get('notification', None)
                session = values['session']
                ban_list = values.get('ban list', None)
                message_id = values.get('message id', None)
                dodo_code = values.get('dodo code', None)
                max_entries = values.get('max entries', None)
                members_per_group = values.get('members per group', None)
                welcome = values.get('welcome', None)
                groups = values.get('groups', None)
                afk = values.get('afk').get('active', False)
                minutes = values.get('afk').get('minutes', 0)

                return (session_code, host, notification, session,
                        ban_list, message_id, dodo_code, max_entries,
                        members_per_group, welcome, groups, afk, minutes)
        #
        #
        # for code, v in data.items():
        #     if v.get('host') == author.id:
        #         session_code = code
        #         if v.get('notification', None) is not None:
        #             notification = v.get(notification)
        #         session = v.get('session', None)
        #
        #
        # return None

    @commands.command()
    async def kick(self, ctx, member: discord.Member):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        # dms = await self.get_session(ctx.author)
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)
        dms = self.client.get_channel(session)

        user_removed = False
        groups = data[session_code]['groups']
        for place, member_list in groups.items():
            for uid in member_list:
                if self.client.get_user(uid) == member:
                    member_list.remove(uid)
                    user_removed = True

        if user_removed:
            await tools.write_sessions(data)
            await dms.send(embed=tools.single_embed(f'Member **{member.mention}** kicked from session.'))
            await member.send(embed=tools.single_embed_neg(f'You have been removed from **Session {session_code}**'))
            await self.reshow(ctx)
        else:
            await dms.send(embed=tools.single_embed_neg(f'Unable to find and kick **{member}**.'))

    @commands.command()
    async def send(self, ctx):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        # dms = await self.get_session(ctx.author)
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome_message, groups, afk, minutes) = await self.get_dms_session(ctx.author)
        dms = self.client.get_channel(session)

        host = discord.utils.get(ctx.guild.members, id=host)

        # groups = data[session_code]['groups']
        place = list(groups.keys())[0]
        await dms.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'))

        # welcome_message = data[session_code]['welcome']

        for user in data[session_code]['groups'][place]:
            member = self.client.get_user(int(user))
            msg = f'You have gotten your Session Code for **{host.display_name}\'s** Session!\n' \
                  f'Please do not forget to leave a review for your host when you finish.\n'\
                  f'**Dodo Code**: `{data[session_code]["dodo code"]}`\n'
            if welcome_message is not None:
                msg += f'\n\n**Your host left you a message!**\n"{welcome_message}"'
            if member is not None:
                await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        del data[session_code]['groups'][place]
        await tools.write_sessions(data)

        # notify groups that they have moved up
        for place, member_list in data[session_code]['groups'].items():
            for uid in member_list:
                member = self.client.get_user(uid)
                position = list(groups.keys()).index(place) + 1
                msg = f'Your group in **Session {session_code}** has moved up! \n' \
                      f'You are now in **Position** `{position}` of `{len(list(groups.keys()))}`.'
                await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        try:
            await self.reshow(ctx)
        except Exception as e:
            print(e)

    @commands.command()
    async def notify(self, ctx, group: str = None, *, message):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        # send a message to everyone in the queue
        # data = await tools.read_sessions()
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)
        # dms = await self.get_session(ctx.author)
        dms = self.client.get_channel(session)
        # groups = data[session_code]['groups']
        members_to_notify = []
        try:
            int(group)
            for uid in groups.get(str(group)):
                members_to_notify.append(uid)
        except ValueError:
            for place, member_list in groups.items():
                for uid in member_list:
                    members_to_notify.append(uid)

        for uid in members_to_notify:
            member = self.client.get_user(uid)
            msg = f'You\'ve received a message from your Session host **{ctx.author.display_name}**:\n' \
                  f'"{message}"'
            await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        await dms.send(embed=tools.single_embed(f'Your message has been sent.'))

    @commands.command()
    async def ban(self, ctx, member: discord.Member):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)

        # if member.id not in data[session_code]['ban list']:

        data = await tools.read_sessions()
        if member.id not in ban_list:
            data[session_code]['ban list'].append(member.id)
        else:
            await ctx.send(embed=tools.single_embed(f'**{member.mention}** is already banned from your session.'))
            return
        for place, member_list in data[session_code]['groups'].items():
            if member.id in member_list:
                member_list.remove(member.id)
                await member.send(embed=tools.single_embed(f'You have been removed from Session **{session_code}**'))
        await tools.write_sessions(data)
        await ctx.send(embed=tools.single_embed(f'You have banned **{member.mention}** from your session.'))
        await self.reshow(ctx)

    @commands.command()
    async def unban(self, ctx, member: discord.Member):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)

        if member.id in data[session_code]['ban list']:
            data[session_code]['ban list'].remove(member.id)
            await tools.write_sessions(data)
            await ctx.send(embed=tools.single_embed(f'You have unbanned **{member.mention}** from your session.'))
        else:
            await ctx.send(embed=tools.single_embed(f'**{member.mention}** is not in the ban list.'))

    @commands.command()
    async def bans(self, ctx):
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        # session_code = await self.get_session_code(ctx.author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(ctx.author)

        banned_members = []
        for uid in data[session_code]['ban list']:
            banned_members.append(discord.utils.get(ctx.guild.members, id=uid).mention)
        banned_members = '\n'.join(banned_members)
        if len(banned_members) is 0:
            banned_members = None
        await ctx.send(embed=tools.single_embed(f'**Banned Members**\n{banned_members}', avatar=self.client.user.avatar_url))

    @commands.command()
    async def join(self, ctx, session_code: str):
        prefix = await self.show_prefix(ctx.guild)
        # if await self.is_host(ctx.author):
        #     await ctx.send(embed=tools.single_embed_neg(f'You cannot **join** a session if you are **Hosting**.'))
        #     return
        session_code = session_code.upper()
        data = await tools.read_sessions()
        session = data[session_code]
        dms = self.client.get_channel(data[session_code]['session'])
        # if ctx.author.id == session['host']:
        #     await ctx.send(embed=tools.single_embed(f'You cannot join your own Session.'))
        #     return
        ban_list = session['ban list']
        if ctx.author.id in ban_list:
            msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
            await ctx.author.send(embed=tools.single_embed_neg(msg))
            return
        members_per_group = session['members per group']
        # for place, group in session['groups'].items():
        #     if ctx.author.id in group:
        #         msg = f'You have already joined Session **{session_code}**.'
        #         await ctx.send(embed=tools.single_embed(msg))
        #         return
        for place, group in session['groups'].items():
            if len(group) < members_per_group:
                group.append(ctx.author.id)
                msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                      f'You can use `{prefix}leave {session_code}` at any time to leave this Session.'
                await ctx.send(embed=tools.single_embed(msg))
                msg = f'**{ctx.author.display_name}** has joined **Group {place}**.'
                await dms.send(embed=tools.single_embed(msg))
                await tools.write_sessions(data)
                await self.reshow(ctx)
                return

        await ctx.send(f'Sorry, the Session you are trying to join is full.')

    async def reshow(self, ctx, host=None, guild=None):
        if ctx is None:
            author = host
        else:
            author = ctx.author
        data = await tools.read_sessions()
        # session_code = await self.get_session_code(author)
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(author)

        dms = await self.get_session(author)
        per_group = data[session_code]['members per group']

        groups = data[session_code]['groups']
        embed = discord.Embed(title=f'Groups Updated for Session {session_code}',
                              color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)

        for place, group in groups.items():
            members = []
            if len(group) == 0:
                group = None
                place = f'Group {place} (0/{per_group})'
            else:
                for uid in group:
                    if ctx is None:
                        member = discord.utils.get(guild.members, id=uid)
                    else:
                        member = discord.utils.get(ctx.guild.members, id=uid)
                    reviewer_rank = await tools.get_reviewer_rank(db.get_reviews_given(member))
                    members.append(f'{member.display_name} (rank: *{reviewer_rank}*)')
            if group is not None:
                group = '\n'.join(members)
                place = f'Group {place} ({len(members)}/{per_group})'
            embed.add_field(name=f'{place}', value=group, inline=False)
        await dms.send(embed=embed)

    @commands.command()
    async def leave(self, ctx, session_code):
        if await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are hosting a Session.'))
            return
        data = await tools.read_sessions()
        dms = await self.get_session(self.client.get_user(data[session_code]['host']))
        groups = data[session_code]['groups']
        for place, member_list in groups.items():
            if ctx.author.id in member_list:
                member_list.remove(ctx.author.id)
                await ctx.author.send(embed=tools.single_embed(f'You have left **Session {session_code}**.'))
                await dms.send(embed=tools.single_embed(f'{ctx.author.display_name} has **left** your queue.'))
                await tools.write_sessions(data)
                await self.reshow(ctx=None, host=ctx.author.id)
                # await self.promote(session_code)
                return
        await ctx.send(embed=tools.single_embed(f'You do not appear to be in a Session.'))

    async def promote(self, session_code):
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

    async def is_host(self, member_obj):
        (session_code, host, notification, session, ban_list, message_id,
         dodo_code, max_entries, per_group, welcome, groups, afk, minutes) = await self.get_dms_session(member_obj)
        if session_code is not None:
            return True
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # if payload isn't turnip
        if payload.emoji.id != _turnip_emoji:
            return

        # on private DM reaction
        if payload.guild_id is None:
            return

        guild = self.client.get_guild(payload.guild_id)
        author = discord.utils.get(guild.members, id=payload.user_id)
        # if bot reacts
        if author == self.client.user:
            return

        data = await tools.read_sessions()
        for session_code, value in data.items():
            # if session doesn't have a message ID, guest cannot join anyway
            check = value.get('message id', None)
            if check is None:
                continue
            # if reaction is to the session's message
            elif value['message id'] == payload.message_id:
                # if await self.is_host(author):
                #     msg = f'You cannot **join** a session if you are **Hosting**.'
                #     await author.send(embed=tools.single_embed_neg(msg))
                #     return

                # session_code = session_code.upper()
                # session = data[session_code]

                # if author.id == data[session_code]['host']:
                #     await author.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                #     return

                ban_list = data[session_code]['ban list']
                if author.id in ban_list:
                    msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                    await author.send(embed=tools.single_embed_neg(msg))
                    return

                for place, group in data[session_code]['groups'].items():
                    if author.id in group:
                        msg = f'You have already joined Session **{session_code}**.'
                        await author.send(embed=tools.single_embed(msg))
                        return

                members_per_group = data[session_code]['members per group']
                for place, group in data[session_code]['groups'].items():
                    if len(group) < members_per_group:
                        group.append(author.id)
                        prefix = await self.show_prefix(guild)
                        msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                              f'You can use `{prefix}leave {session_code}` at any time to leave this Session.'
                        await author.send(embed=tools.single_embed(msg))
                        msg = f'**{author.display_name}** has joined **Group {place}**.'
                        dms = self.client.get_channel(data[session_code]['session'])
                        await dms.send(embed=tools.single_embed(msg))
                        await tools.write_sessions(data)
                        host = self.client.get_user(data[session_code]['host'])
                        await self.reshow(ctx=None, host=host, guild=guild)
                        return

                await author.send(f'Sorry, the Session you are trying to join is full.')

    async def wizard_end(self, ctx):
        data = await tools.read_sessions()

        session_to_close = []
        for session_code, value in data.items():
            if value['host'] == ctx.author.id:
                session_to_close.append(session_code)
                channel = self.client.get_channel(value['session'])

                # edit private session notification if available
                msg = f'Private Session **closed**.'
                await tools.edit_msg(
                    self.client.get_channel(value['notification'][1]),
                    value['notification'][0],
                    msg, delete_after=30
                )
                if channel is not None:
                    await tools.close_private_channel(channel)

                # edit sell embed if available
                try:
                    msg = f'Session **{session_code}** is now **closed**.'
                    await tools.edit_msg(
                        self.client.get_channel(_dms_channel),
                        value['message id'],
                        msg, delete_after=30
                    )
                except KeyError:
                    pass

                try:
                    groups = data[session_code]['groups']
                    for place, member_list in groups.items():
                        for uid in member_list:
                            member = self.client.get_user(uid)
                            msg = f'Session **{session_code}** was **closed** by the host.'
                            await member.send(embed=tools.single_embed(msg))
                except KeyError:
                    pass

        for code in session_to_close:
            del data[code]
            await tools.write_sessions(data)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # click the turnip to leave the session
        # print(payload)
        return

    @kick.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed_neg(f'{error}'))

    @leave.error
    async def on_command_error(self, ctx, error):
        prefix = await self.show_prefix(ctx.guild)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_neg(f'Please enter a Session code.\n`{prefix}leave code`'))

    @ban.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_neg(f'{error}'))


def setup(client):
    client.add_cog(DMS(client))
