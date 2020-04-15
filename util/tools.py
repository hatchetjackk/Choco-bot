import json
import aiohttp
import discord
import string
import random
import util.db as database
from datetime import datetime
from bs4 import BeautifulSoup

intervals = (
    ('years', 31536000),
    ('weeks', 604800),
    ('days', 86400),
    ('hours', 3600),
    ('minutes', 60),
    ('seconds', 1),
    )


def display_time(seconds, granularity=1):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(int(value), name))
    return ', '.join(result[:granularity])


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


def to_lower(arg):
    return arg.lower()


def single_embed(msg, avatar=None):
    embed = discord.Embed(color=discord.Color.green(), description=msg)
    if avatar is not None:
        embed.set_thumbnail(url=avatar)
    return embed


def single_embed_tooltip(msg):
    msg = f'{msg}\nCheck `r:help` for commands.'
    embed = discord.Embed(title='alert', color=discord.Color.dark_green(), description=msg)
    embed.set_thumbnail(url='https://i.imgur.com/Q4WlpFc.png')
    # embed.set_footer(text='Check r:help for commands.')
    return embed


def single_embed_level(msg):
    embed = discord.Embed(color=discord.Color.purple(), description=msg)
    return embed


def single_embed_neg(msg, avatar=None):
    embed = discord.Embed(color=discord.Color.red(), description=msg)
    if avatar is not None:
        embed.set_thumbnail(url=avatar)
    return embed


def find_by_key(data, target):
    for key, value in data.items():
        if isinstance(value, dict):
            yield from find_by_key(value, target)
        elif key == target:
            yield value


def format_date(date_obj, option: int = 0, to_date=False):
    f = ['%m/%d/%Y %H:%M:%S', '%m/%d/%Y']
    if to_date:
        return datetime.strptime(date_obj, f[option])
    return date_obj.strftime(f[option])


def format_date_long(date_obj):
    f = ['%m/%d/%Y %H:%M:%S', '%m/%d/%Y']
    return date_obj.strftime(f[0])


def to_seconds(date_obj):
    return (datetime.now() - date_obj).total_seconds()


def get_key(d, val):
    for k, v in d.items():
        if val == v:
            return k


async def get_inspiration():
    url = 'http://inspirobot.me/api?generate=true'
    async with aiohttp.ClientSession() as session:
        page = await fetch(session, url)
        return page


def get_reviews():
    with open('files/reviews.json') as f:
        reviews = json.load(f)
        return reviews


def write_reviews(host_id, reviewer_id):
    reviews = get_reviews()
    for h, r in reviews.items():
        print(h, r)
    seconds = to_seconds(datetime.now())
    reviews['host'] = [host_id][reviewer_id][seconds]
    with open('files/reviews.json', 'w') as f:
        json.dump(reviews, f)


def check_last_review(host, reviewer):
    reviews = get_reviews()
    data = reviews.get(host)
    time = format_date(data.get(reviewer))
    seconds = to_seconds(time)
    if seconds > 0:
        message = f'You have already reviewed this host today.'
        return message


async def get_reviewer_rank(reviews: int):
    given_rank = None
    with open('files/ranks.json') as f:
        ranks = json.load(f)["reviewer ranks"]
    for rank, level in ranks.items():
        if reviews >= level:
            given_rank = rank
    return given_rank


async def get_host_rank(member):
    try:
        if not database.in_members_table(member):
            database.add_member(member)
        pos, neg = database.get_rep(member)

        with open('files/ranks.json') as f:
            ranks = json.load(f)["host ranks"]
        rank_list = []
        for rank, reviews in ranks.items():
            if pos >= reviews:
                role = discord.utils.get(member.guild.roles, name=rank)
                if role.name in [r.name for r in member.roles]:
                    rank_list.append(role.name)
        return rank_list[-1]
    except IndexError:
        return None


async def write_sessions(data, sessions='sessions/sessions.json'):
    try:
        with open(sessions, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f'An error occurred when writing to {sessions}: {e}')
        return False


async def read_sessions(sessions='sessions/sessions.json'):
    try:
        with open(sessions) as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f'An error occurred when writing to {sessions}: {e}')
        return None


async def random_code(string_length=5):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(string_length)).upper()


async def create_private_channel(ctx, member, session_code=None):
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True)
    }

    channel_name = str(member.id) + '_session'
    if discord.utils.get(ctx.guild.text_channels, name=channel_name) is not None:
        return False
    topic = f'Session Code: {session_code}'
    category = discord.utils.get(ctx.guild.channels, id=697086444082298911)
    channel = await ctx.guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category, topic=topic)
    msg = f'Welcome, {member.mention}! This is your private Daisy-Mae Session.\nYour Session Code is: **{session_code}**'
    await channel.send(embed=single_embed(msg))
    return channel


async def close_private_channel(channel):
    # delete session
    if channel is None:
        return False
    try:
        await channel.delete(reason='Closing Private Session')
        return True
    except Exception as e:
        print(f'Error closing session: {e}')
        return False


async def edit_msg(channel, message_id, after=None, delete_after=None):
    try:
        session_message = await channel.fetch_message(id=message_id)
        if after is None:
            await session_message.delete()
        else:
            await session_message.edit(embed=single_embed_neg(after), delete_after=delete_after)
    except KeyError:
        pass
    except Exception as e:
        print(f'Editing message error. This can be ignored: {e}')

    try:
        session_message = await channel.fetch_message(id=message_id)
        await session_message.clear_reactions()
    except Exception as e:
        print(e)



