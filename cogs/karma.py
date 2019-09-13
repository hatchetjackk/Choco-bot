from discord.ext import commands


class Karma(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group()
    async def karma(self, ctx):
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        return


def setup(client):
    client.add_cog(Karma(client))
