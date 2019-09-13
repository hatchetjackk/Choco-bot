#!/usr/bin/python3

import json
import os
import discord
from discord.ext import commands

client = commands.Bot(command_prefix='!')


@client.event
async def on_ready():
    print('Login successful! Kweh!')


@client.event
async def on_resume():
    print('Connection resumed')


if __name__ == '__main__':
    print('Loading cogs...')
    cogs = [f.replace('.py', '') for f in os.listdir('cogs/') if '__' not in f]
    for cog in cogs:
        print(f'* Loading {cog}')
        client.load_extension('cogs.' + cog)
    with open('files/credentials.json') as f:
        credentials = json.load(f)
    client.run(credentials['token'])