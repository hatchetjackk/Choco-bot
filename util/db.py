import sqlite3
import os
import time
import discord
import util.tools as tools
from datetime import datetime


path = 'files/data.db'


def database_exists():
    if os.path.isfile(path):
        print(f'Database found at {path}')
        return True
    print('Database not found')
    return False


def load_database():
    conn = sqlite3.connect(path)
    curs = conn.cursor()
    return conn, curs


def check_database():
    if not database_exists():
        print('Creating new database')
        conn, curs = load_database()
        with conn:
            print('Creating members table')
            curs.execute(
                """CREATE TABLE members (
                member_id INTEGER,
                pos INTEGER,
                neg INTEGER,
                last_rep INTEGER,
                last_reviewer TEXT.
                last_review TEXT,
                reviews_given INTEGER,
                warnings INTEGER,
                karma INTEGER,
                last_karma INTEGER,
                UNIQUE(member_id)
                )"""
            )
            curs.execute(
                """CREATE TABLE guilds (
                guild_id INTEGER,
                prefix TEXT,
                spam INTEGER,
                administrative INTEGER,
                autorole INTEGER,
                review INTEGER,
                admin INTEGER,
                rep INTEGER,
                karma INTEGER,
                mw INTEGER,
                UNIQUE(guild_id)
                )"""
            )
            curs.execute(
                """CREATE TABLE warnings (
                guild INTEGER,
                member INTEGER,
                warnings INTEGER,
                message TEXT
                UNIQUE(guild_id)
                )"""
            )


def in_guilds(guild):
    try:
        conn, curs = load_database()
        curs.execute("SELECT 1 FROM guilds WHERE guild_id = (:guild_id)", {'guild_id': guild.id})
        try:
            out = curs.fetchone()
            if out[0] == 1:
                return True
        except TypeError:
            return False
    except AttributeError as e:
        print(e)


def add_guild(guild):
    try:
        print(f'Adding {guild.name} to {path}')
        spam = guild.system_channel.id
        conn, curs = load_database()
        with conn:
            curs.execute("INSERT OR IGNORE INTO guilds VALUES (:guild_id, :prefix, :spam, :administrative, :autorole, :review, :admin, :rep, :karma, :mw)",
                         {'guild_id': guild.id, 'prefix': 'r:', 'spam': spam, 'administrative': None, 'autorole': None, 'rep': 0, 'karma': 0, 'mw': 0, 'review': 0, 'admin': 1})
    except AttributeError as e:
        print(e)


def mw_set(guild, mode):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET mw = (:mw) WHERE guild_id = (:guild_id)",
                     {'mw': mode, 'guild_id': guild.id})


def mw_cog(guild):
    conn, curs = load_database()
    curs.execute("SELECT mw FROM guilds WHERE guild_id = (:guild_id)",
                 {'guild_id': guild.id})
    if curs.fetchone()[0] == 1:
        return True
    return False


def karma_set(guild, mode):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET karma = (:karma) WHERE guild_id = (:guild_id)",
                     {'karma': mode, 'guild_id': guild.id})


def karma_cog(guild):
    try:
        conn, curs = load_database()
        curs.execute("SELECT karma FROM guilds WHERE guild_id = (:guild_id)",
                     {'guild_id': guild.id})
        if curs.fetchone()[0] == 1:
            return True
        return False
    except AttributeError:
        print(str(datetime.now()) + ': An error occurred when checking karma cog')
        return False


def admin_set(guild, mode):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET admin = (:admin) WHERE guild_id = (:guild_id)",
                     {'admin': mode, 'guild_id': guild.id})


def admin_cog(guild):
    if guild is None:
        return False
    conn, curs = load_database()
    curs.execute("SELECT admin FROM guilds WHERE guild_id = (:guild_id)",
                 {'guild_id': guild.id})
    if curs.fetchone()[0] == 1:
        return True
    else:
        return False


def rep_set(guild, mode):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET rep = (:rep) WHERE guild_id = (:guild_id)",
                     {'rep': mode, 'guild_id': guild.id})


def rep_cog(guild):
    conn, curs = load_database()
    curs.execute("SELECT rep FROM guilds WHERE guild_id = (:guild_id)",
                 {'guild_id': guild.id})
    if curs.fetchone()[0] == 1:
        return True
    else:
        return False


def add_member(member):
    if not in_members_table(member):
        print(f'* Adding {member.display_name} to {path}')
        conn, curs = load_database()
        with conn:
            curs.execute("INSERT OR IGNORE INTO members VALUES (:member_id, :pos, :neg, :last_rep, :last_reviewer, :last_review, :reviews_given, :karma, :last_karma)",
                         {'member_id': member.id, 'pos': 0, 'neg': 0, 'last_rep': None, 'last_reviewer': None, 'last_review': None, 'reviews_given': 0, 'karma': 0, 'last_karma': 0})


