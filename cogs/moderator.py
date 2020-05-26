import asyncio
import sys
import os
import json
import discord
import util.db as database
import util.tools as tools
from discord.ext import commands
from datetime import datetime

mae_banner = 'https://i.imgur.com/HffuudZ.jpg'
mae_thumb = 'https://i.imgur.com/wl2MZIV.png'


class Moderator(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.custom_commands = {}
        with open('files/custom_commands.json', 'r') as f:
            self.custom_commands = json.load(f)

    """
    Owner Commands
    """

    @commands.command(aliases=['reload-mod'])
    async def mod_restart(self, ctx):
        print('* Unloading moderator')
        self.client.unload_extension('cogs.moderator')
        # print('Cancelling loops')
        print('* Loading moderator')
        self.client.load_extension('cogs.moderator')
        await ctx.send(embed=tools.single_embed('Moderator reloaded'))

    @commands.command()
    @commands.is_owner()
    async def reboot(self, ctx):
        await ctx.send(embed=tools.single_embed("Rebooting! *snort*"))
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @commands.command()
    @commands.is_owner()
    async def ping(self, ctx):
        msg = f'Ping is {round(self.client.latency * 1000)}ms'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command()
    @commands.is_owner()
    async def force_update(self, ctx):
        await ctx.send(embed=tools.single_embed('Running forced update'))
        num_members_added = database.force_update(ctx)
        await ctx.send(embed=tools.single_embed(f'{num_members_added} user(s) added to {ctx.guild.name}'))

    @commands.command(aliases=['force-role'])
    @commands.is_owner()
    async def force_role(self, ctx, role1: discord.Role, role2: discord.Role):
        members = [member for member in ctx.guild.members if not member.bot and role2 not in member.roles and role1 not in member.roles]
        async with ctx.channel.typing():
            for member in members:
                print(member)
                await member.add_roles(role1)
        msg = f'{len(members)} received {role1.name}'
        embed = discord.Embed(description=msg, color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def edit_embed(self, ctx, channel: discord.TextChannel, message_id: int, *, new_message):
        embed = discord.Embed(description=new_message, color=discord.Color.green())
        message = await channel.fetch_message(message_id)
        await message.edit(embed=embed)
        await ctx.send(embed=tools.single_embed('Messaged updated.'), delete_after=5)

    """
    Custom Commands
    """

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addcommand(self, ctx, command, *, output):
        self.custom_commands[command] = output
        with open('files/custom_commands.json', 'w') as f:
            json.dump(self.custom_commands, f, indent=4)
        await ctx.send(embed=tools.single_embed(f'Command **{command}** added to custom commands.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delcommand(self, ctx, command):
        del self.custom_commands[command]
        with open('files/custom_commands.json', 'w') as f:
            json.dump(self.custom_commands, f, indent=4)
        await ctx.send(embed=tools.single_embed(f'Command **{command}** removed from custom commands.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def editcommand(self, ctx, command, *, output):
        self.custom_commands[command] = output
        with open('files/custom_commands.json', 'w') as f:
            json.dump(self.custom_commands, f, indent=4)
        await ctx.send(embed=tools.single_embed(f'Command **{command}** has been updated.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def showcommand(self, ctx):
        embed = discord.Embed(title='Custom Commands', color=discord.Color.green())
        for k, v in self.custom_commands.items():
            embed.add_field(name=f'!{k}', value=v, inline=False)
        await ctx.send(embed=embed)

    """
    Settings Commands
    """

    @staticmethod
    async def admin_cog_on(ctx):
        if database.admin_cog(ctx.guild):
            return True
        msg = f'**Admin** is not turned on'
        await ctx.send(embed=tools.single_embed_neg(msg))
        return False

    @commands.group()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = database.get_prefix(ctx.guild)[0]
            spam = database.get_spam(ctx.guild)
            autorole = database.get_autorole(ctx.guild)
            administrative = database.get_administrative(ctx.guild)
            review_channel = database.get_review_channel(ctx.guild)
            # get cog status
            admin = database.admin_cog(ctx.guild)
            rep = database.rep_cog(ctx.guild)
            karma = database.karma_cog(ctx.guild)
            mw = database.mw_cog(ctx.guild)
            # assign on/off values
            cogs = [admin, rep, karma, mw]
            for c in range(len(cogs)):
                if cogs[c] is True:
                    cogs[c] = 'On'
                else:
                    cogs[c] = 'Off'

            embed = discord.Embed(title='Settings', color=discord.Color.blue())
            embed.add_field(name='Prefix', value=f'`{prefix}`')
            embed.add_field(name='Autorole', value=autorole)
            msg = f'Spam: {spam.mention}\n'\
                  f'Admin: {administrative.mention}\n'\
                  f'Review (rep): {review_channel.mention}'
            embed.add_field(name='Channel Redirects', value=msg, inline=False)
            msg = f'Admin: `{cogs[0]}`\nRep: `{cogs[1]}`\nKarma: `{cogs[2]}`\n~~MW~~: `{cogs[3]}`'
            embed.add_field(name='Cogs', value=msg, inline=False)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            await ctx.send(embed=embed)

    @settings.group()
    @commands.has_permissions(administrator=True)
    async def admin(self, ctx, state):
        if state.lower() not in ['on', 'off']:
            msg = 'Supported states are `on` and `off`.'
            await ctx.send(embed=tools.single_embed(msg))
        else:
            m = {'on': 1, 'off': 0}
            database.admin_set(ctx.guild, m.get(state.lower()))
            msg = f'**Admin** cog turned **{state}**'
            await ctx.send(embed=tools.single_embed(msg))

    @settings.group()
    @commands.has_permissions(administrator=True)
    async def karma(self, ctx, state):
        if state.lower() not in ['on', 'off']:
            msg = 'Supported states are `on` and `off`.'
            await ctx.send(embed=tools.single_embed(msg))
        else:
            m = {'on': 1, 'off': 0}
            database.karma_set(ctx.guild, m.get(state.lower()))
            msg = f'**Karma** cog turned **{state}**'
            await ctx.send(embed=tools.single_embed(msg))

    @settings.group()
    @commands.has_permissions(administrator=True)
    async def mw(self, ctx, state):
        if state.lower() not in ['on', 'off']:
            msg = 'Supported states are `on` and `off`.'
            await ctx.send(embed=tools.single_embed(msg))
        else:
            m = {'on': 1, 'off': 0}
            database.mw_set(ctx.guild, m.get(state.lower()))
            msg = f'**MW** cog turned **{state}**'
            await ctx.send(embed=tools.single_embed(msg))

    @settings.group()
    @commands.has_permissions(administrator=True)
    async def rep(self, ctx, state):
        if state.lower() not in ['on', 'off']:
            msg = 'Supported states are `on` and `off`.'
            await ctx.send(embed=tools.single_embed(msg))
        else:
            m = {'on': 1, 'off': 0}
            database.rep_set(ctx.guild, m.get(state.lower()))
            msg = f'**Rep** cog turned **{state}**'
            await ctx.send(embed=tools.single_embed(msg))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx, role: discord.Role = None):
        if not await self.admin_cog_on(ctx):
            return
        admin_channel = database.get_administrative(ctx.guild)
        if role is None:
            database.update_autorole(ctx.guild, role)
            await admin_channel.send(embed=tools.single_embed(f'Autorole set to `none`'))
        else:
            database.update_autorole(ctx.guild, role)
            await admin_channel.send(embed=tools.single_embed(f'Autorole set to `{role}`'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix: str):
        if not await self.admin_cog_on(ctx):
            return
        database.set_prefix(prefix, guild=ctx.guild)
        await ctx.send(embed=tools.single_embed(f'{self.client.user.display_name}\'s prefix set to `{prefix}`.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, channel: discord.TextChannel):
        if not await self.admin_cog_on(ctx):
            return
        database.set_spam(channel, guild=ctx.guild)
        await ctx.send(embed=tools.single_embed(f'{self.client.user.display_name}\'s spam channel set to {channel.mention}.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def review_channel(self, ctx, channel: discord.TextChannel):
        if not await self.admin_cog_on(ctx):
            return
        database.set_review_channel(channel, ctx.guild)
        msg = f'{self.client.user.display_name}\'s review channel set to {channel.mention}.'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def admin_channel(self, ctx, channel: discord.TextChannel):
        if not await self.admin_cog_on(ctx):
            return
        database.set_administrative(channel, ctx.guild)
        msg = f'{self.client.user.display_name}\'s administrative channel set to {channel.mention}.'
        await ctx.send(embed=tools.single_embed(msg))

    """
    Member Management
    """

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def messages(self, ctx, member: discord.Member, channel: discord.TextChannel, num: int):
        member_messages = []
        count = 0
        if not ctx.author.permissions_in(channel).read_messages:
            await ctx.send(embed=tools.single_embed(f'You do not have permission to view message history in {channel.name}'))
            return
        async with ctx.channel.typing():
            async for message in channel.history(limit=100, oldest_first=False, around=datetime.now()):
                if message.author == member:
                    if count >= num:
                        break
                    else:
                        member_messages.append(message)
                        count += 1
        title = f'Last {num} messages for {member.display_name} in {channel.name}'
        description = [f'{member_messages.index(message) + 1}. {message.content[:200]} [jump to]({message.jump_url})' for message in member_messages]
        try:
            embed = discord.Embed(title=title, description='\n'.join(description), color=discord.Color.green())
            await ctx.send(embed=embed)
        except discord.HTTPException:
            msg = f'Your request was too long. Try an interval smaller than {num}.'
            await ctx.send(embed=tools.single_embed(msg))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def allmessages(self, ctx, member: discord.Member, num: int):
        member_messages = []
        count = 0
        async with ctx.channel.typing():
            for channel in ctx.guild.text_channels:
                try:
                    print(channel.name)
                    # async for message in channel.history(oldest_first=False, around=datetime.utcnow()):
                    async for message in channel.history(limit=200):
                        if message.author == member:
                            if count >= num:
                                break
                            else:
                                member_messages.append(message)
                                count += 1
                    if len(member_messages) > 0:
                        title = f'Last {num} messages for {member.display_name} in {channel.name}'
                        description = [f'{member_messages.index(message) + 1}. {message.content[:200]} [jump to]({message.jump_url})' for message in member_messages]
                        embed = discord.Embed(title=title, description='\n'.join(description), color=discord.Color.green())
                        await ctx.send(embed=embed)
                        member_messages = []
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reaction_role(self, ctx):
        def check_msg(m):
            return m.author == ctx.message.author and m.channel == ctx.channel

        def check_react(react, user):
            return react.message.id == prompt.id and user.id == ctx.message.author.id

        def react_embed(_msg):
            return discord.Embed(description=_msg, color=discord.Color.green())

        prompt = await ctx.send(embed=react_embed('Mention a channel'))
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.channel_mentions) > 0:
                posting_channel = msg.channel_mentions[0]
                await msg.delete()
                break
            else:
                await ctx.send(embed=react_embed('That is not a valid channel. Try again.'), delete_after=5)

        await prompt.edit(embed=react_embed('Enter a message'))
        message = await self.client.wait_for('message', check=check_msg)
        content = message.content
        await message.delete()

        await prompt.edit(embed=react_embed('Mention a role'))
        while True:
            msg = await self.client.wait_for('message', check=check_msg)
            if len(msg.role_mentions) > 0:
                role = msg.role_mentions[0]
                await msg.delete()
                break
            else:
                await ctx.send(embed=react_embed('That is not a valid role. Try again.'), delete_after=5)

        await prompt.edit(embed=react_embed('React to this message'))
        reaction, member = await self.client.wait_for('reaction_add', check=check_react)

        msg = await posting_channel.send(embed=tools.single_embed(content))
        await msg.add_reaction(reaction)

        await prompt.edit(embed=react_embed(f'Your reaction message was posted to {posting_channel.mention}'))
        await prompt.clear_reactions()

        database.set_reaction_message(ctx.guild, msg, role, reaction.emoji)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def selfrole(self, ctx, role: discord.Role, *, message):
        embed = discord.Embed(description=message, color=discord.Color.green())
        prompt = await ctx.send(embed=embed)
        await prompt.add_reaction('👍')
        database.set_reaction_message(ctx.guild, prompt, role, '👍')
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        if not await self.admin_cog_on(ctx):
            return

        msg = f'Are you sure you want to ban {member.display_name}?'
        if reason is not None:
            msg += f'\nReason: {reason}'
        prompt = await ctx.send(embed=tools.single_embed(msg))

        answer = await self.yes_no_buttons(prompt, ctx.author)
        if answer == 'yes':
            await ctx.send(embed=tools.single_embed(f'{member.mention}: **See ya, my guy.** :hammer:'))
            try:
                await member.ban(reason=reason, delete_message_days=7)
            except Exception as e:
                print(e)
                await member.ban()
            if reason is None:
                reason = 'A reason was not given.'
            try:
                await member.send(f'You have been banned from {ctx.guild.name}.\n'
                                  f'Reason: {reason}')
            except discord.Forbidden:
                pass
        if answer == 'no':
            await ctx.send(embed=tools.single_embed(f'Ban cancelled.'), delete_after=30)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        if not await self.admin_cog_on(ctx):
            return

        msg = f'Are you sure you want to kick {member.display_name}?'
        if reason is not None:
            msg += f'\nReason: {reason}'
        else:
            msg += 'A reason was not given.'
        prompt = await ctx.send(embed=tools.single_embed(msg))
        answer = await self.yes_no_buttons(prompt, ctx.author)

        if answer == 'yes':

            if reason is None:
                reason = 'A reason was not given.'
            try:
                msg = f'You have been kicked from {ctx.guild.name}.\nReason: {reason}'
                await member.send(embed=tools.single_embed_neg(msg))
            except discord.Forbidden:
                msg = f'{member.display_name} have been kicked from {ctx.guild.name}.\nReason: {reason}'
                await ctx.send(embed=tools.single_embed_neg(msg))
            await member.kick()
            await ctx.send(embed=tools.single_embed(f'{member.mention}: **See ya, my guy.** :hiking_boot:'))
        if answer == 'no':
            await ctx.send(embed=tools.single_embed(f'Kick cancelled.'))

    @commands.command()
    @commands.is_owner()
    async def x(self, ctx):
        print(self.client.user.id)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, message: str = None):
        if not await self.admin_cog_on(ctx):
            return

        def check(react, user):
            return admin_channel == react.message.channel and not user.bot

        database.add_warning(member, message, ctx.author)
        warnings, messages = database.get_warnings(member)
        fmt = [f'{m[4]} - {m[3]} *Issuer: {discord.utils.get(ctx.guild.members, id=m[5]).display_name}' for m in messages]

        msg = f'You have received a warning from an administrator or mod in {ctx.guild.name}.\n> "{message}"'
        try:
            await member.send(embed=tools.single_embed_neg(msg))
        except discord.Forbidden:
            spam = database.get_spam(ctx.guild)
            await spam.send(embed=f'{member.mention}: {msg}')

        embed = discord.Embed(color=discord.Color.red(), description=f'{member.mention} has been warned:\n"{message}"')
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

        if warnings >= 2:
            admin_channel = database.get_administrative(ctx.guild)
            msg = f'**{member.display_name}** has reached `{warnings}` warnings. Should they be kicked?\n' \
                  f'__Past Warnings__\n' + '\n'.join(fmt)
            embed = discord.Embed(color=discord.Color.red(), description=msg)
            embed.set_thumbnail(url=member.avatar_url)
            msg = await admin_channel.send(embed=embed)
            await msg.add_reaction('✔')
            await msg.add_reaction('❌')
            yes = 0
            no = 0
            limit = 4
            while True:
                try:
                    reaction, reactor = await self.client.wait_for('reaction_add', check=check, timeout=28800)
                    if reaction.emoji == '✔':
                        yes = reaction.count
                        if yes >= limit:
                            break
                    if reaction.emoji == '❌':
                        no = reaction.count
                        if no >= limit:
                            break
                except asyncio.TimeoutError:
                    embed.add_field(name='Timeout', value='The vote has timed out.')
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()
                    return
            if yes > no:
                await member.kick(reason=f'You have been kicked from {ctx.guild.name}. The last warning was: "{message}"')
                embed.add_field(name='Vote completed', value=f'{member.display_name} has been kicked.')
                await msg.edit(embed=embed)
                await msg.clear_reactions()
            if no > yes:
                embed.add_field(name='Vote completed', value=f'{member.display_name} has been voted to stay.')
                await msg.edit(embed=embed)
                await msg.clear_reactions()

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        if not await self.admin_cog_on(ctx):
            return
        if not database.in_warnings_table(member, ctx.guild):
            msg = f'**{member.display_name}** has `0` warnings.'
            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_thumbnail(url=member.avatar_url)
            await ctx.send(embed=embed)
        else:
            warnings, messages = database.get_warnings(member)
            count = 1
            fmt = []
            for m in messages:
                fmt.append([m[0], f'{count}. {m[4]} - {m[3]} *Issuer: {discord.utils.get(ctx.guild.members, id=m[5]).display_name}'])
                count += 1
            # fmt = [f'{count}. {m[1]} - {m[0]}' for m in messages]
            # while True:
            if len(fmt) > 0:
                msg = f'**{member.display_name}** has `{warnings}` warning(s).\n' \
                      f'__Past Warnings__\n' + '\n'.join(m[1] for m in fmt)
                embed = discord.Embed(color=discord.Color.red(), description=msg)
                embed.set_thumbnail(url=member.avatar_url)
                prompt = await ctx.send(embed=embed)
                reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '⏩', '⏹']

                # msg = '\n'.join(fmt[:10])
                # embed = discord.Embed(title='Who do you want to kick?', description=msg, color=discord.Color.green())
                # embed.set_thumbnail(url=self.client.user.avatar_url)
                # prompt = await ctx.channel.send(embed=embed)
                # for i in range(0, len(fmt[:11])):
                #     await prompt.add_reaction(reactions[i])
                # await prompt.add_reaction('⏹')
                #
                # def check_react(react, user):
                #     return react.message.id == prompt.id and user.id == ctx.author.id
                #
                # reaction, member = await self.client.wait_for('reaction_add', check=check_react)
                # removed_warning = None
                # if reaction.emoji == reactions[0]:
                #     removed_warning = fmt[0]
                # if reaction.emoji == reactions[1]:
                #     removed_warning = fmt[1]
                # if reaction.emoji == reactions[2]:
                #     removed_warning = fmt[2]
                # if reaction.emoji == reactions[3]:
                #     removed_warning = fmt[3]
                # if reaction.emoji == reactions[4]:
                #     removed_warning = fmt[4]
                # if reaction.emoji == reactions[5]:
                #     removed_warning = fmt[5]
                # if reaction.emoji == reactions[6]:
                #     removed_warning = fmt[6]
                # if reaction.emoji == reactions[7]:
                #     removed_warning = fmt[7]
                # if reaction.emoji == reactions[8]:
                #     removed_warning = fmt[8]
                # if reaction.emoji == reactions[9]:
                #     removed_warning = fmt[9]
                # if reaction.emoji == reactions[10]:
                #     del fmt[:10]
                #     await prompt.delete()
                #     continue
                # if reaction.emoji == '⏹':
                #     await prompt.delete()
                #     return

                # remove the warning

    @commands.command(aliases=['cwarn'])
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx, member: discord.Member):
        if not await self.admin_cog_on(ctx):
            return
        database.clear_warnings(member)
        msg = f'**{member.display_name}**\'s warnings have been cleared.'
        embed = discord.Embed(color=discord.Color.green(), description=msg)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    """
    Utility Commands
    """

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def archive(self, ctx):
        current_channel = ctx.channel
        await ctx.channel.clone(name=current_channel.name)
        new_category = discord.utils.get(ctx.guild.categories, name='[――staff archives――]')
        time = tools.format_date(datetime.now(), 2)
        new_channel_name = f'{current_channel.name}-{time}'
        await current_channel.edit(name=new_channel_name, category=new_category, sync_permissions=True)

    """
    Content Management
    """

    @commands.command(aliases=['delbl', 'dbl'])
    @commands.has_permissions(administrator=True)
    async def remove_blacklist(self, ctx, *item):
        if not await self.admin_cog_on(ctx):
            return
        void = []
        deleted = []
        for b in item:
            if database.in_check_blacklist(ctx.guild, b):
                database.remove_from_blacklist(ctx.guild, b)
                deleted.append(b)
            else:
                void.append(b)
        if len(deleted) > 0:
            await ctx.send(embed=tools.single_embed(f'Item(s) removed: {", ".join(deleted)}'))
        if len(void) > 0:
            await ctx.send(embed=tools.single_embed_neg(f'{", ".join(void)} not found.'))

    @commands.command(aliases=['getbl', 'gbl'])
    @commands.has_permissions(administrator=True)
    async def get_blacklist(self, ctx):
        if not await self.admin_cog_on(ctx):
            return
        blacklist = '\n'.join(database.get_blacklist(ctx.guild))
        msg = f'**Blacklist**\n' \
              f'```\n{blacklist}```'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command(aliases=['bl'])
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx, *blacklist):
        if not await self.admin_cog_on(ctx):
            return
        exists = []
        added = []
        for b in blacklist:
            if database.in_check_blacklist(ctx.guild, b):
                exists.append(b)
            else:
                database.add_to_blacklist(ctx.guild, b)
                added.append(b)
        if len(added) > 0:
            await ctx.send(embed=tools.single_embed(f'Item(s) blacklisted: {", ".join(added)}'))
        if len(exists) > 0:
            await ctx.send(embed=tools.single_embed_neg(f'{", ".join(exists)} already blacklisted.'))

    @commands.command(aliases=['delfilter', 'df'])
    @commands.has_permissions(administrator=True)
    async def remove_filter(self, ctx, *item):
        if not await self.admin_cog_on(ctx):
            return
        void = []
        deleted = []
        for b in item:
            if database.in_check_filter(ctx.guild, b):
                database.remove_from_filter(ctx.guild, b)
                deleted.append(b)
            else:
                void.append(b)
        if len(deleted) > 0:
            await ctx.send(embed=tools.single_embed(f'Item(s) removed: {", ".join(deleted)}'))
        if len(void) > 0:
            await ctx.send(embed=tools.single_embed_neg(f'{", ".join(void)} not found.'))

    @commands.command(aliases=['gfilter', 'gf'])
    @commands.has_permissions(administrator=True)
    async def get_filter(self, ctx):
        if not await self.admin_cog_on(ctx):
            return
        fltr = '\n'.join(database.get_filter(ctx.guild))
        msg = f'**Current Filters**\n' \
              f'```\n{fltr}```'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command(aliases=['filter', 'f'])
    @commands.has_permissions(administrator=True)
    async def _filter(self, ctx, *words):
        if not await self.admin_cog_on(ctx):
            return
        exists = []
        added = []
        for b in words:
            if database.in_check_filter(ctx.guild, b):
                exists.append(b)
            else:
                database.add_to_filter(ctx.guild, b)
                added.append(b)
        if len(added) > 0:
            await ctx.send(embed=tools.single_embed(f'Item(s) filtered: {", ".join(added)}'))
        if len(exists) > 0:
            await ctx.send(embed=tools.single_embed_neg(f'{", ".join(exists)} already filtered.'))

    @commands.command(aliases=['clm'])
    @commands.has_permissions(manage_messages=True)
    async def clean_messages(self, ctx, member: discord.Member, num: int):
        def is_member(m):
            return m.author == member
        if not await self.admin_cog_on(ctx):
            return
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=num, check=is_member)
        await ctx.send(embed=tools.single_embed(f'{len(deleted)} messages removed.'), delete_after=5)

    @commands.command(aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, num: int):
        if not await self.admin_cog_on(ctx):
            return
        await ctx.message.delete()
        await ctx.channel.purge(limit=num)

    """
    Utility Functions
    """

    async def yes_no_buttons(self, prompt, user):
        await prompt.add_reaction('🇾')
        await prompt.add_reaction('🇳')
        await asyncio.sleep(0)

        def check_react(react, actor):
            return react.message.id == prompt.id and actor.id == user.id

        try:
            reaction, member = await self.client.wait_for('reaction_add', check=check_react, timeout=20)
            if reaction.emoji == '🇾':
                await prompt.clear_reactions()
                return 'yes'
            if reaction.emoji == '🇳':
                await prompt.clear_reactions()
                return 'no'
        except asyncio.TimeoutError:
            await prompt.edit(embed=tools.single_embed('Request timed out.'), delete_after=10)
            await prompt.clear_reactions()

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        # search messages for discord links
        if message is None or message.author.bot:
            return

        # check for custom commands
        if message.content.startswith('!'):
            for k, v in self.custom_commands.items():
                if k == message.content.split(' ')[0][1:]:
                    await message.channel.send(embed=tools.single_embed(v))

    """
    Error Handling
    """

    @warnings.error
    @clear_warnings.error
    @selfrole.error
    @warn.error
    @clean_messages.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_tooltip(f'You are missing the `{error.param.name}` argument.'),
                           delete_after=30)
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed(f'{error}'), delete_after=30)


def setup(client):
    client.add_cog(Moderator(client))
