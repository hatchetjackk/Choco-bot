import inspect
import discord
import util.db as database
from discord.ext import commands

rep_cmds = ['rep', 'pos', 'mpos', 'neg', 'repboard', 'karma', 'karmaboard', 'top_reviewers']
dms_cmds = ['create', 'leave', 'queue']
fun_cmds = ['roll', 'yt', 'card', 'rps', 'inspire', 'rd', 'who', 'guild', 'pfp', 'find']
adm_cmds = ['settings', 'prefix', 'spam', 'admin_channel', 'autorole', 'add', 'sub', 'reset', 'warn',
            'warnings', 'clear_warnings', 'kick', 'ban', 'purge', 'clm', 'blacklist', 'get_blacklist',
            'delete_blacklist', 'role', 'archive']
misc_cmds = ['bug', 'nick', 'afk', 'report']
dev_cmds = ['reboot', 'reload', 'load']


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(aliases=['help'])
    async def help_page(self, ctx):
        # format commands into readable lists
        def list_cmds(cmds):
            if 7 < len(cmds) < 10:
                a = cmds[:7]
                b = cmds[7:]
                lst = []
                if len(b) < len(a):
                    r = len(a) - len(b)
                    for i in range(r):
                        b.append('')
                for x, y in zip(a, b):
                    spaces_x = 15 - (len(x))
                    lst.append(f'{x}{" " * spaces_x}{y}')
                lst = '\n' + '\n'.join(lst)
            elif len(cmds) > 10:
                a = cmds[:6]
                b = cmds[6:12]
                c = cmds[12:]
                lst = []
                if len(c) < len(b):
                    r = len(b) - len(c)
                    for i in range(r):
                        c.append('')
                for x, y, z in zip(a, b, c):
                    spaces_x = 15 - (len(x))
                    spaces_y = 15 - (len(y))
                    lst.append(f'{x}{" " * spaces_x}{y}{" " * spaces_y}{z}')
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
            embed.add_field(name='> Queueing System', value=list_cmds(dms_cmds), inline=False)
            embed.add_field(name='> Administrative', value=list_cmds(adm_cmds), inline=False)
            embed.add_field(name='> Developer', value=list_cmds(dev_cmds))
            embed.add_field(name='> Misc', value=list_cmds(misc_cmds))
            about = f'This bot is owned and actively developed by **{self.client.get_user(self.client.owner_id).display_name}**. ' \
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

    async def help2_embed(self, ctx, args, description, aliases=None):
        prefix = database.get_prefix(ctx.guild)[0]
        func = inspect.stack()[1][3]
        title = f'{func.capitalize()} Help'
        desc = prefix + func
        if args is not None:
            desc += f' {args}'
        if func == 'thanks':
            desc = f'{func} {args}'
        embed = discord.Embed(title=title, color=discord.Color.green(), description=f'```\n{desc}```')
        embed.add_field(name=f'> Description', value=description, inline=False)
        if aliases is not None:
            if type(aliases) == list:
                embed.add_field(name='> Aliases', value=', '.join([f'`{a}`' for a in aliases]), inline=False)
            else:
                embed.add_field(name='> Aliases', value=f'`{aliases}`', inline=False)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        for lst in [misc_cmds, rep_cmds, dms_cmds, fun_cmds, adm_cmds, dev_cmds]:
            if func in lst:
                footer = f'Related commands: {", ".join([r for r in lst if r != func])}'
                embed.set_footer(text=footer)
        await ctx.send(embed=embed)

    """ misc commands """

    @help_page.group()
    async def report(self, ctx):
        args = '@user message'
        description = f'Report a user for harmful content. Reports are sent to staff and deleted.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def afk(self, ctx):
        args = 'autoresponse'
        description = f'Set an autoresponse if you are AFK. Whenever a user pings you, this response will be displayed. ' \
                      f'Enter the command again to turn off AFK.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def nick(self, ctx):
        args = 'nickname'
        description = f'Change your nickname. This command does not work for roles higher than ' \
                      f'{self.client.user.display_name}.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def bug(self, ctx):
        args = 'message'
        description = 'Send a bug report to the developer. Add a screenshot of the bug to the command when possible.'
        await self.help2_embed(ctx, args, description)

    """ karma commands """

    @help_page.group(aliases=['kboard'])
    async def karmaboard(self, ctx):
        args = ''
        description = 'Get the top 10 karma leaders.\n\n' \
                      'Karma is a point system established around constructive communities. ' \
                      'If another member has done something for you please think about giving them ' \
                      'karma.'
        await self.help2_embed(ctx, args, description, aliases=self.karmaboard.aliases)

    @help_page.group()
    async def karma(self, ctx):
        args = None
        description = 'See how much karma you have.\n\n' \
                      'Karma is a point system established around constructive communities. ' \
                      'If another member has done something for you please think about giving them ' \
                      'karma.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['cheers'])
    async def thanks(self, ctx):
        args = '@user'
        description = 'Give another user karma. You can also use `cheers`. This function is unique as it does **not** ' \
                      'require a prefix. It can uniquely be called anywhere in a message. \nAffected by *cooldown*.\n\n' \
                      'Karma is a point system established around constructive communities. ' \
                      'If another member has done something for you please think about giving them ' \
                      'karma.'
        await self.help2_embed(ctx, args, description, self.thanks.aliases)

    """ dms commands """

    @help_page.group()
    async def rep(self, ctx):
        args = '@optional_user'
        description = 'Get your or the (optional) mentioned user\'s reputation. If you do not want to ping the user, you ' \
                      'can enter the user\'s ID or type out their username inside of quotes.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def pos(self, ctx):
        args = '@user optional_message'
        description = 'Give a user a positive review which increases their **rep**. The message is optional and appears in ' \
                      'the review channel if configured. This command is purged immediately after sending.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def mpos(self, ctx):
        args = '@user1 @user2 @user3 (etc) optional_message'
        description = 'Need to give a lot of reviews at once? Now you can do it all in one message. Anyone mentioned in ' \
                      'the mpos message will get a positive review. Affected by a 1 minute cooldown.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def neg(self, ctx):
        args = '@user required_message'
        description = 'Give a user a negative review which affects their **rating**. The message is **required** and ' \
                      'appears in the administrative support channel if configured. This command is purged immediately ' \
                      'for privacy.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['rboard'])
    async def repboard(self, ctx):
        args = None
        description = 'Get the top 10 best reviewed.'
        await self.help2_embed(ctx, args, description, self.repboard.aliases)

    @help_page.group(aliases=['reviewers', 'reviews'])
    async def top_reviewers(self, ctx):
        args = None
        description = 'Get a list of the top reviewers. Not all heroes wear capes.'
        await self.help2_embed(ctx, args, description, aliases=self.top_reviewers.aliases)

    """ Session commands """

    @help_page.group()
    async def create(self, ctx):
        args = None
        description = 'Create a Session. A Session allows you to create queues for Timmy/Tommy, Daisy, and ' \
                      'trading. Creating a Session will generate a private channel for you to manage your queue.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def leave(self, ctx):
        args = None
        description = f'`leave` gives you an interactive prompt with a list of the sessions you are currently in. Use ' \
                      f'numbered reactions to choose a session to leave.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def queue(self, ctx):
        args = None
        description = f'Show a list of sessions you currently belong to.'
        await self.help2_embed(ctx, args, description)

    """ fun commands """

    @help_page.group()
    async def find(self, ctx):
        args = 'input'
        description = f'Search for users in the server.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def roll(self, ctx):
        args = 'ndn'
        description = f'Roll dice!'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def pfp(self, ctx):
        args = '@user'
        description = f'Is a user\'s profile picture too small? Use this to see all the details!'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def yt(self, ctx):
        args = 'query'
        description = f'Search for a YouTube video. Returns the first result.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def card(self, ctx):
        args = None
        description = f'Draw a random card.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def rps(self, ctx):
        args = 'rock/paper/scissors'
        description = f'Play rock, paper, scissors against {self.client.user.display_name.capitalize()}.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def inspire(self, ctx):
        args = None
        description = f'Get a random inspiration poster.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def rd(self, ctx):
        args = 'subreddit'
        description = f'Get a link for the queried subreddit.'
        await self.help2_embed(ctx, args, description)

    """ admin commands """

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
    async def clm(self, ctx):
        args = '@user int'
        description = 'Clear `int` number of messages from a user in the current channel. This does not work if a user ' \
                      'has left the server.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def archive(self, ctx):
        args = None
        description = 'Archive the current channel. This replaces the channel with a new clone!'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def role(self, ctx):
        args = 'role'
        description = 'See who has the specified role. No need to @ it.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def ban(self, ctx):
        args = '@user optional_message'
        description = 'Ban the mentioned user and send them an optional message about why they were banned. They will ' \
                      'not be able to return to the server.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def kick(self, ctx):
        args = '@user optional_message'
        description = 'Kick the mentioned user and send them an optional message about why they were kicked. They could ' \
                      'rejoin using a different invite link.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def who(self, ctx):
        args = '@user'
        description = 'Get information about a user.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def guild(self, ctx):
        args = None
        description = 'Get information about the server.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx):
        args = 'prefix'
        description = 'Change the guild\'s prefix.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx):
        args = '#channel'
        description = 'Change the guild\'s spam channel. Member join/leave messages and ' \
                      f'other miscellaneous output are dumped here. If not set, the default spam channel is the guild\'s ' \
                      f'system channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def admin_channel(self, ctx):
        args = '#channel'
        description = 'Change the guild\'s administration channel. Certain output such ' \
                      f'as votes to kick will appear in this channel. If not set the default admin_channel is the guild\'s ' \
                      f'system channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(administrator=True)
    async def autorole(self, ctx):
        args = 'optional_rolename'
        description = 'Change the guild\'s autorole. New members joining the guild will receive ' \
                      f'this role by default. **Call the command without a role to clear it.**'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx):
        args = '@user message'
        description = 'Give a member a warning for misconduct. When the member reaches ' \
                      f'two or more warnings, a "vote to kick" dialogue will appear in the administrative channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx):
        args = '@user'
        description = 'Check a member\'s list of warnings.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['cwarn'])
    @commands.has_permissions(kick_members=True)
    async def clear_warnings(self, ctx):
        args = '@user'
        description = 'Clear all warnings for mentioned user.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['getbl'])
    async def get_blacklist(self, ctx):
        args = None
        description = 'See blacklisted items'
        await self.help2_embed(ctx, args, description, aliases=self.get_blacklist.aliases)

    @help_page.group(aliases=['bl'])
    async def blacklist(self, ctx):
        args = 'item1 item2 item3...'
        description = 'Blacklist items from messages. Messages with blacklisted items will automatically be deleted.'
        await self.help2_embed(ctx, args, description, aliases=self.blacklist.aliases)

    @help_page.group(aliases=['delbl'])
    async def delete_blacklist(self, ctx):
        args = 'item1 item2 item3...'
        description = 'Remove items from the blacklist.'
        await self.help2_embed(ctx, args, description, aliases=self.delete_blacklist.aliases)

    @help_page.group()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx):
        args = 'num'
        description = f'Delete `num` messages in the current channel.'
        await self.help2_embed(ctx, args, description, self.purge.aliases)

    @help_page.group()
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
        args = '[pos/neg] @user message'
        description = 'Modify a member\'s reputation by subtracting pos or neg ' \
                      f'points. A message is optional but helpful for keeping track of changes. Output is sent to the ' \
                      f'administrative channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=[])
    @commands.has_permissions(kick_members=True)
    async def reset(self, ctx):
        args = '@user message'
        description = 'Modify a member\'s reputation removing all pos and neg ' \
                      f'points. A message is optional but helpful for keeping track of changes. Output is sent to the ' \
                      f'administrative channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def reboot(self, ctx):
        args = None
        description = f'Restart {self.client.user.display_name.capitalize()}.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def reload(self, ctx):
        args = 'cog'
        description = 'Reload a cog. Useful when making changes without rebooting.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=[])
    @commands.is_owner()
    async def load(self, ctx):
        args = 'cog'
        description = 'Load a cog. Useful if a cog does not load properly during a reload.'
        await self.help2_embed(ctx, args, description)


def setup(client):
    client.add_cog(Help(client))
