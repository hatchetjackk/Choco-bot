from discord.ext import commands


class Personality(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        # if mae is mentioned
        if self.client.user.mentioned_in(message):
            try:
                await message.add_reaction('🐷')
            except Exception:
                pass

        if message.author.bot:
            pass
        else:
            pass
            # if message.author.id == 505019512702238730:
            #     await message.add_reaction('🇸')
            #     await message.add_reaction('🇮')
            #     await message.add_reaction('🇲')
            #     await message.add_reaction('🇵')

            # if 'cube' in message.content:
            #     await message.add_reaction('🧊')

            # key = ['turnip', 'turnips']
            # if any(item == message.content.lower() for item in key):
            #     try:
            #         turnip_emoji = self.client.get_emoji(694822764699320411)
            #         await message.add_reaction(turnip_emoji)
            #     except Exception:
            #         pass


def setup(client):
    client.add_cog(Personality(client))
