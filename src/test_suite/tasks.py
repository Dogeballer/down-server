from __future__ import absolute_import, unicode_literals

import datetime
import json
import time
import uuid

from celery import shared_task
from django_celery_beat.models import *
from down.celery import app
from celery.utils.log import get_task_logger

from executor.UseCaseExecutor import use_case_executor, dispose_params
from executor.getUacToken import GetToken
from executor.get_auth_header import GetAuthHeader
from interfaces.views import merge_dicts
from test_suite.models import TestSuite, TestSuiteCases
from usecases.models import CaseLog, TaskLog
from usecases.tasks import async_execute_use_case, udf_dispose

logger = get_task_logger(__name__)


@shared_task(bind=True)
def dispatch_execute_test_suite(self, name, id):
    # 获取任务对应计划
    suite_info = TestSuite.objects.get(periodic_task_id=id)
    start_time = datetime.datetime.now() + timedelta(minutes=-15)
    end_time = datetime.datetime.now() + timedelta(minutes=15)
    if start_time < datetime.datetime.combine(datetime.date.today(), suite_info.timing) < end_time:
        name = suite_info.name
        tags = suite_info.suite_class.name
        environment = suite_info.environment
        job_id = uuid.uuid4()
        authentication_environment = environment.authentication_environment
        headers_get = GetAuthHeader(authentication_environment)
        header_str, headers_get_status = headers_get.header_get()
        if not headers_get_status:
            msg = "鉴权环境获取请求头异常"
            return msg
        try:
            header_dict = json.loads(header_str)
        except:
            msg = "鉴权环境获取请求头异常"
            return msg
        try:
            global_params = json.loads(suite_info.global_params)
        except:
            global_params = {}
        try:
            public_headers = json.loads(suite_info.public_headers)
        except:
            public_headers = {}
        precondition_case = suite_info.precondition_case
        case_list = TestSuiteCases.objects.filter(delete=False, test_suite=suite_info)
        case_count = case_list.count()
        # use_case_id_list = [case.case.id for case in case_list]
        use_case_list = [case for case in case_list]
        taskLog = TaskLog.objects.create(job_id=job_id, name=name, execute_status=2, mode=1, tags=tags,
                                         execute_type=1, success_count=0, failed_count=0, executor='调度')
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        instance_date = int(time.mktime(time.strptime(current_date, "%Y-%m-%d")) * 1000)
        instance_time = int(round(time.time() * 1000))
        time_params_dict = {'{{currentDate}}': current_date, '{{currentTime}}': current_time,
                            '{{instanceTime}}': instance_time, '{{instanceDate}}': instance_date}
        public_headers_str = json.dumps(public_headers)
        global_params_str = json.dumps(global_params)
        global_params_str = dispose_params(time_params_dict, global_params_str)
        if global_params_str.find('${') != -1 or public_headers_str.find('${'):
            case_log = CaseLog.objects.create(use_case=suite_info.suite_log_case, task_log=taskLog,
                                              global_parameter=global_params_str, callback_parameter='[]',
                                              execute_status=2, success_count=0,
                                              failed_count=0, spend_time=0)
        global_params = json.loads(global_params_str)
        execute_status = True
        for key in global_params:
            value = str(global_params[key])
            if value.find('${') != -1:
                global_params[key] = udf_dispose(value, case_log)
                if not value:
                    execute_status = False
        public_headers_str = dispose_params(global_params, public_headers_str)
        public_headers = json.loads(public_headers_str)
        for key in public_headers:
            value = str(public_headers[key])
            if value.find('${') != -1:
                public_headers[key] = udf_dispose(value, case_log)
                if not value:
                    execute_status = False
        if global_params_str.find('${') != -1 or public_headers_str.find('${'):
            if execute_status:
                case_log.execute_status = 1
            else:
                case_log.execute_status = 0
            case_log.save()
        if not execute_status:
            print('前置函数执行失败，请检查配置。')
            return
        public_headers = merge_dicts(header_dict, public_headers)
        if precondition_case:
            precondition_case_log_id = async_execute_use_case(use_case_id=precondition_case.id,
                                                              taskLog_id=taskLog.id,
                                                              environment_id=environment.id,
                                                              suite_global_params=global_params,
                                                              public_headers=public_headers,
                                                              case_count=case_count, payload={})
            precondition_case_log = CaseLog.objects.get(pk=precondition_case_log_id)
            lead_param = json.loads(precondition_case_log.callback_parameter)
            if precondition_case_log.execute_status == 0:
                print('前置用例执行失败，请检查用例执行情况。')
                return
        else:
            lead_param = None
        for use_case in use_case_list:
            if use_case.environment:
                environment_id = use_case.environment.id
            else:
                environment_id = environment.id
            async_execute_use_case.delay(use_case_id=use_case.case.id, taskLog_id=taskLog.id,
                                         environment_id=environment_id,
                                         suite_global_params=global_params, public_headers=public_headers,
                                         case_count=case_count, payload={},
                                         lead_param=lead_param)
        msg = name + '调度任务执行完成'
        print(msg)
        return msg
    else:
        return '当前时间%s未在调度时间段(%s-%s)' % (str(TestSuite.timing), str(start_time), str(end_time))


