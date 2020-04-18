import inspect
import discord
import util.db as database
from discord.ext import commands

rep_cmds = ['rep', 'pos', 'neg', 'repboard', 'karma', 'karmaboard', 'top_reviewers']
dms_cmds = ['create', 'close', 'opn', 'end', 'join', 'leave', 'menu', 'send', 'dodo', 'show', 'notify', 'welcome',
            'guest_kick', 'guest_ban', 'guest_unban', 'guest_bans', 'admin_end']
fun_cmds = ['roll', 'yt', 'card', 'rps', 'inspire', 'rd', 'who', 'guild']
adm_cmds = ['settings', 'prefix', 'spam', 'admin_channel', 'autorole', 'add', 'sub', 'reset', 'warn',
            'warnings', 'clear_warnings', 'kick', 'ban', 'purge_messages', 'blacklist', 'get_blacklist',
            'delete_blacklist']
misc_cmds = ['bug', 'nick', 'afk']
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

    @help_page.group()
    async def create(self, ctx):
        args = None
        description = 'Create a new Daisy-Mae Session (DMS). A DMS allows you to create queues and comes with its own ' \
                      'list of powerful commands that are only usable when hosting. Creating a DMS will generate a ' \
                      'private channel for you to manage your queue.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def close(self, ctx):
        args = None
        description = 'Close the doors to your DMS to prevent new guests from joining. This does not end your session. ' \
                      'Closing your session will shutdown any embeds generated by creating your DMS.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def admin_end(self, ctx):
        args = 'session_code'
        description = 'Forcibly close a DMS session.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['open'])
    async def opn(self, ctx):
        args = None
        description = 'Close the doors to your DMS to prevent new guests from joining. This does not end your session. ' \
                      'Closing your session will shutdown any embeds generated by creating your DMS.'
        await self.help2_embed(ctx, args, description, aliases=self.opn.aliases)

    @help_page.group()
    async def end(self, ctx):
        args = None
        description = 'Shut down your DMS. Any guests still in your queue will be notified that the session is over. This ' \
                      'removes any embeds generated by creating your DMS session.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def join(self, ctx):
        args = 'session_code'
        description = f'Join an existing session using a DMS code. If the DMS session was posted publicly, try clicking ' \
                      f'the :Turnip: reaction instead!'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def leave(self, ctx):
        args = 'session_code'
        description = f'Leave a DMS queue using the corresponding session_code. You can find your session_code in your ' \
                      f'DMS notification.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def menu(self, ctx):
        args = None
        description = f'Get all host options while hosting a DMS.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def send(self, ctx):
        args = None
        description = f'Send your Dodo code to the next group in your DMS queue. This clears the group ' \
                      f'and notifies all groups that they have moved up in the queue.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def dodo(self, ctx):
        args = 'code'
        description = f'Change your Dodo code on the fly in your DMS'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def show(self, ctx):
        args = 'code'
        description = f'Show your current DMS queue.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def notify(self, ctx):
        args = 'optional_group message'
        description = f'Send a message to guests in your queue. You can target a specific group before starting the ' \
                      f'message. For example, `notify 2 This will send a message to group 2`. The group number is ' \
                      f'literal and not relative to the position in the queue. If group 2 has already gone, this message ' \
                      f'will not reach anyone.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def welcome(self, ctx):
        args = 'message'
        description = f'Set a welcome message that guests will receive when they join your DMS. This is helpful if you ' \
                      f'want to include more information than what was in your original DMS post, or if you want to be ' \
                      f'more certain that a guest knows to "leave via the airport" or "wait to be kicked."'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def guest_kick(self, ctx):
        args = '"guest name"'
        description = f'Kick a guest from your DMS queue. Due to limitations, the guest\'s full ' \
                      f'name needs to be included in quotes.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def guest_ban(self, ctx):
        args = '"guest name"'
        description = f'Ban a guest from entering or re-entering your DMS queue. Due to ' \
                      f'limitations, the guest\'s full name needs to be included. If the guest name has a space in it, ' \
                      f'the name must be wrapped in quotes.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def guest_unban(self, ctx):
        args = '"guest name"'
        description = f'Unban a guest so that may re-enter your queue. Due to ' \
                      f'limitations, the guest\'s full name needs to be included. If the guest name has a space in it, ' \
                      f'the name must be wrapped in quotes.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def guest_bans(self, ctx):
        args = None
        description = f'Show a list of guests banned from your DMS.'
        await self.help2_embed(ctx, args, description)

    """ fun commands """

    @help_page.group()
    async def roll(self, ctx):
        args = 'ndn'
        description = f'Roll dice!'
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

    @help_page.group(aliases=['purge'])
    @commands.has_permissions(manage_messages=True)
    async def purge_messages(self, ctx):
        args = 'num'
        description = f'Delete `num` messages in the current channel.'
        await self.help2_embed(ctx, args, description, self.purge_messages.aliases)

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
