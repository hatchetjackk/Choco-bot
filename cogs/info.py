import discord
import util.db as db
import util.tools as tools
from discord.ext import commands


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

    @commands.command()
    @commands.cooldown(5, 60, commands.BucketType.user)
    async def who(self, ctx, member: discord.Member):
        joined_guild_human_readable = tools.display_time(tools.to_seconds(member.joined_at), 3)
        joined_discord_human_readable = tools.display_time(tools.to_seconds(member.created_at), 3)
        embed = discord.Embed(title=member.display_name, color=member.colour)
        embed.add_field(name='Status', value=member.status)
        if member.activity is not None:
            embed.add_field(name='Activity', value=member.activity.name)
        embed.add_field(name='Joined Guild', value=f'{tools.format_date(member.joined_at)}\n{joined_guild_human_readable} ago', inline=False)
        embed.add_field(name='Roles', value=', '.join([role.name for role in member.roles if role.name != '@everyone']))
        embed.set_footer(text=f'Joined Discord {tools.format_date(member.joined_at)} ({joined_discord_human_readable} ago)')
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 60*60, commands.BucketType.user)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(self, ctx, *nickname):
        spam = db.get_spam(ctx.guild)
        msg = f'{ctx.author.display_name} changed their nickname to {" ".join(nickname)}.'
        await ctx.author.edit(nick=' '.join(nickname))
        await ctx.send(embed=tools.single_embed(msg))
        await spam.send(embed=tools.single_embed(msg))

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
