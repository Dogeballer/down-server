import os
import time
from datetime import datetime
import requests
from automated_test_platform.settings import BASE_DIR
from projects.models import *
from interfaces.models import *
from usecases.models import *
import pytest
import json
import jsonpath


with open(os.path.join(BASE_DIR, 'executor/') + "test_data.json", 'r') as load_file:
    test_data = json.load(load_file)
    print(test_data)
    load_file.close()

use_case_list = UseCases.objects.filter(pk__in=test_data['useCaseList'])
taskLog = TaskLog.objects.get(pk=test_data['taskLog'])
environment = Environment.objects.get(pk=test_data['environmentId'])


@pytest.mark.parametrize('use_case', use_case_list)
def test_interfaces(use_case):
    global_params = use_case.global_params
    use_case_callback_params = use_case.params
    case_steps = CaseSteps.objects.filter(use_case=use_case).order_by('sort')
    case_log = CaseLog.objects.create(use_case=use_case,
                                      global_parameter=global_params,
                                      callback_parameter=use_case_callback_params,
                                      execute_status=2,
                                      success_count=0,
                                      failed_count=0,
                                      task_log=taskLog)
    if global_params:
        global_params_dict = json.loads(use_case.global_params)
    else:
        global_params_dict = {}
    if use_case_callback_params:
        use_case_callback_params_dict = json.loads(use_case.params)
    else:
        use_case_callback_params_dict = {}
    for case_step in case_steps:
        if case_step.type == 0:
            interface = case_step.case_interface
            method = interface.method
            path = interface.path
            url = str(environment.url) + str(path)
            interface_callback_params = InterfaceCallBackParams.objects.filter(return_interface=interface)
            # params = json.loads(case_step.param)
            params = case_step.param
            params = dispose_params(global_params_dict, params)
            params = json.loads(dispose_params(use_case_callback_params_dict, params))
            body = case_step.body
            body = dispose_params(global_params_dict, body)
            body = dispose_params(use_case_callback_params_dict, body)
            path_param = {}
            query_param = {}
            url_query_param = '?'
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "authorization": "683cbaf5089fd559ca5ec81c81385a24"
            }
            test_param = []
            for param in params:
                if param['param_in'].lower() == 'path':
                    path_param['name'] = param['name']
                    path_param['value'] = param['value']
                    test_param.append(param)
                elif param['param_in'].lower() == 'query':
                    query_param[param['name']] = param['value']
                    url_query_param += param['name'] + '=' + param['value'] + '&'
                    test_param.append(param)
                elif param['param_in'].lower() == 'header':
                    headers[param['name']] = param['value']
            request_body = json.loads(body)
            request_body = json.dumps(request_body)
            test_param = json.dumps(test_param)
            if url.find('{') != -1:
                url = url.replace('{' + path_param['name'] + '}', str(path_param['value']))
            if len(url_query_param) > 1:
                if url_query_param.rfind('&') != -1:
                    url_query_param = url_query_param[:url_query_param.rfind('&')]
                query_url = url + url_query_param
            else:
                query_url = url
            case_step_log = CaseStepLog.objects.create(request_url=query_url, param=test_param, body=request_body,
                                                       case_log=case_log, case_step=case_step)
            msg, response_code, response_headers, response_body, response_time = requests_func(method,
                                                                                               url,
                                                                                               query_param,
                                                                                               headers,
                                                                                               request_body)
            for callback_param in interface_callback_params:
                callback_param_jsonpath = callback_param.json_path
                callback_param_name = callback_param.param_name
                try:
                    callback_param_value = jsonpath.jsonpath(response_body, callback_param_jsonpath)[0]
                except:
                    callback_param_value = ''
                use_case_callback_params_dict[callback_param_name] = callback_param_value
                case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
                case_log.save()
            case_step_log.step_body = response_body
            # print(response_body)
            checkout_list = CaseAssert.objects.filter(case_step=case_step)
            checkout_result = []
            for item in checkout_list:
                checkout = {}
                if item.type_from == 0:
                    value_jsonpath = item.value_statement
                    verify_value = item.verify_value
                    assert_type = item.assert_type
                    try:
                        value = jsonpath.jsonpath(response_body, value_jsonpath)[0]
                    except:
                        value = ''
                    assert_result, message, verify_type = assert_func(assert_type, str(value), verify_value)
                    checkout['assert_type'] = verify_type
                    checkout['value_statement'] = value_jsonpath
                    checkout['type_from'] = '消息体校验'
                    checkout['result'] = assert_result
                    checkout['msg'] = message
                    print(message)
                elif item.type_from == 1:
                    assert_type = item.assert_type
                    verify_value = item.verify_value
                    assert_result, message, verify_type = assert_func(assert_type, str(response_code), verify_value)
                    checkout['assert_type'] = verify_type
                    checkout['value_statement'] = ''
                    checkout['type_from'] = '消息体校验'
                    checkout['result'] = assert_result
                    checkout['msg'] = message
                    print(message)
                elif item.type_from == 2:
                    print(1)
                checkout_result.append(checkout)
            case_step_log.execute_status = 1
            for checkout in checkout_result:
                if not checkout['result']:
                    case_step_log.execute_status = 0
            case_step_log.assert_result = json.dumps(checkout_result)
            case_step_log.save()
        elif case_step.type == 1:
            wait_time = json.loads(case_step.body)['time']
            time.sleep(wait_time)
            CaseStepLog.objects.create(body=case_step.body, execute_status=1, case_log=case_log, case_step=case_step)
    count_step_log = CaseStepLog.objects.filter(case_log=case_log).count()
    count_failed_step = CaseStepLog.objects.filter(case_log=case_log, execute_status=0).count()
    count_success_step = count_step_log - count_failed_step
    case_log.success_count = count_success_step
    case_log.failed_count = count_failed_step
    if count_success_step != count_step_log:
        case_log.execute_status = 0
    else:
        case_log.execute_status = 1
    end_time = datetime.now()
    start_time = case_log.start_time
    case_log.end_time = end_time
    spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
    case_log.spend_time = spend_time
    case_log.save()


