import discord
import json
import time
import util.db as db
import util.tools as tools
from discord.ext import commands
from datetime import datetime


class Information(commands.Cog):
    def __init__(self, client):
        self.client = client

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
        print(ctx.guild.created_at)

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

    # @commands.group()
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

    # @commands.command()
    # async def omit(self, ctx, *criteria):
    #     results = []
    #     members = ctx.guild.members
    #     for m in members:
    #         for c in criteria:
    #             if c not in m.display_name:
    #                 if m not in results:
    #                     results.append(m)
    #     # members = [m for m in ctx.guild.members if member not in m.display_name.lower()]
    #     description = '\n'.join([f'{m.name} / {m.display_name} ({m.id})' for m in results])
    #     if len(description) > 2000:
    #         await ctx.send(embed=tools.single_embed(f'Your search is too broad. Try to be more specific. Results: {len(results)}'))
    #         return
    #     embed = discord.Embed(title='Found Members', description=description, color=discord.Color.green())
    #     await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def who(self, ctx, member: discord.Member):
        joined_guild_human_readable = tools.display_time(tools.to_seconds(member.joined_at), 3)
        joined_discord_human_readable = tools.display_time(tools.to_seconds(member.created_at), 3)
        embed = discord.Embed(title=member.display_name, color=member.colour)
        embed.add_field(name='ID', value=member.id)
        embed.add_field(name='Status', value=member.status)
        if member.activity is not None:
            embed.add_field(name='Activity', value=member.activity.name)
        embed.add_field(name='Joined Guild', value=f'{tools.format_date(member.joined_at)}\n{joined_guild_human_readable} ago', inline=False)
        embed.add_field(name='Roles', value=', '.join([role.name for role in member.roles if role.name != '@everyone']))
        embed.set_footer(text=f'Joined Discord {tools.format_date(member.joined_at)} ({joined_discord_human_readable} ago)')
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

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

    @commands.command()
    @commands.cooldown(2, 60, commands.BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(self, ctx, *nickname):
        spam = db.get_spam(ctx.guild)
        msg = f'{ctx.author.display_name} changed their nickname to {" ".join(nickname)}.'
        await ctx.author.edit(nick=' '.join([w.replace("'", "\'") for w in nickname]))
        await ctx.send(embed=tools.single_embed(msg))
        await spam.send(embed=tools.single_embed(msg))

    @commands.command()
    async def afk(self, ctx, *autoresponse):
        if len(autoresponse) == 0:
            await ctx.send(embed=tools.single_embed('You are no longer **AFK**.'))
            db.set_afk(ctx.author, 0, None)
            return
        else:
            db.set_afk(ctx.author, 1, ' '.join(autoresponse).replace("'", "\'"))
            await ctx.send(embed=tools.single_embed(f'AFK message set to \n> {" ".join(autoresponse)}'))
            # add image

    @commands.command()
    async def report(self, ctx, member: discord.Member, *, report: str = None):
        await ctx.message.delete()
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
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # if message.author.id == 505019512702238730:
        #     await message.add_reaction('🇸')
        #     await message.add_reaction('🇮')
        #     await message.add_reaction('🇲')
        #     await message.add_reaction('🇵')

        if 'cube' in message.content:
            await message.add_reaction('🧊')

        if message.author.bot:
            return

        for member in message.mentions:
            if db.is_afk(member):
                afk, response = db.get_afk(member)
                msg = f'**{member.display_name}** is **AFK**.\n' \
                      f'> {response}'
                await message.author.send(embed=tools.single_embed_neg(msg, avatar=member.avatar_url))

    @nick.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            msg = f'**{self.client.user.display_name}** does not have permission to change your nickname.'
            await ctx.send(embed=tools.single_embed_neg(msg))

    @who.error
    async def member_info_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(embed=tools.single_embed('I could not find that member'), delete_after=15)
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=tools.single_embed(f'{error}'), delete_after=30)


def setup(client):
    client.add_cog(Information(client))
