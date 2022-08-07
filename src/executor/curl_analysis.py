import copy

import requests
from torequests.utils import curlparse
import urllib.parse as urlparse

curl = '''curl 'https://iot.cntepower.com/api/cnte-iot-data/log/list?did=HES00100100001B721902201&mid=MCU-1&startTime=2022-07-30+17:03:57&endTime=2022-08-06+17:03:57&current=1&size=10&descs=reqTime' \
  -H 'authority: iot.cntepower.com' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: zh-CN,zh;q=0.9' \
  -H 'authorization: Basic Y250ZS1pb3Q6N2MyYjE5NzE4ZDkzNGQxY2FmZWNmOTQyN2VmMDIxMGE=' \
  -H 'blade-auth: bearer eyJ0eXAiOiJKc29uV2ViVG9rZW4iLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJpc3N1c2VyIiwiYXVkIjoiYXVkaWVuY2UiLCJ0ZW5hbnRfaWQiOiIwMDAwMDAiLCJ1c2VyX25hbWUiOiIxNTcwNTk1MDE1NyIsInRva2VuX3R5cGUiOiJhY2Nlc3NfdG9rZW4iLCJhcHBfcm9sZV9yZWxhdGlvbiI6IntcImNudGUtaW90XCI6W3tcImlkXCI6XCJcIixcImtleVwiOlwi54mp6IGU5bmz5Y-w6K6-5aSH5p-l55yL5Lq65ZGYXCIsXCJ2YWx1ZVwiOlwiMTU1MzkxOTg5NTA4NTQyNDY0MlwifV0sXCJjbnRlLWRhdGFcIjpbe1wiaWRcIjpcIlwiLFwia2V5XCI6XCLova_ku7bmtYvor5VcIixcInZhbHVlXCI6XCIxNTA2ODc4NDc3OTIzOTc5MjY1XCJ9XSxcImNudGUtbW1zXCI6W3tcImlkXCI6XCJcIixcImtleVwiOlwi6L2v5Lu25rWL6K-VXCIsXCJ2YWx1ZVwiOlwiMTUwNjg3ODQ3NzkyMzk3OTI2NVwifV0sXCJjbnRlLW9tc1wiOlt7XCJpZFwiOlwiXCIsXCJrZXlcIjpcIui9r-S7tua1i-ivlVwiLFwidmFsdWVcIjpcIjE1MDY4Nzg0Nzc5MjM5NzkyNjVcIn1dfSIsInJvbGVfbmFtZSI6Iui9r-S7tua1i-ivlSznianogZTlubPlj7Dorr7lpIfmn6XnnIvkurrlkZgiLCJ1c2VyX2lkIjoiMTU1NTAxODE1Mzc4MDg3OTM2MSIsInJvbGVfaWQiOiIxNTA2ODc4NDc3OTIzOTc5MjY1LDE1NTM5MTk4OTUwODU0MjQ2NDIiLCJNRVJDSEFOVF9TVEFURSI6IiIsIm9hdXRoX2lkIjoiIiwiYWNjb3VudCI6IjE1NzA1OTUwMTU3IiwiTUVSQ0hBTlRfVFlQRSI6Ii0xIiwiY2xpZW50X2lkIjoiY250ZS1pb3QiLCJleHAiOjE2NTk3Nzk0MTcsIm5iZiI6MTY1OTc3NTgxN30.sdtN5iftOewkGpxa6iVmQLJ9-n2xIBt3qrh_N1wosGQ' \
  -H 'cookie: x-access-userInfo={%22tokenType%22:%22bearer%22%2C%22userId%22:%221555018153780879361%22%2C%22tenantId%22:%22000000%22%2C%22oauthId%22:%22%22%2C%22avatar%22:%22https://charge.cntepower.com/group1/M00/00/00/CmSkAGKBxPGAago7AAB6DNXQ4Ks568.png%22%2C%22authority%22:%22%E8%BD%AF%E4%BB%B6%E6%B5%8B%E8%AF%95%2C%E7%89%A9%E8%81%94%E5%B9%B3%E5%8F%B0%E8%AE%BE%E5%A4%87%E6%9F%A5%E7%9C%8B%E4%BA%BA%E5%91%98%22%2C%22userName%22:%22%E5%BE%90%E5%87%A1%22%2C%22account%22:%2215705950157%22%2C%22expiresIn%22:3600%2C%22license%22:%22powered%20by%20CNTE%22%2C%22merchantId%22:%22%22%2C%22merchantType%22:%22-1%22%2C%22vendorId%22:%22%22}; x-access-token=eyJ0eXAiOiJKc29uV2ViVG9rZW4iLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJpc3N1c2VyIiwiYXVkIjoiYXVkaWVuY2UiLCJ0ZW5hbnRfaWQiOiIwMDAwMDAiLCJ1c2VyX25hbWUiOiIxNTcwNTk1MDE1NyIsInRva2VuX3R5cGUiOiJhY2Nlc3NfdG9rZW4iLCJhcHBfcm9sZV9yZWxhdGlvbiI6IntcImNudGUtaW90XCI6W3tcImlkXCI6XCJcIixcImtleVwiOlwi54mp6IGU5bmz5Y-w6K6-5aSH5p-l55yL5Lq65ZGYXCIsXCJ2YWx1ZVwiOlwiMTU1MzkxOTg5NTA4NTQyNDY0MlwifV0sXCJjbnRlLWRhdGFcIjpbe1wiaWRcIjpcIlwiLFwia2V5XCI6XCLova_ku7bmtYvor5VcIixcInZhbHVlXCI6XCIxNTA2ODc4NDc3OTIzOTc5MjY1XCJ9XSxcImNudGUtbW1zXCI6W3tcImlkXCI6XCJcIixcImtleVwiOlwi6L2v5Lu25rWL6K-VXCIsXCJ2YWx1ZVwiOlwiMTUwNjg3ODQ3NzkyMzk3OTI2NVwifV0sXCJjbnRlLW9tc1wiOlt7XCJpZFwiOlwiXCIsXCJrZXlcIjpcIui9r-S7tua1i-ivlVwiLFwidmFsdWVcIjpcIjE1MDY4Nzg0Nzc5MjM5NzkyNjVcIn1dfSIsInJvbGVfbmFtZSI6Iui9r-S7tua1i-ivlSznianogZTlubPlj7Dorr7lpIfmn6XnnIvkurrlkZgiLCJ1c2VyX2lkIjoiMTU1NTAxODE1Mzc4MDg3OTM2MSIsInJvbGVfaWQiOiIxNTA2ODc4NDc3OTIzOTc5MjY1LDE1NTM5MTk4OTUwODU0MjQ2NDIiLCJNRVJDSEFOVF9TVEFURSI6IiIsIm9hdXRoX2lkIjoiIiwiYWNjb3VudCI6IjE1NzA1OTUwMTU3IiwiTUVSQ0hBTlRfVFlQRSI6Ii0xIiwiY2xpZW50X2lkIjoiY250ZS1pb3QiLCJleHAiOjE2NTk3Nzk0MTcsIm5iZiI6MTY1OTc3NTgxN30.sdtN5iftOewkGpxa6iVmQLJ9-n2xIBt3qrh_N1wosGQ; x-access-refreshToken=eyJ0eXAiOiJKc29uV2ViVG9rZW4iLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJpc3N1c2VyIiwiYXVkIjoiYXVkaWVuY2UiLCJ1c2VyX2lkIjoiMTU1NTAxODE1Mzc4MDg3OTM2MSIsInRva2VuX3R5cGUiOiJyZWZyZXNoX3Rva2VuIiwiY2xpZW50X2lkIjoiY250ZS1pb3QiLCJleHAiOjE2NjAzODA2MTcsIm5iZiI6MTY1OTc3NTgxN30.rgSpdYIOMGYQx3FCFgRvT_fkez0mxPjeWjz4GX54CPA; x-access-tokenExp=1659779417202' \
  -H 'referer: https://iot.cntepower.com/device/device?cGFnZT1kZXRhaWwmZGV2aWNlPSU3QiUyMmlkJTIyJTNBJTIyMTUxNTg3NDU5MTk4MjkwNzM5MyUyMiU3RCZ0YWJOYW1lPTQ' \
  -H 'sec-ch-ua: " Not;A Brand";v="99", "Microsoft Edge";v="103", "Chromium";v="103"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36 Edg/103.0.1264.77' \
  --compressed'''


def url_parse(url):
    parsed = urlparse.urlparse(url)
    query = urlparse.parse_qs(parsed.query)
    query = {k: v[0] for k, v in query.items()}
    return query


if __name__ == '__main__':
    request_info = curlparse(curl)
    full_url = request_info.get('url', None)
    url = full_url.split('?')[0]
    full_request_info = copy.deepcopy(request_info)
    full_request_info["full_url"] = full_url
    query = url_parse(full_url)
    full_request_info["url"] = url
    full_request_info["query"] = query
    print(request_info)
    r = requests.request(**request_info)
    # print(r.cookies.get_dict())
    # print(r.json())
    print(r.text)
    print(full_request_info)
