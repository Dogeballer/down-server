from __future__ import absolute_import, unicode_literals

import ast
import json
import time

import jsonpath
import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone

from executor.UseCaseExecutor import test_interfaces, assert_func, requests_func, dispose_params, instantiation_time
from executor.mqtt_publish_client import MQTTPublishClient
from executor.script_execution import udf_execute
from executor.sql_executor import SqlExecutor
from projects.models import *
from system_settings.models import UdfArgs
from usecases.models import *

logger = get_task_logger(__name__)


@shared_task
def use_case_executor(use_case_id_list, taskLog_id, environment_id, token, global_params, public_headers, execute_type):
    use_case_list = UseCases.objects.filter(pk__in=use_case_id_list)
    taskLog = TaskLog.objects.get(pk=taskLog_id)
    environment = Environment.objects.get(pk=environment_id)
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
    taskLog.success_count = CaseLog.objects.filter(task_log=taskLog, execute_status=1).count()
    taskLog.failed_count = CaseLog.objects.filter(task_log=taskLog, execute_status=0).count()
    taskLog.execute_status = 1
    end_time = timezone.now()
    start_time = taskLog.start_time
    taskLog.end_time = end_time
    spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
    taskLog.spend_time = spend_time
    taskLog.save()


# 异步执行用例
@shared_task
def async_execute_use_case(use_case_id, taskLog_id, environment_id, suite_global_params, public_headers,
                           case_count, payload, lead_param=None):
    # 前置用例参数
    if lead_param is None:
        lead_param = {}
    use_case = UseCases.objects.get(pk=use_case_id)
    taskLog = TaskLog.objects.get(pk=taskLog_id)
    environment = Environment.objects.get(pk=environment_id)
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
        use_case_callback_params_dict = dict(json.loads(use_case.params), **lead_param)
    else:
        use_case_callback_params_dict = {}
    current_date = timezone.now().strftime('%Y-%m-%d')
    current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    instance_date = int(time.mktime(time.strptime(current_date, "%Y-%m-%d")) * 1000)
    instance_time = int(round(time.time() * 1000))
    time_params_dict = {'{{currentDate}}': current_date, '{{currentTime}}': current_time,
                        '{{instanceTime}}': instance_time, '{{instanceDate}}': instance_date}
    global_params_dict = json.dumps(global_params_dict)
    global_params_dict = dispose_params(time_params_dict, global_params_dict)
    global_params_dict = dispose_params(suite_global_params, global_params_dict)
    global_params_dict = json.loads(global_params_dict)
    global_params_dict['{{currentDate}}'] = current_date
    global_params_dict['{{currentTime}}'] = current_time
    global_params_dict['{{instanceTime}}'] = instance_time
    global_params_dict['{{instanceDate}}'] = instance_date
    # global_params_dict['{{token}}'] = token
    for key in global_params_dict:
        value = str(global_params_dict[key])
        if value.find('${') != -1:
            global_params_dict[key] = udf_dispose(value, case_log)
    for case_step in case_steps:
        start_time = timezone.now()
        failed_case_steps = CaseStepLog.objects.filter(case_log=case_log, execute_status=0)
        for key in global_params_dict:
            slice_int = str(global_params_dict[key]).find('instantiation_time(')
            if slice_int != -1:
                string_param = str(global_params_dict[key])[slice_int + 19:-1]
                time_param = string_param.split(',')
                func_type = time_param[0].lower().replace("'", "")
                value = int(time_param[1])
                format_str = time_param[2].replace("'", "")
                try:
                    instantiation_datetime = instantiation_time(func_type, value, format_str)
                except:
                    instantiation_datetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                global_params_dict[key] = str(instantiation_datetime)
        for key in suite_global_params:
            slice_int = str(suite_global_params[key]).find('instantiation_time(')
            if slice_int != -1:
                string_param = str(suite_global_params[key])[slice_int + 19:-1]
                time_param = string_param.split(',')
                func_type = time_param[0].lower().replace("'", "")
                value = int(time_param[1])
                format_str = time_param[2].replace("'", "")
                try:
                    instantiation_datetime = instantiation_time(func_type, value, format_str)
                except:
                    instantiation_datetime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                suite_global_params[key] = str(instantiation_datetime)
        forward_operation_list = StepForwardAfterOperation.objects.filter(delete=False, mode=0, step=case_step)
        # 步骤前置处理
        step_forward_after_operation(forward_operation_list, suite_global_params, global_params_dict,
                                     use_case_callback_params_dict, case_log)
        case_log.global_parameter = json.dumps(global_params_dict)
        case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
        case_log.save()
        if failed_case_steps:
            if case_step.type in [0, 2, 3]:
                method = case_step.case_interface.method
            elif case_step.type in [4, 6, 8]:
                method = '查询'
            elif case_step.type in [5, 9]:
                method = '执行'
            else:
                method = '-'
            case_step_log = CaseStepLog.objects.create(request_url='-', method=method,
                                                       param=[], body={},
                                                       case_log=case_log, case_step=case_step, execute_status=2,
                                                       step_body=[], assert_result=[])
            continue
        # 类型为接口或是轮询接口
        if case_step.type == 0 or case_step.type == 2:
            method, query_param, headers, test_param, body, request_body, url, query_url, interface_callback_params = request_execute_prepare(
                case_step,
                environment,
                suite_global_params,
                global_params_dict,
                use_case_callback_params_dict,
                # global_params_dict["{{token}}"],
                public_headers)
            case_step_log = CaseStepLog.objects.create(request_url=query_url, method=method, param=test_param,
                                                       body=body,
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
                case_step_polls = CaseStepPoll.objects.filter(case_step=case_step, delete=False)
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
                    checkout_result = []
                    for item in case_step_polls:
                        checkout, assert_result = assert_execute(item, suite_global_params, global_params_dict,
                                                                 use_case_callback_params_dict,
                                                                 response_body, response_code)
                        checkout_result.append(checkout)
                        if assert_result:
                            pass
                        else:
                            poll_result = False
                    if poll_result:
                        break
                    else:
                        time.sleep(polling_interval)
                case_step_log.poll_assert_result = json.dumps(checkout_result)
                case_step_log.save()
            # 步骤后置处理
            step_postposition_deal(case_step,
                                   use_case_callback_params_dict, suite_global_params, global_params_dict,
                                   interface_callback_params, response_body, response_code, start_time,
                                   case_log, case_step_log)
        elif case_step.type == 1:
            wait_time = json.loads(case_step.body)['time']
            time.sleep(wait_time)
            end_time = timezone.now()
            spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
            CaseStepLog.objects.create(body=case_step.body, execute_status=1, case_log=case_log, case_step=case_step,
                                       spend_time=spend_time)
        # 步骤类型为循环接口
        elif case_step.type == 3:
            loop_parameter = case_step.loop_parameter
            loop_list = use_case_callback_params_dict[loop_parameter]
            keys = StepCircularKey.objects.filter(case_step=case_step, delete=False)
            interface = case_step.case_interface
            if str(type(loop_list)) == "<class 'list'>" and len(loop_list) != 0:
                try:
                    # 循环回调列表参数
                    for item in loop_list:
                        method, query_param, headers, test_param, body, request_body, url, query_url, interface_callback_params = request_execute_prepare(
                            case_step, environment, suite_global_params, global_params_dict,
                            use_case_callback_params_dict,
                            # global_params_dict["{{token}}"],
                            public_headers,
                            loop_parameter=loop_parameter, keys=keys, item=item)
                        msg, response_code, response_headers, response_body, response_time = requests_func(method,
                                                                                                           url,
                                                                                                           query_url,
                                                                                                           query_param,
                                                                                                           headers,
                                                                                                           request_body)
                        case_step_log = CaseStepLog.objects.create(request_url=query_url, method=method,
                                                                   param=test_param,
                                                                   body=body,
                                                                   case_log=case_log, case_step=case_step)
                        step_postposition_deal(case_step,
                                               use_case_callback_params_dict, suite_global_params, global_params_dict,
                                               interface_callback_params, response_body, response_code, start_time,
                                               case_log, case_step_log)
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
                execute_status = 0
                body = ["取值异常,请检查参数"]
                if len(loop_list) == 0:
                    execute_status = 1
                    body = ["列表长度为0"]
                case_step_log = CaseStepLog.objects.create(request_url=url, method=method, param=[],
                                                           body={},
                                                           case_log=case_log, case_step=case_step,
                                                           execute_status=execute_status,
                                                           step_body=json.dumps(body), assert_result=[])
        elif case_step.type in [4, 5, 6]:
            if case_step.type in [4, 6]:
                method = '查询'
            else:
                method = '执行'
            data_source = case_step.data_source
            sql_script = case_step.sql_script
            sql_script = dispose_params(suite_global_params, sql_script)
            sql_script = dispose_params(global_params_dict, sql_script)
            sql_script = dispose_params(use_case_callback_params_dict, sql_script)
            callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
            if not data_source:
                data_source = case_step.use_case.data_source
                if not data_source:
                    case_step_log = CaseStepLog.objects.create(request_url='--', method=method, param=[],
                                                               body=[], sql_script=sql_script,
                                                               case_log=case_log, case_step=case_step, execute_status=0,
                                                               step_body=json.dumps(
                                                                   [{"code": 3000, "message": "未配置数据库链接"}]),
                                                               assert_result=[])
                    continue
            sql = SqlExecutor()
            connect = sql.connect_database(data_source.database_type, data_source.host, data_source.port,
                                           data_source.username, data_source.password, data_source.database,
                                           data_source.sid)
            connect_info = str(data_source.host) + ':' + str(data_source.port) + '--' + data_source.database
            if not connect:
                case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method, param=[],
                                                           body=[], sql_script=sql_script,
                                                           case_log=case_log, case_step=case_step, execute_status=0,
                                                           step_body=json.dumps(
                                                               [{"code": 3000, "message": "数据库链接异常，请检查配置或网络"}]),
                                                           assert_result=[])
                continue
            else:
                cur = sql.conn.cursor()
                case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method, param=[],
                                                           body=[], sql_script=sql_script,
                                                           case_log=case_log, case_step=case_step)
                if case_step.type == 4:  # SQL查询
                    response_code, result_data, query_field = sql_execute_func(cur, True, sql, sql_script)
                elif case_step.type == 5:  # SQL执行
                    response_code, result_data, query_field = sql_execute_func(cur, False, sql, sql_script)
                elif case_step.type == 6:  # SQL轮询查询
                    case_step_polls = CaseStepPoll.objects.filter(case_step=case_step, delete=False)
                    wrap_count = case_step.wrap_count
                    polling_interval = case_step.polling_interval
                    for i in range(wrap_count):
                        response_code, result_data, query_field = sql_execute_func(cur, True, sql, sql_script)
                        poll_result = True
                        if len(case_step_polls) == 0:
                            poll_result = False
                        checkout_result = []
                        for item in case_step_polls:
                            checkout, assert_result = assert_execute(item, suite_global_params, global_params_dict,
                                                                     use_case_callback_params_dict,
                                                                     result_data, response_code)
                            checkout_result.append(checkout)
                            if assert_result:
                                pass
                            else:
                                poll_result = False
                        if poll_result:
                            break
                        else:
                            time.sleep(polling_interval)
                    case_step_log.poll_assert_result = json.dumps(checkout_result)
                cur.connection.close()
                case_step_log.query_field = json.dumps(query_field)
                case_step_log.save()
                step_postposition_deal(case_step,
                                       use_case_callback_params_dict, suite_global_params, global_params_dict,
                                       callback_params, result_data, response_code, start_time,
                                       case_log, case_step_log)
        elif case_step.type in [8, 9]:
            if case_step.type == 8:
                method = '查询'
            else:
                method = '执行'
            data_source = case_step.data_source
            sql_script = case_step.sql_script
            sql_script = dispose_params(suite_global_params, sql_script)
            sql_script = dispose_params(global_params_dict, sql_script)
            sql_script = dispose_params(use_case_callback_params_dict, sql_script)
            callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
            loop_parameter = case_step.loop_parameter
            loop_list = use_case_callback_params_dict[loop_parameter]
            keys = StepCircularKey.objects.filter(case_step=case_step, delete=False)
            connect_info = '--'
            if not data_source:
                data_source = case_step.use_case.data_source
                if not data_source:
                    case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method, param=[],
                                                               body=[], sql_script=sql_script,
                                                               case_log=case_log, case_step=case_step,
                                                               execute_status=0,
                                                               step_body=json.dumps(
                                                                   [{"code": 3000, "message": "未配置数据库链接"}]),
                                                               assert_result=[])
                else:
                    connect_info = str(data_source.host) + ':' + str(data_source.port) + '--' + data_source.database
                    sql = SqlExecutor()
                    connect = sql.connect_database(data_source.database_type, data_source.host, data_source.port,
                                                   data_source.username, data_source.password, data_source.database,
                                                   data_source.sid)
                    if not connect:
                        case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                                   param=[],
                                                                   body=[], sql_script=sql_script,
                                                                   case_log=case_log, case_step=case_step,
                                                                   execute_status=0,
                                                                   step_body=json.dumps(
                                                                       [{"code": 3000,
                                                                         "message": "数据库链接异常，请检查配置或网络"}]),
                                                                   assert_result=[])
                    else:
                        cur = sql.conn.cursor()
                        if str(type(loop_list)) == "<class 'list'>" and len(loop_list) != 0:
                            try:
                                # 循环回调列表参数
                                for item in loop_list:
                                    replace_sql = sql_script
                                    if len(keys) != 0:
                                        for key in keys:
                                            key_name = key.key_name
                                            key = key.key
                                            try:
                                                value = item[key]
                                            except:
                                                value = ''
                                            replace_sql = replace_sql.replace(key_name, str(value))
                                    else:
                                        replace_sql = replace_sql.replace(str(loop_parameter) + '.item', str(item))
                                    execute_sql_script = replace_sql
                                    case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                                               param=[],
                                                                               body=[], sql_script=execute_sql_script,
                                                                               case_log=case_log, case_step=case_step)
                                    if case_step.type == 8:  # SQL查询
                                        response_code, result_data, query_field = sql_execute_func(cur, True, sql,
                                                                                                   execute_sql_script)
                                    elif case_step.type == 9:  # SQL执行
                                        response_code, result_data, query_field = sql_execute_func(cur, False, sql,
                                                                                                   execute_sql_script)
                                    case_step_log.query_field = json.dumps(query_field)
                                    case_step_log.save()
                                    step_postposition_deal(case_step,
                                                           use_case_callback_params_dict, suite_global_params,
                                                           global_params_dict,
                                                           callback_params, result_data, response_code, start_time,
                                                           case_log, case_step_log)
                            except Exception as e:
                                print(e)
                                case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                                           param=[],
                                                                           body=[], sql_script=sql_script,
                                                                           case_log=case_log, case_step=case_step,
                                                                           execute_status=0,
                                                                           step_body=json.dumps(
                                                                               [{"code": 3000,
                                                                                 "message": "取值异常,请检查参数"}]),
                                                                           assert_result=[])
                        else:
                            execute_status = 0
                            body = [{"code": 3000, "message": "取值异常,请检查参数"}]
                            if len(loop_list) == 0:
                                execute_status = 1
                                body = [{"code": 0, "message": "列表长度为0"}]
                            case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                                       param=[],
                                                                       body=[], sql_script=sql_script,
                                                                       case_log=case_log, case_step=case_step,
                                                                       execute_status=execute_status,
                                                                       step_body=json.dumps(body), assert_result=[])
                        # 关闭数据库链接（很关键）
                        cur.connection.close()
        elif case_step.type == 10:
            method = '推送'
            mqtt = case_step.mqtt
            topic = case_step.topic
            qos = case_step.qos
            body = case_step.body
            topic = dispose_params(suite_global_params, topic)
            topic = dispose_params(global_params_dict, topic)
            topic = dispose_params(use_case_callback_params_dict, topic)
            body = dispose_params(suite_global_params, body)
            body = dispose_params(global_params_dict, body)
            body = dispose_params(use_case_callback_params_dict, body)
            callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
            if not mqtt:
                case_step_log = CaseStepLog.objects.create(request_url='--', method=method, param=[],
                                                           body=body,
                                                           case_log=case_log, case_step=case_step, execute_status=0,
                                                           step_body=json.dumps(
                                                               [{"code": 3000, "message": "未配置MQTT客户端"}]),
                                                           assert_result=[])
                continue
            mqtt_client = MQTTPublishClient(mqtt.broker, mqtt.port, mqtt.username, mqtt.password)
            connect_info = f"{mqtt.broker}:{str(mqtt.port)}/topic--{topic}/qos=={qos}"
            status, msg = mqtt_client.publish_msg(topic, payload, qos)
            if status:
                response_code = 200
                step_body = {"code": 0, "message": msg}
            else:
                response_code = 500
                step_body = {"code": 3000, "message": msg}
            case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method, param=[],
                                                       body=body, step_body=json.dumps(step_body),
                                                       case_log=case_log, case_step=case_step)
            step_postposition_deal(case_step,
                                   use_case_callback_params_dict, suite_global_params, global_params_dict,
                                   callback_params, step_body, response_code, start_time,
                                   case_log, case_step_log)

        elif case_step.type == 12:
            method = '推送'
            mqtt = case_step.mqtt
            topic = case_step.topic
            qos = case_step.qos
            body = case_step.body
            topic = dispose_params(suite_global_params, topic)
            topic = dispose_params(global_params_dict, topic)
            topic = dispose_params(use_case_callback_params_dict, topic)
            body = dispose_params(suite_global_params, body)
            body = dispose_params(global_params_dict, body)
            body = dispose_params(use_case_callback_params_dict, body)
            callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
            loop_parameter = case_step.loop_parameter
            loop_list = use_case_callback_params_dict[loop_parameter]
            keys = StepCircularKey.objects.filter(case_step=case_step, delete=False)
            if not mqtt:
                case_step_log = CaseStepLog.objects.create(request_url='--', method=method, param=[],
                                                           body=body,
                                                           case_log=case_log, case_step=case_step, execute_status=0,
                                                           step_body=json.dumps(
                                                               [{"code": 3000, "message": "未配置MQTT客户端"}]),
                                                           assert_result=[])
                continue
            mqtt_client = MQTTPublishClient(mqtt.broker, mqtt.port, mqtt.username, mqtt.password)
            if str(type(loop_list)) == "<class 'list'>" and len(loop_list) != 0:
                try:
                    # 循环回调列表参数
                    for item in loop_list:
                        replace_body = body
                        replace_topic = topic
                        if len(keys) != 0:
                            for key in keys:
                                key_name = key.key_name
                                key = key.key
                                try:
                                    value = item[key]
                                except:
                                    value = ''
                                replace_body = replace_body.replace(key_name, str(value))
                                replace_topic = replace_topic.replace(key_name, str(value))
                        else:
                            replace_body = replace_body.replace(str(loop_parameter) + '.item', str(item))
                            replace_topic = replace_topic.replace(str(loop_parameter) + '.item', str(item))
                        execute_body = replace_body
                        execute_topic = replace_topic
                        status, msg = mqtt_client.publish_msg(execute_topic, execute_body, qos)
                        if status:
                            response_code = 200
                            step_body = {"code": 0, "message": msg}
                        else:
                            response_code = 500
                            step_body = {"code": 3000, "message": msg}
                        connect_info = f'{mqtt.broker}:{str(mqtt.port)}/topic=="{replace_topic}"/qos=={qos}'
                        case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                                   param=[],
                                                                   body=execute_body,
                                                                   step_body=json.dumps(step_body),
                                                                   case_log=case_log, case_step=case_step)
                        step_postposition_deal(case_step,
                                               use_case_callback_params_dict, suite_global_params,
                                               global_params_dict,
                                               callback_params, step_body, response_code, start_time,
                                               case_log, case_step_log)
                except Exception as e:
                    print(e)
                    case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                               param=[],
                                                               body=body,
                                                               case_log=case_log, case_step=case_step,
                                                               execute_status=0,
                                                               step_body=json.dumps(
                                                                   [{"code": 3000,
                                                                     "message": "取值异常,请检查参数"}]),
                                                               assert_result=[])
            else:
                execute_status = 0
                body = [{"code": 3000, "message": "取值异常,请检查参数"}]
                if len(loop_list) == 0:
                    execute_status = 1
                    body = [{"code": 0, "message": "列表长度为0"}]
                case_step_log = CaseStepLog.objects.create(request_url=connect_info, method=method,
                                                           param=[], body=body,
                                                           case_log=case_log, case_step=case_step,
                                                           execute_status=execute_status,
                                                           step_body=json.dumps(body), assert_result=[])
    count_step_log = CaseStepLog.objects.filter(case_log=case_log).count()
    count_failed_step = CaseStepLog.objects.filter(~Q(execute_status=1), case_log=case_log).count()
    count_success_step = count_step_log - count_failed_step
    case_log.success_count = count_success_step
    case_log.failed_count = count_failed_step
    if count_success_step != count_step_log:
        case_log.execute_status = 0
    else:
        case_log.execute_status = 1
    end_time = timezone.now()
    start_time = case_log.start_time
    case_log.end_time = end_time
    spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
    case_log.spend_time = spend_time
    case_log.save()
    case_done_count = CaseLog.objects.filter(~Q(execute_status=2), task_log=taskLog).count()
    if case_done_count == case_count:
        taskLog.success_count = CaseLog.objects.filter(task_log=taskLog, execute_status=1).count()
        taskLog.failed_count = CaseLog.objects.filter(task_log=taskLog, execute_status=0).count()
        taskLog.execute_status = 1
        end_time = timezone.now()
        start_time = taskLog.start_time
        taskLog.end_time = end_time
        spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
        taskLog.spend_time = spend_time
        taskLog.save()
        if payload:
            payload['job_id'] = taskLog.job_id
            payload = json.dumps(payload)
            try:
                headers = {
                    "Content-Type": "application/json; charset=UTF-8",
                    "authorization": "Bearer abc234"
                }
                r = requests.post(url='http://192.168.5.149:49000/generic-webhook-trigger/invoke', data=payload,
                                  headers=headers)
                result = r.json()
                print(result)
            except:
                print('jenkins链接网络异常')
    return case_log.id


