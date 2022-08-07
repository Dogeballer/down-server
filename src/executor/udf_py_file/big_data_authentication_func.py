import requests
import jsonpath

if __name__ == '__main__':
    r = requests.session()
    request_info = {'url': 'http://bdpunify.test.cechealth.cn/commonuser/auth',
                    'headers': {'Proxy-Connection': 'keep-alive', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache',
                                'Accept': 'application/json, text/plain, */*', 'Authorization': 'Bearer undefined',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
                                'Content-Type': 'application/json;charset=UTF-8',
                                'Origin': 'http://bdpunify.test.cechealth.cn',
                                'Referer': 'http://bdpunify.test.cechealth.cn/login',
                                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                                'Cookie': 'ID=0; HOST_NAME=test.cechealth.cn'},
                    'data': b'{"account":"xufan","password":"etl_123456"}',
                    'method': 'post'}
    response = r.request(**request_info)
    # print(response.text)
    result = response.json()
    cookie = response.cookies
    print(cookie)
    token = jsonpath.jsonpath(result, '$.data.token')
    if token:
        token = "Bearer " + token[0]
    else:
        token = ''
    r.headers.update({'Authorization': token})
    request_info = {'url': 'http://etl.test.cechealth.cn/etlapi/scheduler/task/workbench/qeury/types',
                    'method': 'get'}
    response = r.request(**request_info)
    print(response.text)
