import sys
import os
import inspect
import discord
import util.db as database
import util.tools as tools
from discord.ext import commands

rep_cmds = ['rep', 'pos', 'neg', 'repboard', 'karma', 'karmaboard']
dms_cmds = ['create', 'close', 'end', 'join', 'leave', 'menu', 'send', 'dodo', 'show', 'notify', 'welcome', 'kick',
            'ban', 'unban', 'bans']
fun_cmds = ['roll', 'yt', 'card', 'rps', 'inspire', 'rd']
adm_cmds = ['settings', 'info', 'prefix', 'spam', 'admin_channel', 'autorole', 'add', 'sub', 'reset', 'warn',
            'warnings', 'clear_warnings', 'purge_messages']
misc_cmds = ['bug']
dev_cmds = ['reboot', 'reload', 'load']


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(aliases=['help'])
    async def help_page(self, ctx):
        def list_cmds(cmds):
            if len(cmds) > 8:
                a = cmds[:8]
                b = cmds[9:]
                lst = []
                for x, y in zip(a, b):
                    spaces = 27 - (len(x))
                    lst.append(f'{x}{" " * spaces}{y}')
                lst = '\n' + '\n'.join(lst)
            else:
                lst = '\n' + '\n'.join([i for i in cmds])
            return f'```{lst}```'
        if ctx.invoked_subcommand is None:
            prefix = database.get_prefix(ctx.guild)[0]
            msg = f'> Info\nType `{prefix}help [command]` to get more information about a command'
            embed = discord.Embed(title=f'Commands and Features', color=discord.Color.green(), description=msg)
            embed.add_field(name='> Reputation', value=list_cmds(rep_cmds))
            embed.add_field(name='> Fun', value=list_cmds(fun_cmds))
            embed.add_field(name='> DMS Queueing System', value=list_cmds(dms_cmds), inline=False)
            embed.add_field(name='> Administrative', value=list_cmds(adm_cmds), inline=False)
            embed.add_field(name='> Developer', value=list_cmds(dev_cmds))
            embed.add_field(name='> Misc', value=list_cmds(misc_cmds))
            about = f'This bot was created and actively managed by {self.client.get_user(self.client.owner_id).name}. ' \
                    f'If you\'d like to support my work, you can buy me a [coffee](https://ko-fi.com/hatchet_jackk). ' \
                    f'Cheers.'
            embed.add_field(name='> About', value=about, inline=False)
            embed.set_thumbnail(url=self.client.user.avatar_url)
            await ctx.send(embed=embed)

    async def help_embed(self, ctx, title, description, footer):
        embed = discord.Embed(title=title, description=description, color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)
        embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    @help_page.group()
    async def bug(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} message` - Send a bug report to the developer. Add an screenshot of the bug to ' \
                    f'the command when possible.'
        footer = f'Related commands: {", ".join([r for r in misc_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=['kboard'])
    async def karmaboard(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get the top 10 karma leaders.\n' \
                    f'__aliases__: `kboard`\n\n' \
                    f'Karma is a point system established around constructive communities. ' \
                    f'If another member has done something for you please think about giving them ' \
                    f'karma.'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def karma(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get your current karma.\n' \
                    f'`thanks @user` - Give a member karma.\n\n' \
                    f'Karma is a point system established around constructive communities. ' \
                    f'If another member has done something for you please think about giving them ' \
                    f'karma.'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def rep(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get your current reputation.\n' \
                    f'`{prefix}{func} @user` - Get another user\'s reputation.'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def pos(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user optional_message` - Give a user a positive review.'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def neg(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user required_message` - Give a user a negative review.'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=['rboard'])
    async def repboard(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get the top 10.\n__aliases__: `repboard`'
        footer = f'Related commands: {", ".join([r for r in rep_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def create(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Create a new Daisy-Mae Session (DMS).' \
                    f'Great for advertising Turnip prices.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def close(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Close the doors to your DMS to prevent new guests from joining.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def end(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Shut down your DMS. Any guests still in the queue will be notified that the ' \
                    f'session is over.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def join(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} code` - Join an existing session using a DMS code.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def leave(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} code` - Leave a DMS queue using the corresponding code.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def menu(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get all host options while hosting a DMS.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def send(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Send your Dodo code to the next group in your DMS queue. This clears the group ' \
                    f'and notifies all groups that they have moved up the queue.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def dodo(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} code` - Change your Dodo code on the fly in your DMS.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def show(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Show your current DMS queue.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def notify(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} message` - Send a message to all of the guests in your DMS.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def welcome(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} message` - Set a welcome message that guests will receive when they join ' \
                    f'your DMS.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def kick(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} "guest"` - Kick a guest from your DMS queue. Due to limitations, the guest\'s full ' \
                    f'name needs to be included. If the guest name has a space in it, the name must be wrapped in ' \
                    f'quotes. For example `{prefix}kick "test user"`'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def ban(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} "guest"` - Ban a guest from entering or re-entering your DMS queue. Due to ' \
                    f'limitations, the guest\'s full name needs to be included. If the guest name has a space in it, ' \
                    f'the name must be wrapped in quotes. For example `{prefix}ban "test user"`'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def unban(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} "guest"` - Unban a guest so they may join your DMS. Due to ' \
                    f'limitations, the guest\'s full name needs to be included. If the guest name has a space in it, ' \
                    f'the name must be wrapped in quotes. For example `{prefix}unban "test user"`'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def bans(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Show a list of banned guests.'
        footer = f'Related commands: {", ".join([r for r in dms_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def roll(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} ndn` - Roll dice!\nEx: `{prefix}{func} 1d20`'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def yt(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} query` - Search for a YouTube video. Returns the first result.'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def card(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Draw a random card.'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def rps(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Play rock, paper, scissors with {self.client.user.display_name.capitalize()}.'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def inspire(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Get a random inspiration poster.'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    async def rd(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} subreddit` - Get a link for the queried subreddit.'
        footer = f'Related commands: {", ".join([r for r in fun_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Show the server\'s current settings.\n' \
                    f'`{prefix}{func} admin on/off` - Turn the `admin` cog on/off.\n' \
                    f'`{prefix}{func} rep on/off` - Turn the `rep` cog on/off.\n' \
                    f'`{prefix}{func} karma on/off` - Turn the `karma` cog on/off.\n' \
                    f'`{prefix}{func} mw on/off` - Turn the `mw` cog on/off.\n'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def info(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} member @user` - Show a member\'s information\n' \
                    f'`{prefix}{func} guild` - Show the guild\'s information'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} new_prefix` - Change the guild\'s prefix'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} #channel` - Change the guild\'s spam channel. Member join/leave messages and ' \
                    f'other miscellaneous output are dumped here. If not set, the default spam channel is the guild\'s ' \
                    f'system channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def admin_channel(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} #channel` - Change the guild\'s administration channel. Certain output such ' \
                    f'as votes to kick will appear in this channel. If not set the default admin_channel is the guild\'s ' \
                    f'system channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} role` - Change the guild\'s autorole. New members joining the guild will receive ' \
                    f'this role by default. Call the command without a role to clear it.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user message` - Give a member a warning for misconduct. When the member reaches ' \
                    f'two or more warnings, a "vote to kick" dialogue will appear in the administrative channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user` - Check a member\'s list of warnings.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=['cwarn'])
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user` - Clear all of a member\'s warnings.\n__aliases__: `cwarn`'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} num` - Delete `num` messages in the current channel.\n__aliases__: `purge`'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.has_permissions(kick_members=True)
    async def add(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} [pos/neg] @user message` - Modify a member\'s reputation by adding pos or neg ' \
                    f'points. A message is optional but helpful for keeping track of changes. Output is sent to the ' \
                    f'administrative channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.has_permissions(kick_members=True)
    async def sub(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} [pos/neg] @user message` - Modify a member\'s reputation by subtracting pos or neg ' \
                    f'points. A message is optional but helpful for keeping track of changes. Output is sent to the ' \
                    f'administrative channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.has_permissions(kick_members=True)
    async def reset(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} @user message` - Modify a member\'s reputation removing all pos and neg ' \
                    f'points. A message is optional but helpful for keeping track of changes. Output is sent to the ' \
                    f'administrative channel.'
        footer = f'Related commands: {", ".join([r for r in adm_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def reboot(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func}` - Restart {self.client.user.display_name.capitalize()}'
        footer = f'Related commands: {", ".join([r for r in dev_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def reload(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} cog` - Reload a cog. Useful when making changes without rebooting.'
        footer = f'Related commands: {", ".join([r for r in dev_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def load(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[0][3]
        help_menu = f'`{prefix}{func} cog` - Load a cog. Useful if a cog does not load properly during a reload.'
        footer = f'Related commands: {", ".join([r for r in dev_cmds if r != func])}'
        await self.help_embed(ctx, title=f'{func.capitalize()} Help Page', description=help_menu, footer=footer)

    # @commands.command(aliases=['-s'])
    # @commands.has_any_role('MODERATOR', 'SERVER OWNER', 'TECHNICIAN')
    # async def staffhelp(self, ctx):
    #     prefix = database.get_prefix(ctx.guild)[0]
    #     embed = discord.Embed(color=discord.Color.blue(), title='Staff Help Page')
    #     embed.add_field(name=f'`{prefix}reset @user optional: message`',
    #                     value=f'Reset a user\'s positive and negative reviews. This cannot be undone!',
    #                     inline=False)
    #     embed.add_field(name=f'`{prefix}add pos/neg @user num optional: message`',
    #                     value=f'Add either positive or negative reviews to a user.',
    #                     inline=False)
    #     embed.add_field(name=f'`{prefix}sub pos/neg @user num optional: message`',
    #                     value=f'Remove either positive or negative reviews from a user.',
    #                     inline=False)
    #     embed.add_field(name=f'`{prefix}prefix new_prefix`',
    #                     value=f'Change Mae\'s command prefix.',
    #                     inline=False)
    #     await ctx.send(embed=embed)

    @commands.command(aliases=['-h'])
    async def rep_help(self, ctx):
        prefix = database.get_prefix(ctx.guild)[0]
        embed = discord.Embed(color=discord.Color.blue(), title='Rep Help Page')
        embed.add_field(name=f'`{prefix}pos @user optional: message `',
                        value=f'Rep is our way of noticing members who have been exceptional hosts. Don\'t be '
                              f'stingy! After giving rep, you must wait **3 minutes** '
                              f'before giving more.\n'
                              f'ex: `{prefix}pos @user Thanks for the turnip run!`\n'
                              f'alias: `p`',
                        inline=False)
        embed.add_field(name=f'`{prefix}neg @user required: message `',
                        value=f'No one likes getting negative reviews, but it happens! '
                              f'After giving rep, you must wait **3 minutes** '
                              f'before giving more. Your negative reviews are private.\n'
                              f'ex: `{prefix}neg @user The sell price was much lower than stated.`\n'
                              f'alias: `n`',
                        inline=False)
        embed.add_field(name=f'`{prefix}rep optional: user`',
                        value=f'Check your own rep or another user\'s.\n'
                              f'ex: `{prefix}rep` `{prefix}rep @user`'
                              f'alias: `r`',
                        inline=False)
        embed.add_field(name=f'`{prefix}leaderboard`',
                        value=f'Check the top 10 rep leaders. If you aren\'t in the top spots, '
                              f'you will still see where you place overall.\n'
                              f'ex: `{prefix}leaderboard`'
                              f'alias: `board`',
                        inline=False)
        embed.add_field(name=f'`{prefix}bug report`',
                        value=f'Send a bug `report` to the developer. You can attach a picture alongside this command.',
                        inline=False)
        embed.add_field(name=f'Other help menus',
                        value=f'`{prefix}dms` `{prefix}staffhelp`')
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Help(client))