# 接口请求前置处理
def request_execute_prepare(case_step, environment, suite_global_params, global_params_dict,
                            use_case_callback_params_dict, public_headers, loop_parameter='', keys=None,
                            item=None):
    interface = case_step.case_interface
    method = interface.method
    path = interface.path
    body_type = interface.body_type
    url = str(environment.url) + str(path)
    interface_callback_params = StepCallBackParams.objects.filter(step=case_step, delete=False)
    params = case_step.param
    # 替换全局参数以及回调参数
    params = dispose_params(suite_global_params, params)
    params = dispose_params(global_params_dict, params)
    params = dispose_params(use_case_callback_params_dict, params)
    body = case_step.body
    body = dispose_params(suite_global_params, body)
    body = dispose_params(global_params_dict, body)
    body = dispose_params(use_case_callback_params_dict, body)
    # 当类型为循环参数时，特殊处理
    if case_step.type == 3:
        if len(keys) != 0:
            for key in keys:
                key_name = key.key_name
                key = key.key
                print(item[key])
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
    path_param_list = []
    query_param = {}
    url_query_param = '?'
    headers_default = {}
    if body_type == 3:
        headers_default = {
            "Content-Type": "application/json; charset=UTF-8",
        }
    for key in public_headers:
        headers_default[key] = public_headers[key]
    headers = headers_default
    test_param = []
    # 获取请求头和请求参数值
    for key in public_headers:
        test_param.append({"id": -1, "name": key, "param_in": "header", "value": public_headers[key]})
    for param in params:
        if param['param_in'].lower() == 'path':
            path_param = {'name': param['name'], 'value': param['value']}
            path_param_list.append(path_param)
            test_param.append(param)
        elif param['param_in'].lower() == 'query':
            query_param[param['name']] = param['value']
            url_query_param += param['name'] + '=' + param['value'] + '&'
            test_param.append(param)
        elif param['param_in'].lower() == 'header':
            headers[param['name']] = param['value']
            test_param.append(param)
    # 组装所有参数
    if body:
        request_body = json.loads(body)
        request_body = json.dumps(request_body)
    else:
        request_body = []
    test_param = json.dumps(test_param)
    # 生成url值
    for path_param in path_param_list:
        if url.find('{') != -1:
            url = url.replace('{' + path_param['name'] + '}', str(path_param['value']))
    if len(url_query_param) > 1:
        if url_query_param.rfind('&') != -1:
            url_query_param = url_query_param[:url_query_param.rfind('&')]
        query_url = url + url_query_param
    else:
        query_url = url
    return method, query_param, headers, test_param, body, request_body, url, query_url, interface_callback_params


