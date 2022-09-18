import time
from concurrent.futures import ThreadPoolExecutor

from django.db.models import Count, Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from down.CommonStandards import *
from executor.UseCaseExecutor import use_case_executor, instantiation_time
from executor.getUacToken import GetToken
from executor.get_auth_header import GetAuthHeader
from executor.mqtt_publish_client import MQTTPublishClient
from executor.sql_executor import SqlExecutor
from interfaces.models import *
from interfaces.views import merge_dicts
from system_settings.models import MQTTClient
from .filter import *
from .serializers import *
from rest_framework import viewsets, generics, filters, permissions
from .models import *
from projects.models import Modules, Projects, Environment
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
import json

from .tasks import async_execute_use_case


class UseCasesList(StandardListAPI):
    queryset = UseCases.objects.filter(delete=False)
    serializer_class = UseCasesSerializer
    pagination_class = StandardPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = UseCasesFilter
    ordering_fields = ('name', 'user', 'modules',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def get_project(self):
        return Projects.objects.get(pk=self.request.query_params.get('project', None))

    def get_queryset(self):
        try:
            project = self.get_project()
            modules_list = Modules.objects.filter(project=project)
            return self.queryset.filter(modules__in=modules_list)
        except:
            return self.queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        case_type = {0: '正向用例', 1: '异常用例', 2: '场景用例', 3: '流程用例'}
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            data_list = []
            for usecase in data:
                global_params = usecase.get('global_params', {})
                params = usecase.get('params', {})
                if global_params:
                    try:
                        usecase['global_params'] = json.loads(global_params)
                    except:
                        usecase['global_params'] = {}
                else:
                    usecase['global_params'] = {}
                if params:
                    try:
                        usecase['params'] = json.loads(params)
                    except:
                        usecase['params'] = {}
                else:
                    usecase['params'] = {}
                usecase['type'] = case_type[usecase['type']]
                module = Modules.objects.get(pk=usecase['modules'])
                usecase['modules'] = module.name
                usecase['project'] = module.project.name
                data_list.append(usecase)
            return self.get_paginated_response(data_list)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            response = list_return(data)
            return Response(response.get_dic)


class SuiteUseCasesList(StandardListAPI):
    queryset = UseCases.objects.filter(delete=False)
    serializer_class = UseCasesSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = UseCasesFilter
    ordering_fields = ('name', 'user', 'modules',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def get_project(self):
        return Projects.objects.get(pk=self.request.query_params.get('project', None))

    def get_queryset(self):
        try:
            project = self.get_project()
            modules_list = Modules.objects.filter(project=project)
            return self.queryset.filter(modules__in=modules_list)
        except:
            return self.queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        case_type = {0: '正向用例', 1: '异常用例', 2: '场景用例', 3: '流程用例'}
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        data_list = []
        for usecase in data:
            global_params = usecase.get('global_params', {})
            params = usecase.get('params', {})
            if global_params:
                try:
                    usecase['global_params'] = json.loads(global_params)
                except:
                    usecase['global_params'] = {}
            else:
                usecase['global_params'] = {}
            if params:
                try:
                    usecase['params'] = json.loads(params)
                except:
                    usecase['params'] = {}
            else:
                usecase['params'] = {}
            usecase['type'] = case_type[usecase['type']]
            module = Modules.objects.get(pk=usecase['modules'])
            usecase['modules'] = module.name
            usecase['project'] = module.project.name
            data_list.append(usecase)
        response = ResponseStandard()
        response.data["items"] = data_list
        response.msg = '操作成功'
        return Response(response.get_dic)


class UseCasesCreate(StandardCreateAPI):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        data = request.data
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
        global_params = json.dumps(data['global_params'])
        data['global_params'] = global_params
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response.data = serializer.data
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class UseCasesDetail(StandardRetrieveAPI):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        params = {}
        steps = CaseSteps.objects.filter(use_case=instance, delete=False)
        for step in steps:
            # if step.case_interface:
            # call_back_params = InterfaceCallBackParams.objects.filter(return_interface=step.case_interface,
            #                                                           delete=False)
            call_back_params = StepCallBackParams.objects.filter(step=step,
                                                                 delete=False)
            for param in call_back_params:
                params[param.param_name] = ''
        params = json.dumps(params)
        instance.params = params
        instance.save()
        data = serializer.data
        global_params = json.loads(data.get('global_params', ''))
        params = json.loads(data.get('params', ''))
        data['params'] = params
        data['global_params'] = global_params
        response.data = data
        return Response(response.get_dic)


class UseCasesUpdate(StandardUpdateAPI):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
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
        global_params = json.dumps(data['global_params'])
        data['global_params'] = global_params
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


class UpdateUseCaseStatus(generics.UpdateAPIView):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        use_case = self.get_object()
        use_case.status = not use_case.status
        use_case.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class CopyUseCase(generics.CreateAPIView):
    queryset = UseCases.objects.all()
    serializer_class = UseCaseCopySerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            use_case = UseCases.objects.get(pk=data['caseId'])
            case_steps = CaseSteps.objects.filter(use_case=use_case)
            use_case.name = use_case.name + ' 副本'
            use_case.pk = None
            use_case.save()
            for case_step in case_steps:
                case_asserts = CaseAssert.objects.filter(case_step=case_step)
                step_polls = CaseStepPoll.objects.filter(case_step=case_step)
                circular_keys = StepCircularKey.objects.filter(case_step=case_step)
                call_back_params = StepCallBackParams.objects.filter(step=case_step)
                step_operations = StepForwardAfterOperation.objects.filter(step=case_step)
                case_step.pk = None
                case_step.use_case = use_case
                case_step.save()
                for case_assert in case_asserts:
                    case_assert.pk = None
                    case_assert.case_step = case_step
                    copy_assert = case_assert.save()
                for step_poll in step_polls:
                    step_poll.pk = None
                    step_poll.case_step = case_step
                    copy_step_poll = step_poll.save()
                for circular_key in circular_keys:
                    circular_key.pk = None
                    circular_key.case_step = case_step
                    circular_key = circular_key.save()
                for call_back_param in call_back_params:
                    call_back_param.pk = None
                    call_back_param.step = case_step
                    call_back_param = call_back_param.save()
                for step_operation in step_operations:
                    step_operation.pk = None
                    step_operation.step = case_step
                    step_operation = step_operation.save()
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class CopyCaseStep(generics.CreateAPIView):
    queryset = CaseSteps.objects.all()
    serializer_class = CaseStepCopySerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            case_step = CaseSteps.objects.get(pk=serializer.data.get("stepId"))
            use_case = case_step.use_case
            highest_step_sort = CaseSteps.objects.filter(use_case=use_case, delete=False).aggregate(Max('sort'))[
                'sort__max']
            case_asserts = CaseAssert.objects.filter(case_step=case_step)
            step_polls = CaseStepPoll.objects.filter(case_step=case_step)
            circular_keys = StepCircularKey.objects.filter(case_step=case_step)
            call_back_params = StepCallBackParams.objects.filter(step=case_step)
            step_operations = StepForwardAfterOperation.objects.filter(step=case_step)
            case_step.pk = None
            case_step.sort = highest_step_sort + 1
            case_step.save()
            for case_assert in case_asserts:
                case_assert.pk = None
                case_assert.case_step = case_step
                copy_assert = case_assert.save()
            for step_poll in step_polls:
                step_poll.pk = None
                step_poll.case_step = case_step
                copy_step_poll = step_poll.save()
            for circular_key in circular_keys:
                circular_key.pk = None
                circular_key.case_step = case_step
                circular_key = circular_key.save()
            for call_back_param in call_back_params:
                call_back_param.pk = None
                call_back_param.step = case_step
                call_back_param = call_back_param.save()
            for step_operation in step_operations:
                step_operation.pk = None
                step_operation.step = case_step
                step_operation = step_operation.save()
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class UseCasesDelete(StandardDeleteAPI):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)


class UseCasesTree(StandardListAPI):
    queryset = Projects.objects.filter(status=True)
    serializer_class = UseCasesTreeSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        response = ResponseStandard()
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for project in data:
            for module in project['children']:
                case_list = []
                for case in module['children']:
                    if case['delete'] == False:
                        case_list.append(case)
                module['children'] = case_list
        response.data['items'] = data
        response.msg = '操作成功'
        return Response(response.get_dic)


class CaseStepsList(StandardListAPI):
    queryset = CaseSteps.objects.filter(delete=False)
    serializer_class = CaseStepsSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CaseStepsFilter
    ordering = ('sort',)
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
            data_list = []
            for data in serializer.data:
                param = data['param']
                body = data['body']
                try:
                    data['param'] = json.loads(param)
                except:
                    data['param'] = {}
                data_list.append(data)
            response.data["items"] = data_list
            response.msg = '操作成功'
            return Response(response.get_dic)


class CaseStepsCreate(StandardCreateAPI):
    queryset = CaseSteps.objects.all()
    serializer_class = CaseStepsCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            response.data = {"id": serializer.instance.id}
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class CaseStepsDetail(StandardRetrieveAPI):
    queryset = CaseSteps.objects.all()
    serializer_class = CaseStepsSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepsUpdate(StandardUpdateAPI):
    queryset = CaseSteps.objects.all()
    serializer_class = CaseStepsCreateSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepsDelete(StandardDeleteAPI):
    queryset = CaseSteps.objects.all()
    serializer_class = CaseStepsSerializer
    permission_classes = (IsAuthenticated,)


class CaseAssertList(StandardListAPI):
    queryset = CaseAssert.objects.filter(delete=False)
    serializer_class = CaseAssertSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CaseAssertFilter
    permission_classes = (IsAuthenticated,)


class CaseAssertCreate(StandardCreateAPI):
    queryset = CaseAssert.objects.all()
    serializer_class = CaseAssertSerializer
    permission_classes = (IsAuthenticated,)


class CaseAssertDetail(StandardRetrieveAPI):
    queryset = CaseAssert.objects.all()
    serializer_class = CaseAssertSerializer
    permission_classes = (IsAuthenticated,)


class CaseAssertUpdate(StandardUpdateAPI):
    queryset = CaseAssert.objects.all()
    serializer_class = CaseAssertSerializer
    permission_classes = (IsAuthenticated,)


class CaseAssertDelete(StandardDeleteAPI):
    queryset = CaseAssert.objects.all()
    serializer_class = CaseAssertSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepPollList(StandardListAPI):
    queryset = CaseStepPoll.objects.filter(delete=False)
    serializer_class = CaseStepPollSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CaseStepPollFilter
    permission_classes = (IsAuthenticated,)


class CaseStepPollCreate(StandardCreateAPI):
    queryset = CaseStepPoll.objects.all()
    serializer_class = CaseStepPollSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepPollDetail(StandardRetrieveAPI):
    queryset = CaseStepPoll.objects.all()
    serializer_class = CaseStepPollSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepPollUpdate(StandardUpdateAPI):
    queryset = CaseStepPoll.objects.all()
    serializer_class = CaseStepPollSerializer
    permission_classes = (IsAuthenticated,)


class CaseStepPollDelete(StandardDeleteAPI):
    queryset = CaseStepPoll.objects.all()
    serializer_class = CaseStepPollSerializer
    permission_classes = (IsAuthenticated,)


class StepCircularKeyList(StandardListAPI):
    queryset = StepCircularKey.objects.filter(delete=False)
    serializer_class = StepCircularKeySerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = StepCircularKeyFilter
    permission_classes = (IsAuthenticated,)


class StepCircularKeyCreate(StandardCreateAPI):
    queryset = StepCircularKey.objects.all()
    serializer_class = StepCircularKeySerializer
    permission_classes = (IsAuthenticated,)


class StepCircularKeyDetail(StandardRetrieveAPI):
    queryset = StepCircularKey.objects.all()
    serializer_class = StepCircularKeySerializer
    permission_classes = (IsAuthenticated,)


class StepCircularKeyUpdate(StandardUpdateAPI):
    queryset = StepCircularKey.objects.all()
    serializer_class = StepCircularKeySerializer
    permission_classes = (IsAuthenticated,)


class StepCircularKeyDelete(StandardDeleteAPI):
    queryset = StepCircularKey.objects.all()
    serializer_class = StepCircularKeySerializer
    permission_classes = (IsAuthenticated,)


class StepForwardAfterOperationList(StandardListAPI):
    queryset = StepForwardAfterOperation.objects.filter(delete=False)
    serializer_class = StepForwardAfterOperationSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = StepForwardAfterOperationFilter
    permission_classes = (IsAuthenticated,)


class StepForwardAfterOperationCreate(StandardCreateAPI):
    queryset = StepForwardAfterOperation.objects.all()
    serializer_class = StepForwardAfterOperationSerializer
    permission_classes = (IsAuthenticated,)


class StepForwardAfterOperationDetail(StandardRetrieveAPI):
    queryset = StepForwardAfterOperation.objects.all()
    serializer_class = StepForwardAfterOperationSerializer
    permission_classes = (IsAuthenticated,)


class StepForwardAfterOperationUpdate(StandardUpdateAPI):
    queryset = StepForwardAfterOperation.objects.all()
    serializer_class = StepForwardAfterOperationSerializer
    permission_classes = (IsAuthenticated,)


class StepForwardAfterOperationDelete(StandardDeleteAPI):
    queryset = StepForwardAfterOperation.objects.all()
    serializer_class = StepForwardAfterOperationSerializer
    permission_classes = (IsAuthenticated,)


class TaskExecute(generics.GenericAPIView):
    serializer_class = TaskExecuteSerializer

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                # pytest使用 values方法
                # use_case_list = UseCases.objects.filter(pk__in=serializer_class.data.get('useCaseList'),
                #                                         delete=False, status=True).values()
                use_case_list = UseCases.objects.filter(pk__in=serializer_class.data.get('useCaseList'),
                                                        delete=False, status=True)
                execute_type = serializer_class.data.get('type')
                mode = serializer_class.data.get('mode')
                executor = serializer_class.data.get('executor')
                environment_id = serializer_class.data.get('environment_id')
                environment = Environment.objects.get(pk=environment_id)
                uac_url = environment.uac_url
                if len(use_case_list) == 0:
                    response.code = 3000
                    response.msg = '参数传入错误，请检查参数'
                    return JsonResponse(response.get_dic, safe=False)
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            if execute_type == 0:
                if len(use_case_list) > 1:
                    name = "手动执行-" + time.strftime("%Y%m%d%HH%MM", time.localtime())
                else:
                    # name = "手动执行-" + use_case_list[0]['name']
                    name = "手动执行-" + use_case_list[0].name
                try:
                    token = GetToken(uac_url).uacV2_token_get()
                except:
                    response.code = 3000
                    response.msg = 'UAC网络状态错误，请检查网络状态'
                    return JsonResponse(response.get_dic, safe=False)
                taskLog = TaskLog.objects.create(name=name, executor=executor, execute_status=2, mode=mode, tags="手动执行",
                                                 execute_type=execute_type, success_count=0, failed_count=0)
                # use_cases = [useCase['id'] for useCase in use_case_list]
                # executor_msg = {
                #     "taskLog": taskLog.id,
                #     "useCaseList": use_cases,
                #     "environmentId": environment_id
                # }
                # executor_msg = json.dumps(executor_msg)
                # with (open('./executor/' + "test_data.json", "w")) as f:
                #     f.write(executor_msg)
                #     f.close()
                # time.sleep(1)
                # command = 'pytest ' + os.path.join(BASE_DIR, 'executor/') + "test_interface.py"
                # print(command)
                # os.system(command)
                # pytest框架执行
                # pytest.main(["-s", "./executor/test_interface.py"])
                # 方法执行
                use_case_executor(use_case_list, taskLog, environment, token, {}, {}, 0)
            elif execute_type == 1:
                print(1)
            taskLog.success_count = CaseLog.objects.filter(task_log=taskLog, execute_status=1).count()
            taskLog.failed_count = CaseLog.objects.filter(task_log=taskLog, execute_status=0).count()
            taskLog.execute_status = 1
            end_time = datetime.now()
            start_time = taskLog.start_time
            taskLog.end_time = end_time
            spend_time = round((end_time - start_time).total_seconds() * 1000, 2)
            taskLog.spend_time = spend_time
            taskLog.save()
            # if os.path.exists("./executor/test_data.json"):
            #     os.remove("./executor/test_data.json")
            # else:
            #     print("The file does not exist")
            response.msg = '操作成功'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '写入失败,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class UseCaseAsyncExecute(generics.GenericAPIView):
    serializer_class = TaskExecuteSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                use_case_id_list = serializer_class.data.get('useCaseList')
                use_case_list = UseCases.objects.filter(pk__in=use_case_id_list,
                                                        delete=False, status=True)
                case_count = use_case_list.count()
                execute_type = serializer_class.data.get('type')
                mode = serializer_class.data.get('mode')
                executor = serializer_class.data.get('executor')
                environment_id = serializer_class.data.get('environment_id')
                environment = Environment.objects.get(pk=environment_id)
                authentication_environment = environment.authentication_environment
                if len(use_case_list) == 0:
                    response.code = 3000
                    response.msg = '参数传入错误，请检查参数'
                    return JsonResponse(response.get_dic, safe=False)
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            if len(use_case_list) > 1:
                name = "手动执行-" + time.strftime("%Y%m%d%HH%MM", time.localtime())
            else:
                # name = "手动执行-" + use_case_list[0]['name']
                name = "手动执行-" + use_case_list[0].name
            # try:
            #     token = GetToken(uac_url).uacV2_token_get()
            # except:
            #     response.code = 3000
            #     response.msg = 'UAC网络状态错误，请检查网络状态'
            #     return JsonResponse(response.get_dic, safe=False)
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
            taskLog = TaskLog.objects.create(name=name, executor=executor, execute_status=2, mode=mode, tags="手动执行",
                                             execute_type=execute_type, success_count=0, failed_count=0)
            for use_case_id in use_case_id_list:
                async_execute_use_case(use_case_id=use_case_id, taskLog_id=taskLog.id,
                                       environment_id=environment_id,
                                       suite_global_params={}, public_headers=header_dict,
                                       case_count=case_count,
                                       payload={})
                # async_execute_use_case(use_case_id=use_case_id, taskLog_id=taskLog.id,
                #                        environment_id=environment_id,
                #                        token=token, suite_global_params={}, public_headers={},
                #                        case_count=case_count,
                #                        payload={})
            response.msg = '操作成功'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '写入失败,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class LogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 1000

    def get_paginated_response(self, data):
        for item in data:
            try:
                start_time = datetime.strptime(item['start_time'], "%Y-%m-%d %H:%M:%S")
                item['start_time'] = time.mktime(start_time.timetuple()) * 1000
            except:
                item['start_time'] = None
            try:
                end_time = datetime.strptime(item['end_time'], "%Y-%m-%d %H:%M:%S")
                item['end_time'] = time.mktime(end_time.timetuple()) * 1000
            except:
                item['end_time'] = None
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


class TaskLogTree(StandardListAPI):
    queryset = TaskLog.objects.filter(~Q(mode=0)).values("tags").annotate(counts=Count('id'))
    serializer_class = TaskLogSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TaskLogTreeFilter
    ordering = ('-create_time',)

    def list(self, request, *args, **kwargs):
        jenkins_trigger = {
            "folderName": "CI/CD触发",
            "type": "parent",
            "folderId": -4,
            "contentList": []
        }
        performed_manually = {
            "folderName": "手动执行",
            "type": "parent",
            "folderId": -3,
            "contentList": []
        }
        task_scheduling = {
            "folderName": "任务调度",
            "type": "parent",
            "folderId": -2,
            "contentList": []
        }
        data_list = {
            "folderName": "所有任务",
            "type": "parent",
            "folderId": -1,
            "folderList": [task_scheduling, jenkins_trigger, performed_manually],
            "contentList": []
        }
        execute_date = self.request.query_params.get('execute_date', None)
        job_id = self.request.query_params.get('job_id', None)
        if execute_date:
            execute_date = time.strftime("%Y-%m-%d", time.localtime(int(execute_date) / 1000))
            execute_date = datetime.strptime(execute_date, "%Y-%m-%d")
            self.queryset = self.queryset.filter(execute_date=execute_date)
            task_log_queryset = TaskLog.objects.filter(execute_date=execute_date)
        elif job_id:
            self.queryset = self.queryset.filter(job_id=job_id)
            task_log_queryset = TaskLog.objects.filter(job_id=job_id)
        else:
            task_log_queryset = self.get_queryset().all()
        task_scheduling_list = task_log_queryset.filter(mode=1).values("tags").annotate(
            counts=Count('id'))
        id = 0
        for data in task_scheduling_list:
            data['folderName'] = data['tags']
            data['type'] = 'parent'
            id += 1
            data['folderId'] = id
            task_logs = [{
                'id': task_log['id'],
                'contentName': task_log['name'],
                'executor': task_log['executor'],
                'total': task_log['failed_count'] + task_log['success_count'],
                'failed_count': task_log['failed_count'],
                'spend_time': task_log['spend_time'],
                'type': 'child'
            }
                for task_log in
                task_log_queryset.filter(tags=data['tags'], mode=1).order_by("-create_time").values()]
            data['contentList'] = task_logs
        performed_manually_list = task_log_queryset.filter(mode=0).values("tags").annotate(
            counts=Count('id'))
        for data in performed_manually_list:
            data['folderName'] = data['tags']
            data['type'] = 'parent'
            id += 1
            data['folderId'] = id
            task_logs = [{
                'id': task_log['id'],
                'contentName': task_log['name'],
                'executor': task_log['executor'],
                'total': task_log['failed_count'] + task_log['success_count'],
                'failed_count': task_log['failed_count'],
                'spend_time': task_log['spend_time'],
                'type': 'child'
            }
                for task_log in
                task_log_queryset.filter(tags=data['tags'], mode=0).order_by("-create_time").values()]
            data['contentList'] = task_logs
        jenkins_trigger_list = task_log_queryset.filter(mode=2).values("tags").annotate(
            counts=Count('id'))
        for data in jenkins_trigger_list:
            data['folderName'] = data['tags']
            data['type'] = 'parent'
            id += 1
            data['folderId'] = id
            task_logs = [{
                'id': task_log['id'],
                'contentName': task_log['name'],
                'executor': task_log['executor'],
                'total': task_log['failed_count'] + task_log['success_count'],
                'failed_count': task_log['failed_count'],
                'spend_time': task_log['spend_time'],
                'type': 'child'
            }
                for task_log in
                task_log_queryset.filter(tags=data['tags'], mode=2).order_by("-create_time").values()]
            data['contentList'] = task_logs
        task_scheduling['folderList'] = task_scheduling_list
        performed_manually['folderList'] = performed_manually_list
        jenkins_trigger['folderList'] = jenkins_trigger_list
        response = ResponseStandard()
        response.data["items"] = data_list
        response.msg = '操作成功'
        return Response(response.get_dic)


class TaskLogList(StandardListAPI):
    queryset = TaskLog.objects.filter()
    serializer_class = TaskLogSerializer
    pagination_class = LogPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = TaskLogFilter
    ordering_fields = ('name', 'execute_status', 'executor',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            if start_date and end_date:
                start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(start_date) / 1000))
                end_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_date) / 1000))
                # print(start_date, end_date)
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").isoformat()
                end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").isoformat()
                self.queryset = self.queryset.filter(create_time__range=(start_date, end_date))
                return self.queryset
        except:
            return self.queryset

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
                data['start_time'] = time.mktime(create_time.timetuple()) * 1000
                data['end_time'] = time.mktime(create_time.timetuple()) * 1000
                data['create_time'] = time.mktime(create_time.timetuple()) * 1000
                data['update_time'] = time.mktime(update_time.timetuple()) * 1000
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class CaseLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 1000

    def get_paginated_response(self, data):
        for item in data:
            try:
                start_time = datetime.strptime(item['start_time'], "%Y-%m-%d %H:%M:%S")
                item['start_time'] = time.mktime(start_time.timetuple()) * 1000
            except:
                item['start_time'] = None
            try:
                end_time = datetime.strptime(item['end_time'], "%Y-%m-%d %H:%M:%S")
                item['end_time'] = time.mktime(end_time.timetuple()) * 1000
            except:
                item['end_time'] = None
            create_time = datetime.strptime(item['create_time'], "%Y-%m-%d %H:%M:%S")
            update_time = datetime.strptime(item['update_time'], "%Y-%m-%d %H:%M:%S")
            item['create_time'] = time.mktime(create_time.timetuple()) * 1000
            item['update_time'] = time.mktime(update_time.timetuple()) * 1000
            global_parameter = json.loads(item.get('global_parameter', ''))
            callback_parameter = json.loads(item.get('callback_parameter', ''))
            item['global_parameter'] = global_parameter
            item['callback_parameter'] = callback_parameter
        return Response(OrderedDict([
            ('code', 0),
            ('total', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', {'items': data}),
            ('msg', '操作成功')
        ]))


class CaseLogList(StandardListAPI):
    queryset = CaseLog.objects.filter()
    serializer_class = CaseLogSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CaseLogFilter
    ordering_fields = ('name', 'execute_status', 'spend_time',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            if start_date and end_date:
                start_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(start_date) / 1000))
                end_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_date) / 1000))
                start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").isoformat()
                end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").isoformat()
                self.queryset = self.queryset.filter(create_time__range=(start_date, end_date))
                return self.queryset
        except:
            return self.queryset

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
                data['start_time'] = time.mktime(create_time.timetuple()) * 1000
                data['end_time'] = time.mktime(create_time.timetuple()) * 1000
                data['create_time'] = time.mktime(create_time.timetuple()) * 1000
                data['update_time'] = time.mktime(update_time.timetuple()) * 1000
                global_parameter = json.loads(data.get('global_parameter', ''))
                callback_parameter = json.loads(data.get('callback_parameter', ''))
                data['global_parameter'] = global_parameter
                data['callback_parameter'] = callback_parameter
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class CaseLogPageList(StandardListAPI):
    queryset = CaseLog.objects.filter()
    serializer_class = CaseLogSerializer
    pagination_class = CaseLogPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = CaseLogFilter
    ordering_fields = ('name', 'execute_status', 'spend_time',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            start_date = self.request.query_params.get('start_date', None)
            end_date = self.request.query_params.get('end_date', None)
            execute_date = self.request.query_params.get('execute_date', None)
            job_id = self.request.query_params.get('job_id', None)
            if start_date and end_date:
                start_date = time.strftime("%Y-%m-%d", time.localtime(int(start_date) / 1000))
                end_date = time.strftime("%Y-%m-%d", time.localtime(int(end_date) / 1000))
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
                self.queryset = self.queryset.filter(execute_date__range=(start_date, end_date))
                return self.queryset
            if execute_date:
                execute_date = time.strftime("%Y-%m-%d", time.localtime(int(execute_date) / 1000))
                execute_date = datetime.strptime(execute_date, "%Y-%m-%d")
                self.queryset = self.queryset.filter(execute_date=execute_date)
                return self.queryset
            if job_id:
                task_log_list = TaskLog.objects.filter(job_id=job_id)
                # print(task_log_list)
                self.queryset = self.queryset.filter(task_log__in=task_log_list)
                return self.queryset
        except:
            return self.queryset

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
                data['start_time'] = time.mktime(create_time.timetuple()) * 1000
                data['end_time'] = time.mktime(create_time.timetuple()) * 1000
                data['create_time'] = time.mktime(create_time.timetuple()) * 1000
                data['update_time'] = time.mktime(update_time.timetuple()) * 1000
                global_parameter = json.loads(data.get('global_parameter', ''))
                callback_parameter = json.loads(data.get('callback_parameter', ''))
                data['global_parameter'] = global_parameter
                data['callback_parameter'] = callback_parameter
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class StepLogList(StandardListAPI):
    queryset = CaseStepLog.objects.all()
    serializer_class = StepLogSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = StepLogFilter
    ordering = ('id',)
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
            data_list = []
            for data in serializer.data:
                param = data['param']
                body = data['body']
                step_body = data['step_body']
                assert_result = data['assert_result']
                poll_assert_result = data['poll_assert_result']
                query_field = data['query_field']
                try:
                    data['param'] = json.loads(param)
                except:
                    data['param'] = {}
                try:
                    data['step_body'] = json.loads(step_body)
                except:
                    data['step_body'] = {}
                try:
                    data['assert_result'] = json.loads(assert_result)
                except:
                    data['assert_result'] = {}
                try:
                    data['poll_assert_result'] = json.loads(poll_assert_result)
                except:
                    data['poll_assert_result'] = {}
                try:
                    data['query_field'] = json.loads(query_field)
                except:
                    data['query_field'] = {}
                data_list.append(data)
            response.data["items"] = data_list
            response.msg = '操作成功'
            return Response(response.get_dic)


class UdfLogList(StandardListAPI):
    queryset = UdfLog.objects.all()
    serializer_class = UdfLogSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = UdfLogFilter
    ordering = ('id',)
    permission_classes = (IsAuthenticated,)


class InterfaceSaveCase(StandardCreateAPI):
    queryset = UseCases.objects.all()
    serializer_class = InterfaceSaveCaseSerializer
    permission_classes = (IsAuthenticated,)


class CasePollParam(StandardRetrieveAPI):
    queryset = UseCases.objects.all()
    serializer_class = UseCasesSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        params = []
        steps = CaseSteps.objects.filter(use_case=instance, delete=False)
        for step in steps:
            if step.step_type != 1:
                # call_back_params = InterfaceCallBackParams.objects.filter(return_interface=step.case_interface,
                #                                                           delete=False, type=1).values()
                call_back_params = StepCallBackParams.objects.filter(step=step, type=1,
                                                                     delete=False).values()
                for param in call_back_params:
                    params.append(param)
        response.data["items"] = params
        return Response(response.get_dic)


class StepCallBackParamsCreateList(generics.ListCreateAPIView):
    queryset = StepCallBackParams.objects.filter(delete=False)
    serializer_class = CaseStepCallBackParamsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = StepCallBackParamsFilter
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = list_return(serializer.data)
            response.msg = '操作成功'
            return Response(response.get_dic)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        data = request.data
        param_name = data['param_name']
        type = data['type']
        step = data['step']
        step = CaseSteps.objects.get(pk=step)
        if param_name.find('__') != -1:
            if type == 1:
                if param_name.rfind('__') != len(param_name) - 2:
                    response.code = 3000
                    response.msg = '列表类型回调参数,调用名需未按照格式命名'
                    return Response(response.get_dic)

        else:
            response.code = 3000
            response.msg = '参数调用名未按照格式命名'
            return Response(response.get_dic)
        if serializer.is_valid():
            self.perform_create(serializer)
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class StepCallBackParamsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = StepCallBackParams.objects.all()
    serializer_class = CaseStepCallBackParamsSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        param_name = data['param_name']
        type = data['type']
        if param_name.find('__') != -1:
            if type == 1:
                if param_name.rfind('__') != len(param_name) - 2:
                    response.code = 3000
                    response.msg = '列表类型回调参数需未按照格式命名'
                    return Response(response.get_dic)
        else:
            response.code = 3000
            response.msg = '参数名未按照格式命名'
            return Response(response.get_dic)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if serializer.is_valid(raise_exception=True):
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

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete = True
        instance.save(update_fields=['delete'])
        response = ResponseStandard()
        response.msg = '操作成功'
        return Response(response.get_dic)


class UseCaseSelector(StandardListAPI):
    queryset = Modules.objects.all()
    serializer_class = UseCaseSelectorSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data_list = []
            for data in serializer.data:
                children = UseCases.objects.filter(modules_id=data['id'], delete=False).values()
                name = data['name']
                project = data['project']
                data['module_name'] = name + '(' + str(Projects.objects.get(pk=project).name) + ')'
                data['children'] = children
                data_list.append(data)
            response = ResponseStandard()
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class SqlScriptExecute(generics.GenericAPIView):
    serializer_class = SqlScriptExecuteSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                use_case = UseCases.objects.get(pk=serializer_class.validated_data.get('use_case_id'))
                data_source = use_case.data_source
                data_source_id = serializer_class.validated_data.get('data_source_id', '')
                if data_source_id:
                    try:
                        data_source = DataSource.objects.get(pk=data_source_id)
                    except:
                        response.code = 3000
                        response.msg = '参数传入错误，请检查参数'
                        return JsonResponse(response.get_dic, safe=False)
                if not data_source:
                    response.code = 3000
                    response.msg = '请配置要执行的数据库！'
                    return JsonResponse(response.get_dic, safe=False)
                step_type = serializer_class.validated_data.get('step_type', '')
                sql_script = serializer_class.validated_data.get('sql_script', '')
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            sql = SqlExecutor()
            connect = sql.connect_database(data_source.database_type, data_source.host, data_source.port,
                                           data_source.username, data_source.password, data_source.database,
                                           data_source.sid)
            if not connect:
                response.code = 3000
                response.msg = '数据库连接失败，请检查网络'
                return JsonResponse(response.get_dic, safe=False)
            cur = sql.conn.cursor()
            if step_type in [4, 6, 8]:
                start_time = datetime.now()
                result = sql.query_db(cur, sql_script)
                cur.connection.close()
                end_time = datetime.now()
                used_time = round((end_time - start_time).total_seconds() * 1000, 2)
                if result:
                    query_data = {
                        "code": 0,
                        "data": json.loads(sql.query_result),
                        "msg": "操作成功"
                    }
                    response.data['response_code'] = 200
                    response.data['response_body'] = query_data
                    response.data['response_time'] = str(used_time) + 'ms'
                    response.data['query_field'] = sql.query_field
                    response.data['query_result'] = json.loads(sql.query_result)
                    return JsonResponse(response.get_dic, safe=False)
                else:
                    query_data = {
                        "code": 3000,
                        "data": [],
                        "msg": str(sql.error_msg)
                    }
                    response.data['response_code'] = 500
                    response.data['response_body'] = query_data
                    response.data['response_time'] = str(used_time) + 'ms'
                    return JsonResponse(response.get_dic, safe=False)
            else:
                start_time = datetime.now()
                result = sql.execute_db(cur, sql_script)
                cur.connection.close()
                end_time = datetime.now()
                used_time = round((end_time - start_time).total_seconds() * 1000, 2) * 1000
                if result:
                    query_data = {
                        "code": 0,
                        "msg": "执行成功"
                    }
                    response.data['response_code'] = 200
                    response.data['response_body'] = query_data
                    response.data['response_time'] = str(used_time) + 'ms'
                    return JsonResponse(response.get_dic, safe=False)
                else:
                    query_data = {
                        "code": 3000,
                        "msg": str(sql.error_msg)
                    }
                    response.data['response_code'] = 500
                    response.data['response_body'] = query_data
                    response.data['response_time'] = str(used_time) + 'ms'
                    return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '操作失败' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class MqttPublish(generics.GenericAPIView):
    serializer_class = MqttPublishSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            mqtt_id = serializer_class.validated_data.get('mqtt_id', '')
            topic = serializer_class.validated_data.get('topic', '')
            qos = serializer_class.validated_data.get('qos', '')
            payload = serializer_class.validated_data.get('payload', '')
            try:
                mqtt = MQTTClient.objects.get(pk=mqtt_id)
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            if not mqtt:
                response.code = 3000
                response.msg = '请选择要执行的客户端！'
                return JsonResponse(response.get_dic, safe=False)
            start_time = datetime.now()
            mqtt_client = MQTTPublishClient(mqtt.broker, mqtt.port, mqtt.username, mqtt.password)
            status, msg = mqtt_client.publish_msg(topic, payload, qos)
            end_time = datetime.now()
            used_time = round((end_time - start_time).total_seconds() * 1000, 2)
            if not status:
                response.data['response_code'] = 500
                response.data['response_time'] = str(used_time) + 'ms'
                response_body = {
                    "code": 3000,
                    "msg": msg
                }
                response.data['response_body'] = response_body
                response.msg = msg
            else:
                response.data['response_code'] = 200
                response.data['response_time'] = str(used_time) + 'ms'
                response_body = {
                    "code": 0,
                    "msg": msg
                }
                response.data['response_body'] = response_body
                response.msg = msg
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '操作失败' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class MqttSub(generics.GenericAPIView):
    serializer_class = MqttSubSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            mqtt_id = serializer_class.validated_data.get('mqtt_id', '')
            topic = serializer_class.validated_data.get('topic', '')
            qos = serializer_class.validated_data.get('qos', '')
            try:
                mqtt = MQTTClient.objects.get(pk=mqtt_id)
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            if not mqtt:
                response.code = 3000
                response.msg = '请选择要执行的客户端！'
                return JsonResponse(response.get_dic, safe=False)
            start_time = datetime.now()
            mqtt_client = MQTTPublishClient(mqtt.broker, mqtt.port, mqtt.username, mqtt.password)
            pool = ThreadPoolExecutor(max_workers=15)
            task = pool.submit(mqtt_client.sub_msg, topic, qos)
            wait_time = 10
            while True:
                time.sleep(1)
                if task.done():
                    break
                else:
                    wait_time -= 1
                if wait_time == 0:
                    mqtt_client.publish_msg(topic, "订阅等待超时", qos)
                    time.sleep(0.5)
                    break
            end_time = datetime.now()
            used_time = round((end_time - start_time).total_seconds() * 1000, 2)
            status, msg = task.result()
            if not status or msg == "订阅等待超时":
                response.data['response_code'] = 500
                response.data['response_time'] = str(used_time) + 'ms'
                response_body = {
                    "code": 3000,
                    "msg": msg
                }
                response.data['response_body'] = response_body
                response.msg = msg
            else:
                response.data['response_code'] = 200
                response.data['response_time'] = str(used_time) + 'ms'
                try:
                    msg = json.loads(msg)
                except:
                    pass
                response_body = {
                    "code": 0,
                    "data": msg,
                    "msg": "订阅接收成功"
                }
                response.data['response_body'] = response_body
                response.msg = msg
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '操作失败' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)
