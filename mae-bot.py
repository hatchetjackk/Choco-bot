#!/usr/bin/python3
import asyncio
import json
import os
from datetime import datetime
from itertools import cycle

import util.tools as tools
import util.db as database
import discord
from discord.ext import commands


async def prefix(bot, message):
    if type(message) == 'NoneType':
        print(message)
    return database.get_prefix(message.guild)

client = commands.Bot(command_prefix=prefix, case_insensitive=True)

client.remove_command('help')


@client.command()
async def reload(ctx, extension_name: str):
    if not await client.is_owner(ctx.author):
        return
    try:
        client.unload_extension('cogs.' + extension_name)
        client.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        print(e)
    await ctx.send(embed=tools.single_embed(f'{extension_name.capitalize()} reloaded'))
    print(f'* Reloaded {extension_name}')


@client.command()
async def load(ctx, extension_name: str):
    if not await client.is_owner(ctx.author):
        return
    try:
        client.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        print(e)
    await ctx.send(embed=tools.single_embed(f'{extension_name.capitalize()} loaded'))
    print(f'* Loaded {extension_name}')


@client.event
async def on_ready():
    print(f'Login successful at {datetime.now()}')
    database.check_database()
    status_options = ['with turnips', 'with stalks']
    msg = cycle(status_options)
    while not client.is_closed():
        current_status = next(msg)
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name=current_status))
        await asyncio.sleep(60 * 5)


@client.event
async def on_resume():
    print(f'Connection resumed at {datetime.now()}')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=tools.single_embed_tooltip(f'You\'re doing that too fast!\n{error}'))
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=tools.single_embed_tooltip(f'I\'m sorry. You do not have permission to run this command.'))
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(embed=tools.single_embed_tooltip(f'I\'m sorry. That command doesn\'t exist.'))
        print(f'{ctx.author.display_name} encountered a {type(error)} error running {ctx.command} in {ctx.channel.name}: {error}')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f'You do not have permission to run this command.', delete_after=10)
    elif isinstance(error, discord.errors.NotFound):
        pass
    # elif isinstance(error, discord.errors.):
    #     pass
    else:
        # owner = client.get_user(193416878717140992)
        # await ctx.send(embed=tools.single_embed_tooltip(f'We seem to have encountered an error. [{error}].\nI am notifying {owner.mention}!'))
        print(f'{ctx.author.display_name} encountered a {type(error)} error running {ctx.command} in {ctx.channel.name}: {error}')


if __name__ == '__main__':
    print('Loading cogs')
    cogs = [f.replace('.py', '') for f in os.listdir('cogs/') if '__' not in f]
    for cog in cogs:
        print(f'* Loading {cog}')
        client.load_extension('cogs.' + cog)
    with open('files/credentials.json') as f:
        credentials = json.load(f)
    client.run(credentials['token'])
