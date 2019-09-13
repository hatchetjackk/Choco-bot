from discord.ext import commands


class FinalFantasy(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def bounty(self):
        return

    async def characters(self):
        return


def setup(client):
    client.add_cog(FinalFantasy(client))
