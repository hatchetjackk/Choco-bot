import discord
import json
import util.tools as tools
import util.db as database
from discord.ext import commands
from collections import OrderedDict
from datetime import datetime

mae_banner = 'https://i.imgur.com/HffuudZ.jpg'


class Rep(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def can_bypass_cooldown(self, ctx):
        if ctx.author.permissions_in(ctx.channel).administrator:
            return True
        elif await self.client.is_owner(ctx.author):
            return True
        return False

    @staticmethod
    async def prefix(ctx):
        return database.get_prefix(ctx.guild)[0]

    @staticmethod
    async def rep_cog_on(ctx):
        if database.rep_cog(ctx.guild):
            return True
        msg = f'**Rep** is not turned on'
        await ctx.send(embed=tools.single_embed_neg(msg))
        return False

    @commands.command()
    async def bug(self, ctx, *, message: str):
        """
        Send a bug report
        :param ctx:
        :param message:
        :return:
        """
        msg = f'A bug report was filed by **{ctx.author.display_name}**.\n**Message**: {message}'
        if len(ctx.message.attachments) > 0:
            msg += '\n' + ctx.message.attachments[0].url
        channels = [c for c in ctx.guild.channels if 'bug-reports']
        chan = None
        for c in channels:
            if 'bug-report' in c.name:
                chan = c
        if chan is not None:
            await chan.send(embed=tools.single_embed_neg(msg, avatar=ctx.author.avatar_url))
        else:
            owner = self.client.get_user(193416878717140992)
            await owner.send(msg)
        await ctx.send(embed=tools.single_embed_neg(f'Your report has been sent. Thank you.'))

    @commands.command(aliases=['r'])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def rep(self, ctx, member: discord.Member = None):
        if await self.can_bypass_cooldown(ctx):
            self.rep.reset_cooldown(ctx)
        if not await self.rep_cog_on(ctx):
            return
        turnip_emoji = self.client.get_emoji(694822764699320411)
        if turnip_emoji is None:
            turnip_emoji = ':star:'

        if member is None:
            member = ctx.author

        if not database.in_members_table(member):
            database.add_member(member)

        pos, neg = database.get_rep(member)
        reviews_given = database.get_reviews_given(member)
        reviewer_rank = await tools.get_reviewer_rank(reviews_given)
        last_reviewer, last_review = database.get_review(member)

        if pos + neg < 1:
            rating = 0
        else:
            rating = int(pos/(pos+neg)*100)
        if rating == 0:
            stars = 'No Rating'
        elif rating < 20:
            stars = f'{turnip_emoji}'
        elif 20 <= rating < 40:
            stars = f'{turnip_emoji} ' * 2
        elif 40 <= rating < 60:
            stars = f'{turnip_emoji} ' * 3
        elif 60 <= rating < 80:
            stars = f'{turnip_emoji} ' * 4
        else:
            stars = f'{turnip_emoji} ' * 5

        host_rank = await tools.get_host_rank(member)

        msg = f'**Rating**: {stars}\n' \
              f'**Host Rank**: {host_rank}\n'\
              f'**Positive Reviews**: {pos}\n'\
              f'**Negative Reviews**: {neg}\n'\
              f'**Total Reviews**: {neg + pos}\n' \
              f'**Reviews Submitted**: {reviews_given} (rank: {reviewer_rank})\n\n'

        if last_reviewer is not None:
            reviewer = discord.utils.get(ctx.guild.members, id=int(last_reviewer))
            msg += f':tada: **Last Review from __{reviewer.display_name}__**\n'f'"{last_review}"'

        embed = discord.Embed(title=f'{member.display_name}', color=member.color, description=msg)
        embed.set_image(url=mae_banner)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['reviewers', 'reviews'])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def top_reviewers(self, ctx):
        """ return a leaderboard with the top 10 karma leaders. If the requesting member is not in the top 10,
        their place will be added to the bottom of the leaderboard
        """
        if await self.can_bypass_cooldown(ctx):
            self.repboard.reset_cooldown(ctx)
        if not await self.rep_cog_on(ctx):
            return
        # turnip_emoji = self.client.get_emoji(694822764699320411)

        array = {}
        for member in ctx.guild.members:
            if member.bot:
                continue
            if not database.in_members_table(member):
                database.add_member(member)
            reviews_given = database.get_reviews_given(member)
            array[member.display_name] = reviews_given

        # sort users by most to least rep
        counter = 1
        leaderboard = []
        append_author = ''
        sorted_rep = OrderedDict(reversed(sorted(array.items(), key=lambda x: x[1])))
        for member, reviews in sorted_rep.items():
            reviewer_rank = await tools.get_reviewer_rank(reviews)
            msg = f'{counter}: **{member}** (*{reviewer_rank}*) - `{reviews}` points '
            leaderboard.append(msg)
            if ctx.author.display_name == member and counter > 10:
                append_author = f'\n----------------\n{counter}: **{member}** (*{reviewer_rank}*) - `{reviews}` points '
            counter += 1

        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=f'Top Reviewers :star:', value='\n'.join(leaderboard[:10]) + append_author)
        embed.set_image(url=mae_banner)
        # embed.set_thumbnail(url="https://i.imgur.com/wl2MZIV.png")
        await ctx.send(embed=embed)

    @commands.command(aliases=['rboard'])
    @commands.cooldown(2, 30, commands.BucketType.user)
    async def repboard(self, ctx):
        """ return a leaderboard with the top 10 karma leaders. If the requesting member is not in the top 10,
        their place will be added to the bottom of the leaderboard
        """
        if await self.can_bypass_cooldown(ctx):
            self.repboard.reset_cooldown(ctx)
        if not await self.rep_cog_on(ctx):
            return
        turnip_emoji = self.client.get_emoji(694822764699320411)

        array = {}
        top_ten = database.top_ten_rep(ctx.guild)
        for (uid, pos, neg) in top_ten:
            member = discord.utils.get(ctx.guild.members, id=uid)
            if member is None:
                pass
            else:
                array[member.display_name] = pos

        # sort users by most to least rep
        counter = 1
        leaderboard = []
        append_author = ''
        medals = {1: ' :first_place:', 2: ' :second_place:', 3: ' :third_place:'}
        sorted_rep = OrderedDict(reversed(sorted(array.items(), key=lambda x: x[1])))
        for member, rep in sorted_rep.items():
            msg = f'{counter}: **{member}** - `{rep}` points'
            for k, v in medals.items():
                if counter == k:
                    msg = msg + v
            leaderboard.append(msg)
            counter += 1
        if ctx.author.display_name not in array:
            pos, neg, index = database.get_rep_position(ctx.author)
            append_author = f'\n----------------\n{index}: **{ctx.author.display_name}** - `{pos}` points'

        embed = discord.Embed(color=discord.Color.blue())
        embed.add_field(name=f'Rep Leaderboard {turnip_emoji}', value='\n'.join(leaderboard[:10]) + append_author)
        embed.set_image(url=mae_banner)
        embed.set_thumbnail(url="https://i.imgur.com/wl2MZIV.png")
        await ctx.send(embed=embed)

    @commands.command(aliases=['p'])
    @commands.cooldown(2, 360, commands.BucketType.user)
    async def pos(self, ctx, member: discord.Member, *, review: str = None):
        if await self.can_bypass_cooldown(ctx):
            self.pos.reset_cooldown(ctx)
        if not await self.rep_cog_on(ctx):
            return
        if ctx.author == member:
            msg = f'You cannot give yourself a review, {ctx.author.display_name}. *Snort!*'
            await ctx.send(embed=tools.single_embed(msg), delete_after=15)
            return

        if not database.in_members_table(ctx.author):
            database.add_member(ctx.author)

        database.add_pos(member)
        pos, neg = database.get_rep(member)

        message = f'**{member.display_name}** gained 1 positive review from **{ctx.author.display_name}**!\n\n'
        if review is None:
            review = f'Sadly, {ctx.author.display_name} did not leave a message. :pig: *Snort!*'
        message += f'**{ctx.author.display_name}** said: \n"{review}"'

        database.add_review(member, ctx.author, review)
        database.add_reviews_given(ctx.author)

        # create embed and post it in the review channel
        embed = discord.Embed(color=discord.Color.green(), description=message)
        embed.set_thumbnail(url=member.avatar_url)
        time = tools.format_date_long(datetime.now())
        embed.set_footer(text=f'{member.display_name} now has {pos} positive reviews! {time}')
        review_chan = database.get_review_channel(ctx.guild)
        await review_chan.send(embed=embed)

        await self.assign_new_role(member)

        # notify the user if the current channel is not the review channel
        if ctx.channel.id != review_chan.id:
            await ctx.send(embed=tools.single_embed(f'Thank you, **{ctx.author.display_name}**!\n'
                                                    f'Your review has been received and posted in '
                                                    f'{review_chan.mention}.'))

        await ctx.message.delete()

    @commands.command(aliases=['mpos'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def mass_pos(self, ctx, *, review: str = None):
        if await self.can_bypass_cooldown(ctx):
            self.mass_pos.reset_cooldown(ctx)

        if not await self.rep_cog_on(ctx):
            return

        members = [m for m in ctx.guild.members if m.mentioned_in(ctx.message) if m is not ctx.author]
        if len(members) < 1:
            await ctx.send(embed=tools.single_embed(f'No one was mentioned in your review.'))
            return
        for member in members:
            database.add_pos(member)
            database.add_review(member, ctx.author, review)
            await self.assign_new_role(member)

        message = f'**{", ".join(m.display_name for m in members)}**  each gained 1 positive review from **{ctx.author.display_name}**!\n\n'
        if review is None:
            review = f'Sadly, {ctx.author.display_name} did not leave a message. :pig: *Snort!*'
        message += f'**{ctx.author.display_name}** said: \n"{review}"'

        for _ in range(len(members)):
            database.add_reviews_given(ctx.author)

        # create embed and post it in the review channel
        embed = discord.Embed(color=discord.Color.green(), description=message)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        time = tools.format_date_long(datetime.now())
        embed.set_footer(text=f'{time}')
        review_chan = database.get_review_channel(ctx.guild)
        await review_chan.send(embed=embed)

        # notify the user if the current channel is not the review channel
        if ctx.channel.id != review_chan.id:
            await ctx.send(embed=tools.single_embed(f'Thank you, **{ctx.author.display_name}**!\n'
                                                    f'Your review has been received and posted in '
                                                    f'{review_chan.mention}.'))

        await ctx.message.delete()

    @commands.command(aliases=['n'])
    @commands.cooldown(2, 360, commands.BucketType.user)
    async def neg(self, ctx, member: discord.Member, *, message: str):
        # take message from user and send to staff support
        if await self.can_bypass_cooldown(ctx):
            self.neg.reset_cooldown(ctx)
        if not await self.rep_cog_on(ctx):
            return
        if ctx.author == member:
            msg = f'You cannot give yourself a review, {ctx.author.display_name}. :pig: *squee!*'
            await ctx.send(embed=tools.single_embed(msg))
            await ctx.message.delete()
            return
        if len(ctx.message.attachments) < 1:
            msg = f'Your negative review is incomplete. Please attach a screenshot or picture verifying your claim.'
            await ctx.author.send(embed=tools.single_embed(msg))
            await ctx.message.delete()
            return

        if not database.in_members_table(ctx.author):
            database.add_member(ctx.author)

        database.add_neg(member)
        database.add_reviews_given(ctx.author)

        staff_support_channel = database.get_administrative(ctx.guild)
        msg = f'**{member.display_name}** gained 1 negative review from '\
              f'**{ctx.author.display_name}**.\n\n'\
              f'**{ctx.author.display_name}** said:\n "{message}"'

        embed = discord.Embed(color=discord.Color.red(), description=msg)
        try:
            img = ctx.message.attachments[0].url
            embed.set_image(url=img)
        except IndexError:
            pass
        embed.set_thumbnail(url=member.avatar_url)
        await staff_support_channel.send(embed=embed)

        msg = f'Your review has been submitted and forwarded to staff. Thank you.'
        await ctx.send(embed=tools.single_embed_neg(msg), delete_after=30)
        await ctx.message.delete()

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def add(self, ctx, method, member: discord.Member, points: int, *, message: str = None):
        if not await self.rep_cog_on(ctx):
            return
        if message is None:
            message = 'No additional information given.'

        if not database.in_members_table(ctx.author):
            database.add_member(ctx.author)

        bot_spam = database.get_spam(ctx.guild)

        message = f'**{ctx.author.display_name}** gave **{member.display_name}** '\
                  f'{points} {method} point(s).\n'\
                  f'> {message}'

        if method == 'pos':
            database.add_pos(member, points)
            await bot_spam.send(embed=tools.single_embed(message))
            await self.assign_new_role(member)

        if method == 'neg':
            database.add_neg(member, points)
            await bot_spam.send(embed=tools.single_embed_neg(message))

        await ctx.send(embed=tools.single_embed(f'Your changes have been updated.'))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def sub(self, ctx, method, member: discord.Member, points: int, *, message: str = None):
        if not await self.rep_cog_on(ctx):
            return
        if message is None:
            message = 'No additional information given.'

        if not database.in_members_table(ctx.author):
            database.add_member(ctx.author)

        bot_spam = database.get_spam(ctx.guild)

        message = f'**{ctx.author.display_name}** removed {points} {method} point(s) from **{member.display_name}**.\n'\
                  f'> {message}'

        if method == 'pos':
            database.sub_pos(member, points)
            await bot_spam.send(embed=tools.single_embed(message))
            await self.assign_new_role(member)

        if method == 'neg':
            database.sub_neg(member, points)
            await bot_spam.send(embed=tools.single_embed_neg(message))

        await ctx.send(embed=tools.single_embed(f'Your changes have been updated.'))

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def reset(self, ctx, member: discord.Member, *, message: str = None):
        if not await self.rep_cog_on(ctx):
            return
        if message is None:
            message = 'No additional information given.'

        if not database.in_members_table(ctx.author):
            database.add_member(ctx.author)

        pos, neg = database.get_rep(member)
        database.reset(member)

        # staff_support_channel = self.client.get_channel(694036188813721610)
        staff_support_channel = database.get_administrative(ctx.guild)
        await staff_support_channel.send(
            embed=tools.single_embed(f'**{ctx.author.display_name}** reset '
                                     f'**{member.display_name}\'s** reviews to 0.\n'
                                     f'{member.display_name}\'s original score was {pos} pos and {neg} neg.\n'
                                     f'Log: {message}'))

    @staticmethod
    async def assign_new_role(member: discord.Member):
        # send new role notifications to general
        chan = None
        channels = [c for c in member.guild.channels if 'general']
        for c in channels:
            if 'general' in c.name:
                chan = c
        if chan is None:
            chan = database.get_spam(member.guild)
        if not database.in_members_table(member):
            database.add_member(member)
        pos, neg = database.get_rep(member)

        with open('files/ranks.json') as f:
            ranks = json.load(f)["host ranks"]
        for rank, reviews in ranks.items():
            if pos >= reviews:
                if rank not in [role.name for role in member.guild.roles]:
                    await member.guild.create_role(name=rank, hoist=True)
                role = discord.utils.get(member.guild.roles, name=rank)
                if role.name not in [r.name for r in member.roles]:
                    await member.add_roles(role)
                    await chan.send(embed=tools.single_embed(f':tada: {member.mention} has earned the **{role}** role!'))

    @pos.error
    async def on_command_error(self, ctx, error):
        prefix = await self.prefix(ctx)
        if isinstance(error, commands.BadArgument):
            msg = f'{error}.\n'\
                  f'To add a positive review, please use `{prefix}pos @member message` '\
                  f'where `@member` can be a user mention, user ID, or the username in quotes. '\
                  f'Messages are optional.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))
            msg = f'{ctx.author.display_name} encountered a {type(error)} error running {ctx.command} in {ctx.channel.name}: {error}'
            print(msg)

        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'You appear to be missing the `{error.param.name}` argument required for this command. ' \
                  f'Please use `{prefix}pos @member message` for positive reviews. Messages are optional.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

    @neg.error
    async def on_command_error(self, ctx, error):
        prefix = await self.prefix(ctx)
        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            msg = f'{error}.\n'\
                  f'To add a negative review, please use `{prefix}neg @member message` '\
                  f'where `@member` can be a user mention, user ID, or the username in quotes. '\
                  f'**Messages are required.**'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.delete()
            msg = f'You appear to be missing the `{error.param.name}` argument required for this command.\n' \
                  f'Please use `{prefix}neg @member message` for positive reviews. **Messages are required.**'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            # await ctx.send(embed=tools.single_embed_tooltip(f'You\'re doing that too fast!\n{error}'))

    @add.error
    async def on_command_error(self, ctx, error):
        prefix = await self.prefix(ctx)
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'You appear to be missing the `{error.param.name}` argument required for this command. ' \
                  f'Please use `{prefix}add pos/neg @member points message`. Messages are optional.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

    @bug.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'Please enter a message for the bug report.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

    @sub.error
    async def on_command_error(self, ctx, error):
        prefix = await self.prefix(ctx)
        if isinstance(error, commands.MissingRequiredArgument):
            msg = f'You appear to be missing the `{error.param.name}` argument required for this command. ' \
                  f'Please use `{prefix}sub pos/neg @member points message`. Messages are optional.'
            await ctx.send(embed=tools.single_embed_tooltip(msg))

    @reset.error
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=tools.single_embed_tooltip(f'{error}'))


def setup(client):
    client.add_cog(Rep(client))