def assert_execute(item, suite_global_params, global_params_dict, use_case_callback_params_dict, response_body,
                   response_code):
    checkout = {}
    if item.type_from == 0:
        value_jsonpath = dispose_params(suite_global_params, item.value_statement)
        value_jsonpath = dispose_params(global_params_dict, value_jsonpath)
        value_jsonpath = dispose_params(use_case_callback_params_dict, value_jsonpath)
        verify_value = dispose_params(suite_global_params, item.verify_value)
        verify_value = dispose_params(global_params_dict, verify_value)
        verify_value = dispose_params(use_case_callback_params_dict, verify_value)
        assert_type = item.assert_type
        if value_jsonpath.find('.length()') != -1:
            value = jsonpath.jsonpath(response_body, value_jsonpath.replace('.length()', ''))
            if value:
                try:
                    value = len(value)
                except:
                    value = 'None'
        else:
            value = jsonpath.jsonpath(response_body, value_jsonpath)
            if value:
                try:
                    value = value[0]
                except:
                    value = 'None'
            else:
                value = 'None'
        assert_result, message, verify_type = assert_func(assert_type, str(value), verify_value)
        checkout['assert_type'] = verify_type
        checkout['value_statement'] = value_jsonpath
        checkout['type_from'] = '消息体校验'
        checkout['result'] = assert_result
        checkout['msg'] = message
        checkout['value'] = str(value)
        checkout['verify_value'] = str(verify_value)
    elif item.type_from == 1:
        assert_type = item.assert_type
        verify_value = dispose_params(suite_global_params, item.verify_value)
        verify_value = dispose_params(global_params_dict, verify_value)
        verify_value = dispose_params(use_case_callback_params_dict, verify_value)
        assert_result, message, verify_type = assert_func(assert_type, str(response_code), verify_value)
        checkout['assert_type'] = verify_type
        checkout['value_statement'] = ''
        checkout['type_from'] = '返回值校验'
        checkout['result'] = assert_result
        checkout['msg'] = message
        checkout['value'] = str(response_code)
        checkout['verify_value'] = str(verify_value)
    return checkout, assert_result


