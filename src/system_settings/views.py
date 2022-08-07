from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from down.CommonStandards import StandardDeleteAPI, ResponseStandard, StandardListAPI, StandardCreateAPI, \
    StandardRetrieveAPI, StandardUpdateAPI, StandardPagination
from executor.script_execution import DebugCode
from executor.sql_executor import SqlExecutor
from system_settings.filter import UdfFilter, DataSourceFilter, UdfArgsFilter
from system_settings.models import UdfArgs, DataSource, Udf
from system_settings.serializers import UdfSerializer, DataSourceSerializer, UdfOnlineDebugSerializer, \
    UdfArgsSerializer, ConsumerTokenSerializer
from rest_framework.response import Response
from rest_framework import viewsets, generics, filters, permissions, status, serializers
from django.db.models import Q


# Create your views here.
class TokenViewBase(generics.GenericAPIView):
    permission_classes = ()
    authentication_classes = ()
    serializer_class = None
    www_authenticate_realm = 'api'

    def get_authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def post(self, request, *args, **kwargs):
        response = ResponseStandard()
        data = request.data
        serializer = self.get_serializer(data=data)

        try:
            if serializer.is_valid(raise_exception=False):
                response.data = serializer.validated_data
                response.msg = '操作成功'
                response.data['username'] = data['username']
                return JsonResponse(response.get_dic)
            else:
                response.code = 3001
                response.msg = '账户名或密码不正确!'
                return JsonResponse(response.get_dic, safe=False)
        except TokenError as e:
            response.code = 3002
            response.msg = 'refresh token错误!'
            return JsonResponse(response.get_dic, safe=False)


class ConsumerTokenGet(TokenViewBase):
    serializer_class = ConsumerTokenSerializer


class ConsumerTokenRefresh(TokenViewBase):
    serializer_class = TokenRefreshSerializer


class DataSourceList(StandardListAPI):
    queryset = DataSource.objects.filter(delete=False)
    serializer_class = DataSourceSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = DataSourceFilter
    permission_classes = (IsAuthenticated,)


class DataSourceCreate(StandardCreateAPI):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)


class DataSourceDetail(StandardRetrieveAPI):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)


class DataSourceUpdate(StandardUpdateAPI):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)


class DataSourceDelete(StandardDeleteAPI):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)


class DataSourceTest(StandardCreateAPI):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            database_type = serializer.data.get('database_type')
            host = serializer.data.get('host')
            port = serializer.data.get('port')
            username = serializer.data.get('username')
            password = serializer.data.get('password')
            database = serializer.data.get('database')
            sql = SqlExecutor()
            connect = sql.connect_database(database_type, host, port, username, password, database)
            if not connect:
                print(sql.error_msg)
                response.code = 3000
                response.msg = sql.error_msg
            else:
                response.msg = '连接成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class UpdateDataSourceStatus(generics.UpdateAPIView):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        data_source = self.get_object()
        data_source.status = not data_source.status
        data_source.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class UdfOnlineDebug(generics.GenericAPIView):
    serializer_class = UdfOnlineDebugSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            source_code = serializer_class.data.get('SourceCode')
            debug_code = DebugCode(code=source_code)
            debug_code.run()
            resp = debug_code.resp
            response.data = resp
            # func_name, func_kwargs, execution_status, msg = udf_execute_setup(
            #     "${uac_token_get(uac_item=0||userName=\"qatestuser\"||userPwd=\"92d7ddd2a010c59511dc2905b7e14f64\")}")
            # print(udf_execute(func_name, func_kwargs))
            # print(func_name)
            # print(func_kwargs)
            # print(msg)
            return Response(response.get_dic)
        else:
            response.code = 3000
            response.msg = '参数错误,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class UdfPageList(StandardListAPI):
    queryset = Udf.objects.filter(delete=False)
    serializer_class = UdfSerializer
    pagination_class = StandardPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = UdfFilter
    ordering_fields = ('name', 'zh_name', 'user',)
    ordering = ('-create_time',)
    permission_classes = (IsAuthenticated,)


