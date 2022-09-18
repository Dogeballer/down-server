import datetime
import json
import time
import requests
import hashlib


def pity_header(userName, userPwd):
    url = 'http://121.5.2.74'
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }
    payload = {
        "username": userName,
        "password": userPwd,
    }
    r = requests.post(url=url + '/auth/login', data=json.dumps(payload), headers=headers)
    # print(r.text)
    access_token = r.json()['data']['token']
    header_str = json.dumps({'token':access_token})
    return header_str
    
# print(pity_header('tester','tester'))