def sql_execute_func(cur, is_query, sql, sql_script):
    if is_query:
        result = sql.query_db(cur, sql_script)
    else:
        result = sql.execute_db(cur, sql_script)
    result_data = {
        "code": 0,
        "msg": ""
    }
    query_field = []
    if result:
        response_code = 200
        if is_query:
            result_data['data'] = json.loads(sql.query_result)
            result_data['msg'] = '操作成功'
            query_field = sql.query_field
        else:
            result_data['msg'] = '执行成功'
    else:
        response_code = 500
        result_data['code'] = 3000
        result_data['msg'] = str(sql.error_msg)
    return response_code, result_data, query_field


# 步骤后置处理
def step_postposition_deal(case_step,
                           use_case_callback_params_dict, suite_global_params, global_params_dict,
                           callback_params, result_data, response_code, start_time,
                           case_log, case_step_log):
    for callback_param in callback_params:
        callback_param_jsonpath = callback_param.json_path
        callback_param_name = callback_param.param_name
        callback_param_type = callback_param.type
        if callback_param_type == 0:
            callback_param_value = jsonpath.jsonpath(result_data, callback_param_jsonpath)
            if callback_param_value:
                try:
                    callback_param_value = callback_param_value[0]
                except:
                    callback_param_value = ''
            else:
                callback_param_value = ''
        elif callback_param_type == 1:
            callback_param_value = jsonpath.jsonpath(result_data, callback_param_jsonpath)
            if not callback_param_value:
                callback_param_value = []
        use_case_callback_params_dict[callback_param_name] = callback_param_value
        case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
        case_log.save()
    case_step_log.step_body = json.dumps(result_data)
    forward_operation_list = StepForwardAfterOperation.objects.filter(delete=False, mode=1, step=case_step)
    # 步骤后置处理
    step_forward_after_operation(forward_operation_list, suite_global_params, global_params_dict,
                                 use_case_callback_params_dict, case_log)
    case_log.global_parameter = json.dumps(global_params_dict)
    case_log.callback_parameter = json.dumps(use_case_callback_params_dict)
    case_log.save()
    # 步骤断言执行
    checkout_list = CaseAssert.objects.filter(case_step=case_step, delete=False)
    checkout_result = []
    for item in checkout_list:
        checkout, assert_result = assert_execute(item, suite_global_params, global_params_dict,
                                                 use_case_callback_params_dict,
                                                 result_data, response_code)
        checkout_result.append(checkout)
    case_step_log.execute_status = 1
    # 判断步骤是否执行成功
    for checkout in checkout_result:
        if not checkout['result']:
            case_step_log.execute_status = 0
    case_step_log.assert_result = json.dumps(checkout_result)
    end_time = timezone.now()
    spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
    case_step_log.spend_time = spend_time
    case_step_log.save()


