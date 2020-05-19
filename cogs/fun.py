import discord
import random
import util.tools as tools
import urllib.request
import urllib.parse
import re
import aiohttp
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def gif(self, ctx, *, query):
        async with aiohttp.ClientSession() as cs:
            q = f"https://api.giphy.com/v1/gifs/search?api_key=mAOI8C4Eu2yq6ez7kb3NNp19q07owL9M&q={query}&limit=25&offset=0&rating=G&lang=en"
            async with cs.get(q) as r:
                f = await r.json()
        data = f["data"]
        url = data[random.randint(0, len(data) - 1)]["images"]["original"]["url"]
        embed = discord.Embed(colour=discord.Color.green())
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['in'])
    async def inspire(self, ctx):
        image = await tools.get_inspiration()
        await ctx.send(image)

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx, *query):
        query_string = urllib.parse.urlencode({"search_query": ' '.join(query)})
        html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
        search_results = re.findall(r'href=\"/watch\?v=(.{11})', html_content.read().decode())
        await ctx.send("http://www.youtube.com/watch?v=" + search_results[0])

    @commands.command(aliases=['c'])
    async def card(self, ctx):
        """ draw a random card from a deck """
        card = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 'Ace', 'King', 'Queen', 'Jack']
        style = ['Spades', 'Hearts', 'Clubs', 'Diamonds']
        await ctx.send(embed=tools.single_embed(f'You drew the {random.choice(card)} of {random.choice(style)}!'))

    @commands.command()
    async def rps(self, ctx, choice: str):
        rps = ['rock', 'paper', 'scissors']
        win = {'rock': 'paper', 'paper': 'scissors', 'scissors': 'rock'}
        lose = {'paper': 'rock', 'rock': 'scissors', 'scissors': 'paper'}

        if choice not in rps:
            await ctx.send(embed=tools.single_embed('You have to pick rock, paper, or scissors.'))

        bot_choice = random.choice(rps)
        bot = self.client.user.display_name.capitalize()
        if bot_choice == choice:
            await ctx.send(embed=tools.single_embed(f'{bot} chose {bot_choice}! It\'s a tie!'))
        if choice == lose.get(bot_choice):
            await ctx.send(embed=tools.single_embed(f'{bot} chose {bot_choice}! You lost!'))
        if choice == win.get(bot_choice):
            await ctx.send(embed=tools.single_embed(f'{bot} chose {bot_choice}! You win!'))

    @commands.command(aliases=[])
    async def roll(self, ctx, arg: str):
        dice, sides = map(int, arg.split('d'))
        rolls = [random.randint(1, sides) for _ in range(dice)]
        result = ', '.join([f'`{str(roll)}`' for roll in rolls])
        await ctx.send(embed=tools.single_embed(f'You rolled {result} for a total of `{sum(rolls)}`'))

    @commands.command(aliases=['rd'])
    async def reddit(self, ctx, subreddit: str):
        reddit_search = 'https://reddit.com/r/' + subreddit
        await ctx.send(reddit_search)

    @roll.error
    async def roll_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(embed=tools.single_embed('Use the `ndn` format for rolling dice.'))


def setup(client):
    client.add_cog(Fun(client))
