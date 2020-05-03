import asyncio
import sys
import os
import discord
import random
import util.db as database
import util.tools as tools
from discord.ext import commands
from datetime import datetime

mae_banner = 'https://i.imgur.com/HffuudZ.jpg'
mae_thumb = 'https://i.imgur.com/wl2MZIV.png'
# _staff_support = 694673589940781126
_staff_support = 506813223949828147


class Moderator(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def admin_cog_on(ctx):
        if database.admin_cog(ctx.guild):
            return True
        msg = f'**Admin** is not turned on'
        await ctx.send(embed=tools.single_embed_neg(msg))
        return False

    @commands.group(aliases=['mod'])
    @commands.is_owner()
    async def moderator(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Use `mod -h` for the help menu')

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

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def test_spam(self, ctx):
        channel = database.get_spam(ctx.guild)
        await channel.send('test spam')
        # await ctx.send(embed=tools.single_embed(f'{self.client.user.display_name}\'s spam channel is {channel.mention}.'))

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
            await member.ban()
            if reason is None:
                reason = 'A reason was not given.'
            await member.send(f'You have been banned from {ctx.guild.name}.\n'
                              f'Reason: {reason}')
        if answer == 'no':
            await ctx.send(embed=tools.single_embed(f'Ban cancelled.'))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        if not await self.admin_cog_on(ctx):
            return

        msg = f'Are you sure you want to kick {member.display_name}?'
        if reason is not None:
            msg += f'\nReason: {reason}'
        prompt = await ctx.send(embed=tools.single_embed(msg))
        answer = await self.yes_no_buttons(prompt, ctx.author)
        if answer == 'yes':
            await ctx.send(embed=tools.single_embed(f'{member.mention}: **See ya, my guy.** :hiking_boot:'))
            await member.kick()

            if reason is None:
                reason = 'A reason was not given.'
            await member.send(f'You have been kicked from {ctx.guild.name}.\n'
                              f'Reason: {reason}')
        if answer == 'no':
            await ctx.send(embed=tools.single_embed(f'Kick cancelled.'))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def archive(self, ctx):
        current_channel = ctx.channel
        await ctx.channel.clone(name=current_channel.name)
        new_category = discord.utils.get(ctx.guild.categories, name='[――staff archives――]')
        time = tools.format_date(datetime.now(), 2)
        new_channel_name = f'{current_channel.name}-{time}'
        await current_channel.edit(name=new_channel_name, category=new_category, sync_permissions=True)

    @commands.command(aliases=['delbl'])
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

    @commands.command(aliases=['getbl'])
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

    @commands.command(aliases=['delfilter'])
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

    @commands.command(aliases=['gfilter'])
    @commands.has_permissions(administrator=True)
    async def get_filter(self, ctx, *words):
        if not await self.admin_cog_on(ctx):
            return
        fltr = '\n'.join(database.get_filter(ctx.guild))
        msg = f'**Current Filters**\n' \
              f'```\n{fltr}```'
        await ctx.send(embed=tools.single_embed(msg))

    @commands.command(aliases=['filter'])
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

    @commands.command(aliases=['mute'])
    @commands.is_owner()
    async def mute_user(self, ctx, member: discord.Member, reason: str = None):
        channel = self.client.get_channel(694023815331708972)

        def check(m):
            return m.author == ctx.message.author and m.channel == ctx.channel

        await ctx.send(embed=tools.single_embed(f'Would you like to mute {member.display_name}?'))
        msg = await self.client.wait_for('message', check=check)
        if 'yes' in msg.content:
            await channel.send(embed=tools.single_embed(f'{member.mention}: **Shhh, my guy.** :shushing_face:'))
            await member.edit(reason=reason, mute=True)
        if reason is None:
            reason = 'A reason was not given.'
        await member.send(f'You have been muted in {ctx.guild.name}.\n'
                          f'Reason: {reason}')

    @commands.command(aliases=['unmute'])
    @commands.is_owner()
    async def unmute_user(self, ctx, member: discord.Member):
        channel = self.client.get_channel(694023815331708972)

        def check(m):
            return m.author == ctx.message.author and m.channel == ctx.channel

        await ctx.send(embed=tools.single_embed(f'Would you like to unmute {member.display_name}?'))
        msg = await self.client.wait_for('message', check=check)
        if 'yes' in msg.content:
            await channel.send(embed=tools.single_embed(f'{member.mention} has been unmuted.'))
            await member.edit(mute=False)
        await member.send(f'You have been unmuted in {ctx.guild.name}.\n')

    @commands.command(aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, num: int):
        if not await self.admin_cog_on(ctx):
            return
        num += 1
        await ctx.channel.purge(limit=num)

    @commands.command()
    @commands.is_owner()
    async def reboot(self, ctx):
        await ctx.send(embed=tools.single_embed("Rebooting! *snort*"))
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @commands.command()
    @commands.is_owner()
    async def force_update(self, ctx):
        await ctx.send(embed=tools.single_embed('Running forced update'))
        num_members_added = database.force_update(ctx)
        await ctx.send(embed=tools.single_embed(f'{num_members_added} user(s) added to {ctx.guild.name}'))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, message: str = None):
        if not await self.admin_cog_on(ctx):
            return

        def check(react, user):
            return ctx.message.channel == react.message.channel

        database.add_warning(member, message)
        warnings, messages = database.get_warnings(member)
        fmt = [f'{m[1]} - {m[0]}' for m in messages]

        await member.send(f'You have received a warning from an administrator or mod in {ctx.guild.name}.\n> "{message}"')
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
            while yes < 2:
                reaction, member = await self.client.wait_for('reaction_add', check=check)
                if reaction.emoji == '✔':
                    yes = reaction.count
            await member.kick(reason=f'You have been kicked from {ctx.guild.name}. The last warning was: "{message}"')
            await admin_channel.send(embed=tools.single_embed_neg(f'{member.display_name} has been kicked.'))

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
            fmt = [f'{m[1]} - {m[0]}' for m in messages]
            msg = f'**{member.display_name}** has `{warnings}` warning(s).\n' \
                  f'__Past Warnings__\n' + '\n'.join(fmt)
            embed = discord.Embed(color=discord.Color.red(), description=msg)
            embed.set_thumbnail(url=member.avatar_url)
            await ctx.send(embed=embed)

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

    @moderator.error
    async def on_message_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=tools.single_embed_tooltip(f'You do not have permission to run this command.'),
                           delete_after=30)

    @warnings.error
    @clear_warnings.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_tooltip(f'You are missing the `{error.param.name}` argument.'),
                           delete_after=30)

    @warn.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_tooltip(f'You are missing the `{error.param.name}` argument.'),
                           delete_after=30)
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed(f'{error}'),
                           delete_after=30)


def setup(client):
    client.add_cog(Moderator(client))
