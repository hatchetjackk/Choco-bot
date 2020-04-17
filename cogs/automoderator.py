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

    @commands.Cog.listener()
    async def on_message(self, message):
        # search messages for discord links
        if not database.admin_cog(message.guild):
            return

        # ignore this guild's invites
        for w in message.content.split(' '):
            if w in [f'https://discord.gg/{invite.code}' for invite in await message.guild.invites()]:
                return
            if w in [f'http://discord.gg/{invite.code}' for invite in await message.guild.invites()]:
                return

        if message.author.guild_permissions.create_instant_invite:
            return

        blacklist = database.get_blacklist(message.guild)
        for b in blacklist:
            if b in message.content.lower():
                try:
                    await message.delete()
                    msg = f'You have entered a blacklisted link in **{message.guild.name}** ' \
                          f'Your message has been deleted.'
                    await message.author.send(embed=tools.single_embed_neg(msg))
                except Exception as e:
                    print(e)

        # if link found, delete and warn
        if 'https://discord.gg' in message.content or 'http://discord.gg' in message.content:
            try:
                await message.delete()
            except Exception as e:
                print(e)
            msg = f'Advertising other Discord servers is not allowed.'
            database.add_warning(message.author, msg)
            fmt = f'You have received an automatic warning for posting a Discord link in ' \
                  f'**{message.guild.name}**.\n> "{msg}"'
            await message.author.send(embed=tools.single_embed_neg(fmt))

            # def check(react, user):
            #     return message.channel == react.message.channel

            # if member's warnings are 2 or greater, commence a vote to kick
            warnings, messages = database.get_warnings(message.author)
            fmt = [f'{m[1]} - {m[0]}' for m in messages]
            if warnings >= 2:
                admin_channel = database.get_administrative(message.guild)
                msg = f'**{message.author.display_name}** has reached `{warnings}` warnings. Should they be kicked?\n' \
                      f'__Past Warnings__\n' + '\n'.join(fmt)
                embed = discord.Embed(color=discord.Color.red(), description=msg)
                embed.set_thumbnail(url=message.author.avatar_url)
                msg = await admin_channel.send(embed=embed)
                await msg.add_reaction('✔')
                await msg.add_reaction('❌')
                # yes = 0
                # while yes < 2:
                #     reaction, member = await self.client.wait_for('reaction_add', check=check)
                #     print(reaction)
                #     if reaction.emoji == '✔':
                #         yes = reaction.count
                #         print(yes)
                # await message.author.kick(reason=f'You have been kicked from {message.guild.name}. The last warning was: "{message}"')
                # await admin_channel.send(embed=tools.single_embed_neg(f'{message.author.display_name} has been kicked.'))


def setup(client):
    client.add_cog(Automoderator(client))
