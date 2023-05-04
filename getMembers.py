#!/usr/bin/python3
import discord
import sqlite3
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# enable logging
logger = logging.getLogger('dgTracker')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# file logging output
file_handler = logging.FileHandler('logs/timerTracker.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# add a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

load_dotenv()
memberFile = os.environ.get('MEMBER_FILE')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = int(os.environ.get('SERVER_ID'))
channel_id = int(os.environ.get('CHANNEL_ID'))
client_id = os.environ.get('CLIENT_ID')
sqlite_data = 'data/userdata-dev.db'

intents = discord.Intents.all()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(server_id)  # Replace with the ID of the guild
    members = guild.members
    conn = sqlite3.connect(sqlite_data)
    cursor = conn.cursor()
    for member in members:
        roles = [role.name for role in member.roles]
        if 'SSR' in roles or 'Chaos' in roles:
            if member.nick is None:
                name = f'{member.name}'
            else:
                name = f'{member.nick}'
            ign = name.split(" ", 1)[0]
            if 'SSR' in roles:
                guild = 'SSR'
            elif 'Chaos' in roles:
                guild = 'Chaos'
            else:
                guild = 'unknown'
            inGameName = name.split(" ", 1)[0]

            cursor.execute("""
                INSERT INTO users (discordId, discordName, tracking, guild, active, discordNick, inGameName) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (discordId) DO UPDATE SET
                    discordName = excluded.discordName,
                    guild = excluded.guild,
                    active = excluded.active,
                    discordNick = excluded.discordNick,
                    inGameName = excluded.inGameName
            """, (member.id, member.name, '0', guild, 1, member.nick, inGameName))
     
            logger.info(f"{member.name}\t{member.nick}\t{ign}\t{guild}")
    conn.commit()
    cursor.close()
    await client.close()


client.run(client_secret)
