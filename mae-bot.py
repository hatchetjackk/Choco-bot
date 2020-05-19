#!/usr/bin/python3
import asyncio
import json
import os
import logging
from datetime import datetime
from itertools import cycle
import util.tools as tools
import util.db as database
import discord
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='files/logs/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


async def prefix(bot, message):
    return database.get_prefix(message.guild)

client = commands.Bot(command_prefix=prefix, case_insensitive=True)

client.remove_command('help')


@client.command()
async def reload(ctx, extension_name: str):
    await ctx.channel.purge(limit=1)
    if not await client.is_owner(ctx.author):
        return
    try:
        client.unload_extension('cogs.' + extension_name)
        client.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        print(e)
    await ctx.send(embed=tools.single_embed(f'{extension_name.capitalize()} reloaded'), delete_after=3)
    print(f'* Reloaded {extension_name}')


@client.command()
async def load(ctx, extension_name: str):
    if not await client.is_owner(ctx.author):
        return
    try:
        client.load_extension('cogs.' + extension_name)
    except (AttributeError, ImportError) as e:
        print(f'* Error loading cog {extension_name}: {e}')
    await ctx.send(embed=tools.single_embed(f'{extension_name.capitalize()} loaded'))
    print(f'* Loaded {extension_name}')


@client.event
async def on_ready():
    print(f'{datetime.now().strftime("%I:%M:%S %p")}\tLogin successful')
    database.check_database()
    status_options = ['with turnips', 'with stalks']
    msg = cycle(status_options)
    while not client.is_closed():
        current_status = next(msg)
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name=current_status))
        await asyncio.sleep(60 * 5)


@client.event
async def on_resume():
    print(f'{datetime.now().strftime("%I:%M:%S %p")}\tConnection resumed')


@client.event
async def on_command(ctx):
    msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}] Channel:[{ctx.channel.name}] | Triggered Command [{ctx.command}]'
    print(msg)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered cooldown [{ctx.command}]'
        print(msg)
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(embed=tools.single_embed_tooltip(f'I\'m sorry. That command doesn\'t exist.'))
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered CommandNotFound [{ctx.command}]'
        print(msg)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=tools.single_embed(f'You do not have permission to run this command.'), delete_after=10)
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered permissions error [{ctx.command}]'
        print(msg)
    elif isinstance(error, discord.errors.NotFound):
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered permissions error [{ctx.command}]'
        print(msg)
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(embed=tools.single_embed(f'An error occurred when running {ctx.command}.'))
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered CommandInvokeError [{ctx.command}] {error}'
        print(msg)
    else:
        msg = f'{datetime.now().strftime("%I:%M:%S %p")}\tUser:[{ctx.author}]\tChannel:[{ctx.channel.name}]\tTriggered an error [{ctx.command}:{error}]'
        print(msg)


if __name__ == '__main__':
    print('Loading cogs')
    cogs = [f.replace('.py', '') for f in os.listdir('cogs/') if '__' not in f]
    for cog in cogs:
        print(f'* Loading {cog}')
        client.load_extension('cogs.' + cog)
    with open('files/credentials.json') as f:
        credentials = json.load(f)
    client.run(credentials['token'])
