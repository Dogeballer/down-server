import uuid

from django.shortcuts import render
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from down.CommonStandards import *
from executor.UseCaseExecutor import use_case_executor, instantiation_time, dispose_params
from executor.getUacToken import GetToken
from executor.get_auth_header import GetAuthHeader
from interfaces.views import merge_dicts
from test_suite.filter import *
from test_suite.models import *
from test_suite.serializers import *
from rest_framework import viewsets, generics, filters, permissions
from test_suite.tasks import jenkins_trigger_suite_execute
# Create your views here.
from usecases.tasks import async_execute_use_case, udf_dispose


class TestSuiteClassList(StandardListAPI):
    queryset = TestSuiteClass.objects.filter(parent=0, delete=False)
    serializer_class = TestSuiteClassSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = self.list_structure(serializer.data)
            response = ResponseStandard()
            response.data["items"] = data
            response.msg = '操作成功'
            return Response(response.get_dic)

    def list_structure(self, data):
        parent_list = data
        for item in parent_list:
            children_list = TestSuiteClass.objects.filter(parent=item['id'], delete=False).values()
            item['testSuiteList'] = TestSuite.objects.filter(suite_class_id=item['id'], delete=False).values()
            item['children'] = self.parent_item(children_list)
        return data

    def parent_item(self, children_list):
        children_return = []
        for item in children_list:
            children_list = TestSuiteClass.objects.filter(parent=item['id'], delete=False).values()
            item['children'] = self.parent_item(children_list)
            item['testSuiteList'] = TestSuite.objects.filter(suite_class_id=item['id'], delete=False).values()
            children_return.append(item)
        return children_return


class TestSuiteClassCreate(StandardCreateAPI):
    queryset = TestSuiteClass.objects.all()
    serializer_class = TestSuiteClassSerializer
    permission_classes = (IsAuthenticated,)


class TestSuiteClassDetail(StandardRetrieveAPI):
    queryset = TestSuiteClass.objects.all()
    serializer_class = TestSuiteClassSerializer
    permission_classes = (IsAuthenticated,)


class TestSuiteClassUpdate(StandardUpdateAPI):
    queryset = TestSuiteClass.objects.all()
    serializer_class = TestSuiteClassSerializer
    permission_classes = (IsAuthenticated,)


class TestSuiteClassDelete(StandardDeleteAPI):
    queryset = TestSuiteClass.objects.all()
    serializer_class = TestSuiteClassSerializer
    permission_classes = (IsAuthenticated,)


