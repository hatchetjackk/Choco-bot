import asyncio
import util.db as database
import util.tools as tools
import discord
from datetime import datetime
from discord.ext import commands, tasks

mention_counter = {}
attachment_counter = {}


class Automoderator(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.spam_reset.start()

    @commands.group(aliases=['automod'])
    @commands.is_owner()
    async def automoderator(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @automoderator.group(aliases=['reload'])
    async def restart(self, ctx):
        print('Unloading automoderator')
        self.client.unload_extension('cogs.automoderator')
        print('Cancelling loops')
        self.spam_reset.cancel()
        print('Loading automoderator')
        self.client.load_extension('cogs.automoderator')
        await ctx.send(embed=tools.single_embed('Automoderator reloaded'))

    @commands.command()
    @commands.is_owner()
    async def react_role(self, ctx):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == ctx.channel

        def check(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        prompt = await ctx.send(embed=tools.single_embed('What is your message?'))
        msg = await self.client.wait_for('message', check=check_msg)
        message = msg.content
        await msg.delete()

        await prompt.edit(embed=tools.single_embed(f'Message: {message}\n'f'Choose a reaction'))
        reaction, member = await self.client.wait_for('reaction_add', check=check)

        await prompt.edit(embed=tools.single_embed(f'Message: {message}\n'f'Choose a role'))
        msg = await self.client.wait_for('message', check=check_msg)
        role = msg.content
        await msg.delete()

        await prompt.edit(embed=tools.single_embed(f'Message: {message}\n'
                                                   f'Role: {role}\n'
                                                   f'Enter yes to confirm or no to cancel.\n'
                                                   f'This will timeout in 60 seconds.'))
        await prompt.add_reaction(reaction)
        try:
            msg = await self.client.wait_for('message', check=check_msg, timeout=60)
            if 'yes' in msg.content:
                embed = discord.Embed(description=message, color=discord.Color.green())
                await prompt.edit(embed=embed)
            if 'no' in msg.content:
                await prompt.clear_reactions()
                await prompt.delete()
        except asyncio.TimeoutError:
            await prompt.clear_reactions()
            await prompt.delete()

        # tie reaction to the role

        # ask for a channel to post in

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name == after.display_name:
            return
        nicknames = [n[0] for n in database.get_member_nick_history(before)]
        if after.display_name in nicknames:
            return
        database.add_member_nick_history(before, after.display_name)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # find server stats channel
        try:
            member_stats = self.client.get_channel(706099708434841621)
            members = [m for m in member.guild.members if not m.bot]
            await member_stats.edit(name=f'Members: {len(members)}')
        except Exception as e:
            print(e)
            pass

        one_day = 86400
        eight_hours = 28800
        if tools.to_seconds(member.created_at) < eight_hours and member.premium_since is None:
            # if member.id == 702834544373530735:
            review = self.client.get_channel(707917383628619888)
            msg = f'{member.mention} has been flagged as a new account. Please review this user.'
            embed = discord.Embed(description=msg, color=discord.Color.red())
            embed.set_thumbnail(url=member.avatar_url)
            embed.add_field(name='Joined Discord', value=member.created_at, inline=False)
            embed.add_field(name='Joined Server', value=member.joined_at, inline=False)
            await review.send(embed=embed)

        await self.member_join_tutorial(member)

        if len(member.guild.members) % 1000 == 0:
            chan = self.client.get_channel(694013862667616310)
            msg = f'Welcome {member.mention} as our {len(member.guild.members)}th member!'
            await chan.send(embed=tools.single_embed(msg))
        database.add_member(member)

        # if admin cog is not set, do not give autorole
        if not database.admin_cog(member.guild):
            return
        autorole = database.get_autorole(member.guild)
        if autorole is not None:
            member.add_roles(autorole)
            spam = database.get_spam(member.guild)
            msg = f'{member.display_name} was given the role {autorole.name}'
            await spam.send(embed=tools.single_embed(msg))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            member_stats = self.client.get_channel(706099708434841621)
            members = [m for m in member.guild.members if not m.bot]
            await member_stats.edit(name=f'Members: {len(members)}')
        except Exception as e:
            print(e)
            pass

        if not database.admin_cog(member.guild):
            return
        spam = member.guild.system_channel
        embed = discord.Embed(description=f'{member.display_name} has left the server.', color=discord.Color.red())
        embed.set_thumbnail(url=member.avatar_url)
        await spam.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        spam = await guild.system_channel
        msg = f'{self.client.user.display_name} has joined {guild.name}'
        await spam.send(embed=tools.single_embed(msg))
        database.add_guild(guild)
        for member in guild.members:
            database.add_member(member)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not database.admin_cog(after.guild):
            return
        if before.guild is None:
            return
        spam = database.get_spam(after.guild)
        if before.author.bot or before.content.startswith('http') or before.content == '':
            return
        embed = discord.Embed(description=f'{before.author.display_name} edited a message in {before.channel.mention}')
        embed.set_thumbnail(url=before.author.avatar_url)
        embed.add_field(name='Before', value=before.content, inline=False)

        if len(after.content) > 1024:
            embed.add_field(name='After', value=after.content[:100] + '...', inline=False)
        else:
            embed.add_field(name='After', value=after.content, inline=False)

        await spam.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message is None:
            return
        if not database.admin_cog(message.guild):
            return
        if message.channel.id == 700538064224780298:
            return
        spam = database.get_spam(message.guild)
        if message.author.bot:
            return
        msg = f'**A message was deleted**\n'\
              f'Author: {message.author.display_name}\n'\
              f'Channel: {message.channel.mention}\n'\
              f'Message: {message.content}'
        embed = discord.Embed(color=discord.Color.red(), description=msg)
        embed.set_thumbnail(url=message.author.avatar_url)
        await spam.send(embed=embed)

    @staticmethod
    async def profanity_filter(message):
        filter_list = database.get_filter(message.guild)
        message = [w.lower() for w in message.content.split(' ')]
        if any(w in ''.join(message).replace(' ', '') for w in filter_list):
            return True

    @commands.Cog.listener()
    async def on_message(self, message):
        # search messages for discord links
        if message is None or message.author.bot:
            return

        # verify admin cog is on
        if not database.admin_cog(message.guild):
            return

        # check for mention spamming
        spam_kick = 5
        spam_notify = 3
        if len(message.mentions) > 0:
            global mention_counter
            if message.author.bot or message.author.permissions_in(message.channel).manage_messages:
                pass
            elif message.author.id not in mention_counter:
                mention_counter[message.author.id] = 1
            else:
                admin_channel = database.get_administrative(message.guild)
                mention_counter[message.author.id] += 1

                if mention_counter[message.author.id] >= spam_kick:
                    msg = f'{message.author.mention} has been kicked for spamming mentions.'
                    embed = discord.Embed(description=msg, color=discord.Color.red())
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                    await admin_channel.send(embed=embed)
                    await message.author.kick(reason='Spamming mentions')

                elif mention_counter[message.author.id] == spam_notify:
                    msg = f'Please stop spamming mentions! If you keep doing this you may be auto-kicked.'
                    try:
                        await message.author.send(embed=tools.single_embed_neg(msg))
                    except discord.Forbidden:
                        await message.channel.send(embed=tools.single_embed_neg(message.author.mention + ' ' + msg))
                    msg = f'{message.author.mention} has been notified that they are spamming mentions.\n' \
                          f'[Jump to Message]({message.jump_url})'
                    embed = discord.Embed(description=msg, color=discord.Color.red())
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                    await admin_channel.send(embed=embed)

        if len(message.attachments) > 0:
            global attachment_counter
            if message.author.bot or message.author.permissions_in(message.channel).administrator:
                pass
            elif message.author.id not in attachment_counter:
                attachment_counter[message.author.id] = 1
            else:
                admin_channel = database.get_administrative(message.guild)
                attachment_counter[message.author.id] += 1

                if attachment_counter[message.author.id] >= spam_kick:
                    msg = f'{message.author.mention} has been kicked for spamming attachments.'
                    embed = discord.Embed(description=msg, color=discord.Color.red())
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                    await admin_channel.send(embed=embed)
                    await message.author.kick(reason='Spamming attachments')

                elif attachment_counter[message.author.id] == spam_notify:
                    msg = f'Please stop spamming attachments! If you keep doing this you may be auto-kicked.'
                    await message.author.send(embed=tools.single_embed_neg(msg))
                    msg = f'{message.author.mention} has been notified that they are spamming attachments.\n' \
                          f'[Jump to Message]({message.jump_url})'
                    embed = discord.Embed(description=msg, color=discord.Color.red())
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                    await admin_channel.send(embed=embed)

        if await self.profanity_filter(message) and not message.author.permissions_in(message.channel).manage_messages:
            staff_support = database.get_administrative(message.guild)
            description = f'Author: {message.author.mention} \n' \
                          f'Message: "{message.content}" \n' \
                          f'[Jump to Message]({message.jump_url})'
            embed = discord.Embed(title='Slur/Profanity Detected', description=description, color=discord.Color.red())
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
            try:
                url = message.attachments[0].url
                embed.set_image(url=url)
            except IndexError:
                pass
            options = ['🚫', '⚠️', '⭕', '❌']
            value = '🚫: Kick\n' \
                    '⚠️: Warn\n' \
                    '⭕: Ignore\n' \
                    '❌: Delete'
            embed.add_field(name='Staff Options', value=value)
            prompt = await staff_support.send(embed=embed)

            def check_react(react, actor):
                return react.message.id == prompt.id and not actor.bot and actor.permissions_in(staff_support).kick_members

            while True:
                embed.remove_field(1)

                for r in options:
                    await prompt.add_reaction(r)
                reaction, reactor = await self.client.wait_for('reaction_add', check=check_react)

                # kick
                if reaction.emoji == options[0]:
                    await prompt.clear_reactions()
                    embed.add_field(
                        name='Confirm',
                        value=f'Are you sure you want to **kick** {message.author.display_name}?', inline=False)
                    await prompt.edit(embed=embed)
                    await prompt.add_reaction('✅')
                    await prompt.add_reaction('❌')
                    reaction, reactor = await self.client.wait_for('reaction_add', check=check_react)

                    if reaction.emoji == '✅':
                        try:
                            msg = f'You have been kicked by an administrator or mod in {message.guild.name} for the ' \
                                  f'following content\n' \
                                  f'> "{message.content}"'
                            await message.author.send(embed=tools.single_embed_neg(msg))
                        except discord.Forbidden:
                            msg = f'{message.author.mention} has been kicked for inappropriate or obscene language.'
                            await message.channel.send(embed=tools.single_embed_neg(msg))

                        msg = f'{message.author.mention} has been kicked by **{reactor.display_name}**'
                        # remove confirmation dialogue
                        embed.remove_field(1)
                        embed.remove_field(0)
                        embed.add_field(name='Action', value=msg, inline=False)
                        await prompt.edit(embed=embed)
                        await prompt.clear_reactions()
                        await message.delete()
                        await message.author.kick(reason='inappropriate or obscene language')
                        break
                    elif reaction.emoji == '❌':
                        await prompt.clear_reactions()

                # warn
                elif reaction.emoji == options[1]:
                    embed.remove_field(1)
                    # embed.remove_field(0)
                    await prompt.clear_reactions()
                    embed.add_field(
                        name='Confirm',
                        value=f'Are you sure you want to **warn** {message.author.mention}?',
                        inline=False)
                    await prompt.edit(embed=embed)
                    await prompt.add_reaction('✅')
                    await prompt.add_reaction('❌')
                    reaction, reactor = await self.client.wait_for('reaction_add', check=check_react)
                    if reaction.emoji == '✅':
                        warning = 'inappropriate or obscene language'
                        database.add_warning(message.author, warning)

                        try:
                            msg = f'You have received a warning from an administrator or mod in {message.guild.name} for the ' \
                                  f'following content\n' \
                                  f'> "{message.content}"'
                            await message.author.send(embed=tools.single_embed_neg(msg))
                        except discord.Forbidden:
                            msg = f'{message.author.mention} has been given a warning for inappropriate language.'
                            await message.channel.send(embed=tools.single_embed_neg(msg))

                        # remove confirmation dialogue
                        embed.remove_field(1)
                        embed.remove_field(0)
                        warn = f'{message.author.display_name} was issued a warning by {reactor.display_name}'
                        embed.add_field(name='Action', value=warn, inline=False)
                        await prompt.edit(embed=embed)
                        await prompt.clear_reactions()
                        await message.delete()
                        break
                    elif reaction.emoji == '❌':
                        embed.remove_field(1)
                        embed.remove_field(0)
                        await prompt.clear_reactions()

                # ignore
                elif reaction.emoji == options[2]:
                    embed.remove_field(1)
                    embed.remove_field(0)
                    embed.add_field(name='Action',
                                    value=f'{message.author.display_name}\'s message was ignored by {reactor.display_name}',
                                    inline=False)
                    await prompt.edit(embed=embed)
                    await prompt.clear_reactions()
                    break

                elif reaction.emoji == options[3]:
                    try:
                        msg = f'Your message was deleted by a mod or admin for inappropriate content.\n' \
                              f'Your original message: "{message.content}"'
                        await message.author.send(embed=tools.single_embed_neg(msg))
                    except discord.Forbidden:
                        msg = f'{message.author.mention} your message was deleted by a mod or admin for inappropriate content.\n' \
                              f'Your original message: "{message.content}"'
                        await message.channel.send(embed=tools.single_embed_neg(msg))
                    embed.remove_field(1)
                    embed.remove_field(0)
                    deleted = f'{message.author.display_name}\'s message was deleted by {reactor.display_name}'
                    embed.add_field(name='Action', value=deleted, inline=False)
                    await prompt.edit(embed=embed)
                    await prompt.clear_reactions()
                    await message.delete()
                    break

        # ignore links created by moderators
        if message.author.guild_permissions.create_instant_invite:
            return

        # ignore this guild's invites
        for w in message.content.split(' '):
            if w in [f'https://discord.gg/{invite.code}' for invite in await message.guild.invites()]:
                return
            if w in [f'http://discord.gg/{invite.code}' for invite in await message.guild.invites()]:
                return

        blacklist = database.get_blacklist(message.guild)
        for b in blacklist:
            if b in message.content.lower():
                try:
                    await message.delete()
                    msg = f'You have entered a blacklisted link in **{message.guild.name}** ' \
                          f'Your message has been deleted.'
                    await message.author.send(embed=tools.single_embed_neg(msg))
                except Exception as e:
                    print(e)

        # if link found, delete and warn
        if 'https://discord.gg' in message.content or 'http://discord.gg' in message.content:
            try:
                await message.delete()
            except Exception as e:
                print(f'Could not delete message {message}: {e}')
            msg = f'Advertising other Discord servers is not allowed.'
            database.add_warning(message.author, msg)
            fmt = f'You have received an automatic warning for posting a Discord link in ' \
                  f'**{message.guild.name}**.\n> "{msg}"'
            await message.author.send(embed=tools.single_embed_neg(fmt))

        if 'https://turnip.exchange' in message.content or 'http://turnip.exchange' in message.content:
            try:
                await message.delete()
            except Exception as e:
                print(f'Could not delete message {message}: {e}')
            msg = f'Advertising Turnip Exchange links is not allowed.'
            database.add_warning(message.author, msg)
            fmt = f'You have received an automatic warning for posting a Turnip Exchange link in ' \
                  f'**{message.guild.name}**.\n> "{msg}"'
            await message.author.send(embed=tools.single_embed_neg(fmt))

            def check(react, user):
                return react.message.id == cache_msg.id and user.permissions_in(admin_channel).kick_members

            # if member's warnings are 2 or greater, commence a vote to kick
            warnings, messages = database.get_warnings(message.author)
            fmt = [f'{m[1]} - {m[0]}' for m in messages]
            if warnings >= 2:
                admin_channel = database.get_administrative(message.guild)
                msg = f'**{message.author.display_name}** has reached `{warnings}` warnings. Should they be kicked?\n' \
                      f'__Past Warnings__\n' + '\n'.join(fmt)
                embed = discord.Embed(color=discord.Color.red(), description=msg)
                embed.set_thumbnail(url=message.author.avatar_url)
                msg = await admin_channel.send(embed=embed)
                await msg.add_reaction('✔')
                await msg.add_reaction('❌')
                await asyncio.sleep(1)

                cache_msg = await admin_channel.fetch_message(msg.id)
                yes = 0
                while yes < 4:
                    reaction, member = await self.client.wait_for('reaction_add', check=check)
                    if reaction.emoji == '✔':
                        yes = reaction.count
                msg = f'You have been kicked from {message.guild.name}. The last warning was: "{message}"'
                await message.author.kick(reason=msg)
                await admin_channel.send(embed=tools.single_embed_neg(f'{message.author.display_name} has been kicked.'))

    async def member_join_tutorial(self, member):
        # if member.id != 702834544373530735:
        #     return
        overwrite = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True)
        }
        tutorial = await member.guild.create_text_channel(name='welcome-to-the-stalk-market', overwrites=overwrite)
        guest = member.guild.get_role(707939531529125898)
        await member.add_roles(guest)

        # tutorial embed
        def tut_embed(description, thumb=False):
            e = discord.Embed(description=description, color=discord.Color.green())
            if thumb:
                e.set_thumbnail(url=self.client.user.avatar_url)
            return e

        # greet member
        msg = f'Hi, {member.mention}! Welcome to the Stalk Market. I\'m {self.client.user.display_name}, and my job is ' \
              f'to help you get settled in to your new home. Please note that prompts have a 10 minute timeout!'
        embed = tut_embed(msg, True)
        await tutorial.send(embed=embed)
        await asyncio.sleep(3)

        # show rules
        msg = f'First, before we can open up the gates to our little Island, I have to go over the rules! Please read ' \
              f'them carefully before accepting.\n'
        rules = f'**1.** Be respectful of all members of the server. This includes staff. Treat others as you would ' \
                f'like to be treated.\n' \
                f'**2.** Keep it PG-15. No overtly sexual or mature language. You can swear but not at another member - ' \
                f'we don\'t want any fights!\n' \
                f'**3.** No spamming. This includes mentions, images, and messages.\n' \
                f'**4.** Keep all content in the appropriate channels please. This includes buying and selling.\n' \
                f'**5.** Advertising other Discord servers or your own social media platforms either through server ' \
                f'channels or member DMs is strictly prohibited. This includes but is not limited to Discord, Reddit, ' \
                f'Facebook, Twitter, Youtube, Twitch, and Instagram.\n' \
                f'**6.** No political or religious conversations.\n' \
                f'**7.** Absolutely no discrimination of any kind. This will result in an immediate ban. \n' \
                f'**8.** Entry fees are strictly forbidden. Tips are not mandatory, but they are appreciated.\n' \
                f'**9.** You are never permitted to share another user\'s dodo code in DMs, channels, or any other ' \
                f'platform.\n' \
                f'**10.** You are only allowed to send **one** (1) DM to a host. Host harassment will not be tolerated.\n' \
                f'**11.** You **must** leave a host review in #⭐-reviews-and-reports once your transaction ends. ' \
                f'This helps the mod team to track and deal with issues.\n' \
                f'**12.** You are not allowed to sell **anything** for real world currency.\n' \
                f'**13.** The usage of turnip.exchange is not permitted on this server as it violates Nintendo\'s TOS.\n' \
                f'**14.** Attempts to circumvent the blacklist or filter are prohibited.\n' \
                f'**15.** Please follow Discord\'s ToS.\n\n' \
                f'Choose ✅ to accept or ❌ to decline.'
        embed = discord.Embed(description=msg + '\n' + rules, color=discord.Color.green())
        prompt = await tutorial.send(embed=embed)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == member.id

        try:
            reaction, member = await self.client.wait_for('reaction_add', check=check_react, timeout=600)
            if reaction.emoji == '✅':
                pass
            elif reaction.emoji == '❌':
                msg = 'Oh no! I\'m sorry, but you won\'t be able to access our little island without accepting the rules.\n' \
                      'We appreciate your visit, and if you ever think about coming back we\'ll be here!'
                embed = tut_embed(msg, thumb=True)
                await tutorial.send(embed=embed)
                await asyncio.sleep(10)
                await member.kick()
                try:
                    await tutorial.delete()
                except discord.NotFound:
                    pass
                return
        except asyncio.TimeoutError:
            msg = 'Unfortunately, your prompt has timed out. To keep everything flowing, the channel will be closed, ' \
                  'and you will be kicked. Please join again to retry.'
            embed = tut_embed(msg, thumb=True)
            await tutorial.send(embed=embed)
            await asyncio.sleep(20)
            await member.kick()
            try:
                await tutorial.delete()
            except discord.NotFound:
                pass
            return

        def check_msg(m):
            return m.author == member and m.channel == tutorial

        msg = 'Thank you for accepting the rules for our slice of paradise! We need to do one more thing before you can ' \
              'join the rest of the islanders here. We need to give you a unique name that shows the rest of our guests ' \
              'who you are and where you are from! There is a 26 character limit.'
        embed = tut_embed(msg)
        await tutorial.send(embed=embed)

        while True:
            while True:
                try:
                    msg = 'Please tell me what your desired **nickname** is. This is usually your current name or a display name ' \
                          'that you would like to use for this server. '
                    embed = tut_embed(msg)
                    prompt = await tutorial.send(embed=embed)
                    while True:
                        msg = await self.client.wait_for('message', check=check_msg, timeout=600)
                        displayname = msg.content
                        if database.in_check_filter(member.guild, displayname):
                            edit = 'Sorry, your name appears to have been caught in our profanity filter. If you believe this is a ' \
                                   'mistake, you can request a name change once you gain access to the server. In the meantime, ' \
                                   'please choose another name.'
                            embed = tut_embed(edit)
                            await msg.delete()
                            await prompt.edit(embed=embed)
                        else:
                            break
                except asyncio.TimeoutError:
                    msg = 'Unfortunately, your prompt has timed out. To keep everything flowing, the channel will be closed, ' \
                          'and you will be kicked. Please join again to retry.'
                    embed = tut_embed(msg, thumb=True)
                    await tutorial.send(embed=embed)
                    await asyncio.sleep(20)
                    await member.kick()
                    try:
                        await tutorial.delete()
                    except discord.NotFound:
                        pass
                    return

                try:
                    msg = f'Thank you. Now, please tell me what your **in-game name** is. If you don\'t have one because you don\'t play ACNH, you ' \
                          f'can just use your current name or make one up! *characters left: {26 - len(displayname)}*'
                    embed = tut_embed(msg)
                    prompt = await tutorial.send(embed=embed)
                    while True:
                        msg = await self.client.wait_for('message', check=check_msg, timeout=600)
                        ign = msg.content
                        if database.in_check_filter(member.guild, ign):
                            edit = 'Sorry, your name appears to have been caught in our profanity filter. If you believe this is a ' \
                                  'mistake, you can request a name change once you gain access to the server. In the meantime, ' \
                                  'please choose another name.'
                            embed = tut_embed(edit)
                            await msg.delete()
                            await prompt.edit(embed=embed)
                        else:
                            break
                except asyncio.TimeoutError:
                    msg = 'Unfortunately, your prompt has timed out. To keep everything flowing, the channel will be closed, ' \
                          'and you will be kicked. Please join again to retry.'
                    embed = tut_embed(msg, thumb=True)
                    await tutorial.send(embed=embed)
                    await asyncio.sleep(20)
                    await member.kick()
                    try:
                        await tutorial.delete()
                    except discord.NotFound:
                        pass
                    return

                try:
                    msg = f'Great! If there is a problem with your in-game name, you can ask a moderator to fix it later. So, ' \
                          f'what is your Island :island: name? *characters left: {26 - (len(displayname) + len(ign))}*'
                    embed = tut_embed(msg)
                    await tutorial.send(embed=embed)
                    while True:
                        msg = await self.client.wait_for('message', check=check_msg, timeout=600)
                        island = msg.content
                        if database.in_check_filter(member.guild, island):
                            edit = 'Sorry, your Island name appears to have been caught in our profanity filter. If you believe this is a ' \
                                  'mistake, you can request a name change once you gain access to the server. In the meantime, ' \
                                  'please choose another Island name.'
                            embed = tut_embed(edit)
                            await msg.delete()
                            await prompt.edit(embed=embed)
                        else:
                            break
                except asyncio.TimeoutError:
                    msg = 'Unfortunately, your prompt has timed out. To keep everything flowing, the channel will be closed, ' \
                          'and you will be kicked. Please join again to retry.'
                    embed = tut_embed(msg, thumb=True)
                    await tutorial.send(embed=embed)
                    await asyncio.sleep(20)
                    await member.kick()
                    try:
                        await tutorial.delete()
                    except discord.NotFound:
                        pass
                    return

                if len(f'{displayname} - {ign}, {island}') >= 32:
                    msg = 'Oh no! It appears your display name will be too long. Display names cannot be longer than 32 ' \
                          'characters. Let\'s take a step back and try again. Because of name formatting, please limit your ' \
                          'total length to 27 characters. This **includes** white space.'
                    embed = tut_embed(msg)
                    await tutorial.send(embed=embed)
                else:
                    break

            msg = 'Awesome. To comply with the server\'s rules, I\'m changing your display name to match our ' \
                  'requirements! :star:'
            embed = tut_embed(msg)
            await tutorial.send(embed=embed)
            await member.edit(nick=f'{displayname} - {ign}, {island}')

            await asyncio.sleep(1)

            msg = f'Your display name for this server is now **{member.display_name}**. If this is ok, please confirm by using ' \
                  f'✅. If you want to try again, please use ❌.'
            embed = tut_embed(msg)
            prompt = await tutorial.send(embed=embed)
            await prompt.add_reaction('✅')
            await prompt.add_reaction('❌')
            try:
                reaction, member = await self.client.wait_for('reaction_add', check=check_react, timeout=600)
                if reaction.emoji == '✅':
                    break
                elif reaction.emoji == '❌':
                    pass
            except asyncio.TimeoutError:
                msg = 'Unfortunately, your prompt has timed out. To keep everything flowing, the channel will be closed, ' \
                      'and you will be kicked. Please join again to retry.'
                embed = tut_embed(msg, thumb=True)
                await tutorial.send(embed=embed)
                await asyncio.sleep(20)
                await member.kick()
                try:
                    await tutorial.delete()
                except discord.NotFound:
                    pass
                return

        member_role = member.guild.get_role(694016677616156692)
        await member.add_roles(member_role)

        msg = 'Thank you so much for joining our Island. You now have access to the rest of the server! This channel ' \
              'will be removed in a few seconds!'
        embed = tut_embed(msg)
        await tutorial.send(embed=embed)
        await member.remove_roles(guest)

        await asyncio.sleep(10)
        try:
            await tutorial.delete()
        except discord.NotFound:
            pass

    @commands.command()
    @commands.is_owner()
    async def mem_counter(self, ctx):
        members = [m for m in ctx.guild.members if not m.bot]
        await ctx.guild.create_category(name='📈 SERVER STATS')
        cat = discord.utils.get(ctx.guild.categories, name='📈 SERVER STATS')
        await cat.create_voice_channel(name=f'Members: {len(members)}')
        voice = discord.utils.get(ctx.guild.voice_channels, name=f'Members: {len(members)}')
        try:
            database.set_member_stats(ctx.guild, cat.id, voice.id)
        except Exception as e:
            print(e)

    @tasks.loop(minutes=1)
    async def spam_reset(self):
        try:
            global mention_counter
            global attachment_counter
            mention_counter.clear()
            attachment_counter.clear()
        except Exception as e:
            print(e)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def update_counter(self, ctx):
        try:
            member_stats = self.client.get_channel(706099708434841621)
            members = [m for m in ctx.guild.members if not m.bot]
            await member_stats.edit(name=f'Members: {len(members)}')
            await ctx.send(embed=tools.single_embed('Member count updated!'))
        except Exception as e:
            print(e)
            await ctx.send(embed=tools.single_embed_neg(f'An error occurred when updating the member count.\n{e}'))


def setup(client):
    client.add_cog(Automoderator(client))
