import asyncio
import inspect

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
        """
        Create a DMS session and generate the wizard
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
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
            "ban list": [],
            "message id": 0,
            "dodo code": None,
            "max entries": 0,
            "members per group": 0,
            "welcome": None,
            "groups": {},
            "auto": {'active': False, 'minutes': 0},
            "closed": False
        }
        await tools.write_sessions(data)
        await self.wizard(ctx, dms, session_code)

        host_menu = f'**Daisy-Mae Session Commands**\n\n' \
                    f'`{prefix}send` to send out codes to the next group in the queue\n' \
                    f'`{prefix}close` to close the session off to **new** guests\n' \
                    f'`{prefix}open` to open the session back up to **new** guests\n' \
                    f'`{prefix}end` to end the session.\n' \
                    f'`{prefix}dodo code` change your dodo `code`. ex: `{prefix}dodo ABCDEF`\n' \
                    f'`{prefix}show` to show the current queue\n' \
                    f'`{prefix}notify message` send a message to everyone in your queue\n' \
                    f'`{prefix}welcome message` set a message for your guests\n\n' \
                    f'`{prefix}guest_kick member` to kick `member` from the queue.\n' \
                    f'`{prefix}guest_bans` show current list of banned members\n' \
                    f'`{prefix}guest_ban member` ban a `member` and prevent them from joining again \n' \
                    f'`{prefix}guest_unban member` unban a `member`\n\n' \
                    f'`{prefix}menu` to see these options again\n' \
                    f'`{prefix}auto num` set an auto timer that sends the next group every `num` minutes.\n'\
                    f'`{prefix}auto stop` stop an auto timer.'

        await dms.send(embed=tools.single_embed(host_menu, avatar=self.client.user.avatar_url))

    async def wizard(self, ctx, dms, session_code):
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
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
        msg = '**How Many Groups?**\nPlease enter the maximum number of groups you will accept between `1` and `100`.'
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
                f'**Groups**: {max_entries}\n' \
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

        for i in range(max_entries):
            print(i)
            groups[i + 1] = []

        print(groups)
        new_data = {
            "message id": session_message,
            "dodo code": dodo.upper(),
            "max entries": max_entries,
            "members per group": per_group,
            "welcome": welcome,
            "groups": groups,
        }

        for k, v in new_data.items():
            data[session_code][k] = v

        await tools.write_sessions(data)
        return session_code

    @commands.command(aliases=['open'])
    async def _open(self, ctx):
        """
        Open a closed session
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            msg = f'You cannot run this command if you are not hosting a Session.'
            await ctx.send(embed=tools.single_embed_neg(msg))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        notification = data[session_code]['notification']
        data[session_code]['closed'] = False
        await tools.write_sessions(data)

        channel = self.client.get_channel(data[session_code]['session'])
        await channel.send(embed=tools.single_embed(f'Your session has been **reopened** to new guests.'))
        msg = f'Private Session **closed**.'
        await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)

        # edit sell embed if available
        msg = f'Session **{session_code}** has **reopened**.'
        await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def admin_end(self, ctx, session_code):
        """
        Close a session and prevent guests from joining
        :param ctx:
        :param session_code:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        data = await tools.read_sessions()
        try:
            data[session_code]
        except KeyError:
            await ctx.send(embed=tools.single_embed(f'That session does not exist.'))
            return

        notification = data[session_code]['notification']
        data[session_code]['closed'] = True
        await tools.write_sessions(data)

        channel = self.client.get_channel(data[session_code]['session'])
        await tools.close_private_channel(channel)
        msg = f'Private Session **ended**.'
        await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)

        # edit sell embed if available
        try:
            msg = f'Session **{session_code}** has **ended**.'
            await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)
        except Exception as e:
            print(e, ' ending session ' + session_code)

        del data[session_code]
        await tools.write_sessions(data)

    @commands.command()
    async def close(self, ctx):
        """
        Close a session and prevent guests from joining
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        notification = data[session_code]['notification']
        data[session_code]['closed'] = True
        await tools.write_sessions(data)

        channel = self.client.get_channel(data[session_code]['session'])
        await channel.send(embed=tools.single_embed(f'Your session has been **closed** to new guests.'))
        msg = f'Private Session **closed**.'
        await tools.edit_msg(self.client.get_channel(notification[1]), notification[0], msg)

        # edit sell embed if available
        msg = f'Session **{session_code}** is currently **closed**.'
        await tools.edit_msg(self.client.get_channel(_dms_channel), data[session_code]['message id'], msg)

    @commands.command()
    async def end(self, ctx):
        """
        End a session
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
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
                    msg = f'Session **{session_code}** has **ended**.'
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
                            msg = f'Session **{session_code}** was **ended** by the host.'
                            await member.send(embed=tools.single_embed(msg))
                except KeyError:
                    pass

        for code in session_to_close:
            del data[code]
            await tools.write_sessions(data)

    @commands.command()
    async def dodo(self, ctx, *, dodo):
        """
        Change the session's dodo code
        :param ctx:
        :param dodo:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        for session_code, value in data.items():
            if value['host'] == ctx.author.id:
                value['dodo code'] = dodo.upper()
                dms_channel = await self.get_session_channel(ctx.author)
                await dms_channel.send(embed=tools.single_embed(f'Your Dodo code has been changed to **{dodo.upper()}**'))
        await tools.write_sessions(data)

    @commands.command()
    async def welcome(self, ctx, *, message):
        """
        Set a welcome message. This message is sent to users when they get their dodo code
        :param ctx:
        :param message:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        prefix = await self.show_prefix(ctx.guild)
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        data[session_code]['welcome'] = message
        await tools.write_sessions(data)
        msg = f'Your **welcome** message has been set to:\n' \
              f'"{message}"\n' \
              f'Members will receive it when you use the `{prefix}send` command.'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command()
    async def menu(self, ctx):
        """
        Display a menu of possible host commands
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        prefix = await self.show_prefix(ctx.guild)
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        host_menu = f'**Daisy-Mae Session Commands**\n\n' \
                    f'`{prefix}send` to send out codes to the next group in the queue\n' \
                    f'`{prefix}close` to close the session off to **new** guests\n' \
                    f'`{prefix}open` to open the session back up to **new** guests\n' \
                    f'`{prefix}end` to end the session.\n' \
                    f'`{prefix}dodo code` change your dodo `code`. ex: `{prefix}dodo ABCDEF`\n' \
                    f'`{prefix}show` to show the current queue\n' \
                    f'`{prefix}notify message` send a message to everyone in your queue\n' \
                    f'`{prefix}welcome message` set a message for your guests\n\n' \
                    f'`{prefix}guest_kick member` to kick `member` from the queue.\n' \
                    f'`{prefix}guest_bans` show current list of banned members\n' \
                    f'`{prefix}guest_ban member` ban a `member` and prevent them from joining again \n' \
                    f'`{prefix}guest_unban member` unban a `member`\n\n' \
                    f'`{prefix}menu` to see these options again\n' \
                    f'`{prefix}auto num` set an auto timer that sends the next group every `num` minutes.\n'\
                    f'`{prefix}auto stop` stop an auto timer.'
        dms_channel = await self.get_session_channel(ctx.author)
        await dms_channel.send(embed=tools.single_embed(host_menu, avatar=self.client.user.avatar_url))

    @commands.command()
    async def auto(self, ctx, minutes):
        """
        Create a looping auto timer that sends dodo codes every n minutes unless the next group is empty.
        :param ctx:
        :param minutes: Number of minutes before sending the next code. Use 'stop' to end the timer.
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        await ctx.send(embed=tools.single_embed_neg(f'Auto has been turned off for now. Please pardon our dust.'))
        return
        #
        # if not await self.is_host(ctx.author):
        #     await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
        #     return
        #
        # prefix = await self.show_prefix(ctx.guild)
        # session_code = await self.get_session_code(ctx.author)
        # dms_channel = await self.get_session_channel(ctx.author)
        #
        # # stop the timer and notify guests
        # if minutes.lower() == 'stop':
        #     data = await tools.read_sessions()
        #     data[session_code]['auto']['active'] = False
        #     await tools.write_sessions(data)
        #     await ctx.send(embed=tools.single_embed_neg(f'Your auto session was ended.'))
        #
        #     members_to_notify = []
        #     for place, member_list in data[session_code]['groups'].items():
        #         for uid in member_list:
        #             members_to_notify.append(uid)
        #
        #     for uid in members_to_notify:
        #         member = self.client.get_user(uid)
        #         msg = f'Your host for session **{session_code}** has turned off their **auto** timer.'
        #         await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        #     return
        #
        # # set the loop for n minutes and begin loop
        # else:
        #     try:
        #         minutes = int(minutes)
        #         if minutes < 1:
        #             await ctx.send(embed=tools.single_embed_neg(f'Please choose an integer greater than `0`.'))
        #             return
        #     except Exception as e:
        #         print(e)
        #         await ctx.send(embed=tools.single_embed_neg(f'Minutes must be an integer.'))
        #         return
        #
        #     msg = f'Your auto timer is set to {minutes} minutes. Every {minutes} minutes, a group will be sent ' \
        #           f'until you run out of groups or you enter `{prefix}auto stop`.'
        #     await ctx.send(embed=tools.single_embed(msg))
        #
        #     data = await tools.read_sessions()
        #     data[session_code]['auto']['active'] = True
        #     data[session_code]['auto']['minutes'] = minutes
        #     await tools.write_sessions(data)
        #
        #     while True:
        #         data = await tools.read_sessions()
        #         welcome = data[session_code]['welcome']
        #         dodo_code = data[session_code]['dodo code']
        #         auto = data[session_code]['auto']
        #         groups = data[session_code]['groups']
        #
        #         # recheck the session every loop to determine if the timer has been turned off
        #         if auto is False:
        #             return
        #
        #         # send invite to group when auto timer clicks
        #         if len(groups) >= 1:
        #             place = list(groups.keys())[0]
        #             if len(groups[place]) > 0:
        #
        #                 await dms_channel.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'))
        #
        #                 for user in data[session_code]['groups'][place]:
        #                     member = self.client.get_user(int(user))
        #                     if member is None:
        #                         continue
        #                     msg = f'You have gotten your Session Code for **{ctx.author.display_name}\'s** Session!\n' \
        #                           f'Please do not forget to leave a review for your host when you finish.\n' \
        #                           f'**Dodo Code**: `{dodo_code}`\n'
        #                     if welcome is not None:
        #                         msg += f'\n\n**Your host left you a message!**\n"{welcome}"'
        #                     await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        #                 del data[session_code]['groups'][place]
        #                 await tools.write_sessions(data)
        #
        #                 # notify groups that they have moved up
        #                 for place, member_list in data[session_code]['groups'].items():
        #                     for uid in member_list:
        #                         member = self.client.get_user(uid)
        #                         position = list(groups.keys()).index(place) + 1
        #                         msg = f'Your group in **Session {session_code}** has moved up! \n' \
        #                               f'You are now in **Position** `{position}` of `{len(list(groups.keys()))}`.\n' \
        #                               f'**note**: Your host is using an auto timer. Dodo codes will be sent every {minutes} ' \
        #                               f'minute(s). \n__Please conduct your business as quickly as possible__.'
        #                         await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        #                 try:
        #                     await self.reshow(ctx.author)
        #                 except Exception as e:
        #                     print(f'An error occurred when trying to reshow during auto {e}')
        #                 await asyncio.sleep(60 * data[session_code]['auto']['minutes'])
        #         else:
        #             await dms_channel.send(embed=tools.single_embed(f'Your auto session has ended.'))
        #             return

    @commands.command()
    async def show(self, ctx):
        """
        Display a list of groups and guests in the host's DMS
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)

        embed = discord.Embed(title=f'Groups in Queue for Session {session_code}', color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)

        per_group = data[session_code]['members per group']
        dms_channel = await self.get_session_channel(ctx.author)

        if len(data[session_code]['groups'].keys()) < 1:
            msg = f'You are at the end of your groups. Consider starting a new session.'
            await dms_channel.send(embed=tools.single_embed(msg))
            return

        for place, group in data[session_code]['groups'].items():
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
        await dms_channel.send(embed=embed)

    async def get_session_channel(self, dms_host):
        data = await tools.read_sessions()
        for k, v in data.items():
            if v['host'] == dms_host.id:
                return self.client.get_channel(v['session'])

    @staticmethod
    async def get_session_code(author):
        data = await tools.read_sessions()
        for session_code, values in data.items():
            if values['host'] == author.id:
                return session_code

    @commands.command()
    async def guest_kick(self, ctx, member: discord.Member):
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)

        user_removed = False
        groups = data[session_code]['groups']
        for place, member_list in groups.items():
            for uid in member_list:
                if self.client.get_user(uid) == member:
                    member_list.remove(uid)
                    user_removed = True

        if user_removed:
            await tools.write_sessions(data)
            await dms_channel.send(embed=tools.single_embed(f'Member **{member.mention}** kicked from session.'))
            await member.send(embed=tools.single_embed_neg(f'You have been removed from **Session {session_code}**'))
            await self.reshow(ctx.author)
        else:
            await dms_channel.send(embed=tools.single_embed_neg(f'Unable to find and kick **{member}**.'))

    @commands.command()
    async def send(self, ctx):
        """
        Send a dodo code to the next group in a DMS queue
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)

        welcome = data[session_code]['welcome']
        groups = data[session_code]['groups']
        place = list(groups.keys())[0]
        await dms_channel.send(embed=tools.single_embed(f'Sending Dodo code to **Group {place}**'))

        for user in data[session_code]['groups'][place]:
            try:
                member = self.client.get_user(int(user))
                if member is None:
                    continue
                msg = f'You have gotten your Session Code for **{ctx.author.display_name}\'s** Session!\n' \
                      f'Please do not forget to leave a review for your host when you finish.\n'\
                      f'**Dodo Code**: `{data[session_code]["dodo code"]}`\n'
                if welcome is not None:
                    msg += f'\n\n**Your host left you a message!**\n"{welcome}"'
                await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
            except Exception as e:
                print(f'an error occurred when sending a dodo code: {e}')
        del data[session_code]['groups'][place]
        await tools.write_sessions(data)

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
        try:
            await self.reshow(ctx.author)
        except Exception as e:
            print(f'An error occurred when trying to reshow in the send command in channel {ctx.channel}: {e}')

    @commands.command()
    async def notify(self, ctx, group: str = None, *, message):
        """
        Send a DM to guests in a DMS queue
        :param ctx:
        :param group: The group to send a message to, if any
        :param message:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)
        groups = data[session_code]['groups']

        members_to_notify = []
        try:
            # try to send messages to a single group if possible.
            # This fails if the first arg isn't an integer
            int(group)
            for uid in groups.get(str(group)):
                members_to_notify.append(uid)
        except ValueError:
            # if a group isn't identified, send the message
            # to all guests in the queue
            for place, member_list in groups.items():
                for uid in member_list:
                    members_to_notify.append(uid)

        for uid in members_to_notify:
            member = self.client.get_user(uid)
            if member is None:
                continue
            msg = f'You\'ve received a message from your Session host **{ctx.author.display_name}**:\n' \
                  f'"{message}"'
            await member.send(embed=tools.single_embed(msg, avatar=self.client.user.avatar_url))
        await dms_channel.send(embed=tools.single_embed(f'Your message has been sent.'))

    @commands.command()
    async def guest_ban(self, ctx, member: discord.Member):
        """
        Remove a guest from the queue and add them to the ban list to prevent them from rejoining.
        :param ctx:
        :param member:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)
        ban_list = data[session_code]['ban list']

        data = await tools.read_sessions()
        if member.id not in ban_list:
            data[session_code]['ban list'].append(member.id)
        else:
            await dms_channel.send(embed=tools.single_embed(f'**{member.mention}** is already banned from your session.'))
            return
        for place, member_list in data[session_code]['groups'].items():
            if member.id in member_list:
                member_list.remove(member.id)
                await member.send(embed=tools.single_embed(f'You have been removed from Session **{session_code}**'))
        await tools.write_sessions(data)
        await dms_channel.send(embed=tools.single_embed(f'You have banned **{member.mention}** from your session.'))
        await self.reshow(ctx.author)

    @commands.command()
    async def guest_unban(self, ctx, member: discord.Member):
        """
        Remove a guest from the ban list
        :param ctx:
        :param member:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return
        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)

        if member.id in data[session_code]['ban list']:
            data[session_code]['ban list'].remove(member.id)
            await tools.write_sessions(data)
            await ctx.send(embed=tools.single_embed(f'You have unbanned **{member.mention}** from your session.'))
            member = self.client.get_user(member.id)
            await member.send(embed=tools.single_embed(f'You have been unbanned from Session **{session_code}**'))
        else:
            await dms_channel.send(embed=tools.single_embed(f'**{member.mention}** is not in the ban list.'))

    @commands.command()
    async def guest_bans(self, ctx):
        """
        Show a list of currently banned guests
        :param ctx:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        if not await self.is_host(ctx.author):
            await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are not hosting a Session.'))
            return

        data = await tools.read_sessions()
        session_code = await self.get_session_code(ctx.author)
        dms_channel = await self.get_session_channel(ctx.author)
        ban_list = data[session_code]['ban list']

        banned = '\n'.join([discord.utils.get(ctx.guild.members, id=m).display_name for m in ban_list])
        if len(banned) is 0:
            banned = None
        await dms_channel.send(embed=tools.single_embed(f'**Banned Members**\n{banned}', avatar=self.client.user.avatar_url))

    @commands.command()
    async def join(self, ctx, session_code: str):
        """
        GUEST ACTION
        Join a host's DMS session using the provided session code
        :param ctx:
        :param session_code:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        prefix = await self.show_prefix(ctx.guild)
        session_code = session_code.upper()
        data = await tools.read_sessions()

        if await self.is_host(ctx.author) and ctx.author.id != 193416878717140992:
            await ctx.send(embed=tools.single_embed_neg(f'You cannot **join** a session if you are **Hosting**.'))
            return

        # if session does not exist, notify the guest
        try:
            data[session_code]
        except KeyError:
            await ctx.send(embed=tools.single_embed(f'That session does not exist.'))

        if data[session_code]['closed']:
            await ctx.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
            return

        host = discord.utils.get(ctx.guild.members, id=data[session_code]['host'])
        dms_channel = await self.get_session_channel(host)

        if ctx.author.id == host.id and ctx.author.id != 193416878717140992:
            await ctx.send(embed=tools.single_embed(f'You cannot join your own Session.'))
            return

        if ctx.author.id in data[session_code]['ban list']:
            msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
            await ctx.author.send(embed=tools.single_embed_neg(msg))
            return

        groups = data[session_code]['groups']
        for place, group in groups.items():
            if ctx.author.id in group and ctx.author.id != 193416878717140992:
                msg = f'You have already joined Session **{session_code}**.'
                await ctx.send(embed=tools.single_embed(msg))
                return

        for place, group in groups.items():
            if len(group) < data[session_code]['members per group']:
                print('x')
                group.append(ctx.author.id)
                msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                      f'You can use `{prefix}leave {session_code}` at any time to leave this Session.'
                await ctx.send(embed=tools.single_embed(msg))
                msg = f'**{ctx.author.display_name}** has joined **Group {place}**.'
                await dms_channel.send(embed=tools.single_embed(msg))
                await tools.write_sessions(data)
                await self.reshow(host)
                return
            else:
                continue

        await ctx.send(f'Sorry, the Session you are trying to join is full.')

    @commands.command()
    async def leave(self, ctx, session_code):
        """
        GUEST ACTION
        Leave a DMS queue with the corresponding session code
        :param ctx:
        :param session_code:
        :return:
        """
        # if await self.is_host(ctx.author):
        #     await ctx.send(embed=tools.single_embed_neg(f'You cannot run this command if you are hosting a Session.'))
        #     return

        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        data = await tools.read_sessions()
        session_code = session_code.upper()

        # get host because this is called by guests
        host = discord.utils.get(ctx.guild.members, id=data[session_code]['host'])
        dms_channel = await self.get_session_channel(host)

        groups = data[session_code]['groups']
        for place, group in groups.items():
            if ctx.author.id in group:
                print('gr', group, ctx.author.id)

                data[session_code]['groups'][place].remove(ctx.author.id)
                await ctx.author.send(embed=tools.single_embed(f'You have left **Session {session_code}**.'))
                await dms_channel.send(embed=tools.single_embed(f'{ctx.author.display_name} has **left** your queue.'))
                await tools.write_sessions(data)
                host = discord.utils.get(ctx.guild.members, id=data[session_code]['host'])
                await self.reshow(host)
                return
            else:
                continue

        # groups = data[session_code]['groups']
        # for place, member_list in groups.items():
        #     if ctx.author.id in member_list:
        #         member_list.remove(ctx.author.id)
        #
        #         await tools.write_sessions(data)
        #         await self.reshow(host)
        #         return
        await ctx.send(embed=tools.single_embed(f'You do not appear to be in a Session.'))

    async def reshow(self, host):
        """
        Show current groups and guests. Usually called after a host action but can be triggered by
        join or leave which requires the host arg
        :param host: Required because this can be called by guest actions
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        data = await tools.read_sessions()
        session_code = await self.get_session_code(host)
        dms_channel = await self.get_session_channel(host)

        groups = data[session_code]['groups']
        per_group = data[session_code]['members per group']

        if len(data[session_code]['groups'].keys()) < 1:
            msg = f'You are at the end of your groups. Consider starting a new session.'
            await dms_channel.send(embed=tools.single_embed(msg))
            return

        embed = discord.Embed(title=f'Groups Updated for Session {session_code}', color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)

        for place, group in groups.items():
            members = []
            if len(group) == 0:
                group = None
                place = f'Group {place} (0/{per_group})'
            else:
                for uid in group:
                    member = discord.utils.get(host.guild.members, id=uid)
                    if member is None:
                        data[session_code]['groups'][place].remove(uid)
                        continue
                    else:
                        reviewer_rank = await tools.get_reviewer_rank(db.get_reviews_given(member))
                        members.append(f'{member.display_name} (rank: *{reviewer_rank}*)')
                        # members.append(f'{member.display_name}')
            if group is not None:
                group = '\n'.join(members)
                place = f'Group {place} ({len(members)}/{per_group})'
            embed.add_field(name=f'{place}', value=group, inline=False)
        await dms_channel.send(embed=embed)

    async def promote(self, session_code):
        """
        Notify groups in a queue that they have moved up one position
        :param session_code:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
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

    async def is_host(self, member):
        session_code = await self.get_session_code(member)
        if session_code is not None:
            return True
        return False

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Allow a guest to join a session by using reactions
        :param payload:
        :return:
        """
        print(inspect.stack()[1][3], '->', inspect.stack()[0][3])
        # if payload isn't turnip
        if payload.emoji.id != _turnip_emoji:
            return

        # ignore DMs
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
                if await self.is_host(author):
                    msg = f'You cannot **join** a session if you are **Hosting**.'
                    await author.send(embed=tools.single_embed_neg(msg))
                    return

                if author.id == data[session_code]['host']:
                    await author.send(embed=tools.single_embed(f'You cannot join your own Session.'))
                    return

                ban_list = data[session_code]['ban list']
                if author.id in ban_list:
                    msg = f'I\'m sorry. You are unable to join Session **{session_code}**.'
                    await author.send(embed=tools.single_embed_neg(msg))
                    return

                opn = data[session_code]['closed']
                if opn and payload.user_id != 193416878717140992:
                    await author.send(embed=tools.single_embed(f'This session is currently closed to new guests.'))
                    return

                for place, group in data[session_code]['groups'].items():
                    if author.id in group and payload.user_id != 193416878717140992:
                        msg = f'You have already joined Session **{session_code}**.'
                        await author.send(embed=tools.single_embed(msg))
                        return

                groups = data[session_code]['groups']
                for place, group in groups.items():
                    if len(group) < data[session_code]['members per group']:
                        group.append(author.id)
                        prefix = await self.show_prefix(guild)
                        msg = f'You have joined **Group {place}** in Session **{session_code}**\n' \
                              f'You can use `{prefix}leave {session_code}` at any time to leave this Session.'
                        await author.send(embed=tools.single_embed(msg))
                        msg = f'**{author.display_name}** has joined **Group {place}**.'
                        dms = self.client.get_channel(data[session_code]['session'])
                        await dms.send(embed=tools.single_embed(msg))
                        await tools.write_sessions(data)
                        host = discord.utils.get(guild.members, id=data[session_code]['host'])
                        await self.reshow(host)
                        return
                    else:
                        continue

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
        return

    @join.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, AttributeError):
            func = inspect.stack()[1][3]
            await print(func + ' ' + error)

    @guest_kick.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed_neg(f'{error}'))

    @leave.error
    async def on_command_error(self, ctx, error):
        prefix = await self.show_prefix(ctx.guild)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_neg(f'Please enter a Session code.\n`{prefix}leave code`'))

    @guest_ban.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_neg(f'{error}'))


def setup(client):
    client.add_cog(DMS(client))
