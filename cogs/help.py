import inspect
import discord
import util.db as database
from discord.ext import commands
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

rep_cmds = ['rep', 'pos', 'mpos', 'neg', 'repboard', 'karma', 'karmaboard', 'top_reviewers']
dms_cmds = ['create', 'leave', 'queue', 'villager', 'personality', 'species', 'insects', 'bugs', 'diy', 'art']
fun_cmds = ['roll', 'yt', 'card', 'rps', 'inspire', 'rd', 'guild', 'pfp', 'pf', 'find', 'sw-set', 'sw-get',
            'remindme', 'reminders', 'delreminder', 'time']
game_cmds = ['dig', 'net', 'cast', 'slots', 'bells', 'appraise']
adm_cmds = ['settings', 'prefix', 'spam', 'reputation', 'disciplinary', 'admin_channel', 'purge', 'clm', 'blacklist',
            'get_blacklist', 'delete_blacklist', 'selfrole', 'autorole', 'role', 'archive', 'messages']
misc_cmds = ['bug', 'nick', 'afk', 'report', 'support', 'my_warnings']
dev_cmds = ['reboot', 'reload', 'load', 'clean_session']


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(aliases=['help'])
    async def help_page(self, ctx):
        if ctx.invoked_subcommand is None:
            embeds = []
            color = discord.Color.green()
            owner = discord.utils.get(ctx.guild.members, id=self.client.owner_id).display_name
            footer = f'Owned and actively developed by {owner}'
            name = f'> Use `r:help command` to learn more'

            description = '[Reputation](http://localhost) - Fun - ACNH - Games - Administrative - Misc - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(rep_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - [Fun](http://localhost) - ACNH - Games -Administrative - Misc - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(fun_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - Fun - [ACNH](http://localhost) - Games -Administrative - Misc - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(dms_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - Fun - ACNH - [Games](http://localhost) - Administrative - Misc - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(game_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - Fun - ACNH - Games - [Administrative](http://localhost) - Misc - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(adm_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - Fun - ACNH - Games - Administrative - [Misc](http://localhost) - Developer'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(misc_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            embed.set_footer(text=footer)
            embeds.append(embed)

            description = 'Reputation - Fun - ACNH - Games - Administrative - Misc - [Developer](http://localhost)'
            embed = discord.Embed(title='Help Pages', description=description, color=color)
            value = "\n".join(dev_cmds)
            embed.add_field(name=name, value=f'```\n{value}```')
            msg = f'This bot is owned and actively developed by {owner}. If you\'d like to support my work, you can buy me a [coffee](https://ko-fi.com/hatchet_jackk).\nCheers.'
            embed.add_field(name='About', value=msg, inline=False)
            embed.set_footer(text=footer)
            embeds.append(embed)

            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()

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

    @help_page.group(aliases=['mywarns'])
    async def my_warnings(self, ctx):
        args = None
        description = 'Get a private DM that shows your warnings.'
        await self.help2_embed(ctx, args, description, aliases=self.my_warnings.aliases)

    @help_page.group(aliases=['ticket'])
    async def support(self, ctx):
        args = 'tech/ingame/server message'
        description = f'Submit a support ticket for help with the related topic.\n' \
                      f'Mae-Bot: submit a ticket with `support tech \'your message\'`.\n' \
                      f'aliases: `bot`, `technical`\n' \
                      f'ACNH: submit a ticket with `support acnh \'your message\'`.\n' \
                      f'aliases: `ingame`, `ig`\n' \
                      f'Server: submit a ticket with `support server \'your message\'`.\n' \
                      f''
        await self.help2_embed(ctx, args, description, aliases=self.support.aliases)

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
    async def diy(self, ctx):
        args = 'item'
        description = 'Get general information about a DIY recipe including required materials.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def art(self, ctx):
        args = 'artwork_name'
        description = 'Get a list of all art in ACNH. You can use the item name to get more information about it. \n' \
                      'Example: `r:art famous painting` will give you more information about the Mona Lisa!'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def fossils(self, ctx):
        args = None
        description = 'Get a list of available fossils and their sell value in ACNH.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['bugs'])
    async def insects(self, ctx):
        args = 'insect_name / month'
        description = '`month`: If you call a month, you will get all insects available for that month **and** a list of insects leaving next month.\n' \
                      '`insect_name`: If you call an insect name you will get relevant information about that insect plus an image.'
        await self.help2_embed(ctx, args, description, aliases=self.insects.aliases)

    @help_page.group()
    async def fish(self, ctx):
        args = 'fish_name / month'
        description = '`month`: If you call a month, you will get all fish available for that month **and** a list of fish leaving next month.\n' \
                      '`fish_name`: If you call a fish name you will get relevant information about that fish plus an image.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def villager(self, ctx):
        args = 'villager_name'
        description = 'Find quick info about a villager.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def species(self, ctx):
        args = 'species'
        description = 'Quickly find all villagers of a certain species.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['pers'])
    async def personality(self, ctx):
        args = 'personality_type'
        description = 'Get a list of villagers with the associated personality type.'
        await self.help2_embed(ctx, args, description, aliases=self.personality.aliases)

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

    @help_page.group(aliases=['remind_me', 'remind-me'])
    async def remindme(self, ctx):
        args = 'number denominator message'
        description = f'This is a simple reminder tool which you can set to send you a message at minutes, hours, or days ' \
                      f'from the time to create the command. You can only use the denominators `m` for minutes, `h` ' \
                      f'for hours, and `d` for days using this format:' \
                      f'```\n' \
                      f'r:remindme 1 m This will send me a DM in 1 minute\n' \
                      f'r:remindme 1 h This will send me a DM in 1 hour\n' \
                      f'r:remindme 1 d This will send me a DM in 1 day```'
        await self.help2_embed(ctx, args, description, aliases=self.remindme.aliases)

    @help_page.group()
    async def reminders(self, ctx):
        args = None
        description = f'Get a list of current reminders.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def delreminder(self, ctx):
        args = 'number'
        description = f'Delete one of your reminders. You must know the index number of your reminder. To get the index ' \
                      f'number, use the `reminders` command and note the **number** before the date (ie: 1.) of the ' \
                      f'reminder you want to delete. That is the number you want to use.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def time(self, ctx):
        args = None
        description = f'Get the current time in UTC format.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def find(self, ctx):
        args = 'input'
        description = f'Search for users in the server.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['sw-set'])
    async def sw_set(self, ctx):
        args = 'switch-code'
        description = f'Store your switch code for later retrieval.'
        await self.help2_embed(ctx, args, description, aliases=self.sw_set.aliases)

    @help_page.group(aliases=['sw-get'])
    async def sw_get(self, ctx):
        args = None
        description = f'Show your Switch friend code.'
        await self.help2_embed(ctx, args, description, aliases=self.sw_get.aliases)

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

    """ Game Commands """

    @help_page.group()
    async def bells(self, ctx):
        args = None
        description = f'Gather some bells. You can do this once per day. Mae-Supporters earn 50% more bells per use.'
        await self.help2_embed(ctx, args, description)

    @help_page.group(aliases=['paint'])
    async def appraise(self, ctx):
        args = None
        description = f'Add some art to your collection. Art costs 10 bells each.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def dig(self, ctx):
        args = None
        description = f'Dig up some fossils! Each attempt costs 10 bells for "excavation permits."'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def net(self, ctx):
        args = None
        description = f'Try to catch some bugs for your collection! Each attempt uses 10 bells for "bug bait!"'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def cast(self, ctx):
        args = None
        description = f'Try to catch some fish for your collection! Each attempt uses 10 bells for "fish bait!"'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def slots(self, ctx):
        args = 'bells'
        description = f'Bet some bells at the slots for a chance to hit the jackpot! Default bet is 10 bells.\n\n' \
                      f'Winning Scenarios:\n' \
                      f'🍒 x3 ........................ Win 10x!\n' \
                      f'Match all 3 .............. Win 4x!\n' \
                      f'Match any 2 ............ Win 2x!'
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
    async def messages(self, ctx):
        args = '@user #channel num'
        description = 'Get the last (num) messages for the @user in #channel.'
        await self.help2_embed(ctx, args, description)

    @help_page.group()
    async def reputation(self, ctx):
        args = None
        description = 'Mae-Bot manages reputation. Mods and admins can correct rep with the following commands:\n' \
                      '`add`, `sub`, and `reset`. Please use the `help` command to see how to use them.'
        await self.help2_embed(ctx, args, description)

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
    async def pf(self, ctx):
        args = '@user'
        description = 'Get all of the available information about yourself or am optional user.\n' \
                      'You can update your Fruit, Flower, and Hemisphere sections using these commands:\n' \
                      '`r:set_fruit your_fruit`\n' \
                      '`r:set_flower your_flower`\n' \
                      '`r:set_hemisphere your_hemisphere`'
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
    @commands.has_permissions(administrator=True)
    async def selfrole(self, ctx):
        args = '@role message'
        description = 'Create a message that automatically gives a user a role when they use the reaction.'
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
    async def disciplinary(self, ctx):
        args = None
        description = 'Managing negative behavior is done with warnings, kicks, and bans. Some warnings are automatic ' \
                      'while others have to be given by the Mod and Admin teams. Disciplinary commands include: \n' \
                      '`warnings`, `warn`, `clear_warnings`, `delete_warning`, `kick`, `ban`\n' \
                      'Use the `help` command for more information on each command.'
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
        await self.help2_embed(ctx, args, description, aliases=self.clear_warnings.aliases)

    @help_page.group(aliases=['delwarn'])
    @commands.has_permissions(kick_members=True)
    async def delete_warnings(self, ctx):
        args = 'warning_id'
        description = 'Delete a user\'s warning. You can get the message/warning ID from the `warnings` command.'
        await self.help2_embed(ctx, args, description, aliases=self.delete_warnings.aliases)

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