class UpdateTestSuiteClassStatus(generics.UpdateAPIView):
    queryset = TestSuiteClass.objects.all()
    serializer_class = TestSuiteClassSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = not instance.status
        instance.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class TestSuitePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 1000
    mode_options = {0: '手动执行', 1: '调度执行'}
    type_options = {0: '按项目', 1: '按模块', 2: '自定义'}
    execute_frequency_options = {0: '每日执行', 1: '每周一次'}

    def get_paginated_response(self, data):
        for item in data:
            # try:
            # timing = datetime.strptime(item['timing'], "%Y-%m-%d %H:%M:%S")
            # timing = datetime.strptime(item['timing'], "%H:%M")
            # item['timing'] = time.mktime(timing.timetuple()) * 1000
            # item['timing'] = timing.time()
            # except:
            #     item['timing'] = None
            # item['type'] = self.type_options[item['type']]
            # print(item['timing'])
            item['mode'] = self.mode_options[item['mode']]
            item['execute_frequency'] = self.execute_frequency_options[item['execute_frequency']]
            item['environment'] = Environment.objects.get(pk=item['environment']).name
            create_time = datetime.strptime(item['create_time'], "%Y-%m-%d %H:%M:%S")
            update_time = datetime.strptime(item['update_time'], "%Y-%m-%d %H:%M:%S")
            item['create_time'] = time.mktime(create_time.timetuple()) * 1000
            item['update_time'] = time.mktime(update_time.timetuple()) * 1000
        return Response(OrderedDict([
            ('code', 0),
            ('total', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', {'items': data}),
            ('msg', '操作成功')
        ]))


class TestSuiteList(StandardListAPI):
    queryset = TestSuite.objects.filter(delete=False)
    serializer_class = TestSuiteSerializer
    pagination_class = TestSuitePagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TestSuiteFilter
    ordering_fields = ('name', 'type', 'mode',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = ResponseStandard()
            data_list = serializer.data
            for data in data_list:
                create_time = datetime.strptime(data['create_time'], "%Y-%m-%d %H:%M:%S")
                update_time = datetime.strptime(data['update_time'], "%Y-%m-%d %H:%M:%S")
                data['create_time'] = time.mktime(create_time.timetuple()) * 1000
                data['update_time'] = time.mktime(update_time.timetuple()) * 1000
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class TestSuiteCreate(StandardCreateAPI):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        data = request.data
        name = data['name']
        suite_log_case = UseCases.objects.create(name=name + '套件日志用例', type=0, describe=name + '套件日志用例', user='system',
                                                 delete=True)
        data['suite_log_case'] = suite_log_case.id
        try:
            timing = data.pop('timing') / 1000
            timing = datetime.strftime(datetime.fromtimestamp(timing), "%H:%M")
            data['timing'] = timing
        except:
            pass
        global_params = data['global_params']
        for key in global_params:
            if global_params[key].find('"') != -1 or key.find('"') != -1:
                response.code = 3000
                response.msg = '全局参数不能含有json相关字符'
                return JsonResponse(response.get_dic)
            slice_int = str(global_params[key]).find('instantiation_time(')
            if slice_int != -1:
                string_param = str(global_params[key])[slice_int + 19:-1]
                time_param = string_param.split(',')
                type = time_param[0].lower().replace("'", "")
                value = int(time_param[1])
                format = time_param[2].replace("'", "")
                try:
                    instantiation_datetime = instantiation_time(type, value, format)
                except:
                    response.code = 3000
                    response.msg = '全局参数函数校验失败，请检查参数'
                    return JsonResponse(response.get_dic)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class TestSuiteDetail(StandardRetrieveAPI):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteDetailSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        try:
            timing = datetime.strftime(datetime.today(), '%Y-%m-%d') + ' ' + data['timing']
            timing = datetime.strptime(timing, "%Y-%m-%d %H:%M:%S")
            data['timing'] = time.mktime(timing.timetuple()) * 1000
        except:
            data['timing'] = None
        cases = data['cases']
        try:
            global_params = json.loads(data.get('global_params', ''))
        except:
            global_params = []
        try:
            public_headers = json.loads(data.get('public_headers', ''))
        except:
            public_headers = []
        data['global_params'] = global_params
        data['public_headers'] = public_headers
        for case in cases:
            case_type = {0: '正向用例', 1: '异常用例', 2: '场景用例', 3: '流程用例'}
            caseInfo = UseCases.objects.get(pk=case['case'])
            case['id'] = caseInfo.id
            case['name'] = caseInfo.name
            modules = caseInfo.modules
            case['modules'] = modules.name
            case['project'] = modules.project.name
            case['type'] = case_type[caseInfo.type]
            case['user'] = caseInfo.user
            try:
                global_params = json.loads(case.get('global_params', ''))
            except:
                global_params = []
            case['global_params'] = global_params
        response.data = data
        return Response(response.get_dic)


class TestSuiteUpdate(StandardUpdateAPI):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteCreateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        name = data['name']
        suite_log_case = instance.suite_log_case
        if not suite_log_case:
            suite_log_case = UseCases.objects.create(name=name + '套件日志用例', type=0, describe=name + '套件日志用例',
                                                     modules=None,
                                                     user='system', delete=True)
            instance.suite_log_case = suite_log_case
            instance.save()
        else:
            suite_log_case.name = name + '套件日志用例'
            suite_log_case.save()
        try:
            timing = data.pop('timing') / 1000
            # timing = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timing) / 1000))
            # timing = datetime.fromtimestamp(timing).time()
            timing = datetime.strftime(datetime.fromtimestamp(timing), "%H:%M")
            # timing = datetime.strptime(timing, "%Y-%m-%d %H:%M:%S")
            data['timing'] = timing
        except:
            pass
        global_params = data['global_params']
        for key in global_params:
            if global_params[key].find('"') != -1 or key.find('"') != -1:
                response.code = 3000
                response.msg = '全局参数不能含有json相关字符'
                return JsonResponse(response.get_dic)
            slice_int = str(global_params[key]).find('instantiation_time(')
            if slice_int != -1:
                string_param = str(global_params[key])[slice_int + 19:-1]
                time_param = string_param.split(',')
                type = time_param[0].lower().replace("'", "")
                value = int(time_param[1])
                format = time_param[2].replace("'", "")
                try:
                    instantiation_datetime = instantiation_time(type, value, format)
                except:
                    response.code = 3000
                    response.msg = '全局参数函数校验失败，请检查参数'
                    return JsonResponse(response.get_dic)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if serializer.is_valid(raise_exception=False):
            self.perform_update(serializer)
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return Response(response.get_dic)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(response.get_dic)


class TestSuiteDelete(StandardDeleteAPI):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete = True
        instance.periodic_task.enabled = False
        instance.periodic_task.save()
        instance.save(update_fields=['delete'])
        response = ResponseStandard()
        response.msg = '操作成功'
        return Response(response.get_dic)


class TestSuiteBatchDelete(StandardDeleteAPI):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        delete_list = request.data['ids']
        for suite_id in delete_list:
            suite = TestSuite.objects.get(pk=suite_id)
            suite.delete = True
            suite.periodic_task.enabled = False
            suite.periodic_task.save()
            suite.save(update_fields=['delete'])
        response = ResponseStandard()
        response.msg = '操作成功'
        return Response(response.get_dic)


class UpdateTestSuiteStatus(generics.UpdateAPIView):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        status = not instance.status
        instance.status = status
        instance.periodic_task.enabled = status
        instance.save()
        instance.periodic_task.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class SuiteExecute(generics.GenericAPIView):
    serializer_class = TestSuiteSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        suite_id = request.GET.get('id')
        suite_info = TestSuite.objects.get(pk=suite_id)
        name = suite_info.name
        environment = suite_info.environment
        uac_url = environment.uac_url
        try:
            global_params = json.loads(suite_info.global_params)
        except:
            global_params = {}
        try:
            public_headers = json.loads(suite_info.public_headers)
        except:
            public_headers = {}
        case_list = TestSuiteCases.objects.filter(delete=False, test_suite=suite_info)
        job_id = uuid.uuid4()
        taskLog = TaskLog.objects.create(job_id=job_id, name=name, execute_status=2, mode=0, tags=name,
                                         execute_type=1, success_count=0, failed_count=0, executor='调度')
        try:
            # token = GetToken().access_token_get()
            token = GetToken(uac_url).uacV2_token_get()
        except:
            response.code = 3000
            response.msg = 'UAC网络状态错误，请检查网络状态'
            return JsonResponse(response.get_dic, safe=False)
        use_case_executor(case_list, taskLog, environment, token, global_params, public_headers, 1)
        taskLog.success_count = CaseLog.objects.filter(task_log=taskLog, execute_status=1).count()
        taskLog.failed_count = CaseLog.objects.filter(task_log=taskLog, execute_status=0).count()
        taskLog.execute_status = 1
        end_time = datetime.now()
        start_time = taskLog.start_time
        taskLog.end_time = end_time
        spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
        taskLog.spend_time = spend_time
        taskLog.save()
        response.data = {"job_id": job_id}
        response.msg = '操作成功'
        return JsonResponse(response.get_dic, safe=False)


class AsyncSuiteExecute(generics.GenericAPIView):
    serializer_class = TestSuiteSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        suite_id = request.GET.get('id')
        suite_info = TestSuite.objects.get(pk=suite_id)
        name = suite_info.name
        tags = suite_info.suite_class.name
        environment = suite_info.environment
        authentication_environment = environment.authentication_environment
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
        # use_case_id_list = [case.case.id for case in case_list]
        use_case_list = [case for case in case_list]
        case_count = case_list.count()
        job_id = uuid.uuid4()
        taskLog = TaskLog.objects.create(job_id=job_id, name=name, execute_status=2, mode=0, tags=tags,
                                         execute_type=1, success_count=0, failed_count=0, executor='调度')
        headers_get = GetAuthHeader(authentication_environment)
        header_str, headers_get_status = headers_get.header_get()
        if not headers_get_status:
            response.code = 3000
            response.msg = "鉴权环境获取请求头异常"
            return JsonResponse(response.get_dic, safe=False)
        try:
            header_dict = json.loads(header_str)
        except:
            response.code = 3000
            response.msg = "鉴权环境获取请求头异常"
            return JsonResponse(response.get_dic, safe=False)
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                                              execute_status=2, success_count=0, end_time=datetime.now(),
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
            response.code = 3000
            response.msg = '前置函数执行失败，请检查配置。'
            return JsonResponse(response.get_dic, safe=False)
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
                response.code = 3000
                response.msg = '前置用例执行失败，请检查用例执行情况。'
                return JsonResponse(response.get_dic, safe=False)
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
                                         case_count=case_count, payload={}, lead_param=lead_param)
        response.data = {"task_id": job_id}
        response.msg = '操作成功'
        return JsonResponse(response.get_dic, safe=False)


class JenkinsTrigger(generics.GenericAPIView):
    serializer_class = JenkinsTriggerExecuteSerializer

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                ci_task_name = serializer_class.data.get('ci_task_name')
                ci_task_build_id = serializer_class.data.get('ci_task_build_id')
                ci_env = serializer_class.data.get('ci_env')
                code = ci_task_name.lower() + '-' + ci_env.lower()
                case_suite_list = TestSuite.objects.filter(code=code, status=True, delete=False)
                if len(case_suite_list) == 0:
                    response.code = 3000
                    response.msg = '参数传入错误，请检查参数'
                    return JsonResponse(response.get_dic, safe=False)
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            job_id = uuid.uuid4()
            for suite_info in case_suite_list:
                name = ci_task_name + '-' + suite_info.name
                environment = suite_info.environment
                authentication_environment = environment.authentication_environment
                headers_get = GetAuthHeader(authentication_environment)
                header_str, headers_get_status = headers_get.header_get()
                if not headers_get_status:
                    response.code = 3000
                    response.msg = "鉴权环境获取请求头异常"
                    return JsonResponse(response.get_dic, safe=False)
                try:
                    header_dict = json.loads(header_str)
                except:
                    response.code = 3000
                    response.msg = "鉴权环境获取请求头异常"
                    return JsonResponse(response.get_dic, safe=False)
                jenkins_trigger_suite_execute.delay(job_id, serializer_class.data, suite_info.id, name, header_dict)
            response.data = {"job_id": job_id}
            response.msg = '操作成功'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '写入失败,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)
