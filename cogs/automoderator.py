import util.db as database
import util.tools as tools
import discord
from discord.ext import commands


class Automoderator(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        database.add_member(member)
        # if admin cog is not set, do not give autorole
        if not database.admin_cog(member.guild):
            return
        autorole = database.get_autorole(member.guild)
        if autorole is not None:
            member.add_roles(autorole)
            spam = database.get_spam(member.guild)
            msg = f'{member.display_name} was given the role {autorole.name}'
            await spam.send(embed=tools.single_embed(msg))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if not database.admin_cog(member.guild):
            return
        spam = member.guild.system_channel
        embed = discord.Embed(description=f'{member.display_name} has left the server.')
        embed.set_thumbnail(url=member.avatar_url)
        await spam.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        spam = await guild.system_channel
        msg = f'{self.client.user.display_name} has joined {guild.name}'
        await spam.send(embed=tools.single_embed(msg))
        database.add_guild(guild)
        for member in guild.members:
            database.add_member(member)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not database.admin_cog(after.guild):
            return
        if before.guild is None:
            return
        spam = database.get_spam(after.guild)
        if before.author.bot or before.content.startswith('http') or before.content == '':
            return
        embed = discord.Embed(description=f'{before.author.display_name} edited a message in {before.channel.mention}')
        embed.set_thumbnail(url=before.author.avatar_url)
        embed.add_field(name='Before', value=before.content, inline=False)
        embed.add_field(name='After', value=after.content, inline=False)
        await spam.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not database.admin_cog(message.guild):
            return
        spam = database.get_spam(message.guild)
        if message.author.bot:
            return
        msg = f'**A message was deleted**\n'\
              f'Author: {message.author.display_name}\n'\
              f'Channel: {message.channel.mention}\n'\
              f'Message: {message.content}'
        embed = discord.Embed(color=discord.Color.red(), description=msg)
        embed.set_thumbnail(url=message.author.avatar_url)
        await spam.send(embed=embed)


def setup(client):
    client.add_cog(Automoderator(client))
