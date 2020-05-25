import inspect
import discord
import aiohttp
import json
import util.tools as tools
from discord.ext import commands
from bs4 import BeautifulSoup
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

# API offered by VillChurch
# will_url = 'http://161.35.160.226:8080/'
will_url = 'http://157.245.28.81/'
image_url = 'http://williamspires.co.uk:9876/villagers/'


class ACNH(commands.Cog):
    def __init__(self, client):
        self.client = client

    """
    Owner Commands
    """

    @commands.command(aliases=['reload-acnh'])
    async def acnh_restart(self, ctx):
        print('* Unloading ACNH')
        self.client.unload_extension('cogs.acnh')
        print('* Loading ACNH')
        self.client.load_extension('cogs.acnh')
        await ctx.send(embed=tools.single_embed('ACNH reloaded'))

    """
    Utility Functions
    """

    @staticmethod
    async def fix_capitalize(word):
        return word.lower().capitalize()


    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.text(), int(response.status)

    """
    Villager Commands
    """

    @commands.command()
    @commands.has_role('mae-supporters')
    async def villager2(self, ctx, villager):
        async with aiohttp.ClientSession() as session:
            url = f'{will_url}/villager/{villager.lower().capitalize()}'
            f, status = await self.fetch(session, url)
            if status != 200 or len(f) < 1:
                await ctx.send(embed=tools.single_embed_neg(f'Could not find villager \"{villager}\"!'))
                return
            data = json.loads(f)
        embed = discord.Embed(title=data['name'], color=discord.Color.green())
        embed.add_field(name='Species', value=data['species'])
        embed.add_field(name='Gender', value=data['gender'])
        embed.add_field(name='Birthday', value=data['birthday'])
        embed.add_field(name='Personality', value=data['personality'])
        embed.add_field(name='Phrase', value=f'\"{data["catchphrase"].capitalize()}\"')
        embed.add_field(name='Hobby', value=data['hobby'])
        embed.add_field(name='Favorite K.K. Song', value=data['favorite_Song'])
        embed.set_thumbnail(url=f'{image_url}{data["filename"]}.png')
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)
        embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
        await ctx.send(embed=embed)

    @commands.command(aliases=['species'])
    @commands.has_role('mae-supporters')
    async def species_lookup(self, ctx, species):
        async with aiohttp.ClientSession() as session:
            url = f'{will_url}/villager/species/{species.lower()}'
            f = await self.fetch(session, url)
            data = json.loads(f[0])
        villagers = [f'{k["name"]} {"." * (15 - len(k["name"]))} {k["personality"]}' for k in data]
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)

        if len(villagers) < 1:
            await ctx.send(embed=tools.single_embed_neg(f'Species "{species}" not found.'))
            return

        embeds = []
        embed = discord.Embed(title=f'{species.capitalize()} Villagers', color=discord.Color.green())

        if len(villagers) > 10:
            list1 = '\n'.join(villagers[int(len(villagers)/2):])
            embed.add_field(name='\u200b', value=f'```\n{list1}```')
        else:
            single_list = '\n'.join(villagers)
            embed.add_field(name='\u200b', value=f'```\n{single_list}```')
        embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
        if len(villagers) > 10:
            embeds.append(embed)

        if len(villagers) > 10:
            embed = discord.Embed(title=f'{species.capitalize()} Villagers', color=discord.Color.green())
            list2 = '\n'.join(villagers[:int(len(villagers)/2)])
            embed.add_field(name='\u200b', value=f'```\n{list2}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        if len(villagers) > 10:
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
        else:
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_role('mae-supporters')
    async def insect_lookup(self, ctx, insect):
        async with aiohttp.ClientSession() as session:
            url = f'{will_url}/insect/available/{insect.lower()}'
            f, status = await self.fetch(session, url)
            if status != 200 or len(f) < 1:
                await ctx.send(embed=tools.single_embed_neg(f'Could not find insect \"{insect}\"!'))
                return
            data = json.loads(f)

        embed = discord.Embed(name=insect.capitalize(), color=discord.Color.green())
        # availability = [f'{}']
        # embed.add_field(name='\u200b', value=)

    @commands.command(aliases=['catch'])
    @commands.has_role('mae-supporters')
    async def available(self, ctx, month):
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)

        month = await self.fix_capitalize(month)
        async with aiohttp.ClientSession() as session:
            url = f'{will_url}/insect/available/{month.lower().capitalize()}'
            f, status = await self.fetch(session, url)
            if status != 200 or len(f) < 1:
                await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                return
            insects_raw = json.loads(f)

            url = f'{will_url}/fish/available/{month.lower().capitalize()}'
            f, status = await self.fetch(session, url)
            if status != 200 or len(f) < 1:
                await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                return
            fish_raw = json.loads(f)

        embeds = []
        nh_insects = [k for k in insects_raw if k['nh' + month[:3]] != 'NA']

        title = f'{month} (Northern Hemisphere)'
        insect_list = []
        count = 1
        for insect in nh_insects:
            if len(insect_list) == 25:
                insect_list = '\n'.join(insect_list)
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.add_field(name=f'Insects Part {count}', value=f'```\n{insect_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)
                insect_list = []
                count += 1
            else:
                insect_list.append(f'{insect["name"]} {"." * (25 - len(insect["name"]))} {insect["nh" + month[:3]]}')

        if len(insect_list) > 0:
            fish_list = '\n'.join(insect_list)
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name=f'Insects Part {count}', value=f'```\n{fish_list}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        sh_insects = [k for k in insects_raw if k['sh' + month[:3]] != 'NA']
        title = f'{month} (Southern Hemisphere)'
        insect_list = []
        count = 1
        for insect in sh_insects:
            if len(insect_list) == 25:
                insect_list = '\n'.join(insect_list)
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.add_field(name=f'Insects Part {count}', value=f'```\n{insect_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)
                insect_list = []
                count += 1
            else:
                insect_list.append(f'{insect["name"]} {"." * (25 - len(insect["name"]))} {insect["sh" + month[:3]]}')

        if len(insect_list) > 0:
            insect_list = '\n'.join(insect_list)
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name=f'Insects Part {count}', value=f'```\n{insect_list}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        nh_fish = [k for k in fish_raw if k['nh' + month[:3]] != 'NA']
        title = f'{month} (Northern Hemisphere)'
        fish_list = []
        count = 1
        for fish in nh_fish:
            if len(fish_list) == 25:
                fish_list = '\n'.join(fish_list)
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.add_field(name=f'Fish Part {count}', value=f'```\n{fish_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)
                fish_list = []
                count += 1
            else:
                fish_list.append(f'{fish["name"]} {"." * (20 - len(fish["name"]))} {fish["nh" + month[:3]]}')

        if len(fish_list) > 0:
            fish_list = '\n'.join(fish_list)
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name=f'Fish Part {count}', value=f'```\n{fish_list}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        sh_fish = [k for k in fish_raw if k['sh' + month[:3]] != 'NA']
        title = f'{month} (Southern Hemisphere)'
        fish_list = []
        count = 1
        for fish in sh_fish:
            if len(fish_list) == 25:
                fish_list = '\n'.join(fish_list)
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.add_field(name=f'Fish Part {count}', value=f'```\n{fish_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)
                fish_list = []
                count += 1
            else:
                fish_list.append(f'{fish["name"]} {"." * (20 - len(fish["name"]))} {fish["sh" + month[:3]]}')

        if len(fish_list) > 0:
            fish_list = '\n'.join(fish_list)
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name=f'Fish Part {count}', value=f'```\n{fish_list}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.command(aliases=['villager'])
    @commands.has_role('mae-supporters')
    async def villager_lookup(self, ctx, villager):
        def generate_embed(*args):
            embed = discord.Embed(title=args[0], color=discord.Color.green())
            embed.add_field(name='Species', value=args[2])
            embed.add_field(name='Gender', value=args[4])
            embed.add_field(name='Birthday', value=args[5])
            embed.add_field(name='Personality', value=args[3])
            embed.add_field(name='Phrase', value=args[7])
            embed.add_field(name='\u200b', value='\u200b')
            embed.set_thumbnail(url=args[6])
            return embed

        villager = villager.lower().capitalize()
        async with aiohttp.ClientSession() as session:
            url = f'https://nookipedia.com/wiki/{villager}'
            f = await self.fetch(session, url)
            soup = BeautifulSoup(f, 'lxml')
            table = soup.find("table", {"class": "infobox"})
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')

            image_url = rows[6].find('img')['src']

            details = rows[9]

            species = details.find('a')['title']
            species_link = details.find('a')['href']

            personality_row = details.find_all('td')
            personality = personality_row[1].text.strip()
            personality_link = personality_row[1].find('a')['href']

            gender = details.find_all('td')[2].text

            birthday_details = rows[10]
            birthday = birthday_details.find_all('td')[0].text.strip()
            try:
                birthday_link = birthday_details.find_all('td')[0].find('a')['href']
            except TypeError:
                birthday_link = None

            starsign = birthday_details.find_all('td')[1].find('a')['title']
            starsign_link = birthday_details.find_all('td')[1].find('a')['href']

            phrase = rows[11].find('td').text.split('\n')[0]

        wiki_link = f'[wiki](https://nookipedia.com/wiki/{villager})'
        species = f'[{species}](https://nookipedia.com{species_link})'
        if birthday_link is not None:
            birthday = f'[{birthday}](https://nookipedia.com{birthday_link}), [{starsign}](https://nookipedia.com{starsign_link})'
        else:
            birthday = f'{birthday}, [{starsign}](https://nookipedia.com{starsign_link})'
        personality = f'[{personality}](https://nookipedia.com{personality_link})'

        embed = generate_embed(villager, wiki_link, species, personality, gender, birthday, image_url, phrase)
        await ctx.send(embed=embed)

    @commands.command(aliases=['pers', 'personality'])
    @commands.has_role('mae-supporters')
    # @commands.is_owner()
    async def personality_lookup(self, ctx, personality):
        async with aiohttp.ClientSession() as session:
            url = f'https://nookipedia.com/wiki/{personality}'
            f = await self.fetch(session, url)
            soup = BeautifulSoup(f, 'lxml')
            divs = soup.find_all("div", {"class": "gallerytext"})
            villagers = []
            for div in divs:
                link = div.find('a')['href']
                name = div.find('a').text
                villagers.append(f'[{name}](https://nookipedia.com{link})')

        slce = int(len(villagers)/2)
        l1 = villagers[slce:]
        l2 = villagers[:slce]

        embeds = []
        embed = discord.Embed(title=f'{personality.capitalize()} Villagers', color=discord.Color.green())
        embed.add_field(name='\u200b', value='\n'.join(l2[:int(len(l2)/2)]))
        embed.add_field(name='\u200b', value='\u200b')
        embed.add_field(name='\u200b', value='\n'.join(l2[int(len(l2)/2):]))
        embeds.append(embed)

        embed = discord.Embed(title=f'{personality.capitalize()} Villagers', color=discord.Color.green())
        embed.add_field(name='\u200b', value='\n'.join(l1[:int(len(l1)/2)]))
        embed.add_field(name='\u200b', value='\u200b')
        embed.add_field(name='\u200b', value='\n'.join(l1[int(len(l1)/2):]))
        embeds.append(embed)

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    """
    Error Handling
    """

    @villager_lookup.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = 'Please enter a villager to search for. `r:villager villager_name`'
            await ctx.send(embed=tools.single_embed(msg))

    @personality_lookup.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = 'Please enter a personality to search for. `r:pers personality_type`'
            await ctx.send(embed=tools.single_embed(msg))


def setup(client):
    client.add_cog(ACNH(client))
