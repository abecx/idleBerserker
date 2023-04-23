#!/usr/bin/python3
import asyncio
import discord
from discord.ext import commands,tasks
import json
from collections import defaultdict
import time
import threading
import os

userDataFile = os.environ.get('JSON_DATAFILE')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')

intents = discord.Intents.all()
intents.members = True
file_lock = threading.Lock()

bot = commands.Bot(intents=intents,command_prefix='!')

def userData(discordUserId,discordUserName):
    print('getting userdata lock')
    file_lock.acquire()
    defaultUserData = {'name': '', 'timers': {
#        'debug': {
#            'startTime': 0,
#            'alert': False,
#            'notify': False,
#            'boost': True,
#            },
        'uniqueGate': {
            'startTime': 0,
            'alert': False,
            'notify': False,
            'boost': False,
            },
        'epicGate': {
            'startTime': 0,
            'alert': False,
            'notify': False,
            'boost': False,
            },
        'legendaryGate': {
            'startTime': 0,
            'alert': False,
            'notify': False,
            'boost': False,
            },
        'mythicGate': {
            'startTime': 0,
            'alert': False,
            'notify': False,
            'boost': False,
            },
        }}

    with open(userDataFile, 'r') as f:
        data = json.load(f)

    default_dict = defaultdict(lambda: defaultUserData.copy(), data)

    if discordUserId is not False and discordUserName is not False:
        print('data passed') 
        if discordUserId not in data:
            data[discordUserId] = defaultUserData.copy()
            data[discordUserId]['name'] = discordUserName
            print(json.dumps(data))
            with open(userDataFile, 'w') as f:
                json.dump(data, f)

    file_lock.release()
    return data



def generateTimers():
    timers = {
 #   			'debug': { 'normal': 10, 'boost': 2 },
                'uniqueGate': { 'normal': 10800, 'boost': 3600 },
                'epicGate': { 'normal': 18000, 'boost': 3600 },
                'legendaryGate': { 'normal': 32400, 'boost': 25200 },
                'mythicGate': { 'normal': 72000, 'boost': 64800 }
            }
    return timers



async def dgTimers():
    await bot.wait_until_ready()
    timers = generateTimers()
    while not bot.is_closed():
        print('getting timer filelock')
        users = userData(False,False)
        file_lock.acquire()
        for timerName in timers:
            for userName in users:
                if timerName in users[userName]['timers']:
                    key = 'normal' if users[userName]['timers'][timerName]['boost'] is False else 'boost'
                    print(f'Checking timer: {users[userName]["name"]} {timerName}:{key}.')
                    timerDifference = round(time.time()) - users[userName]['timers'][timerName]['startTime']
                    if timerDifference >= timers[timerName][key]:
                        # Alert Triggered
                        users[userName]['timers'][timerName]['alert'] = not users[userName]['timers'][timerName]['alert']
                        if users[userName]['timers'][timerName]['notify'] is False:
                            print(f'Notify {userName} that {timerName} has completed')
                            msgUser = bot.get_user(int(userName))
                            message_response = await msgUser.send(f'{timerName} has completed. React with :thumbsup: for normal or :fire: for boosted to start a new timer.')
                            users[userName]['timers'][timerName]['notify'] = not users[userName]['timers'][timerName]['notify']
                            users[userName]['timers'][timerName]['notifyId'] = message_response.id
                        else:
                            print(f'Checking to see if {userName} has reacted to {timerName}.')
                            if users[userName]['timers'][timerName]['notifyId']:
                                msgUser = bot.get_user(int(userName))
                                message = await msgUser.fetch_message(int(users[userName]['timers'][timerName]['notifyId']))
                                for reaction in message.reactions:
                                    if reaction.emoji == '\N{THUMBS UP SIGN}':
                                        print("removing message")
                                        await message.delete()
                                        print(f"Reseting timer for {timerName}.")
                                        users[userName]['timers'][timerName]['notify'] = False
                                        users[userName]['timers'][timerName]['startTime'] = round(time.time())
                                        users[userName]['timers'][timerName]['alert'] = False
                                        users[userName]['timers'][timerName]['boost'] = False
                                    if reaction.emoji == '\U0001F525':
                                        print("remove message")
                                        await message.delete()
                                        print(f"Reseting timer for {timerName} with boost.")
                                        users[userName]['timers'][timerName]['notify'] = False
                                        users[userName]['timers'][timerName]['startTime'] = round(time.time())
                                        users[userName]['timers'][timerName]['alert'] = False
                                        users[userName]['timers'][timerName]['boost'] = True

                else:
                    print(f"\tBROKEN: timerName does not exist in users.")
        with open(userDataFile, 'w') as f:
            json.dump(users,f)
        file_lock.release()
        await asyncio.sleep(5)


@bot.event
async def on_ready():
    bot.loop.create_task(dgTimers())
    print('Bot is ready.')

@bot.command()
async def startTimers(ctx):
    print("starting timers!")
    await ctx.send('bg task started...')

@bot.command(name='track')
async def track(ctx):
    if ctx.author == bot.user:
        # ignore if the bot accidently created the timer
        return

    users = userData(ctx.author.id, ctx.author.name) 

    if ctx.author.name in users:
        message = f'{ctx.author.name} is already being tracked.'

    else:
        message = f'Starting tracking for {ctx.author.name}.'


    await ctx.author.send(message)


bot.run(client_secret)

