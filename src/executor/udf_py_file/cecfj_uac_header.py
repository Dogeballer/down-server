import datetime
import json
import time
import requests
import hashlib


def cecfj_uac_header(uac_item, userName, userPwd):
    uac_obj = {
        0: 'http://uac-server.test-app.cecdata.com',  # 测试环境
        1: 'http://uac-server.dev-app.cecdata.com',  # 开发环境
        2: 'http://uac-server.cecdata.com',  # 预生产环境
        3: 'http://192.168.1.82:10123',  # HMO-UAC测试环境
        4: 'http://192.168.6.140:7071',  # HMO-UAC开发环境
    }
    uac_url = uac_obj[uac_item]
    hl = hashlib.md5()
    if uac_item in [0, 1, 2]:
        sid = 'ea17c588683f4763bb7535f676f1258e'
        key = '17353d5b667946759fc677424a4ddd55'
    else:
        sid = 'f3e517ad654242f0a2976fb529256ec2'
        key = 'd56362c297b140bcba1d3a6504ecf308'
    ckhTime = str(int(round(time.time() * 1000)))
    md5_string = "ckhSecret[%s];ckhSid[%s];ckhTime[%s];" % (key, sid, ckhTime)
    hl.update(bytes(md5_string, encoding="utf8"))
    ck = hl.hexdigest().lower()
    print(ckhTime)
    print(sid)
    print(ck)
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "ck": ck,
        "ckhSid": sid,
        "ckhTime": ckhTime
    }
    payload = {
        "userName": userName,
        "userPwd": userPwd,
    }
    if uac_item in [0, 1, 2]:
        r = requests.post(url=uac_url + '/v2/api/login', data=json.dumps(payload), headers=headers)
        # print(r.text)
        access_token = r.json()['data']['token']['token']
    else:
        r = requests.post(url=uac_url + '/V1.0/api/login', data=json.dumps(payload), headers=headers)
        token = r.json()['data']['loginToken']
        r = requests.post(url=uac_url + '/V1.0/web/access/token', data=json.dumps({'token': token}),
                          headers=headers)
        # print(r.text)
        access_token = r.json()['data']['accessToken']
    header_str = json.dumps({'authorization':access_token})
    return header_str