class UdfCreate(StandardCreateAPI):
    queryset = Udf.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            source_code = serializer.validated_data.get('source_code')
            name = serializer.validated_data.get('name')
            if Udf.objects.filter(name=name, delete=False):
                response.code = 3000
                response.msg = '函数名重复，请更换参数名'
            else:
                debug_code = DebugCode(code=source_code)
                try:
                    check_function_result = debug_code.check_function_name(name)
                    if check_function_result:
                        self.perform_create(serializer)
                        response.data = {'id': serializer.instance.id}
                        response.msg = '操作成功'
                    else:
                        response.code = 3000
                        response.msg = '源码函数与函数名不匹配，请检查'

                except Exception as e:
                    response.code = 3000
                    response.msg = '源码校验异常，具体报错为:%s' % e
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class UdfUpdate(StandardUpdateAPI):
    queryset = Udf.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=False):
            source_code = serializer.validated_data.get('source_code')
            name = serializer.validated_data.get('name')
            if Udf.objects.filter(~Q(pk=instance.id), name=name, delete=False):
                response.code = 3000
                response.msg = '函数名重复，请更换参数名'
            else:
                debug_code = DebugCode(code=source_code)
                check_function_result = debug_code.check_function_name(name)
                if check_function_result:
                    self.perform_update(serializer)
                    # 更新udf表达式
                    expression = expression_conversion(instance)
                    instance.expression = expression
                    instance.save()
                    print(instance.source_code)
                    response.msg = '操作成功'
                else:
                    response.code = 3000
                    response.msg = '源码函数与函数名不匹配，请检查'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return Response(response.get_dic)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(response.get_dic)


class UdfDelete(StandardDeleteAPI):
    queryset = Udf.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)


class UdfRetrieve(StandardRetrieveAPI):
    queryset = Udf.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)


class UpdateUdfStatus(generics.UpdateAPIView):
    queryset = Udf.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        udf = self.get_object()
        udf.status = not udf.status
        udf.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class UdfArgsList(StandardListAPI):
    queryset = UdfArgs.objects.all()
    serializer_class = UdfArgsSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = UdfArgsFilter
    permission_classes = (IsAuthenticated,)


class UdfArgsCreate(StandardCreateAPI):
    queryset = UdfArgs.objects.all()
    serializer_class = UdfArgsSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            # 更新udf表达式
            udf = serializer.instance.udf
            expression = expression_conversion(udf)
            udf.expression = expression
            udf.save()
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class UdfArgsUpdate(StandardUpdateAPI):
    queryset = UdfArgs.objects.all()
    serializer_class = UdfArgsSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=False):
            self.perform_update(serializer)
            udf = serializer.instance.udf
            expression = expression_conversion(udf)
            udf.expression = expression
            udf.save()
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


class UdfArgsDelete(StandardDeleteAPI):
    queryset = UdfArgs.objects.all()
    serializer_class = UdfSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        udf = instance.udf
        instance.delete()
        expression = expression_conversion(udf)
        udf.expression = expression
        udf.save()
        response = ResponseStandard()
        response.msg = '操作成功'
        return Response(response.get_dic)


def expression_conversion(udf):
    udf_args = UdfArgs.objects.filter(udf=udf)
    expression = "${%s(" % udf.name
    for args in udf_args:
        args_type = args.args_type
        if args_type == 0:  # int
            expression = expression + args.name + '=' + '1' + '||'
        elif args_type == 1:  # str
            expression = expression + args.name + '=' + "'string'" + '||'
        elif args_type == 2:  # list
            expression = expression + args.name + '=' + '[1,2,3]' + '||'
        elif args_type == 3:  # dict
            expression = expression + args.name + '=' + "{'key':'value'}" + '||'
        elif args_type == 4:  # boolean
            expression = expression + args.name + '=' + 'True' + '||'
        elif args_type == 5:  # float
            expression = expression + args.name + '=' + '0.01' + '||'
    if expression.rfind('||') != -1:
        expression = expression[0:expression.rfind('||')] + ')}'
    else:
        expression = "${%s()}" % udf.name
    return expression