def in_members_table(member):
    conn, curs = load_database()
    curs.execute("SELECT 1 FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    try:
        out = curs.fetchone()
        if out[0] == 1:
            return True
    except TypeError:
        return False


def add_to_warnings(member, guild):
    if not in_warnings_table(member, guild):
        conn, curs = load_database()
        with conn:
            curs.execute("INSERT INTO warnings VALUES (:guild, :member, :message)",
                         {'guild': guild.id, 'member': member.id, 'message': None})


def in_warnings_table(member, guild):
    conn, curs = load_database()
    curs.execute("SELECT 1 FROM warnings WHERE member = (:member) AND guild = (:guild)",
                 {'member': member.id, 'guild': guild.id})
    try:
        out = curs.fetchone()
        if out[0] == 1:
            return True
    except TypeError:
        return False


def get_warnings(member):
    conn, curs = load_database()
    curs.execute("SELECT message, date FROM warnings WHERE member = (:member) AND guild = (:guild)",
                 {'member': member.id, 'guild': member.guild.id})
    messages = curs.fetchall()
    return len(messages), messages


def add_warning(member, message):
    conn, curs = load_database()
    with conn:
        curs.execute("INSERT INTO warnings VALUES (:guild, :member, :message, :date)",
                     {'guild': member.guild.id, 'member': member.id, 'message': message, 'date': tools.format_date(datetime.now(), 1)})


def clear_warnings(member):
    conn, curs = load_database()
    with conn:
        curs.execute("DELETE FROM warnings WHERE member = (:member) AND guild = (:guild)",
                     {'guild': member.guild.id, 'member': member.id})


def get_administrative(guild):
    conn, curs = load_database()
    curs.execute("SELECT administrative FROM  guilds WHERE guild_id = (:guild_id)", {'guild_id': guild.id})
    administrative = discord.utils.get(guild.channels, id=curs.fetchone()[0])
    if administrative is None:
        administrative = guild.system_channel
    return administrative


def set_administrative(channel, guild):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET administrative = (:administrative) WHERE guild_id = (:guild_id)",
                     {'administrative': channel.id, 'guild_id': guild.id})


