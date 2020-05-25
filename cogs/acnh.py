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
image = 'http://williamspires.co.uk:9876/'
months = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']


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

    @commands.command(aliases=['villager', 'villagers'])
    @commands.has_role('mae-supporters')
    async def villager_lookup(self, ctx, villager):
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
        embed.add_field(name='Favorite K.K. Song', value=data['favoriteSong'])
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

    @commands.command(aliases=['insects', 'bugs', 'insect'])
    @commands.has_role('mae-supporters')
    async def insect_lookup(self, ctx, *, query):
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)
        month = await self.fix_capitalize(query)
        embeds = []
        # collect all insect data for selected month
        if month in months:
            async with aiohttp.ClientSession() as session:
                url = f'{will_url}/insect/available/{month}'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                insects_raw = json.loads(f)

                url = f'{will_url}/insect/leaving/{month}/NH'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                insects_leaving_nh = json.loads(f)

                url = f'{will_url}/insect/leaving/{month}/SH'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                insects_leaving_sh = json.loads(f)

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
                count += 1

            nh_insects_leaving = [k['name'] for k in insects_leaving_nh]
            if len(nh_insects_leaving) > 0:
                nh_insects_leaving = '\n'.join(nh_insects_leaving)
                embed = discord.Embed(title=f'{title}\nInsects Leaving Next Month', color=discord.Color.green())
                embed.add_field(name=f'Insects Part {count}', value=f'```\n{nh_insects_leaving}```')
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
                count += 1

            sh_insects_leaving = [k['name'] for k in insects_leaving_sh]
            if len(sh_insects_leaving) > 0:
                sh_insects_leaving = '\n'.join(sh_insects_leaving)
                embed = discord.Embed(title=f'{title}\nInsects Leaving Next Month', color=discord.Color.green())
                embed.add_field(name=f'Insects Part {count}', value=f'```\n{sh_insects_leaving}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)

        # find specific insect data
        else:
            async with aiohttp.ClientSession() as session:
                url = f'{will_url}/insect/{query.lower()}'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find insect \"{query}\"!'))
                    return
                data = json.loads(f)

            thumbnail = f'{image}insects/{data["critterpediaFilename"]}.png'
            description = f'```\n' \
                          f'Value: {data["sell"]} bells\n' \
                          f'Weather: {data["weather"]}\n' \
                          f'Where: {data["whereOrHow"]}```'
            embed = discord.Embed(title=data['name'].capitalize(), description=description, color=discord.Color.green())
            nh_availability = '\n'.join([f'{k[2:]} {"." * 5} {v}' for k, v in data.items() if v != 'NA' and k.startswith('nh')])
            embed.add_field(name='Northern Hemisphere Availability', value=f'```\n{nh_availability}```')
            embed.set_image(url=thumbnail)
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

            embed = discord.Embed(title=data['name'].capitalize(), description=description, color=discord.Color.green())
            sh_availability = '\n'.join([f'{k[2:]} {"." * 5} {v}' for k, v in data.items() if v != 'NA' and k.startswith('sh')])
            embed.add_field(name='Southern Hemisphere Availability', value=f'```\n{sh_availability}```')
            embed.set_image(url=thumbnail)
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.command(aliases=['fish'])
    @commands.has_role('mae-supporters')
    async def fish_lookup(self, ctx, *, query):
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)
        month = await self.fix_capitalize(query)
        embeds = []
        # collect all insect data for selected month
        if month in months:
            async with aiohttp.ClientSession() as session:
                url = f'{will_url}/fish/available/{month}'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                fish_raw = json.loads(f)

                url = f'{will_url}/fish/leaving/{month}/NH'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                fish_leaving_nh = json.loads(f)

                url = f'{will_url}/fish/leaving/{month}/SH'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find month \"{month}\"!'))
                    return
                fish_leaving_sh = json.loads(f)

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
                count += 1

            nh_fish_leaving = [k['name'] for k in fish_leaving_nh]
            if len(nh_fish_leaving) > 0:
                fish_list = '\n'.join(nh_fish_leaving)
                embed = discord.Embed(title=f'{title}\nFish Leaving Next Month', color=discord.Color.green())
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
                count += 1

            sh_fish_leaving = [k['name'] for k in fish_leaving_sh]
            if len(nh_fish_leaving) > 0:
                fish_list = '\n'.join(sh_fish_leaving)
                embed = discord.Embed(title=f'{title}\nFish Leaving Next Month', color=discord.Color.green())
                embed.add_field(name=f'Fish Part {count}', value=f'```\n{fish_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)

        else:
            async with aiohttp.ClientSession() as session:
                url = f'{will_url}/fish/{query.lower()}'
                f, status = await self.fetch(session, url)
                if status != 200 or len(f) < 1:
                    await ctx.send(embed=tools.single_embed_neg(f'Could not find insect \"{query}\"!'))
                    return
                data = json.loads(f)

            thumbnail = f'{image}Fish/{data["critterpediaFilename"]}.png'
            description = f'```\n' \
                          f'Value: {data["sell"]} bells\n' \
                          f'Where: {data["whereOrHow"]}\n' \
                          f'Shadow: {data["shadow"]}```'
            embed = discord.Embed(title=data['name'].capitalize(), description=description, color=discord.Color.green())
            nh_availability = '\n'.join([f'{k[2:]} {"." * 5} {v}' for k, v in data.items() if v != 'NA' and k.startswith('nh')])
            embed.add_field(name='Northern Hemisphere Availability', value=f'```\n{nh_availability}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embed.set_image(url=thumbnail)
            embeds.append(embed)

            embed = discord.Embed(title=data['name'].capitalize(), description=description, color=discord.Color.green())
            sh_availability = '\n'.join([f'{k[2:]} {"." * 5} {v}' for k, v in data.items() if v != 'NA' and k.startswith('sh') and k != 'shadow'])
            embed.add_field(name='Southern Hemisphere Availability', value=f'```\n{sh_availability}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embed.set_image(url=thumbnail)
            embeds.append(embed)

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.command(aliases=['pers', 'personality'])
    @commands.has_role('mae-supporters')
    async def personality_lookup(self, ctx, personality):
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)
        async with aiohttp.ClientSession() as session:
            url = f'http://157.245.28.81/villager/personality/{personality.lower()}'
            print(url)
            f, status = await self.fetch(session, url)
            data = json.loads(f)

        embeds = []
        title = f'{personality.lower().capitalize()} Personality'
        villager_list = []
        for villager in data:
            if len(villager_list) == 25:
                villager_list = '\n'.join(villager_list)
                embed = discord.Embed(title=title, color=discord.Color.green())
                embed.add_field(name='\u200b', value=f'```\n{villager_list}```')
                embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
                embeds.append(embed)
                villager_list = []
            else:
                villager_list.append(f"{villager['name']} {'.' * (20 - len(villager['name']))} {villager['species']}")

        if len(villager_list) > 0:
            villager_list = '\n'.join(villager_list)
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'```\n{villager_list}```')
            embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
            embeds.append(embed)

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.command()
    @commands.has_role('mae-supporters')
    async def diy(self, ctx, *, recipe):
        credit = discord.utils.get(ctx.guild.members, id=272151652344266762)
        async with aiohttp.ClientSession() as session:
            url = f'{will_url}diy/{recipe.lower()}'
            f, status = await self.fetch(session, url)
            data = json.loads(f)

        materials = [v for k, v in data.items() if v != '' and k.startswith('material_')]
        material_amounts = [v for k, v in data.items() if v != 0 and k.startswith('matnum')]
        mats = []
        for x, y in zip(materials, material_amounts):
            mats.append(f'{x} {"." * (20 - len(x))} {y}')
        mats = '\n'.join(mats)
        description = f'```\n' \
                      f'Value: {data["sell"]}\n' \
                      f'Category: {data["category"]}\n' \
                      f'Source: {data["source"]}\n' \
                      f'```'
        embed = discord.Embed(title=data['name'].capitalize(), description=description, color=discord.Color.green())
        embed.add_field(name='Materials', value=f'```\n{mats}```')
        embed.set_footer(text=f'API courtesy of {credit.display_name} ({credit})')
        await ctx.send(embed=embed)

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
