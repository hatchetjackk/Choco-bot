import discord
import string
import util.tools as tools
import util.db as database
from discord.ext import commands
from collections import OrderedDict


class Karma(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def karma_cog_on(ctx):
        if database.karma_cog(ctx.guild):
            return True
        msg = f'**Karma** is not turned on'
        await ctx.send(embed=tools.single_embed_neg(msg))
        return False

    @commands.group()
    async def karma(self, ctx):
        if ctx.invoked_subcommand is None:
            karma = database.get_karma(ctx.author)
            await ctx.send(embed=tools.single_embed(f'**{ctx.author.display_name}** has `{karma}` point(s)!'))

    @karma.group(aliases=['-h'])
    async def help(self, ctx):
        embed = discord.Embed(color=discord.Color.blue(), title='Karma Help Page')
        embed.add_field(name='`thanks @user`',
                        value='Karma is our way of noticing members who have been helpful within the server. Don\'t be '
                              'stingy! Give karma to one or more users. After giving karma, you must wait 3 minutes '
                              'before giving more. ex: `thanks @user1 @user2` will thank two users at the same time. '
                              'Triggers include "thanks" and "cheers."',
                        inline=False)
        embed.add_field(name='`!karma`', value='Check your own karma.', inline=False)
        embed.add_field(name='`!leaderboard`',
                        value='Check the top 10 karma leaders. If you aren\'t in the top spots, '
                              'you will still see where you place overall.', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['kboard'])
    async def karmaboard(self, ctx):
        """ return a leaderboard with the top 10 karma leaders. If the requesting member is not in the top 10,
        their place will be added to the bottom of the leaderboard
        """
        if not await self.karma_cog_on(ctx):
            return
        array = {}
        for member_obj in ctx.guild.members:
            if member_obj.bot:
                continue
            if not database.in_members_table(member_obj):
                database.add_member(member_obj)
            karma = database.get_karma(member_obj)
            array[member_obj.display_name] = karma

        counter = 1
        leaderboard = []
        append_author = ''
        medals = {1: ' :first_place:', 2: ' :second_place:', 3: ' :third_place:'}
        sorted_karma = OrderedDict(reversed(sorted(array.items(), key=lambda x: x[1])))
        for member, karma in sorted_karma.items():
            msg = f'{counter}: **{member}** - `{karma}` points'
            for k, v in medals.items():
                if counter == k:
                    msg = msg + v
            leaderboard.append(msg)
            if ctx.author.display_name == member and counter > 10:
                append_author = f'\n----------------\n{counter}: **{member}** - `{karma}` points'
            counter += 1

        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name='Karma Leaderboard',
                        value='\n'.join(leaderboard[:10]) + append_author)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            # check message contents for keywords that indicate a user is being thanked
            if message.author.bot:
                return
            if not database.karma_cog(message.guild):
                return
            keywords = ['thanks', 'thank', 'cheers']
            msg = [word.lower() for word in message.content.split(' ') if word != '@everyone']

            # remove punctuation that prevent keywords from being recognized
            content = [''.join(character for character in word if character not in string.punctuation) for word in msg]
            mentioned_members = [member for member in message.guild.members if member.mentioned_in(message) and not member.bot and member != message.author]
            if len(mentioned_members) < 1:
                return
            if any(word in keywords for word in content):
                if await database.karma_too_soon(message):
                    return
                for member in mentioned_members:
                    if not database.in_members_table(member):
                        database.add_member(member)
                    database.add_karma(member, 1)
                    database.update_karma_timer(message.author)
            msg = f':tada: {", ".join([f"**{m.display_name}**" for m in mentioned_members])} earned 1 karma'
            embed = discord.Embed(color=discord.Color.blue(), description=msg)
            await message.channel.send(embed=embed)
        except Exception as e:
            print('on message karma', e)


def setup(client):
    client.add_cog(Karma(client))
