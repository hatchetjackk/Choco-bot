import asyncio

import discord
import sqlite3
import util.tools as tools
from discord.ext import commands, tasks
from _datetime import datetime, timedelta


class Information(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.check_reminders.start()

    """
    Owner Commands
    """

    @commands.command(aliases=['reload-reminders'])
    @commands.is_owner()
    async def reload_reminders(self, ctx):
        print('* Cancelling tasks')
        self.check_reminders.cancel()
        print('* Unloading reminders')
        self.client.unload_extension('cogs.reminders')
        print('* Loading reminders')
        self.client.load_extension('cogs.reminders')
        await ctx.send(embed=tools.single_embed('reminders reloaded'))

    @commands.command(aliases=['unload-reminders'])
    @commands.is_owner()
    async def unload_reminders(self, ctx):
        print('* Cancelling tasks')
        self.check_reminders.cancel()
        print('* Unloading reminders')
        self.client.unload_extension('cogs.reminders')
        await ctx.send(embed=tools.single_embed('reminders unloaded'))

    """
    Commands
    """

    @commands.command()
    async def time(self, ctx):
        await ctx.send(embed=tools.single_embed(f'The current time is {tools.format_date(datetime.utcnow())} UTC'))

    @commands.command()
    @commands.has_any_role('mae-supporters', 'ADMIN', 'MODERATOR')
    async def reminders(self, ctx):
        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=':sparkles: Upcoming Reminders', value='\u200b')
        embed.set_thumbnail(url=ctx.author.avatar_url)

        conn, curs = await self.load_db()
        curs.execute("SELECT * FROM reminders WHERE member = (:member) ORDER BY date", {'member': ctx.author.id})
        reminders = curs.fetchall()
        counter = 1
        for [member, date, message] in reminders:
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
            embed.add_field(name=f'{counter}. {tools.format_date(date)} UTC',
                            value=f'> {message}',
                            inline=False)
            counter += 1
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role('mae-supporters', 'ADMIN', 'MODERATOR')
    async def delreminder(self, ctx, number: int):
        conn, curs = await self.load_db()
        curs.execute("SELECT * FROM reminders WHERE member = (:member) ORDER BY date", {'member': ctx.author.id})
        reminders = curs.fetchall()
        [member, date, message] = reminders[number - 1]
        date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        embed = discord.Embed(color=discord.Color.green())
        embed.add_field(name=f'{tools.format_date(date)} UTC', value=message, inline=False)
        embed.add_field(value='Are you sure you want to delete your session?', name='\u200b')
        confirm = await ctx.send(embed=embed)
        await confirm.add_reaction('🇾')
        await confirm.add_reaction('🇳')
        await asyncio.sleep(0)

        def check_react(react, actor):
            return react.message.id == confirm.id and actor == ctx.author

        reaction, member = await self.client.wait_for('reaction_add', check=check_react)
        if reaction.emoji == '🇾':
            conn, curs = await self.load_db()
            with conn:
                curs.execute("DELETE FROM reminders where member = (:member) AND message = (:message)",
                             {'member': ctx.author.id, 'message': message})
            await confirm.edit(embed=tools.single_embed(f'Your reminder has been deleted.'))
            await confirm.clear_reactions()
        if reaction.emoji == '🇳':
            await confirm.edit(embed=tools.single_embed(f'Cancelled.'))
            await confirm.clear_reactions()

    @commands.command(aliases=['remindme', 'remind-me'])
    @commands.has_any_role('mae-supporters', 'ADMIN', 'MODERATOR')
    async def remind_me(self, ctx, value: int, denominator: str, *, message):
        if denominator == 'm':
            date = datetime.utcnow() + timedelta(minutes=value)
        elif denominator == 'h':
            date = datetime.utcnow() + timedelta(hours=value)
        elif denominator == 'd':
            date = datetime.utcnow() + timedelta(days=value)
        else:
            await ctx.send(embed=tools.single_embed('Please use denominators m, h, or d'))
            return

        conn, curs = await self.load_db()
        with conn:
            curs.execute("INSERT INTO reminders VALUES (:member, :date, :message)",
                         {'member': ctx.author.id, 'date': date, 'message': message})

        await ctx.send(embed=tools.single_embed(f'Your reminder has been set for {tools.format_date(date)} UTC'))

    """
    Utility Functions
    """
    @staticmethod
    async def load_db():
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        return conn, curs

    """
    Looping Tasks
    """

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        conn, curs = await self.load_db()
        curs.execute("SELECT * FROM reminders")
        reminders = curs.fetchall()
        for [member, date, message] in reminders:
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
            if date <= datetime.utcnow():
                print(True)
                try:
                    with conn:
                        curs.execute("DELETE FROM reminders where member = (:member) AND message = (:message)",
                                     {'member': member, 'message': message})
                except Exception as e:
                    print(e)
                member = self.client.get_user(member)
                embed = discord.Embed(title='This is a reminder!', description=f'> {message}',
                                      color=discord.Color.green())
                await member.send(embed=embed)

    """
    Error handling
    """

    @remind_me.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'You appear to be missing the `{error.param.name}` argument required for this command.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))
        if isinstance(error, commands.BadArgument):
            msg = f'You must declare the `m`, `h`, or `d` denominator separately from your number value. Ex: `1 m`'
            await ctx.send(embed=tools.single_embed_tooltip(msg))


def setup(client):
    client.add_cog(Information(client))