@shared_task
def jenkins_trigger_suite_execute(job_id, serializer_class_data, suite_id, name, header_dict):
    time.sleep(60)
    suite_info = TestSuite.objects.get(pk=suite_id)
    environment = suite_info.environment
    try:
        global_params = json.loads(suite_info.global_params)
    except:
        global_params = {}
    try:
        public_headers = json.loads(suite_info.public_headers)
    except:
        public_headers = {}
    precondition_case = suite_info.precondition_case
    case_list = TestSuiteCases.objects.filter(delete=False, test_suite=suite_info)
    case_count = case_list.count()
    # use_case_id_list = [case.case.id for case in case_list]
    use_case_list = [case for case in case_list]
    taskLog = TaskLog.objects.create(job_id=job_id, name=name, execute_status=2, mode=2,
                                     tags=suite_info.suite_class.name,
                                     execute_type=1, success_count=0, failed_count=0, executor='jenkins')
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    instance_date = int(time.mktime(time.strptime(current_date, "%Y-%m-%d")) * 1000)
    instance_time = int(round(time.time() * 1000))
    time_params_dict = {'{{currentDate}}': current_date, '{{currentTime}}': current_time,
                        '{{instanceTime}}': instance_time, '{{instanceDate}}': instance_date}
    public_headers_str = json.dumps(public_headers)
    global_params_str = json.dumps(global_params)
    global_params_str = dispose_params(time_params_dict, global_params_str)
    if global_params_str.find('${') != -1 or public_headers_str.find('${'):
        case_log = CaseLog.objects.create(use_case=suite_info.suite_log_case, task_log=taskLog,
                                          global_parameter=global_params_str, callback_parameter='[]',
                                          execute_status=2, success_count=0,
                                          failed_count=0, spend_time=0)
    global_params = json.loads(global_params_str)
    execute_status = True
    for key in global_params:
        value = str(global_params[key])
        if value.find('${') != -1:
            global_params[key] = udf_dispose(value, case_log)
            if not value:
                execute_status = False
    public_headers_str = dispose_params(global_params, public_headers_str)
    public_headers = json.loads(public_headers_str)
    for key in public_headers:
        value = str(public_headers[key])
        if value.find('${') != -1:
            public_headers[key] = udf_dispose(value, case_log)
            if not value:
                execute_status = False
    if global_params_str.find('${') != -1 or public_headers_str.find('${'):
        if execute_status:
            case_log.execute_status = 1
        else:
            case_log.execute_status = 0
        case_log.save()
    if not execute_status:
        print('前置函数执行失败，请检查配置。')
        return
    public_headers = merge_dicts(header_dict, public_headers)
    if precondition_case:
        precondition_case_log_id = async_execute_use_case(use_case_id=precondition_case.id,
                                                          taskLog_id=taskLog.id,
                                                          environment_id=environment.id,
                                                          suite_global_params=global_params,
                                                          public_headers=public_headers,
                                                          case_count=case_count,
                                                          payload=serializer_class_data)
        precondition_case_log = CaseLog.objects.get(pk=precondition_case_log_id)
        lead_param = json.loads(precondition_case_log.callback_parameter)
        if precondition_case_log.execute_status == 0:
            # response.code = 3000
            # response.msg = '前置用例执行失败，请检查用例执行情况。'
            # return JsonResponse(response.get_dic, safe=False)
            print('前置用例执行失败，请检查用例执行情况。')
            return
    else:
        lead_param = None
    for use_case in use_case_list:
        if use_case.environment:
            environment_id = use_case.environment.id
        else:
            environment_id = environment.id
        async_execute_use_case.delay(use_case_id=use_case.case.id, taskLog_id=taskLog.id,
                                     environment_id=environment_id,
                                     suite_global_params=global_params,
                                     public_headers=public_headers,
                                     case_count=case_count, payload=serializer_class_data,
                                     lead_param=lead_param)