def udf_execute_setup(original_function_str):
    # 用例配置初始字符串提取函数和参数并判断是否符合参数条件
    # 示例为---"${funcName(str_args="string"||int_args=2||list_args=[1,2,3]||dict_args={"abc":"abc"}||boolean_args=True||float_args=0.01)}"
    func_name = ''
    args = ''
    func_name_slice_start = original_function_str.find('${')
    func_name_slice_end = original_function_str.find('(')
    args_slice_start = original_function_str.find('(')
    args_slice_end = original_function_str.rfind(')}')
    if func_name_slice_start == -1 or func_name_slice_end == -1 or args_slice_start == -1 or args_slice_end == -1:
        execution_status = False
        msg = "传入函数书写格式异常"
        return func_name, args, execution_status, msg
    func_name = original_function_str[func_name_slice_start + 2: func_name_slice_end]
    try:
        udf = Udf.objects.get(name=func_name)
    except Udf.DoesNotExist:
        execution_status = False
        msg = "未找到对应udf函数，请检查函数书写格式"
        return func_name, args, execution_status, msg
    args_str = original_function_str[args_slice_start + 1: args_slice_end]
    args_list = args_str.split('||')
    fun_args = UdfArgs.objects.filter(udf=udf)
    if len(args_list) != fun_args.count():
        execution_status = False
        msg = "传入参数校验异常，请检查函数传参"
        return func_name, args, execution_status, msg
    func_kwargs = {}
    try:
        for args in args_list:
            args_split_result = args.split('=')
            args_name = args_split_result[0]
            args_value = args_split_result[1]
            args_type = UdfArgs.objects.get(udf=udf, name=args_name).args_type
            if args_type == 0:  # int
                args_value = int(args_value)
            elif args_type == 1:  # str
                args_value = args_value.replace("'", '').replace('"', '')
            elif args_type == 2:  # list
                args_value = json.loads(args_value)
            elif args_type == 3:  # dict
                args_value = ast.literal_eval(args_value)
            elif args_type == 4:
                if args_value == "True":
                    args_value = True
                elif args_value == "False":
                    args_value = False
                else:
                    args_value = False
            elif args_type == 5:  # float
                args_value = float(args_value)
            func_kwargs[args_name] = args_value
    except Exception as e:
        execution_status = False
        msg = "传入参数转换异常，具体错误为-'%s'" % e
        return func_name, args, execution_status, msg
    execution_status = True
    msg = "函数转换成功"
    return func_name, func_kwargs, execution_status, msg


