import datetime
import hashlib
import json
import time

from redis import StrictRedis
import requests
import django.utils.timezone as timezone

from interfaces.models import UacTokenRecord


class GetToken:
    def __init__(self, uac_item):
        self.connection_info = {
            "host": "192.168.1.70",
            "port": 6379,
            "db": 5
        }
        # self.uac_url = 'http://192.168.1.70:10120' # 开发环境
        # self.uac_url = 'http://192.168.6.159:7071' # 测试环境
        # self.uac_url = 'http://192.168.5.126:7074'  # 预生产环境
        uac_obj = {
            # 0: 'http://192.168.6.159:7071', # 测试环境
            0: 'http://uac-server.test-app.cecdata.com',  # 测试环境
            # 1: 'http://192.168.1.70:10120',  # 开发环境
            1: 'http://uac-server.dev-app.cecdata.com',  # 开发环境
            # 2: 'http://192.168.5.126:7074',  # 预生产环境
            2: 'http://uac-server.cecdata.com',  # 预生产环境
            3: 'http://192.168.1.82:10123',  # HMO-UAC测试环境
            4: 'http://192.168.6.140:7071',  # HMO-UAC开发环境
        }
        self.uac_url = uac_obj[uac_item]
        self.uac_item = uac_item

    def access_token_get(self):
        r = requests.get(self.uac_url + '/V1.0/uac/captcha')
        captcha_id = r.json()['data']['captchaId']
        redis_key = "CAPTCHA_" + captcha_id
        redis = StrictRedis(host=self.connection_info['host'], port=self.connection_info['port'],
                            db=self.connection_info['db'])
        captcha_code = str(redis.get(redis_key), encoding='utf-8')
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
        }
        payload = {
            "captchaCode": captcha_code,
            "userName": "qatestuser",
            "userPwd": "f4be326a7070a827fd09564f40293dd2",
            "captchaId": captcha_id
        }
        data = json.dumps(payload)
        r = requests.post(url=self.uac_url + '/V1.0/uac/login', data=data, headers=headers)
        login_token = r.json()['data']['loginToken']
        token_data = json.dumps({'token': login_token})
        r = requests.post(url=self.uac_url + '/V1.0/uac/access/token', data=token_data, headers=headers)
        access_token = r.json()['data']['accessToken']
        return access_token

    def uacV2_token_get(self):
        refresh_force_time = datetime.datetime.now() + datetime.timedelta(minutes=-60)
        try:
            token_record = UacTokenRecord.objects.get(uac_url=self.uac_item, token_update_time__gte=refresh_force_time)
            access_token = token_record.token
        except UacTokenRecord.DoesNotExist:
            hl = hashlib.md5()
            if self.uac_item in [0, 1, 2]:
                sid = 'ea17c588683f4763bb7535f676f1258e'
                key = '17353d5b667946759fc677424a4ddd55'
            else:
                sid = 'f3e517ad654242f0a2976fb529256ec2'
                key = 'd56362c297b140bcba1d3a6504ecf308'
            ckhTime = str(int(round(time.time() * 1000)))
            # ckhTime = 1615943903516
            # print(ckhTime)
            md5_string = "ckhSecret[%s];ckhSid[%s];ckhTime[%s];" % (key, sid, ckhTime)
            hl.update(bytes(md5_string, encoding="utf8"))
            ck = hl.hexdigest().lower()
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "ck": ck,
                "ckhSid": sid,
                "ckhTime": ckhTime
            }
            payload = {
                "userName": "qatestuser",
                "userPwd": "92d7ddd2a010c59511dc2905b7e14f64",
            }
            if self.uac_item in [0, 1, 2]:
                r = requests.post(url=self.uac_url + '/v2/api/login', data=json.dumps(payload), headers=headers)
                # print(r.text)
                access_token = r.json()['data']['token']['token']
            else:
                r = requests.post(url=self.uac_url + '/V1.0/api/login', data=json.dumps(payload), headers=headers)
                token = r.json()['data']['loginToken']
                r = requests.post(url=self.uac_url + '/V1.0/web/access/token', data=json.dumps({'token': token}),
                                  headers=headers)
                # print(r.text)
                access_token = r.json()['data']['accessToken']
            try:
                record = UacTokenRecord.objects.get(uac_url=self.uac_item)
                record.token = access_token
                record.token_update_time = timezone.now()
                record.save()
            except UacTokenRecord.DoesNotExist:
                UacTokenRecord.objects.create(uac_url=self.uac_item, token=access_token)
        return access_token


if __name__ == '__main__':
    url = 3
    token = GetToken(url).uacV2_token_get()
    print(token)
