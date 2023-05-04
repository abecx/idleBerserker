#!/usr/bin/python3
import requests
import json
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
import sqlite3


load_dotenv()
#sqlite_data = os.environ.get('SQLITE_DATA')
client_secret = os.environ.get('CLIENT_SECRET')
server_id = os.environ.get('SERVER_ID')
channel_id = os.environ.get('CHANNEL_ID')
test_user = os.environ.get('TEST_USER')
sqlite_data = 'data/userdata-dev.db'

url = 'https://berserker.cookappsgames.com/berserker_web/coupon/reward'

# Codes seem to go into the wild at midnight South Korea time.
tz = pytz.timezone('Asia/Seoul')

couponCodePrefix = [ 'idle', 'update' ]
couponCodeSuffix = [ '{:02d}{:02d}'.format(datetime.now(tz).month,datetime.now(tz).day) ]

conn = sqlite3.connect(sqlite_data)
cursor = conn.cursor()

cursor.execute("select inGameName from users;")
rowData = cursor.fetchone()
users = []
while rowData is not None:
    users.append(rowData[0])
    rowData = cursor.fetchone()


for user in users:
    for prefix in couponCodePrefix:
        for suffix in couponCodeSuffix:
            code = prefix + suffix
            mR = { 
                'nickname': user,
                'coupon': code
            }
            try:
                r = requests.post(url, json=mR)
                r.raise_for_status()
                print(f'{user}\t{code}\t{r.json()}')

            except Exception as err:
                print(f'{user} {code} failed: {err}')

