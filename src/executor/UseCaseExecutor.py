import os
import time
import datetime
import requests
from down.settings import BASE_DIR
from executor.getUacToken import GetToken
from projects.models import *
from interfaces.models import *
from usecases.models import *
from test_suite.models import *
import json
import jsonpath
import psycopg2


def use_case_executor(use_case_list, taskLog, environment, token, global_params, public_headers, execute_type):
    if execute_type == 0:
        for use_case in use_case_list:
            test_interfaces(use_case, taskLog, environment, token, global_params, public_headers, execute_type)
    if execute_type == 1:
        for suite_case in use_case_list:
            use_case = suite_case.case
            case_environment = suite_case.environment
            if case_environment:
                environment = case_environment
            else:
                pass
            test_interfaces(use_case, taskLog, environment, token, global_params, public_headers, execute_type)


def test_interfaces(use_case, taskLog, environment, token, suite_global_params, public_headers, execute_type):
    global_params = use_case.global_params
    use_case_callback_params = use_case.params
    case_steps = CaseSteps.objects.filter(use_case=use_case, delete=False, status=True).order_by('sort')
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
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    instance_date = int(time.mktime(time.strptime(current_date, "%Y-%m-%d")) * 1000)
    global_params_dict['{{currentDate}}'] = current_date
    global_params_dict['{{currentTime}}'] = current_time
    global_params_dict['{{instanceTime}}'] = int(round(time.time() * 1000))
    global_params_dict['{{instanceDate}}'] = instance_date
    for case_step in case_steps:
        # 类型为接口或是轮询接口
        if case_step.type == 0 or case_step.type == 2:
            interface = case_step.case_interface
            method = interface.method
            path = interface.path
            url = str(environment.url) + str(path)
            # interface_callback_params = InterfaceCallBackParams.objects.filter(return_interface=interface, delete=False)
            interface_callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
            # params = json.loads(case_step.param)
            params = case_step.param
            # 替换全局参数以及回调参数
            params = dispose_params(suite_global_params, params)
            params = dispose_params(global_params_dict, params)
            params = json.loads(dispose_params(use_case_callback_params_dict, params))
            body = case_step.body
            body = dispose_params(suite_global_params, body)
            body = dispose_params(global_params_dict, body)
            body = dispose_params(use_case_callback_params_dict, body)
            path_param = {}
            query_param = {}
            url_query_param = '?'
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "authorization": token
            }
            for key in public_headers:
                headers[key] = public_headers[key]
            # print(headers)
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
                    test_param.append(param)
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
            case_step_log = CaseStepLog.objects.create(request_url=query_url, method=method, param=test_param,
                                                       body=request_body,
                                                       case_log=case_log, case_step=case_step)
            if case_step.type == 0:
                msg, response_code, response_headers, response_body, response_time = requests_func(method,
                                                                                                   url,
                                                                                                   query_url,
                                                                                                   query_param,
                                                                                                   headers,
                                                                                                   request_body)
            # 轮询接口查询执行步骤
            elif case_step.type == 2:
                case_step_polls = CaseStepPoll.objects.filter(case_step=case_step)
                wrap_count = case_step.wrap_count
                polling_interval = case_step.polling_interval
                for i in range(wrap_count):
                    msg, response_code, response_headers, response_body, response_time = requests_func(method,
                                                                                                       url,
                                                                                                       query_url,
                                                                                                       query_param,
                                                                                                       headers,
                                                                                                       request_body)
                    poll_result = True
                    if len(case_step_polls) == 0:
                        poll_result = False
                    for item in case_step_polls:
                        if item.type_from == 0:
                            value_jsonpath = item.value_statement
                            verify_value = item.verify_value
                            assert_type = item.assert_type
                            value = jsonpath.jsonpath(response_body, value_jsonpath)
                            if value:
                                try:
                                    value = value[0]
                                except:
                                    value = '未匹配到对应值'
                            else:
                                value = '未匹配到对应值'
                            assert_result, message, verify_type = assert_func(assert_type, str(value), verify_value)
                            if assert_result:
                                pass
                            else:
                                poll_result = False
                        elif item.type_from == 1:
                            assert_type = item.assert_type
                            verify_value = item.verify_value
                            assert_result, message, verify_type = assert_func(assert_type, str(response_code),
                                                                              verify_value)
                            if assert_result:
                                pass
                            else:
                                poll_result = False
                    if poll_result:
                        break
                    else:
                        time.sleep(polling_interval)
            # 获取回调参数
            for callback_param in interface_callback_params:
                callback_param_jsonpath = callback_param.json_path
                callback_param_name = callback_param.param_name
                callback_param_type = callback_param.type
                if callback_param_type == 0:
                    callback_param_value = jsonpath.jsonpath(response_body, callback_param_jsonpath)
                    if callback_param_value:
                        try:
                            callback_param_value = callback_param_value[0]
                        except:
                            callback_param_value = ''
                    else:
                        callback_param_value = ''
                elif callback_param_type == 1:
                    callback_param_value = jsonpath.jsonpath(response_body, callback_param_jsonpath)
                    if not callback_param_value:
                        callback_param_value = []
                use_case_callback_params_dict[callback_param_name] = callback_param_value
                case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
                case_log.save()
            case_step_log.step_body = json.dumps(response_body)
            # print(response_body)
            checkout_list = CaseAssert.objects.filter(case_step=case_step)
            checkout_result = []
            # 步骤断言执行
            for item in checkout_list:
                checkout = {}
                if item.type_from == 0:
                    value_jsonpath = item.value_statement
                    verify_value = item.verify_value
                    assert_type = item.assert_type
                    value = jsonpath.jsonpath(response_body, value_jsonpath)
                    if value:
                        try:
                            value = value[0]
                        except:
                            value = '未匹配到对应值'
                    else:
                        value = '未匹配到对应值'
                    assert_result, message, verify_type = assert_func(assert_type, str(value), verify_value)
                    checkout['assert_type'] = verify_type
                    checkout['value_statement'] = value_jsonpath
                    checkout['type_from'] = '消息体校验'
                    checkout['result'] = assert_result
                    checkout['msg'] = message
                    checkout['value'] = str(value)
                    checkout['verify_value'] = str(verify_value)
                    # print(message)
                elif item.type_from == 1:
                    assert_type = item.assert_type
                    verify_value = item.verify_value
                    assert_result, message, verify_type = assert_func(assert_type, str(response_code), verify_value)
                    checkout['assert_type'] = verify_type
                    checkout['value_statement'] = ''
                    checkout['type_from'] = '返回值校验'
                    checkout['result'] = assert_result
                    checkout['msg'] = message
                    checkout['value'] = str(response_code)
                    checkout['verify_value'] = str(verify_value)
                    # print(message)
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
        elif case_step.type == 3:
            loop_parameter = case_step.loop_parameter
            loop_list = use_case_callback_params_dict[loop_parameter]
            # print(len(loop_list))
            keys = StepCircularKey.objects.filter(case_step=case_step, delete=False)
            interface = case_step.case_interface
            if str(type(loop_list)) == "<class 'list'>" and len(loop_list) != 0:
                try:
                    for item in loop_list:
                        method = interface.method
                        path = interface.path
                        url = str(environment.url) + str(path)
                        # interface_callback_params = InterfaceCallBackParams.objects.filter(return_interface=interface,
                        #                                                                    delete=False)
                        interface_callback_params = StepCallBackParams.objects.filter(step=case_step,
                                                                                      delete=False)
                        # params = json.loads(case_step.param)
                        params = case_step.param
                        # 替换全局参数以及回调参数
                        params = dispose_params(global_params_dict, params)
                        params = dispose_params(use_case_callback_params_dict, params)
                        body = case_step.body
                        body = dispose_params(global_params_dict, body)
                        body = dispose_params(use_case_callback_params_dict, body)
                        if len(keys) != 0:
                            for key in keys:
                                key_name = key.key_name
                                key = key.key
                                # print(item[key])
                                try:
                                    value = item[key]
                                except:
                                    value = ''
                                params = params.replace(key_name, str(value))
                                body = body.replace(key_name, str(value))
                        else:
                            params = params.replace(str(loop_parameter) + '.item', str(item))
                            body = body.replace(str(loop_parameter) + '.item', str(item))
                        params = json.loads(params)
                        path_param = {}
                        query_param = {}
                        url_query_param = '?'
                        headers = {
                            "Content-Type": "application/json; charset=UTF-8",
                            "authorization": token
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
                        msg, response_code, response_headers, response_body, response_time = requests_func(method,
                                                                                                           url,
                                                                                                           query_url,
                                                                                                           query_param,
                                                                                                           headers,
                                                                                                           request_body)
                        case_step_log = CaseStepLog.objects.create(request_url=query_url, method=method,
                                                                   param=test_param,
                                                                   body=request_body,
                                                                   case_log=case_log, case_step=case_step)

                        for callback_param in interface_callback_params:
                            callback_param_jsonpath = callback_param.json_path
                            callback_param_name = callback_param.param_name
                            callback_param_type = callback_param.type
                            if callback_param_type == 0:
                                callback_param_value = jsonpath.jsonpath(response_body, callback_param_jsonpath)
                                if callback_param_value:
                                    try:
                                        callback_param_value = callback_param_value[0]
                                    except:
                                        callback_param_value = ''
                                else:
                                    callback_param_value = ''
                            elif callback_param_type == 1:
                                callback_param_value = jsonpath.jsonpath(response_body, callback_param_jsonpath)
                                if not callback_param_value:
                                    callback_param_value = []
                            use_case_callback_params_dict[callback_param_name] = callback_param_value
                            case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
                            case_log.save()
                        case_step_log.step_body = json.dumps(response_body)
                        # print(response_body)
                        checkout_list = CaseAssert.objects.filter(case_step=case_step)
                        checkout_result = []
                        # 步骤断言执行
                        for item in checkout_list:
                            checkout = {}
                            if item.type_from == 0:
                                value_jsonpath = item.value_statement
                                verify_value = item.verify_value
                                assert_type = item.assert_type
                                value = jsonpath.jsonpath(response_body, value_jsonpath)
                                if value:
                                    try:
                                        value = value[0]
                                    except:
                                        value = '未匹配到对应值'
                                else:
                                    value = '未匹配到对应值'
                                assert_result, message, verify_type = assert_func(assert_type, str(value), verify_value)
                                checkout['assert_type'] = verify_type
                                checkout['value_statement'] = value_jsonpath
                                checkout['type_from'] = '消息体校验'
                                checkout['result'] = assert_result
                                checkout['msg'] = message
                                checkout['value'] = str(value)
                                checkout['verify_value'] = str(verify_value)
                                # print(message)
                            elif item.type_from == 1:
                                assert_type = item.assert_type
                                verify_value = item.verify_value
                                assert_result, message, verify_type = assert_func(assert_type, str(response_code),
                                                                                  verify_value)
                                checkout['assert_type'] = verify_type
                                checkout['value_statement'] = ''
                                checkout['type_from'] = '返回值校验'
                                checkout['result'] = assert_result
                                checkout['msg'] = message
                                checkout['value'] = str(response_code)
                                checkout['verify_value'] = str(verify_value)
                                # print(message)
                            elif item.type_from == 2:
                                print(1)
                            checkout_result.append(checkout)
                        case_step_log.execute_status = 1
                        for checkout in checkout_result:
                            if not checkout['result']:
                                case_step_log.execute_status = 0
                        case_step_log.assert_result = json.dumps(checkout_result)
                        case_step_log.save()
                except:
                    method = interface.method
                    path = interface.path
                    url = str(environment.url) + str(path)
                    case_step_log = CaseStepLog.objects.create(request_url=url, method=method, param=[],
                                                               body={},
                                                               case_log=case_log, case_step=case_step, execute_status=0,
                                                               step_body=json.dumps(["取值异常,请检查参数"]), assert_result=[])
            else:
                method = interface.method
                path = interface.path
                url = str(environment.url) + str(path)
                case_step_log = CaseStepLog.objects.create(request_url=url, method=method, param=[],
                                                           body={},
                                                           case_log=case_log, case_step=case_step, execute_status=0,
                                                           step_body=json.dumps(["取值异常,请检查参数"]), assert_result=[])
    count_step_log = CaseStepLog.objects.filter(case_log=case_log).count()
    count_failed_step = CaseStepLog.objects.filter(case_log=case_log, execute_status=0).count()
    count_success_step = count_step_log - count_failed_step
    case_log.success_count = count_success_step
    case_log.failed_count = count_failed_step
    if count_success_step != count_step_log:
        case_log.execute_status = 0
    else:
        case_log.execute_status = 1
    end_time = datetime.datetime.now()
    start_time = case_log.start_time
    case_log.end_time = end_time
    spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
    case_log.spend_time = spend_time
    case_log.save()


def requests_func(method, url, query_url, query_param, headers, payload):
    try:
        method = method.lower()
        if method == 'get':
            r = requests.get(url, headers=headers, params=query_param)
        elif method == 'post':
            r = requests.post(query_url, headers=headers, data=payload)
        elif method == 'put':
            r = requests.put(query_url, headers=headers, data=payload)
        elif method == 'delete':
            r = requests.delete(query_url, headers=headers, data=payload)
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
    return msg, response_code, response_headers, response_body, response_time


def assert_func(assert_type, value, verify_value):
    verify_result = True
    msg = '校验成功'
    verify_type = ''
    if assert_type == 0:
        if verify_value in value:
            msg = msg + "，实际值：%s 包含 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 不包含 期望值%s" % (str(value), str(verify_value))
        verify_type = '包含'
    elif assert_type == 1:
        if verify_value not in value:
            msg = msg + "，实际值：%s 不包含 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值:%s 包含 期望值%s" % (str(value), str(verify_value))
        verify_type = '不包含'
    elif assert_type == 2:
        if verify_value == value:
            msg = msg + "，实际值：%s 等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 不等于 期望值：%s" % (str(value), str(verify_value))
        verify_type = '等于'
    elif assert_type == 3:
        if verify_value != value:
            msg = msg + "，实际值：%s 不等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 等于 期望值：%s" % (str(value), str(verify_value))
        verify_type = '不等于'
    elif assert_type == 4:
        if value > verify_value:
            msg = msg + "，实际值：%s 大于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 小等于 期望值：%s" % (str(value), str(verify_value))
        verify_type = '大于'
    elif assert_type == 5:
        if value < verify_value:
            msg = msg + "，实际值：%s 小于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 大等于 期望值%s" % (str(value), str(verify_value))
        verify_type = '小于'
    elif assert_type == 6:
        if value >= verify_value:
            msg = msg + "，实际值：%s 大等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 小于 期望值%s" % (str(value), str(verify_value))
        verify_type = '大等于'
    elif assert_type == 7:
        if value <= verify_value:
            msg = msg + "，实际值：%s 小等于 期望值%s" % (str(value), str(verify_value))
        else:
            verify_result = False
            msg = "断言失败，实际值：%s 大于 期望值%s" % (str(value), str(verify_value))
        verify_type = '小等于'
    # print(msg)
    return verify_result, msg, verify_type


def dispose_params(change_params, data, list_replace=False):
    if data:
        for key in change_params:
            if key.rfind('__') == len(key) - 2 and key.find('__') == 0:
                if list_replace:
                    data = str(data).replace(key, json.dumps(change_params[key]))
                else:
                    pass
            else:
                data = str(data).replace(key, str(change_params[key]))
    return data


def instantiation_time(type, value, format):
    if type == 'days':
        instantiation_datetime = (datetime.datetime.now() + datetime.timedelta(days=value))
    elif type == 'weeks':
        instantiation_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=value))
    elif type == 'seconds':
        instantiation_datetime = (datetime.datetime.now() + datetime.timedelta(seconds=value))
    elif type == 'minutes':
        instantiation_datetime = (datetime.datetime.now() + datetime.timedelta(minutes=value))
    elif type == 'hours':
        instantiation_datetime = (datetime.datetime.now() + datetime.timedelta(hours=value))
    else:
        instantiation_datetime = datetime.datetime.now()
    if format == 'timestamp':
        instantiation_datetime = int(instantiation_datetime.timestamp() * 1000)
    else:
        instantiation_datetime = instantiation_datetime.strftime(format)
    return instantiation_datetime
