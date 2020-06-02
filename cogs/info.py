import sqlite3
import discord
import json
import time
import util.db as db
import util.tools as tools
import util.db as database
from datetime import datetime
from discord.ext import commands


class Information(commands.Cog):
    def __init__(self, client):
        self.client = client

    """
    Administrative Info Commands
    """

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def role(self, ctx, role: discord.Role):
        members_with_role = []
        for m in ctx.guild.members:
            if role in m.roles:
                members_with_role.append(m)
        description = '\n'.join([m.display_name for m in members_with_role])
        embed = discord.Embed(title=f'Users with the role {role}', description=description, color=discord.Color.green())
        embed.set_thumbnail(url=self.client.user.avatar_url)
        await ctx.send(embed=embed)

    """
    Information Commands
    """

    @commands.command(aliases=['sw-set'])
    async def sw_set(self, ctx, code: str):
        with open('files/sw.json', 'r') as f:
            data = json.load(f)
        data[str(ctx.author.id)] = code.upper()
        with open('files/sw.json', 'w') as f:
            json.dump(data, f, indent=4)
        await ctx.send(embed=tools.single_embed(f'{ctx.author.display_name}\'s friend code has been set to **{code.upper()}**'))

    @commands.command(aliases=['sw-get'])
    async def sw_get(self, ctx):
        with open('files/sw.json', 'r') as f:
            data = json.load(f)
        sw = data[str(ctx.author.id)]
        await ctx.send(embed=tools.single_embed(f'{ctx.author.display_name}\'s friend code is **{sw}**'))

    @commands.command()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def guild(self, ctx):
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name='Guild Owner', value=ctx.guild.owner)
        embed.add_field(name='Creation Date', value=tools.format_date(ctx.guild.created_at, 1))
        embed.add_field(name='System Channel', value=ctx.guild.system_channel.mention, inline=False)
        embed.add_field(name='Number of Channels', value=str(len(ctx.guild.text_channels)))
        embed.add_field(name='Number of Members', value=str(ctx.guild.member_count))
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def find(self, ctx, member):
        if ctx.invoked_subcommand is None:
            members = [m for m in ctx.guild.members if member in m.display_name.lower() or member in m.name.lower() or member in str(m.id)]
            description = '\n'.join([f'{m.name} / {m.display_name} ({m.id})' for m in members])
            if len(description) > 2000:
                await ctx.send(embed=tools.single_embed(f'Your search is too broad. Try to be more specific.'))
                return
            embed = discord.Embed(title='Found Members', description=description, color=discord.Color.green())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.has_role('guest')
    async def nick(self, ctx, *nickname):
        if len(nickname) < 1:
            msg = 'You name cannot be empty.'
            await ctx.send(embed=tools.single_embed(msg), delete_after=5)
            return
        spam = db.get_spam(ctx.guild)
        msg = f'{ctx.author.display_name} changed their nickname to {" ".join(nickname)}.'
        await ctx.author.edit(nick=' '.join([w.replace("'", "\'") for w in nickname]))
        await ctx.send(embed=tools.single_embed(msg))
        await spam.send(embed=tools.single_embed(msg))

    @commands.command()
    async def pfp(self, ctx, member: discord.Member):
        embed = discord.Embed(title=f'{member.display_name}\'s Avatar', color=member.color)
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def afk(self, ctx, *autoresponse):
        if len(autoresponse) == 0:
            await ctx.send(embed=tools.single_embed('You are no longer **AFK**.'))
            db.set_afk(ctx.author, 0, None)
            return
        else:
            db.set_afk(ctx.author, 1, ' '.join(autoresponse).replace("'", "\'"))
            await ctx.send(embed=tools.single_embed(f'AFK message set to \n {" ".join(autoresponse)}'))

    @commands.command()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def who(self, ctx, member: discord.Member):
        if await self.can_bypass_cooldown(ctx):
            self.who.reset_cooldown(ctx)

        description = f'{member}, {member.mention}'
        one_week = 604800

        if tools.to_seconds(member.joined_at) < one_week:
            description = '🌱 ' + description
        embed = discord.Embed(title=f'{member.display_name}', color=member.colour, description=description)
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Status', value=member.status)
        if member.activity is not None:
            embed.add_field(name='Activity', value=member.activity.name)
        embed.add_field(name='Joined Guild', value=f'{tools.format_date(member.joined_at)}', inline=False)
        roles = [role.name for role in member.roles if role.name != '@everyone']
        if len(roles) > 0:
            embed.add_field(name='Roles', value=', '.join(roles))
        else:
            embed.add_field(name='Roles', value='None')
        nicknames = db.get_member_nick_history(member)
        nicks = [f'{n[0]}' for n in nicknames]
        if len(nicks) > 5:
            nicks = nicks[-5:]
        if len(nicknames) > 0:
            embed.add_field(name='Aliases', value='\n'.join(nicks), inline=False)
        else:
            embed.add_field(name='Aliases', value='None', inline=False)
        embed.set_footer(text=f'Joined Discord {tools.format_date(member.joined_at)}')
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['mywarns'])
    async def my_warnings(self, ctx):
        if not database.in_warnings_table(ctx.author, ctx.guild):
            msg = f'You have `0` warnings.'
            embed = discord.Embed(color=discord.Color.green(), description=msg)
            embed.set_thumbnail(url=ctx.author.avatar_url)
            await ctx.author.send(embed=embed)
            await ctx.send(embed=tools.single_embed('A private DM has been sent.'), delete_after=10)
        else:
            warnings, messages = database.get_warnings(ctx.author)
            fmt = []
            for m in messages:
                fmt.append(f'`{m[0]}.` {m[4]} - {m[3]} ')
            if len(fmt) > 0:
                msg = f'__Past Warnings__\n' + '\n'.join(fmt)
                embed = discord.Embed(color=discord.Color.red(), description=msg)
                embed.set_author(name=f'{ctx.author.display_name} ({ctx.author})', icon_url=ctx.author.avatar_url)
                await ctx.author.send(embed=embed)
                await ctx.send(embed=tools.single_embed('A private DM has been sent.'), delete_after=10)

    """
    Reporting Commands
    """

    @staticmethod
    async def add_ticket(_type, ctx, issue, message):
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        with conn:
            curs.execute(
                "INSERT INTO tickets "
                "VALUES (:number, :type, :member, :issue, :resolved, :message)",
                {'number': None, 'type': _type, 'member': ctx.author.id, 'issue': issue, 'resolved': 0,
                 'message': message.id}
            )

    @staticmethod
    async def resolve_ticket(number):
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        with conn:
            curs.execute("UPDATE tickets SET resolved = 1 WHERE number = (:number)",
                         {'number': number})
        curs.execute("SELECT message FROM tickets WHERE number = (:number)", {'number': number})
        message = curs.fetchone()[0]
        return message

    @staticmethod
    async def get_ticket(number):
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        curs.execute("SELECT * from TICKETS where number = (:number)", {'number': number})
        data = curs.fetchone()
        return data

    @staticmethod
    async def get_ticket_by_message_id(message_id):
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        curs.execute("SELECT * from TICKETS where message = (:message)", {'message': message_id})
        data = curs.fetchone()
        return data

    @staticmethod
    async def get_last_ticket():
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        curs.execute("SELECT number, type, member, issue from TICKETS ORDER BY number DESC LIMIT 1")
        data = curs.fetchone()
        return data

    async def ticket_embed(self, ctx, _type, member, message):
        (number, _type, member_id, issue) = await self.get_last_ticket()
        ticket_type = {'technical': 'red', 'in_game': 'blue', 'server': 'gold'}
        if ticket_type.get(_type) == 'red':
            color = discord.Color.red()
        elif ticket_type.get(_type) == 'blue':
            color = discord.Color.blue()
        else:
            color = discord.Color.gold()
        title = f'A __{_type}__ ticket has been submitted.'
        date = tools.format_date(datetime.utcnow())
        description = f'Created by: {member} / {member.mention}\n' \
                      f'Date: {date} UTC\n' \
                      f'Channel: {ctx.channel.mention}'
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name=f'Ticket Number: **{number + 1}**', value=message)
        embed.set_footer(text='Click the thumbs up to assign this ticket to yourself.')
        if len(ctx.message.attachments) > 0:
            url = ctx.message.attachments[0].url
            embed.set_image(url=url)
        return embed

    async def ticket_channel(self):
        return self.client.get_channel(711981322658119722)

    @commands.group(aliases=['ticket'])
    async def support(self, ctx):
        if ctx.invoked_subcommand is None:
            msg = 'Please submit a ticket using the following format:\n' \
                  '`r:support server/tech/acnh "Enter your message here"`\n' \
                  'Please use `r:help support` for more information.'
            await ctx.send(embed=tools.single_embed(msg))

    @support.group(aliases=['tech', 'bot'])
    async def technical(self, ctx, *, issue: str):
        ticket_channel = await self.ticket_channel()
        embed = await self.ticket_embed(ctx, 'technical', ctx.author, issue)
        message = await ticket_channel.send(embed=embed)
        await message.add_reaction('👍')
        await ctx.send(embed=tools.single_embed(f'Your ticket has been submitted.'))
        await self.add_ticket('technical', ctx, issue, message)
        await ctx.message.delete()

    @support.group(aliases=['in-game', 'ingame', 'ig', 'acnh'])
    async def in_game(self, ctx, *, issue: str):
        ticket_channel = await self.ticket_channel()
        embed = await self.ticket_embed(ctx, 'in_game', ctx.author, issue)
        message = await ticket_channel.send(embed=embed)
        await message.add_reaction('👍')
        await ctx.send(embed=tools.single_embed(f'Your ticket has been submitted.'))
        await self.add_ticket('in_game', ctx, issue, message)
        await ctx.message.delete()

    @support.group()
    async def server(self, ctx, *, issue: str):
        ticket_channel = await self.ticket_channel()
        embed = await self.ticket_embed(ctx, 'server', ctx.author, issue)
        message = await ticket_channel.send(embed=embed)
        await message.add_reaction('👍')
        await ctx.send(embed=tools.single_embed(f'Your ticket has been submitted.'))
        await self.add_ticket('server', ctx, issue, message)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id != 711981322658119722:
            return

        try:
            guild = self.client.get_guild(payload.guild_id)
            user = discord.utils.get(guild.members, id=payload.user_id)
            if user.bot or user is None:
                return
        except AttributeError:
            return

        emoji = payload.emoji.name
        message_id = payload.message_id

        if emoji == '👍':
            (number, _type, member, issue, resolved, message) = await self.get_ticket_by_message_id(message_id)
            member = discord.utils.get(guild.members, id=member)
            try:
                msg = f'Your ticket number **{number}** has been assigned to a helper.\n' \
                      f'> {issue}'
                await member.send(embed=tools.single_embed(msg))
            except discord.Forbidden:
                pass
            await self.resolve_ticket(number)
            message = await self.client.get_channel(711981322658119722).fetch_message(id=message_id)
            new_embed = message.embeds[0].to_dict()
            new_embed['title'] = f'Ticket assigned.'
            new_embed['footer']['text'] = 'Click the check mark to resolve the ticket.'
            name = f'Ticket assigned to:'
            date = tools.format_date(datetime.utcnow())
            value = f'{user}/{user.mention}\nDate: {date} UTC.'
            new_embed['fields'].append({'name': name, 'value': value, 'inline': False})
            embed = discord.Embed.from_dict(new_embed)
            await message.edit(embed=embed)
            await message.clear_reactions()
            await message.add_reaction('✔️')
        elif emoji == '✔️':
            (number, _type, member, issue, resolved, message) = await self.get_ticket_by_message_id(message_id)
            member = discord.utils.get(guild.members, id=member)
            try:
                msg = f'Your ticket number **{number}** has been resolved.\n' \
                      f'> {issue}'
                await member.send(embed=tools.single_embed(msg))
            except discord.Forbidden:
                pass
            await self.resolve_ticket(number)
            message = await self.client.get_channel(711981322658119722).fetch_message(id=message_id)
            new_embed = message.embeds[0].to_dict()
            new_embed['title'] = 'Ticket resolved.'
            new_embed['footer']['text'] = 'no actions required'
            name = f'Ticket resolved by:'
            date = tools.format_date(datetime.utcnow())
            value = f'{user}/{user.mention}\nDate: {date} UTC.'
            new_embed['fields'].append({'name': name, 'value': value, 'inline': False})
            embed = discord.Embed.from_dict(new_embed)
            await message.edit(embed=embed)
            await message.clear_reactions()

    @commands.command()
    async def bug(self, ctx, *, message: str):
        """
        Send a bug report
        :param ctx:
        :param message:
        :return:
        """
        msg = f'A bug report was filed by **{ctx.author.display_name}**.\n**Message**: {message}'
        if len(ctx.message.attachments) > 0:
            msg += '\n' + ctx.message.attachments[0].url
        channels = [c for c in ctx.guild.channels if 'bug-reports']
        chan = None
        for c in channels:
            if 'bug-report' in c.name:
                chan = c
        if chan is not None:
            await chan.send(embed=tools.single_embed_neg(msg, avatar=ctx.author.avatar_url))
        else:
            owner = self.client.get_user(193416878717140992)
            await owner.send(msg)
        await ctx.send(embed=tools.single_embed_neg(f'Your report has been sent. Thank you.'))

    @commands.command()
    async def report(self, ctx, member: discord.Member, *, report: str = None):
        if len(ctx.message.attachments) < 1:
            msg = f'Your negative review is incomplete. Please attach a screenshot or picture verifying your claim.'
            try:
                await ctx.author.send(embed=tools.single_embed(msg))
            except discord.Forbidden:
                await ctx.send(embed=tools.single_embed(msg), delete_after=5)
            await ctx.message.delete()
            return
        channel = db.get_administrative(ctx.guild)
        embed = discord.Embed(title='Report', description=report, color=discord.Color.red())
        reporter = f'Name: {ctx.author.mention} ({ctx.author})\n' \
                   f'Joined: {tools.format_date(ctx.author.joined_at)}\n' \
                   f'Created: {tools.format_date(ctx.author.joined_at)}\n' \
                   f'Context: {ctx.channel.mention}\n' \
                   f'[Jump to Message]({ctx.message.jump_url})'
        embed.add_field(name='Reporter', value=reporter)
        reported = f'Name: {member.mention} ({member})\n' \
                   f'Joined: {tools.format_date(member.joined_at)}\n' \
                   f'Created: {tools.format_date(member.joined_at)}\n' \
                   f'ID: {member.id}'
        embed.add_field(name='Reported', value=reported)
        try:
            url = ctx.message.attachments[0].url
            embed.set_image(url=url)
        except IndexError:
            print('index error')
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await channel.send(embed=embed)
        await ctx.message.delete()
        await ctx.send(embed=tools.single_embed(f'Your report has been delivered. Thank you.'), delete_after=5)

    @commands.group()
    async def incident(self, ctx):
        if ctx.invoked_subcommand is None:
            with open('files/incident.json') as f:
                i = json.load(f)
            last_incident = tools.display_time(int(time.time() - i))
            await ctx.send(embed=tools.single_embed(f'Time since last incident: `{last_incident}`'))

    @incident.group()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx):
        with open('files/incident.json') as f:
            i = json.load(f)
        i = tools.display_time(int(time.time() - i))
        with open('files/incident.json', 'w') as f:
            json.dump(time.time(), f, indent=4)
        await ctx.send(embed=tools.single_embed(f'Incident date recorded. Last incident was `{i}` ago.'))

    """
    Utility functions
    """

    async def can_bypass_cooldown(self, ctx):
        if ctx.author.permissions_in(ctx.channel).administrator:
            return True
        elif await self.client.is_owner(ctx.author):
            return True
        return False

    """
    Listeners
    """

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for member in message.mentions:
            if db.is_afk(member):
                afk, response = db.get_afk(member)
                msg = f'**{member.display_name}** is **AFK**.\n' \
                      f'> {response}'
                try:
                    await message.author.send(embed=tools.single_embed_neg(msg, avatar=member.avatar_url))
                except discord.Forbidden:
                    pass

    """
    Error Handling
    """

    @support.error
    @server.error
    @technical.error
    @in_game.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = 'Please submit a ticket using the following format:\n' \
                  '`r:support server/tech/acnh "Enter your message here"`\n' \
                  'Please use `r:help support` for more information.'
            await ctx.send(embed=tools.single_embed(msg))

    @bug.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'Please enter a message for the bug report.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

    @nick.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            msg = f'**{self.client.user.display_name}** does not have permission to change your nickname.'
            await ctx.send(embed=tools.single_embed_neg(msg))
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'You must declare a new nickname when using this command.'
            await ctx.send(embed=tools.single_embed_neg(msg))

    @who.error
    async def member_info_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed('I could not find that member'), delete_after=15)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=tools.single_embed(f'{error}'), delete_after=30)
        if isinstance(error, discord.HTTPException):
            await ctx.send(embed=tools.single_embed(f'An error occurred when searching for this user.'), delete_after=30)
            print(error)


def setup(client):
    client.add_cog(Information(client))