def get_reviews_given(member):
    if type(member) is None:
        return 0
    conn, curs = load_database()
    curs.execute("SELECT reviews_given FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    reviews_given = curs.fetchone()[0]
    return reviews_given


def add_reviews_given(member, points: int = 1):
    conn, curs = load_database()
    reviews_given = get_reviews_given(member) + points
    with conn:
        curs.execute("UPDATE members SET reviews_given = (:reviews_given) WHERE member_id = (:member_id)",
                     {'reviews_given': reviews_given, 'member_id': member.id})


def get_rep(member):
    conn, curs = load_database()
    curs.execute("SELECT pos, neg FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    rep = curs.fetchone()
    return rep


def add_pos(member, points: int = 1):
    conn, curs = load_database()
    curs.execute("SELECT pos FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    total_pos = int(curs.fetchone()[0]) + points
    with conn:
        curs.execute("UPDATE members SET pos = (:pos) WHERE member_id = (:member_id)",
                     {'pos': total_pos, 'member_id': member.id})


def sub_pos(member, points):
    conn, curs = load_database()
    curs.execute("SELECT pos FROM members WHERE member_id = (:member_id)",
                 {'member_id': member.id})
    total_pos = int(curs.fetchone()[0]) - points
    if total_pos < 1:
        total_pos = 0
    with conn:
        curs.execute("UPDATE members SET pos = (:pos) WHERE member_id = (:member_id)",
                     {'pos': total_pos, 'member_id': member.id})


def add_neg(member, points: int = 1):
    conn, curs = load_database()
    curs.execute("SELECT neg FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    total_neg = int(curs.fetchone()[0]) + points
    with conn:
        curs.execute("UPDATE members SET neg = (:neg) WHERE member_id = (:member_id)",
                     {'neg': total_neg, 'member_id': member.id})


def sub_neg(member, points):
    conn, curs = load_database()
    curs.execute("SELECT neg FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    total_neg = int(curs.fetchone()[0]) - points
    if total_neg < 1:
        total_neg = 0
    with conn:
        curs.execute("UPDATE members SET neg = (:neg) WHERE member_id = (:member_id)",
                     {'neg': total_neg, 'member_id': member.id})


def reset(member):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE members SET neg = (:neg), pos = (:pos) WHERE member_id = (:member_id)",
                     {'neg': 0, 'pos': 0, 'member_id': member.id})


async def rep_too_soon(message):
    conn, curs = load_database()
    curs.execute("SELECT last_rep FROM members WHERE member_id = (:member_id)", {'member_id': message.author.id})
    last_rep = curs.fetchone()[0]
    if last_rep is not None:
        remaining_time = int(time.time() - last_rep)
        if remaining_time < 180:
            await message.channel.send(f'{message.author.nick}, you must wait {180 - remaining_time} seconds to give karma again.')
            return True
        return False


def add_review(member, author, message):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE members SET last_reviewer = (:last_reviewer), last_review = (:last_review) WHERE member_id = (:member_id)",
                     {'member_id': member.id, 'last_reviewer': author.id, 'last_review': message})


def get_review(member):
    conn, curs = load_database()
    curs.execute("SELECT last_reviewer, last_review FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    last_reviewer, last_review = curs.fetchone()
    return last_reviewer, last_review


def update_rep_timer(member):
    conn, curs = load_database()
    last_rep = int(time.time())
    with conn:
        curs.execute("UPDATE members SET last_rep = (:last_rep) WHERE member_id = (:member_id)",
                     {'last_rep': last_rep, 'member_id': member.id})


def update_autorole(guild_obj, role):
    if role is not None:
        role = role.id
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET autorole = (:autorole) WHERE guild_id = (:guild_id)",
                     {'autorole': role, 'guild_id': guild_obj.id})


def get_autorole(guild):
    conn, curs = load_database()
    curs.execute("SELECT autorole FROM guilds WHERE guild_id = (:guild_id)",
                 {'guild_id': guild.id})
    autorole = discord.utils.get(guild.roles, id=curs.fetchone()[0])
    return autorole


def force_update(ctx):
    print('Running forced update')
    conn, curs = load_database()
    curs.execute("SELECT * FROM members")
    member_ids = [member[0] for member in curs.fetchall()]

    num_members_added = 0
    for member in ctx.guild.members:
        if member.id not in member_ids:
            with conn:
                add_member(member)
                num_members_added += 1
    return num_members_added


def set_prefix(prefix, guild):
    if not in_guilds(guild):
        add_guild(guild)
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET prefix = (:prefix) WHERE guild_id = (:guild_id)",
                     {'prefix': prefix, 'guild_id': guild.id})


def get_prefix(guild):
    if not in_guilds(guild):
        add_guild(guild)
    conn, curs = load_database()
    try:
        curs.execute("SELECT prefix FROM guilds WHERE guild_id = (:guild_id)", {'guild_id': guild.id})
        prefix = curs.fetchone()[0]
        prefix_list = (prefix.lower(), prefix.upper())
    except AttributeError:
        prefix = '!'
        prefix_list = (prefix.lower(), prefix.upper())
    return prefix_list


def set_spam(channel, guild):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET spam = (:spam) WHERE guild_id = (:guild_id)",
                     {'spam': channel.id, 'guild_id': guild.id})


def set_review_channel(channel, guild):
    conn, curs = load_database()
    with conn:
        curs.execute("UPDATE guilds SET review = (:review) WHERE guild_id = (:guild_id)",
                     {'review': channel.id, 'guild_id': guild.id})


def get_review_channel(guild):
    conn, curs = load_database()
    curs.execute("SELECT review FROM guilds WHERE guild_id = (:guild_id)",
                 {'guild_id': guild.id})
    channel_id = curs.fetchone()[0]
    if channel_id is None:
        review = guild.system_channel
    else:
        review = discord.utils.get(guild.channels, id=channel_id)
    return review


def get_spam(guild):
    try:
        conn, curs = load_database()
        curs.execute("SELECT spam FROM guilds WHERE guild_id = (:guild_id)",
                     {'guild_id': guild.id})
        channel_id = curs.fetchone()[0]
        if channel_id is None:
            spam = guild.system_channel
        else:
            spam = discord.utils.get(guild.channels, id=channel_id)
        return spam
    except AttributeError:
        print(str(datetime.now()) + ': An error occurred when getting spam')
        return False


def get_karma(member):
    conn, curs = load_database()
    curs.execute("SELECT karma FROM members WHERE member_id = (:member_id)",
                 {'member_id': member.id})
    karma = curs.fetchone()[0]
    return karma


async def karma_too_soon(message):
    conn, curs = load_database()
    curs.execute("SELECT last_karma FROM members WHERE member_id = (:member_id)", {'member_id': message.author.id})
    last_karma = curs.fetchone()[0]
    if last_karma is not None:
        remaining_time = int(time.time() - last_karma)
        if remaining_time < 180:
            msg = f'{message.author.display_name}, you must wait {180 - remaining_time} seconds to give karma again.'
            await message.channel.send(embed=tools.single_embed(msg))
            return True
        return False


def update_karma_timer(member):
    conn, curs = load_database()
    last_karma = int(time.time())
    with conn:
        curs.execute("UPDATE members SET last_karma = (:last_karma) WHERE member_id = (:member_id)",
                     {'last_karma': last_karma, 'member_id': member.id})


def add_karma(member, points):
    conn, curs = load_database()
    curs.execute("SELECT karma FROM members WHERE member_id = (:member_id)", {'member_id': member.id})
    total_karma = int(curs.fetchone()[0]) + points
    with conn:
        curs.execute("UPDATE members SET karma = (:karma) WHERE member_id = (:member_id)",
                     {'karma': total_karma, 'member_id': member.id})
