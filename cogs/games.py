import asyncio
import json
import discord
import random
import sqlite3
import aiohttp
import util.tools as tools
import util.db as database
from datetime import datetime
from discord.ext import commands, tasks

will_url = 'http://157.245.28.81/'
image = 'http://williamspires.co.uk:9876/'


class Games(commands.Cog):
    def __init__(self, client):
        self.client = client

    """
    Owner Commands
    """

    @commands.command(aliases=['reload-games'])
    async def games_restart(self, ctx):
        print('* Unloading games')
        self.client.unload_extension('cogs.games')
        print('* Loading games')
        self.client.load_extension('cogs.games')
        await ctx.send(embed=tools.single_embed('Games reloaded'))

    """
    Utility
    """

    @staticmethod
    async def load_db():
        path = 'files/data.db'
        conn = sqlite3.connect(path)
        curs = conn.cursor()
        return conn, curs

    async def add_to_economy(self, member):
        conn, curs = await self.load_db()
        with conn:
            curs.execute("INSERT OR IGNORE INTO economy VALUES (:member, :bells)",
                         {'member': member.id, 'bells': 0})

    async def get_bells(self, member):
        await self.add_to_economy(member)
        conn, curs = await self.load_db()
        curs.execute("SELECT bells FROM economy WHERE member = (:member)", {'member': member.id})
        bells = curs.fetchone()[0]
        return bells

    async def modify_bells(self, member, value):
        conn, curs = await self.load_db()
        bells = await self.get_bells(member) + value
        with conn:
            curs.execute("UPDATE economy SET bells = (:bells) WHERE member = (:member)",
                         {'member': member.id, 'bells': bells})

    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.text()

    async def add_collection_insects(self, member):
        conn, curs = await self.load_db()
        with conn:
            sql = 'INSERT OR IGNORE INTO collection_insects(member, "golden stag", "wharf roach", "scarab beetle", "mosquito", "tarantula", "stinkbug", "cicada shell", "darner dragonfly", "moth", "orchid mantis", "agrias butterfly", "diving beetle", "robust cicada", "Madagascan sunset moth", "rainbow stag", "pondskater", "brown cicada", "tiger butterfly", "Rajah Brooke\'s birdwing", "mole cricket", "paper kite butterfly", "earth-boring dung beetle", "giant stag", "walking leaf", "evening cicada", "emperor butterfly", "horned elephant", "cyclommatus stag", "rosalia batesi beetle", "giant cicada", "dung beetle", "damselfly", "Queen Alexandra\'s birdwing", "banded dragonfly", "giraffe stag", "long locust", "mantis", "blue weevil beetle", "citrus long-horned beetle", "miyama stag", "bagworm", "flea", "ant", "snail", "spider", "horned atlas", "pill bug", "horned hercules", "common butterfly", "jewel beetle", "hermit crab", "Atlas moth", "centipede", "drone beetle", "common bluebottle", "walking stick", "goliath beetle", "fly", "scorpion", "honeybee", "saw stag", "horned dynastid", "wasp", "grasshopper", "giant water bug", "great purple emperor", "man-faced stink bug", "tiger beetle", "migratory locust", "walker cicada", "rice grasshopper", "yellow butterfly", "monarch butterfly", "bell cricket", "cricket", "red dragonfly", "violin beetle", "ladybug", "peacock butterfly", "firefly") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            curs.execute(sql, (member.id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    async def add_collection_fish(self, member):
        conn, curs = await self.load_db()
        with conn:
            sql = 'INSERT OR IGNORE INTO collection_fish(member, "anchovy", "angelfish", "arapaima", "arowana", "barred knifejaw", "barreleye", "betta", "bitterling", "black bass", "blowfish", "blue marlin", "bluegill", "butterfly fish", "carp", "catfish", "clown fish", "coelacanth", "crawfish", "crucian carp", "dab", "dace", "dorado", "football fish", "freshwater goby", "frog", "gar", "giant snakehead", "giant trevally", "goldfish", "great white shark", "guppy", "hammerhead shark", "horse mackerel", "killifish", "koi", "mahi-mahi", "Napoleonfish", "neon tetra", "nibble fish", "oarfish", "ocean sunfish", "olive flounder", "pale chub", "piranha", "pond smelt", "pop-eyed goldfish", "puffer fish", "rainbowfish", "ranchu goldfish", "red snapper", "ribbon eel", "saddled bichir", "saw shark", "sea bass", "sea butterfly", "sea horse", "snapping turtle", "squid", "stringfish", "sturgeon", "suckerfish", "surgeonfish", "sweetfish", "tadpole", "tilapia", "tuna", "whale shark", "yellow perch", "zebra turkeyfish", "moray eel", "ray", "soft-shelled turtle", "char", "cherry salmon", "golden trout", "king salmon", "loach", "mitten crab", "pike", "salmon") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            curs.execute(sql, (member.id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    async def add_collection_fossils(self, member):
        conn, curs = await self.load_db()
        with conn:
            sql = 'INSERT OR IGNORE INTO collection_fossils(member, "acanthostega", "amber", "ammonite", "ankylo skull", "ankylo tail", "ankylo torso", "anomalocaris", "archaeopteryx", "archelon skull", "archelon tail", "australopith", "brachio chest", "brachio pelvis", "brachio skull", "brachio tail", "coprolite", "deinony tail", "deinony torso", "dimetrodon skull", "dimetrodon torso", "dinosaur track", "diplo chest", "diplo neck", "diplo pelvis", "diplo skull", "diplo tail", "diplo tail tip", "dunkleosteus", "eusthenopteron", "iguanodon skull", "iguanodon tail", "iguanodon torso", "juramaia", "left megalo side", "left ptera wing", "left quetzal wing", "mammoth skull", "mammoth torso", "megacero skull", "megacero tail", "megacero torso", "myllokunmingia", "ophthalmo skull", "ophthalmo torso", "pachy skull", "pachy tail", "parasaur skull", "parasaur tail", "parasaur torso", "plesio body", "plesio skull", "plesio tail", "ptera body", "quetzal torso", "right megalo side", "right ptera wing", "right quetzal wing", "sabertooth skull", "sabertooth tail", "shark-tooth pattern", "spino skull", "spino tail", "spino torso", "stego skull", "stego tail", "stego torso", "T. rex skull", "T. rex tail", "T. rex torso", "tricera skull", "tricera tail", "tricera torso", "trilobite") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            curs.execute(sql, (member.id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    async def get_fossil_collection(self, member):
        await self.add_collection_fossils(member)
        conn, curs = await self.load_db()
        curs.execute('SELECT * FROM collection_fossils WHERE member = (:member)',
                     {'member': member.id})
        caught = len([i for i in curs.fetchone() if i != 0]) - 1
        return caught

    async def check_collection_fossils(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        curs.execute(f"SELECT 1 FROM collection_fossils WHERE member = (:member) AND {item} = 1",
                     {'member': member.id, 'item': item})
        value = curs.fetchone()
        if value is not None:
            return True
        return False

    async def get_fish_collection(self, member):
        await self.add_collection_fish(member)
        conn, curs = await self.load_db()
        curs.execute('SELECT * FROM collection_fish WHERE member = (:member)',
                     {'member': member.id})
        caught = len([i for i in curs.fetchone() if i != 0]) - 1
        return caught

    async def get_insects_collection(self, member):
        await self.add_collection_insects(member)
        conn, curs = await self.load_db()
        curs.execute('SELECT * FROM collection_insects WHERE member = (:member)',
                     {'member': member.id})
        caught = len([i for i in curs.fetchone() if i != 0]) - 1
        return caught

    async def update_collection_fossils(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        with conn:
            curs.execute(f"UPDATE collection_fossils SET {item} = 1 WHERE member = (:member)",
                         {'member': member.id})

    async def update_collection_insects(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        with conn:
            curs.execute(f"UPDATE collection_insects SET {item} = 1 WHERE member = (:member)",
                         {'member': member.id})

    async def update_collection_fish(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        with conn:
            curs.execute(f"UPDATE collection_fish SET {item} = 1 WHERE member = (:member)",
                         {'member': member.id})

    async def check_collection_insects(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        curs.execute(f"SELECT 1 FROM collection_insects WHERE member = (:member) AND {item} = 1",
                     {'member': member.id, 'item': item})
        value = curs.fetchone()
        if value is not None:
            return True
        return False

    async def check_collection_fish(self, member, item):
        item = f'"{item}"'
        conn, curs = await self.load_db()
        curs.execute(f"SELECT 1 FROM collection_fish WHERE member = (:member) AND {item} = 1",
                     {'member': member.id, 'item': item})
        value = curs.fetchone()
        if value is not None:
            return True
        return False

    """
    Games
    """

    @commands.command(aliases=['pf'])
    @commands.has_any_role('ADMIN', 'MODERATOR', 'Dev', 'SERVER OWNER')
    async def _profile(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        bell_icon = self.client.get_emoji(703292022404022353)
        bells = await self.get_bells(member)
        total_insects = await self.get_insects_collection(member)
        total_fish = await self.get_fish_collection(member)
        total_fossils = await self.get_fossil_collection(member)
        karma = database.get_karma(member)
        embed = discord.Embed(color=discord.Color.green(), description=f'{member} :white_small_square: Karma: {karma}')
        embed.set_author(name=f'{member.display_name}\'s Profile', icon_url=member.avatar_url)
        embed.add_field(name=f'Bells', value=f'{bell_icon} {bells}')
        embed.add_field(name='Insects Caught', value=f':bug: {str(total_insects)}/80')
        embed.add_field(name='Fish Caught', value=f':blowfish: {str(total_fish)}/80')
        embed.add_field(name='Art Found', value=f':paintbrush: coming soon')
        embed.add_field(name='Fossils Found', value=f':bone: {total_fossils}/73')
        embed.add_field(name='\u200b', value='\u200b')

        turnip_emoji = self.client.get_emoji(694822764699320411)
        if turnip_emoji is None:
            turnip_emoji = ':star:'

        pos, neg = database.get_rep(member)
        reviews_given = database.get_reviews_given(member)
        reviewer_rank = await tools.get_reviewer_rank(reviews_given)
        last_reviewer, last_review = database.get_review(member)

        if pos + neg < 1:
            rating = 0
        else:
            rating = int(pos / (pos + neg) * 100)
        if rating == 0:
            stars = 'No Rating'
        elif rating < 30:
            stars = f'{turnip_emoji}'
        elif 30 <= rating < 50:
            stars = f'{turnip_emoji} ' * 2
        elif 50 <= rating < 70:
            stars = f'{turnip_emoji} ' * 3
        elif 70 <= rating < 90:
            stars = f'{turnip_emoji} ' * 4
        else:
            stars = f'{turnip_emoji} ' * 5

        host_rank = await tools.get_host_rank(member)
        value = f'**Rating**: {stars}\n' \
                f'**Rank**: {host_rank}\n' \
                f'**Positive Reviews**: {pos}\n' \
                f'**Negative Reviews**: {neg}\n' \
                f'**Reviews Submitted**: {reviews_given} (rank: {reviewer_rank})'
        embed.add_field(name='Rep', value=value, inline=False)

        if last_reviewer is not None:
            reviewer = discord.utils.get(ctx.guild.members, id=int(last_reviewer))
            embed.add_field(name=f'**Last Review from __{reviewer.display_name}__**', value=last_review)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def bells(self, ctx):
        bells = await self.get_bells(ctx.author)
        await ctx.send(embed=tools.single_embed(f'You have **{bells}** bells.'))

    @commands.command()
    @commands.is_owner()
    async def get_bugs(self, ctx):
        total = await self.get_insects_collection(ctx.author)
        await ctx.send(embed=tools.single_embed(f'You\'ve caught {total} out of 80 insects!'))

    @commands.command()
    @commands.is_owner()
    async def get_fish(self, ctx):
        total = await self.get_fish_collection(ctx.author)
        await ctx.send(embed=tools.single_embed(f'You\'ve caught {total} out of 80 fish!'))

    @commands.command()
    @commands.has_any_role('ADMIN', 'MODERATOR', 'Dev', 'SERVER OWNER')
    @commands.cooldown(1, 60*60*24, commands.BucketType.user)
    async def bells(self, ctx):
        await self.add_to_economy(ctx.author)
        critical = random.randint(0, 100)
        roles = [role.name for role in ctx.author.roles]
        bells = 50
        if 'mae-supporters' in roles:
            bells += 20
        msg = f'You gathered **{bells}** bells!'
        if critical == 100:
            bells = bells * 2
            msg = f'Wow! You hit the jackpot and dug up **{bells}** bells!'
        await self.modify_bells(ctx.author, bells)

        await ctx.send(embed=tools.single_embed(msg))
        return

    @commands.command()
    # @commands.has_any_role('ADMIN', 'MODERATOR', 'Dev', 'SERVER OWNER')
    @commands.is_owner()
    async def dig(self, ctx):
        bells = await self.get_bells(ctx.author)
        if bells < 10:
            await ctx.send(embed=tools.single_embed_neg('You do not have enough bells to buy the rights to dig here!'))
            return
        await self.modify_bells(ctx.author, -10)
        await self.add_collection_fossils(ctx.author)
        async with aiohttp.ClientSession() as session:
            f = await self.fetch(session, will_url + 'all/fossils')
            data = json.loads(f)
        fossils = [[k['name'], k['filename']] for k in data]
        discovered = fossils[random.randint(0, len(fossils))]
        if await self.check_collection_fossils(ctx.author, discovered[0]):
            msg = f':x: You\'ve already discovered: **{discovered[0]}**!'
        else:
            await self.update_collection_fossils(ctx.author, discovered[0])
            msg = f'You discovered: **{discovered[0]}**!'
        thumbnail = f'{image}Furniture/{discovered[1]}.png'
        embed = discord.Embed(description=msg, color=discord.Color.purple())
        embed.set_image(url=thumbnail)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def net(self, ctx):
        bells = await self.get_bells(ctx.author)
        if bells < 10:
            await ctx.send(embed=tools.single_embed_neg('You do not have enough bells to buy bug bait!'))
            return
        await self.modify_bells(ctx.author, -10)
        await self.add_collection_insects(ctx.author)
        async with aiohttp.ClientSession() as session:
            f = await self.fetch(session, will_url + 'insect/available/' + datetime.now().strftime("%B"))
            data = json.loads(f)

        insects = [[k['name'], k["critterpediaFilename"], k['spawnRate']] for k in data]

        verify = False
        while not verify:
            try:
                caught = insects[random.randint(0, len(insects))]
                spawn = caught[2]
                if '–' in spawn:
                    spawn = spawn.split('–')[1]
                # 5% chance
                if int(spawn) <= 5:
                    if random.randint(0, 20) == 0:
                        if await self.check_collection_insects(ctx.author, caught[0]):
                            msg = f':x: You\'ve already caught: **{caught[0]}**! *RARE*'
                        else:
                            await self.update_collection_insects(ctx.author, caught[0])
                            msg = f'You caught: **{caught[0]}**! *RARE*'
                        thumbnail = f'{image}insects/{caught[1]}.png'
                        embed = discord.Embed(description=msg, color=discord.Color.purple())
                        embed.set_image(url=thumbnail)
                        await ctx.send(embed=embed)
                        verify = True
                # 20% chance
                elif 5 < int(spawn) <= 25:
                    if random.randint(0, 10) == 0:
                        if await self.check_collection_insects(ctx.author, caught[0]):
                            msg = f':x: You\'ve already caught: **{caught[0]}**! *UNCOMMON*'
                        else:
                            await self.update_collection_insects(ctx.author, caught[0])
                            msg = f'You caught: **{caught[0]}**! *UNCOMMON*'
                        thumbnail = f'{image}insects/{caught[1]}.png'
                        embed = discord.Embed(description=msg, color=discord.Color.blue())
                        embed.set_image(url=thumbnail)
                        await ctx.send(embed=embed)
                        verify = True
                else:
                    if await self.check_collection_insects(ctx.author, caught[0]):
                        msg = f':x: You\'ve already caught: **{caught[0]}**! *COMMON*'
                    else:
                        msg = f'You caught: **{caught[0]}**! *COMMON*'
                        await self.update_collection_insects(ctx.author, caught[0])
                    thumbnail = f'{image}insects/{caught[1]}.png'
                    embed = discord.Embed(description=msg, color=discord.Color.green())
                    embed.set_image(url=thumbnail)
                    await ctx.send(embed=embed)
                    verify = True
            except IndexError:
                pass

    @commands.command()
    @commands.is_owner()
    async def cast(self, ctx):
        bells = await self.get_bells(ctx.author)
        if bells < 10:
            await ctx.send(embed=tools.single_embed_neg('You do not have enough bells to buy bait!'))
            return
        await self.modify_bells(ctx.author, -10)
        await self.add_collection_fish(ctx.author)
        async with aiohttp.ClientSession() as session:
            if random.randint(0, 5) == 0:
                f = await self.fetch(session, will_url + 'fish/sea%20bass')
                data = json.loads(f)
                if await self.check_collection_fish(ctx.author, data['name']):
                    msg = f':x: You\'ve already caught: **{data["name"]}**! *COMMON*'
                else:
                    await self.update_collection_fish(ctx.author, data['name'])
                    msg = f'You caught: **{data["name"]}**! *COMMON*'
                thumbnail = f'{image}Fish/{data["critterpediaFilename"]}.png'
                embed = discord.Embed(description=msg, color=discord.Color.green())
                embed.set_image(url=thumbnail)
                await ctx.send(embed=embed)
                return
            else:
                f = await self.fetch(session, will_url + 'fish/available/' + datetime.now().strftime("%B"))
                data = json.loads(f)

        fish = [[k['name'], k["critterpediaFilename"], k['spawnRate']] for k in data]

        verify = False
        while not verify:
            try:
                caught = fish[random.randint(0, len(fish))]
                spawn = caught[2][0].split('-')[-1]
                # 5% chance
                if int(spawn) <= 2:
                    check = random.randint(0, 20)
                    if check == 0:
                        if await self.check_collection_fish(ctx.author, caught[0]):
                            msg = f':x: You\'ve already caught: **{caught[0]}**! *RARE*'
                        else:
                            await self.update_collection_fish(ctx.author, caught[0])
                            msg = f'You caught: **{caught[0]}**! *RARE*'
                        thumbnail = f'{image}Fish/{caught[1]}.png'
                        embed = discord.Embed(description=msg, color=discord.Color.purple())
                        embed.set_image(url=thumbnail)
                        await ctx.send(embed=embed)
                        verify = True
                # 10% chance
                elif 2 < int(spawn) <= 5:
                    check = random.randint(0, 10)
                    if check == 0:
                        if await self.check_collection_fish(ctx.author, caught[0]):
                            msg = f':x: You\'ve already caught: **{caught[0]}**! *UNCOMMON*'
                        else:
                            await self.update_collection_fish(ctx.author, caught[0])
                            msg = f'You caught: **{caught[0]}**! *UNCOMMON*'
                        thumbnail = f'{image}Fish/{caught[1]}.png'
                        embed = discord.Embed(description=msg, color=discord.Color.blue())
                        embed.set_image(url=thumbnail)
                        await ctx.send(embed=embed)
                        verify = True
                else:
                    if await self.check_collection_fish(ctx.author, caught[0]):
                        msg = f':x: You\'ve already caught: **{caught[0]}**! *COMMON*'
                    else:
                        await self.update_collection_fish(ctx.author, caught[0])
                        msg = f'You caught: **{caught[0]}**! *COMMON*'
                    thumbnail = f'{image}Fish/{caught[1]}.png'
                    embed = discord.Embed(description=msg, color=discord.Color.green())
                    embed.set_image(url=thumbnail)
                    await ctx.send(embed=embed)
                    verify = True
            except IndexError:
                pass

    @commands.command(aliases=['slots'])
    @commands.has_any_role('ADMIN', 'MODERATOR', 'Dev', 'SERVER OWNER')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slot(self, ctx, bet=10):
        if bet < 1:
            await ctx.send(embed=tools.single_embed_neg(f'You cannot bet less than 1 bell.'))
            return
        await self.add_to_economy(ctx.author)
        bells = await self.get_bells(ctx.author)
        if bells <= 0:
            await ctx.send(embed=tools.single_embed_neg(f'You do not have enough bells to play!'))
            return
        elif bells < bet:
            await ctx.send(embed=tools.single_embed_neg(f'Your bet is more than your total bells!'))
            return
        await self.modify_bells(ctx.author, bet * -1)
        bells = await self.get_bells(ctx.author)
        fruits = [':watermelon:', ':grapes:', ':strawberry:',
                  ':cherries:', ':pineapple:', ':peach:',
                  ':coconut:', ':kiwi:', ':banana:']

        slots = self.client.get_emoji(714813946984398909)

        slot1 = fruits[random.randint(0, 8)]
        slot2 = fruits[random.randint(0, 8)]
        slot3 = fruits[random.randint(0, 8)]

        if bet == 1:
            title = f'Betting {bet} bell!'
        else:
            title = f'Betting {bet} bells!'
        winning_scenarios = f'🍒 x3 ........................ Win 10x!\n' \
                            f'Match all 3 .............. Win 4x!\n' \
                            f'Match any 2 ............ Win 2x!'

        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='How to Win', value=winning_scenarios)
        embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
        output = await ctx.send(embed=embed)

        await asyncio.sleep(1)
        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.add_field(name='\u200b', value=f'{slot1}')
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='How to Win', value=winning_scenarios)
        embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
        await output.edit(embed=embed)

        await asyncio.sleep(1)
        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.add_field(name='\u200b', value=f'{slot1}')
        embed.add_field(name='\u200b', value=f'{slot2}')
        embed.add_field(name='\u200b', value=f'{slots}')
        embed.add_field(name='How to Win', value=winning_scenarios)
        embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
        await output.edit(embed=embed)

        await asyncio.sleep(1)
        embed = discord.Embed(title=title, color=discord.Color.green())
        embed.add_field(name='\u200b', value=f'{slot1}')
        embed.add_field(name='\u200b', value=f'{slot2}')
        embed.add_field(name='\u200b', value=f'{slot3}')
        embed.add_field(name='How to Win', value=winning_scenarios)
        embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
        await output.edit(embed=embed)

        jackpot = False
        if all([slot1, slot2, slot3]) == ':cherry:':
            winnings = bet * 10
            jackpot = True
        elif all([slot1, slot2]) == slot3:
            winnings = bet * 4
        elif slot1 == slot2 or slot1 == slot3 or slot2 == slot3:
            winnings = int(bet * 2)
        else:
            winnings = bet * 0

        await self.modify_bells(ctx.author, winnings)

        if int(winnings) > 0:
            bells = await self.get_bells(ctx.author)
            msg = f'You\'ve won **{winnings - bet}** bells!'
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'{slot1}')
            embed.add_field(name='\u200b', value=f'{slot2}')
            embed.add_field(name='\u200b', value=f'{slot3}')
            embed.add_field(name='How to Win', value=winning_scenarios)
            embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
            if jackpot:
                dance = self.client.get_emoji(715295817681993759)
                embed.add_field(name='JACKPOT!', value=f'{dance} {msg} {dance}', inline=False)
            else:
                embed.add_field(name='Winner!', value=f'{slots} {msg} {slots}', inline=False)
            await output.edit(embed=embed)
        else:
            bells = await self.get_bells(ctx.author)
            msg = f'Better luck next time!'
            embed = discord.Embed(title=title, color=discord.Color.green())
            embed.add_field(name='\u200b', value=f'{slot1}')
            embed.add_field(name='\u200b', value=f'{slot2}')
            embed.add_field(name='\u200b', value=f'{slot3}')
            embed.add_field(name='How to Win', value=winning_scenarios, inline=False)
            embed.add_field(name='Balance', value=f'{bells} bells', inline=False)
            embed.add_field(name='No matches', value=msg, inline=False)
            await output.edit(embed=embed)

    """
    Error Handling
    """

    @bells.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=tools.single_embed_neg(f'You can only gather once per day!'))

    @slot.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=tools.single_embed_neg(error))


def setup(client):
    client.add_cog(Games(client))