def requests_func(method, url, query_param, headers, payload):
    try:
        method = method.lower()
        if method == 'get':
            r = requests.get(url, headers=headers, params=query_param)
        elif method == 'post':
            r = requests.post(url, headers=headers, data=payload)
        elif method == 'put':
            r = requests.put(url, headers=headers, data=payload)
        elif method == 'delete':
            r = requests.delete(url, headers=headers, data=payload)
        else:
            r = {}
        try:
            response_code = r.status_code
            response_headers = r.headers
            response_body = r.json()
            response_time = round(r.elapsed.total_seconds() * 1000, 4)
            msg = '返回成功'
        except:
            response_code = -1
            response_headers = -1
            response_body = -1
            response_time = -1
            msg = "服务器返回异常"
    except Exception as e:
        response_code = -1
        response_headers = -1
        response_body = -1
        response_time = -1
        msg = "服务器返回异常，error：%s" % e
        print(msg)
    return msg, response_code, response_headers, response_body, response_time


def assert_func(assert_type, value, verify_value):
    verify_result = True
    msg = '校验成功'
    verify_type = ''
    if assert_type == 0:
        if pytest.assume(verify_value in value):
            msg = msg + "，实际值：%s 包含 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 不包含 期望值%s" % (str(value), str(verify_value))
            verify_type = '包含'
    elif assert_type == 1:
        if pytest.assume(verify_value not in value):
            msg = msg + "，实际值：%s 不包含 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值:%s 包含 期望值%s" % (str(value), str(verify_value))
            verify_type = '不包含'
    elif assert_type == 2:
        if pytest.assume(verify_value == value):
            msg = msg + "，实际值：%s 等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 不等于 期望值：%s" % (str(value), str(verify_value))
            verify_type = '等于'
    elif assert_type == 3:
        if pytest.assume(verify_value != value):
            msg = msg + "，实际值：%s 不等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 等于 期望值：%s" % (str(value), str(verify_value))
            verify_type = '不等于'
    elif assert_type == 4:
        if pytest.assume(value > verify_value):
            msg = msg + "，实际值：%s 大于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 小等于 期望值：%s" % (str(value), str(verify_value))
            verify_type = '大于'
    elif assert_type == 5:
        if pytest.assume(value < verify_value):
            msg = msg + "，实际值：%s 小于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 大等于 期望值%s" % (str(value), str(verify_value))
            verify_type = '小于'
    elif assert_type == 6:
        if pytest.assume(value >= verify_value):
            msg = msg + "，实际值：%s 大等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 小于 期望值%s" % (str(value), str(verify_value))
            verify_type = '大等于'
    elif assert_type == 7:
        if pytest.assume(value <= verify_value):
            msg = msg + "，实际值：%s 小等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 大于 期望值%s" % (str(value), str(verify_value))
            verify_type = '小等于'
    # print(msg)
    return verify_result, msg, verify_type


def dispose_params(change_params, data):
    if data:
        for key in change_params:
            data = str(data).replace(key, str(change_params[key]))
    return data
