import asyncio
import util.db as database
import util.tools as tools
import discord
from discord.ext import commands, tasks

mention_counter = {}
attachment_counter = {}


class Automoderator(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.spam_reset.start()

    """
    Owner Commands
    """

    @commands.command(aliases=['reload-automod'])
    @commands.is_owner()
    async def automod_restart(self, ctx):
        print('Unloading automoderator')
        self.client.unload_extension('cogs.automoderator')
        print('Cancelling loops')
        self.spam_reset.cancel()
        print('Loading automoderator')
        self.client.load_extension('cogs.automoderator')
        await ctx.send(embed=tools.single_embed('Automoderator reloaded'))

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

    """
    Administrator Commands
    """

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

    """
    Utility Functions
    """

    @staticmethod
    async def profanity_filter(message):
        filter_list = database.get_filter(message.guild)
        message = [w.lower() for w in message.content.split(' ')]
        if any(w in ''.join(message).replace(' ', '') for w in filter_list):
            return True

    async def check_warnings(self, message):
        def check(react, user):
            return react.message.id == cache_msg.id and user.permissions_in(admin_channel).kick_members

        # if member's warnings are 2 or greater, commence a vote to kick
        warnings, messages = database.get_warnings(message.author)
        fmt = [f'{m[4]} - {m[3]}' for m in messages]
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

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # check welcome reactions
        guild = self.client.get_guild(payload.guild_id)
        try:
            user = discord.utils.get(guild.members, id=payload.user_id)
        except AttributeError:
            return
        if user.bot or user is None:
            return

        reactions = database.get_reaction_message(guild)
        for (message, role, reaction) in reactions:
            if payload.message_id == message and payload.emoji.name == reaction:
                reaction_role = discord.utils.get(guild.roles, id=role)
                checks = [' - ', ' from ', ', ', ' | ']
                valid = False
                for c in checks:
                    if c in user.display_name:
                        valid = True
                if not valid:
                    channel = self.client.get_channel(payload.channel_id)
                    message = await channel.fetch_message(id=payload.message_id)
                    await message.remove_reaction(payload.emoji.name, user)
                    msg = f'{user.mention} Please change your nickname to match one of these formats:\n' \
                          f'```\n' \
                          f'displayName - inGameName, islandName\n' \
                          f'inGameName, islandName\n' \
                          f'inGameName | islandName\n' \
                          f'inGameName from islandName' \
                          f'```'
                    await channel.send(msg, delete_after=10)
                else:
                    # give reaction role
                    await user.add_roles(reaction_role)
                    try:
                        # remove guest role
                        guest = guild.get_role(707939531529125898)
                        await user.remove_roles(guest)
                    except Exception as e:
                        print(e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # if new name is different than the old name, update the database
        if before.display_name == after.display_name:
            return
        nicknames = [n[0] for n in database.get_member_nick_history(before)]
        if after.display_name in nicknames:
            return
        database.add_member_nick_history(before, after.display_name)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # add member to the database
        database.add_member(member)

        # if admin cog is not set, do not give autorole
        if not database.admin_cog(member.guild):
            return
        autorole = database.get_autorole(member.guild)
        if autorole is not None:
            try:
                await member.add_roles(autorole)
                spam = database.get_spam(member.guild)
                msg = f'{member.display_name} was given the role {autorole.name}'
                await spam.send(embed=tools.single_embed(msg))
                print(f'* Giving {member.display_name} the autorole {autorole.name}')
            except Exception as e:
                spam = database.get_spam(member.guild)
                msg = f'Unable to give {member.display_name} the role {autorole.name}'
                await spam.send(embed=tools.single_embed(msg))
                print(f'* Unable to give {member.display_name} the role {autorole.name}: {e}')

        # store nickname
        nicknames = [n[0] for n in database.get_member_nick_history(member)]
        if member.name not in nicknames:
            database.add_member_nick_history(member, member.name)

        # update the server statistics
        try:
            member_stats = self.client.get_channel(706099708434841621)
            members = [m for m in member.guild.members if not m.bot]
            await member_stats.edit(name=f'Members: {len(members)}')
        except Exception as e:
            print(f'Could not update server stats: {e}')

        # alert general on every 1000th member
        if len([m for m in member.guild.members if not m.bot]) % 1000 == 0:
            chan = self.client.get_channel(694013862667616310)
            msg = f'Welcome {member.mention} as our {len(member.guild.members)}th member!'
            await chan.send(embed=tools.single_embed(msg))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # update the server stats
        try:
            member_stats = self.client.get_channel(706099708434841621)
            members = [m for m in member.guild.members if not m.bot]
            await member_stats.edit(name=f'Members: {len(members)}')
        except Exception as e:
            print(f'Could not update server stats: {e}')
            pass

        if not database.admin_cog(member.guild):
            return

        # notify member leaving
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

        # prevent admin messages from showing in deleted messages
        admin_channel = 700538064224780298
        if before.guild is None or before.channel.id == admin_channel:
            return

        # prevent bot messages from showing in edited messages
        if before.author.bot or before.content.startswith('http') or before.content == '':
            return
        spam = database.get_spam(after.guild)
        try:
            msg = f'{before.author.display_name} edited a message in {before.channel.mention}'
            embed = discord.Embed(description=msg)
            embed.set_thumbnail(url=before.author.avatar_url)
            embed.add_field(name='Before', value=before.content, inline=False)
            embed.add_field(name='After', value=after.content, inline=False)
            await spam.send(embed=embed)
        except discord.HTTPException:
            msg = f'{before.author.display_name} edited a message in {before.channel.mention}'
            embed = discord.Embed(description=msg)
            embed.set_thumbnail(url=before.author.avatar_url)
            embed.add_field(name='Before', value=before.content[:200] + '...', inline=False)
            embed.add_field(name='After', value=after.content[:200] + '...', inline=False)
            await spam.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # block certain messages from deleted message log
        admin_channel = 700538064224780298
        if message is None or not database.admin_cog(message.guild) or message.channel.id == admin_channel or message.author.bot:
            return

        msg = f'**A message was deleted**\n'\
              f'Author: {message.author.display_name}\n'\
              f'Channel: {message.channel.mention}\n'\
              f'Message: {message.content}'
        embed = discord.Embed(color=discord.Color.red(), description=msg)
        embed.set_thumbnail(url=message.author.avatar_url)

        spam = database.get_spam(message.guild)
        await spam.send(embed=embed)

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
                    embed.set_author(name=f'{message.author} | {message.author.display_name}', icon_url=message.author.avatar_url)
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
                    try:
                        await message.author.send(embed=tools.single_embed_neg(msg))
                    except discord.Forbidden:
                        await message.channel.send(embed=tools.single_embed_neg(message.author.mention + ' ' + msg))
                    msg = f'{message.author.mention} has been notified that they are spamming attachments.\n' \
                          f'[Jump to Message]({message.jump_url})'
                    embed = discord.Embed(description=msg, color=discord.Color.red())
                    embed.set_author(name=f'{message.author} | {message.author.display_name}', icon_url=message.author.avatar_url)
                    await admin_channel.send(embed=embed)

        if await self.profanity_filter(message) and not message.author.permissions_in(message.channel).manage_messages:
            staff_support = database.get_administrative(message.guild)
            description = f'Author: {message.author.mention} \n' \
                          f'Message: "{message.content}" \n' \
                          f'[Jump to Message]({message.jump_url})'
            embed = discord.Embed(title='Slur/Profanity Detected', description=description, color=discord.Color.red())
            embed.set_author(name=f'{message.author} | {message.author.display_name}', icon_url=message.author.avatar_url)
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
                            pass

                        # remove confirmation dialogue
                        embed.remove_field(1)
                        embed.remove_field(0)
                        msg = f'{message.author.mention} has been kicked by **{reactor.display_name}**'
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
                        try:
                            await message.delete()
                        except discord.NotFound:
                            pass
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
                        msg = f'{message.author.mention} one of your messages was deleted by a mod or admin for ' \
                              f'inappropriate content."'
                        await message.channel.send(embed=tools.single_embed_neg(msg))
                    embed.remove_field(1)
                    embed.remove_field(0)
                    deleted = f'{message.author.display_name}\'s message was deleted by {reactor.display_name}'
                    embed.add_field(name='Action', value=deleted, inline=False)
                    await prompt.edit(embed=embed)
                    await prompt.clear_reactions()
                    try:
                        await message.delete()
                    except discord.NotFound:
                        pass
                    break

        # ignore links created by moderators
        if message.author.guild_permissions.create_instant_invite:
            return

        # ignore this guild's invites
        for w in message.content.split(' '):
            try:
                if w in [f'discord.gg/{invite.code}' for invite in await message.guild.invites()]:
                    pass
            except discord.HTTPException as e:
                print(e)

        # if link found, delete and warn
        if 'discord.gg/' in message.content and 'discord.gg/stalkmarket' not in message.content:
            try:
                await message.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                print(f'Could not delete discord.gg message {message}: {e}')
            msg = f'Advertising other Discord servers is not allowed.'
            database.add_warning(message.author, msg)
            fmt = f'You have received an automatic warning for posting a Discord link in ' \
                  f'**{message.guild.name}**.\n> "{msg}"'
            try:
                # try to DM the warning to the user
                await message.author.send(embed=tools.single_embed_neg(fmt))
            except discord.Forbidden:
                # warn publicly if DMs are closed
                await message.channel.send(embed=tools.single_embed_neg(fmt))

            await self.check_warnings(message)

        te_links = ['https://turnip.exchange', 'http://turnip.exchange', 'turnip.exchange/island']
        content = [w for w in message.content.split(' ')]
        if any(x in te_links for x in content):
            try:
                await message.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                print(f'Could not delete turnip.exchange message {message}: {e}')
            msg = f'Advertising Turnip Exchange links is not allowed.'
            database.add_warning(message.author, msg)
            fmt = f'You have received an automatic warning for posting a Turnip Exchange link in ' \
                  f'**{message.guild.name}**.\n> "{msg}"'

            try:
                # try to DM the warning to the user
                await message.author.send(embed=tools.single_embed_neg(fmt))
            except discord.Forbidden:
                # warn publicly if DMs are closed
                await message.channel.send(embed=tools.single_embed_neg(fmt))

            await self.check_warnings(message)

        blacklist = database.get_blacklist(message.guild)
        for b in blacklist:
            if b in message.content.lower():
                try:
                    await message.delete()
                    msg = f'You have entered a blacklisted link in **{message.guild.name}** ' \
                          f'Your message has been deleted.'
                    try:
                        await message.author.send(embed=tools.single_embed_neg(msg))
                    except discord.Forbidden:
                        await message.channel.send(embed=tools.single_embed_neg(msg))
                except discord.NotFound as e:
                    print(e)

    """
    Looping Tasks
    """

    @tasks.loop(minutes=1)
    async def spam_reset(self):
        try:
            global mention_counter
            global attachment_counter
            mention_counter.clear()
            attachment_counter.clear()
        except Exception as e:
            print(e)


def setup(client):
    client.add_cog(Automoderator(client))
