#!/usr/bin/python3
import logging
import sqlite3
import requests
import asyncio
import discord
from discord.ext import commands,tasks
import json
import time
import os
from dotenv import load_dotenv

appName = 'couponTracker'

# enable logging
logger = logging.getLogger(appName)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# file logging output
file_handler = logging.FileHandler(f"logs/{appName}.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# add a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

load_dotenv()
#sqlite_data = os.environ.get('SQLITE_DATA')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')
test_user = os.environ.get('TEST_USER')
sqlite_data = 'data/userdata-dev.db'

intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(intents=intents,command_prefix='!')

testData = {'code': 200, 'msg': 'OK', 'data': {'uid': 565633, 'data': [{'uid': 565633, 'post_type': 'idle0418', 'message': 'mail_title_09', 'item_type': 'Gacha_Weapon_30', 'item_idx': 0, 'item_count': 1}, {'uid': 565633, 'post_type': 'idle0418', 'message': 'mail_title_09', 'item_type': 'Gacha_Companion_0', 'item_idx': 0, 'item_count': 1}]}}

conn = sqlite3.connect(sqlite_data)
cursor = conn.cursor()

def couponCheck(user, coupon):
    couponUrl = 'https://berserker.cookappsgames.com/berserker_web/coupon/reward'
    couponRequest = { 'nickname': user, 'coupon': coupon }
    response = requests.post(couponUrl, json=couponRequest)
    jsonData = response.json()
    return(jsonData) 

def commit():
    conn.commit()

async def checkCoupons():
    while True:
        try:
            cursor.execute("SELECT users.discordId, coupons.coupon, users.inGameName, coupons.epochTime FROM coupons JOIN users ON coupons.discordId = users.discordId")
            rows = cursor.fetchall()
            for row in rows:
                discordId, coupon, username, epochTime = row
                if epochTime is None:
                    logger.info(f"Checking rewards for {username}:{coupon}")
                    epochTime = round(time.time())
                    jsonData = couponCheck(username, coupon)
                    if jsonData['code'] == 200:
                        cursor.execute("UPDATE coupons SET epochTime = ?, jsonData = ? where discordId = ? and coupon = ?", (int(epochTime), json.dumps(jsonData), int(discordId), coupon))
                        conn.commit()
                    else:
                        cursor.execute("UPDATE coupons SET epochTime = ?, jsonData = ? where discordId = ? and coupon = ?", (int(epochTime), json.dumps(jsonData), int(discordId), coupon))
                        conn.commit()
        except Exception as e:
            logger.error(f"Encountered an error: {e}")
        await asyncio.sleep(5) 

@bot.event
async def on_ready():
    # debug, info, warning, error, critical
    logger.info("Booting...")
    bot.loop.create_task(checkCoupons())
    logger.info("Boot complete.")


@bot.command(name='coupon')
async def track(ctx, coupon):
    response = None
    logger.info(f"{ctx.author.name} has supplied coupon: {coupon}")
    # Check to see if the coupon works
    if coupon == 'test':
        logger.info("Using test data.")
        jsonData = testData
        response = requests.Response()
        response.status_code = 200
    else:
        jsonData = couponCheck('abec', coupon)

    logger.debug(f"API Response: {response.status_code}")
    logger.debug(f"JSON Data:")
    logger.debug(json.dumps(jsonData))
    logger.debug(f"---end---")
    
    if response.status_code == 200:
        if jsonData['code'] == 200:
            cursor.execute("select discordId from users;")
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute("INSERT OR IGNORE INTO coupons (discordId, coupon) VALUES (?, ?)", (row[0], coupon))
                if cursor.rowcount == 0:
                    logger.info(f"Entry already exists for {row[0]}:{coupon}")
                else:
                    logger.info(f"Adding entry for {row[0]}:{coupon}")

            conn.commit()
            cursor.close()
            conn.close()
            await ctx.send(f"Running '{coupon}' for all users.")
    else:
        await ctx.send("Coupon has already been run for all users.")
    

bot.run(client_secret)
