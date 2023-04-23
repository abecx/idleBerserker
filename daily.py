#!/usr/bin/python3
import requests
import json
from datetime import datetime
import pytz
# https://berserker.cookappsgames.com/berserker_web/coupon

url = 'https://berserker.cookappsgames.com/berserker_web/coupon/reward'
memberFile = 'members.txt'

# Codes seem to go into the wild at midnight South Korea time.
tz = pytz.timezone('Asia/Seoul')

couponCodePrefix = [ 'idle', 'update' ]
couponCodeSuffix = [ '{:02d}{:02d}'.format(datetime.now(tz).month,datetime.now(tz).day) ]

with open(memberFile) as members:
    userlist = [line.rstrip('\n') for line in members]


for nickname in userlist:
    for prefix in couponCodePrefix:
        for suffix in couponCodeSuffix:
            code = prefix + suffix

            mR = { 
                'nickname': nickname,
                'coupon': code
            }
            try:
                r = requests.post(url, json=mR)
                r.raise_for_status()
                print(f'{nickname}\t{code}\t{r.json()}')

            except Exception as err:
                print(f'{nickname} {code} failed: {err}')

