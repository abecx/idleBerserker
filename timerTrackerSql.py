#!/usr/bin/python3
import logging
import sqlite3
import asyncio
import discord
from discord.ext import commands,tasks
import json
import time
import os
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
sqlite_data = os.environ.get('SQLITE_DATA')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(intents=intents,command_prefix='!')

async def checkTimers():
    gateTimers = {
        'debug': { 'normal': 10, 'boost': 2 },
        'uniqueGate': { 'normal': 10800, 'boost': 3600 },
        'epicGate': { 'normal': 18000, 'boost': 10800 },
        'legendaryGate': { 'normal': 32400, 'boost': 25200 },
        'mythicGate': { 'normal': 72000, 'boost': 64800 }
    }

    while True:
        conn = sqlite3.connect(sqlite_data)
        cursor = conn.cursor()
        cursor.execute("SELECT timers.discordId, users.discordName as discordName, timers.timerName, timers.startTime, timers.alert, timers.notify, timers.boost, timers.notifyId from timers JOIN users ON timers.discordId = users.discordId where users.tracking = 1")
        rows = cursor.fetchall()
        for row in rows:
            discordId, discordName, timerName, startTime, alert, notify, boost, notifyId = row
            logger.debug(f"Checking timer: {discordName}: {timerName}")
            if gateTimers[timerName]:
                timeKey = 'normal' if boost is False else 'boost'
                if gateTimers[timerName][timeKey] < round(time.time()) - startTime:
                    logger.debug(f"{timerName} for {discordName}, triggering alert.")
                    cursor.execute('UPDATE timers SET alert = ? WHERE discordId = ? AND timerName = ?', (True, discordId, timerName))
                    if notify == 0: 
                        sendMessage = bot.get_user(discordId)
                        messageResponse = await sendMessage.send(f'{timerName} has completed. React with :thumbsup: for normal or :fire: for boosted to start a new timer.')
                        cursor.execute('UPDATE timers SET notify = ?, notifyId = ? WHERE discordId = ? AND timerName = ?', (True, messageResponse.id, discordId, timerName))
                    else:
                        msgUser = bot.get_user(discordId)
                        message = await msgUser.fetch_message(notifyId)
                        for reaction in message.reactions:
                            if reaction.emoji == '\N{THUMBS UP SIGN}':
                                logger.debug(f"Removing message: {notifyId} / {discordName}")
                                await message.delete()
                                logger.info(f"Resetting {timerName} for {discordName}.")
                                cursor.execute('UPDATE timers SET notify = ?, startTime = ?, alert = ?, boost = ?, notifyId = NULL WHERE discordId = ? AND timerName = ?', (False, round(time.time()), False, False, discordId, timerName))
                            if reaction.emoji == '\U0001F525':
                                logger.debug(f"Removing message: {notifyId} / {discordName}")
                                await message.delete()
                                logger.info(f"Resetting {timerName} for {discordName}.")
                                cursor.execute('UPDATE timers SET notify = ?, startTime = ?, alert = ?, boost = ?, notifyId = NULL WHERE discordId = ? AND timerName = ?', (False, round(time.time()), False, True, discordId, timerName))
        
        logger.debug("Committing sql changes.")
        conn.commit()
        conn.close()
            
        await asyncio.sleep(5)


@bot.event
async def on_ready():
    # debug, info, warning, error, critical
    logger.info("Booting...")
    logger.info("Starting checkTimers async loop.")
    bot.loop.create_task(checkTimers())
    logger.info("Boot complete.")


@bot.command(name='track')
async def track(ctx, action=None):
    discordId = ctx.author.id
    discordName = ctx.author.name
    userTimers = {
        'debug': {'startTime': 0, 'alert': False, 'notify': False, 'boost': True},
        'uniqueGate': {'startTime': 0, 'alert': False, 'notify': False, 'boost': False},
        'epicGate': {'startTime': 0, 'alert': False, 'notify': False, 'boost': False},
        'legendaryGate': {'startTime': 0, 'alert': False, 'notify': False, 'boost': False},
        'mythicGate': {'startTime': 0, 'alert': False, 'notify': False, 'boost': False}
    }

    conn = sqlite3.connect(sqlite_data)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users ( discordId INTEGER PRIMARY KEY, discordName TEXT, tracking INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS timers (discordId INTEGER REFERENCES users(discordId), timerName TEXT, startTime INTEGER, alert INTEGER, notify INTEGER, boost INTEGER, notifyId INTEGER, PRIMARY KEY(discordId, timerName))")

    if action == 'remove':
        logger.info("Disabling tracking for {discordName}")
        message = "Dimension Gate tracking has been disabled."
        trackValue = 0
        cursor.execute("INSERT INTO users (discordId, discordName, tracking) VALUES (?, ?, ?) ON CONFLICT (discordId) DO UPDATE SET tracking = ?", (discordId, discordName, trackValue, trackValue))
        conn.commit()
        conn.close()
	
    if action is None:
        trackValue = 1
        logger.info(f"Attempting to find records for {discordName}.")
        cursor.execute("SELECT discordName from users WHERE discordId=? and tracking = ?", (discordId,1))
        result = cursor.fetchone()
	
        if not result:
            logger.info(f"Adding {discordName} to the database.")
            cursor.execute("INSERT INTO users (discordId, discordName, tracking) VALUES (?, ?, ?) ON CONFLICT (discordId) DO UPDATE SET tracking = ?", (discordId, discordName, trackValue, trackValue))
            for timerName in userTimers:
                logger.info(f"Adding {timerName} with default for {discordName}")
                cursor.execute("INSERT INTO timers (discordId, timerName, startTime, alert, notify, boost, notifyId) VALUES (?, ?, ?, ?, ?, ?, NULL) ON CONFLICT (discordId) DO UPDATE SET startTime = excluded.startTime, alert = excluded.alert, notify = excluded.notify, boost = excluded.boost, notifyId = NULL", (discordId, timerName, 0, False, False, False))
            message = "Dimensional Gate Tracking has been enabled."
        else:
            logger.info(f"{discordName} is already being tracked, no action taken.")
            message = "Dimensional Gates are already being tracked for your user."

        conn.commit()
        conn.close()


    await ctx.author.send(message)

    

bot.run(client_secret)