# UDF函数处理
def udf_dispose(original_function_str, case_log):
    func_name, func_kwargs, execution_status, msg = udf_execute_setup(original_function_str)
    if execution_status:
        udf = Udf.objects.get(name=func_name)
        result, status, error_msg = udf_execute(func_name, func_kwargs)
        if status:
            remark = '执行结果为:%s' % str(result)
        else:
            remark = '报错信息为:%s' % error_msg
        UdfLog.objects.create(udf=udf, case_log=case_log, original_function_str=original_function_str,
                              udf_name=func_name, udf_zh_name=udf.zh_name, args=str(func_kwargs),
                              execution_status=status, remark=remark)
        return result
    else:
        UdfLog.objects.create(case_log=case_log, original_function_str=original_function_str, execution_status=False,
                              remark=msg)
        return ''


def step_forward_after_operation(forward_operation_list, suite_global_params, global_params_dict,
                                 use_case_callback_params_dict, case_log):
    for forward_operation in forward_operation_list:
        # 参数变更操作
        if forward_operation.operation_type == 0:
            param_name = forward_operation.param_name
            param_value = dispose_params(suite_global_params, forward_operation.param_value, True)
            param_value = dispose_params(global_params_dict, param_value, True)
            param_value = dispose_params(use_case_callback_params_dict, param_value, True)
            if param_value.find('${') != -1:
                param_value = udf_dispose(param_value, case_log)
            if param_name.find('{{') == 0:
                global_params_dict[param_name] = param_value
            elif param_name.find('_') == 0:
                use_case_callback_params_dict[param_name] = param_value
