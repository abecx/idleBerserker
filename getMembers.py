#!/usr/bin/python3
import discord
from discord.ext import commands

memberFile = 'members.txt'

memberFile = os.environ.get('MEMBER_FILE')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')
client_id = os.environ.get('CLIENT_ID')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(server_id)  # Replace with the ID of the guild
    members = guild.members
    f = open(memberFile, "w")
    for member in members:
        roles = [role.name for role in member.roles]
        if 'SSR' in roles or 'Chaos' in roles:
            if member.nick is None:
                name = f'{member.name}'
            else:
                name = f'{member.nick}'
            ign = name.split(" ", 1)[0]
            f.write(f'{ign}\n')
    f.close
    await client.close()


client.run(client_secret)
