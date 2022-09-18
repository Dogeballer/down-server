from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from down.CommonStandards import *
from executor.getUacToken import GetToken
from executor.get_auth_header import GetAuthHeader
from .filter import *
from .serializers import *
from rest_framework import viewsets, generics, filters, permissions, status
from .models import Interface, InterfaceBody, InterfaceParam, InterfaceClass, InterfaceTest
from projects.models import Modules, Projects, Environment
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
import requests
import json


class InterfaceClassList(generics.ListAPIView):
    queryset = InterfaceClass.objects.filter(delete=False)
    serializer_class = InterfaceClassListSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = InterfaceClassFilter

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = list_return(serializer.data)
            # print(response.get_dic)
            return Response(response.get_dic)


class InterfaceClassCreate(StandardCreateAPI):
    queryset = InterfaceClass.objects.all()
    serializer_class = InterfaceClassCreateSerializer


class InterfaceClassUpdate(StandardUpdateAPI):
    queryset = InterfaceClass.objects.all()
    serializer_class = InterfaceClassCreateSerializer


class InterfaceClassDelete(StandardDeleteAPI):
    queryset = InterfaceClass.objects.all()
    serializer_class = InterfaceClassCreateSerializer


class InterfaceList(generics.ListAPIView):
    queryset = Interface.objects.all()
    serializer_class = InterfaceListSerializer
    pagination_class = StandardPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = InterfaceFilter

    def get_project(self):
        return Projects.objects.get(pk=self.request.query_params.get('project', None))

    def get_queryset(self):
        try:
            project = self.get_project()
            interface_class_list = InterfaceClass.objects.filter(project=project)
            return self.queryset.filter(interface_class__in=interface_class_list)
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
            response = list_return(serializer.data)
            return Response(response.get_dic)


class InterfaceBodyList(generics.ListAPIView):
    queryset = InterfaceBody.objects.all()
    serializer_class = InterfaceBodySerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ('belong_interface',)

    def list(self, request, *args, **kwargs):
        queryset = self.queryset.filter(belong_interface=request.query_params.get('belong_interface', None), parent=-1)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = self.body_structure(serializer.data)
            response = ResponseStandard()
            response.data["items"] = data
            response.msg = '操作成功'
            return Response(response.get_dic)

    def body_structure(self, data):
        body_list = data
        for param in body_list:
            if param['node']:
                children_list = InterfaceBody.objects.filter(parent=param['id']).values()
                param['children'] = self.parent_body(children_list)
        return data

    def parent_body(self, children_list):
        children_return = []
        for param in children_list:
            if param['node']:
                children_list = InterfaceBody.objects.filter(parent=param['id']).values()
                param['children'] = self.parent_body(children_list)
            children_return.append(param)
        return children_return


class InterfaceCreate(generics.CreateAPIView):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            print(serializer.data)
            response.data = serializer.data
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class InterfaceDetailUpdate(generics.UpdateAPIView):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        interface_param_data = request.data.get('interface_param', [])
        for data in interface_param_data:
            interface_param = InterfaceParam.objects.filter(pk=data['id'])
            if interface_param:
                # print(data)
                try:
                    update_time = data.pop('update_time')
                    create_time = data.pop('create_time')
                except:
                    pass
                interface_param.update(**data)
            else:
                InterfaceParam.objects.create(interface_id=instance.id, **data)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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


class InterfaceBodyUpdate(generics.UpdateAPIView):
    queryset = InterfaceBody.objects.all()
    serializer_class = InterfaceBodyUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        interface = instance.belong_interface
        interface_test = InterfaceTest.objects.get(test_interface=interface)
        if serializer.is_valid(raise_exception=False):
            self.perform_update(serializer)
            body_json = body_example_json_generate(interface)
            if len(body_json) != 0:
                body_example_json = str(json.dumps(body_json))
                interface.body_example_json = body_example_json
                interface.save(update_fields=['body_example_json'])
                interface_test.interface_body = body_example_json
                interface_test.save()
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


class InterfaceBodyCreate(generics.CreateAPIView):
    queryset = InterfaceBody.objects.all()
    serializer_class = InterfaceBodyCreateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        data = request.data
        interface = Interface.objects.get(pk=data['belong_interface'])
        interface_test = InterfaceTest.objects.get(test_interface=interface)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.perform_create(serializer)
            body_json = body_example_json_generate(interface)
            if len(body_json) != 0:
                body_example_json = str(json.dumps(body_json))
                interface.body_example_json = body_example_json
                interface.save(update_fields=['body_example_json'])
                interface_test.interface_body = body_example_json
                interface_test.save()
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class InterfaceDetail(generics.RetrieveDestroyAPIView):
    queryset = Interface.objects.all()
    serializer_class = InterfaceGetSerializer
    permission_classes = (IsAuthenticated,)

    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        project = instance.interface_class.project
        # print(project)
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['project'] = project.id
        response.data = data
        return Response(response.get_dic)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response = ResponseStandard()
        return Response(response.get_dic)


class InterfaceBodyDelete(generics.DestroyAPIView):
    queryset = InterfaceBody.objects.all()
    serializer_class = InterfaceBodySerializer
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        interface_body_children = InterfaceBody.objects.filter(parent=instance.id)
        interface_body_children.delete()
        interface = instance.belong_interface
        interface_test = InterfaceTest.objects.get(test_interface=interface)
        body_json = body_example_json_generate(interface)
        if len(body_json) != 0:
            body_example_json = str(json.dumps(body_json))
            interface.body_example_json = body_example_json
            interface.save(update_fields=['body_example_json'])
            interface_test.interface_body = body_example_json
            interface_test.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class InterfaceParamDelete(StandardDeleteAPI):
    queryset = InterfaceParam.objects.all()
    serializer_class = InterfaceParamSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        response = ResponseStandard()
        return Response(response.get_dic)


class InterfaceTestApi(generics.GenericAPIView):
    serializer_class = InterfaceTestSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                environment = Environment.objects.get(pk=serializer_class.data.get('environmentId'))
                environment_url = environment.url
                # uac_url = environment.uac_url
                authentication_environment = environment.authentication_environment
                interface = Interface.objects.get(pk=serializer_class.data.get('interfaceId'))
                params = serializer_class.data.get('params')
                body = serializer_class.data.get('body')
                if body:
                    body = json.loads(body)
            except Exception as e:
                print(e)
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            method = interface.method
            path = interface.path
            body_type = interface.body_type
            url = str(environment_url) + str(path)
            query_param = {}
            path_param_list = []
            url_query_param = '?'
            headers_default = {}
            if body_type == 3:
                headers_default = {
                    "Content-Type": "application/json; charset=UTF-8",
                }
            # try:
            #     # token = GetToken().access_token_get()
            #     token = GetToken(uac_url).uacV2_token_get()
            # except:
            #     token = ''
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
            headers = merge_dicts(header_dict, headers_default)
            # print(headers)
            test_param = []
            for param in params:
                # print(param)
                if param['param_in'].lower() == 'path':
                    path_param = {'name': param['name'], 'value': param['value']}
                    test_param.append(param)
                    path_param_list.append(path_param)
                elif param['param_in'].lower() == 'query':
                    query_param[param['name']] = param['value']
                    url_query_param += param['name'] + '=' + param['value'] + '&'
                    test_param.append(param)
                elif param['param_in'].lower() == 'header':
                    headers[param['name']] = param['value']
            # print(test_param)
            test_param = json.dumps(test_param)
            if url.find('{') != -1:
                url = url.replace('{' + path_param['name'] + '}', str(path_param['value']))
            if len(url_query_param) > 1:
                if url_query_param.rfind('&') != -1:
                    url_query_param = url_query_param[:url_query_param.rfind('&')]
                query_url = url + url_query_param
            else:
                query_url = url
            try:
                interface_test = InterfaceTest.objects.get(test_interface=interface)
                if body:
                    interface_test.interface_body = body
                    interface_test.save(update_fields=['interface_body'])
                if test_param:
                    interface_test.interface_param = test_param
                    interface_test.save(update_fields=['interface_param'])
            except:
                InterfaceTest.objects.create(test_interface=interface, interface_param=test_param,
                                             interface_body=body)
                # if test_param and body:
                #     InterfaceTest.objects.create(test_interface=interface, interface_param=test_param,
                #                                  interface_body=body)
                # elif test_param and len(body) == 0:
                #     InterfaceTest.objects.create(test_interface=interface, interface_param=test_param,
                #                                  interface_body=body)
                # elif body and len(test_param) == 0:
                #     InterfaceTest.objects.create(test_interface=interface, interface_body=body)
            msg, response_code, response_headers, response_body, response_time = requests_func(method, url, query_url,
                                                                                               query_param,
                                                                                               headers, body)
            # print(type(response_headers.values()))
            response.data.pop('items')
            if response_code == -1:
                response.code = 3000
                response.msg = msg
            else:
                response.msg = msg
                response.data['url'] = query_url
                response.data['response_code'] = response_code
                response.data['response_body'] = response_body
                response.data['response_headers'] = dict(response_headers)
                response.data['response_time'] = str(response_time) + 'ms'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '系统异常' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class SwaggerAnalysisAPI(generics.GenericAPIView):
    serializer_class = SwaggerAnalysisSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            try:
                result = requests.get(serializer_class.data.get('swagger_url'))
                project = Projects.objects.get(pk=serializer_class.data.get('project_id'))
                swagger_result = result.json()
            except:
                response.code = 3000
                response.msg = '参数传入错误，请检查参数'
                return JsonResponse(response.get_dic, safe=False)
            version = serializer_class.data.get('version')
            interfaces_list = swagger_result.get('paths', None)
            definitions_list = swagger_result.get('definitions', None)
            for interface_path in interfaces_list.keys():
                interface_data = interfaces_list.get(interface_path)
                for method in interface_data.keys():
                    interface_method_data = interface_data.get(method)
                    name = interface_method_data.get("summary")
                    description = interface_method_data.get("description")
                    tags = interface_method_data.get('tags')
                    if tags:
                        tags = tags[0]
                    else:
                        tags = project.name + "接口分类"
                    method = method.upper()
                    path = interface_path
                    interface_class = InterfaceClass.objects.filter(class_name=tags, project=project)
                    try:
                        interface_class = interface_class[0]
                    except:
                        interface_class = InterfaceClass.objects.create(class_name=tags, describe=tags, project=project)
                    try:
                        interface = Interface.objects.filter(path=path, method=method, interface_class=interface_class)
                        interface = interface[0]
                        interface.name = name
                        interface.describe = name
                        interface.tags = tags
                        interface.save()
                    except:
                        interface = Interface.objects.create(name=name, method=method, path=path, status=True,
                                                             describe=description, tags=tags, version=version,
                                                             interface_class=interface_class)
                    # interface_param = InterfaceParam.objects.filter(interface=interface)
                    # interface_param.delete()
                    interface_body = InterfaceBody.objects.filter(belong_interface=interface)
                    interface_body.delete()
                    parameters = interface_method_data.get("parameters", {})
                    if len(parameters) != 0:
                        param_name = ''
                        param_description = ''
                        param_required = False
                        param_type = 1
                        parm_example = ''
                        param_in = ''
                        schema = {}
                        for param in parameters:
                            for args in param.keys():
                                if args == 'name':
                                    param_name = param.get(args)
                                if args == 'description':
                                    param_description = param.get(args)
                                if args == 'type':
                                    param_type = param.get(args)
                                    if param_type == 'string':
                                        parm_example = 'string'
                                    elif param_type == 'integer':
                                        parm_example = 0
                                    elif param_type == 'number':
                                        parm_example = 0
                                if args == 'required':
                                    param_required = param.get(args)
                                if args == 'in':
                                    param_in = param.get(args)
                                if args == 'schema':
                                    schema = param.get(args)
                            if param_in != 'body':
                                interface_param = InterfaceParam.objects.filter(interface=interface, name=param_name)
                                if interface_param:
                                    interface_param.update(name=param_name,
                                                           describe=param_description,
                                                           required=param_required,
                                                           param_in=param_in,
                                                           type=param_type,
                                                           example=parm_example,
                                                           interface=interface)
                                else:
                                    interface_param = InterfaceParam.objects.create(name=param_name,
                                                                                    describe=param_description,
                                                                                    required=param_required,
                                                                                    param_in=param_in,
                                                                                    type=param_type,
                                                                                    example=parm_example,
                                                                                    version=version,
                                                                                    interface=interface
                                                                                    )
                            else:
                                self.schema_analyse(schema, definitions_list, parent=-1,
                                                    interface=interface)
            interface_class_list = InterfaceClass.objects.filter(project=project)
            interfaces_list = Interface.objects.filter(interface_class__in=interface_class_list)
            for interface in interfaces_list:
                body_json = body_example_json_generate(interface)
                if len(body_json) != 0:
                    body_example_json = str(json.dumps(body_json))
                    interface.body_example_json = body_example_json
                    interface.save(update_fields=['body_example_json'])
                    try:
                        interface_test = InterfaceTest.objects.get(test_interface=interface)
                        interface_test.interface_body = body_example_json
                        interface_test.save(update_fields=['interface_body'])
                    except:
                        InterfaceTest.objects.create(test_interface=interface, interface_body=body_example_json)
            response.msg = '写入成功'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '写入失败,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)

    def schema_analyse(self, schema, definitions_list, parent, interface):
        schema_item = schema.get('$ref', '')
        body_param_description = ''
        body_param_type = ''
        body_param_required = False
        body_param_example = ''
        body_param_node = False
        body_param_circulation = False
        if schema_item != '':
            # print(schema_item)
            schema_name = schema_item.replace('#/definitions/', '')
            schema = definitions_list.get(schema_name)
            if schema:
                schema = schema.get('properties')
                if len(schema) != 0:
                    for body_param_name in schema.keys():
                        body_params = schema.get(body_param_name)
                        for body_param in body_params.keys():
                            body_param_required = False
                            if body_param == 'description':
                                body_param_description = body_params.get(body_param)
                            if body_param == 'allowEmptyValue':
                                body_param_required = True
                            if body_param == 'type':
                                body_param_type = body_params.get(body_param)
                        if body_param_type == 'string':
                            body_param_example = 'string'
                        elif body_param_type == 'integer':
                            body_param_example = 0
                        elif body_param_type == 'boolean':
                            body_param_example = True
                        elif body_param_type == 'array':
                            body_param_node = True
                            body_param_circulation = True
                            try:
                                interface_body = InterfaceBody.objects.create(name=body_param_name,
                                                                              describe=body_param_description,
                                                                              required=body_param_required,
                                                                              example='',
                                                                              node=body_param_node,
                                                                              circulation=body_param_circulation,
                                                                              type=body_param_type,
                                                                              parent=parent,
                                                                              belong_interface=interface)
                                body_param_items = body_params.get("items", '')
                                # 非父分类节点
                                if parent != -1:
                                    parent_interface_body_name = InterfaceBody.objects.get(pk=parent).name
                                    # 防止出现无限递归情况
                                    if body_param_name == parent_interface_body_name:
                                        pass
                                    else:
                                        self.schema_analyse(body_param_items, definitions_list,
                                                            parent=interface_body.id,
                                                            interface=interface)
                                else:
                                    self.schema_analyse(body_param_items, definitions_list, parent=interface_body.id,
                                                        interface=interface)
                            except:
                                body_param_example = ''
                                # print(body_param_name)
                        else:
                            print(body_param_type)
                        if body_param_type != 'array':
                            interface_body = InterfaceBody.objects.create(name=body_param_name,
                                                                          describe=body_param_description,
                                                                          required=body_param_required,
                                                                          example=body_param_example,
                                                                          node=False,
                                                                          circulation=False,
                                                                          type=body_param_type,
                                                                          parent=parent,
                                                                          belong_interface=interface)
        else:
            # print(interface.name)
            # print(schema)
            body_params = schema
            body_param_name = ''
            for body_param in body_params.keys():
                body_param_required = False
                if body_param == 'description':
                    body_param_description = body_params.get(body_param)
                if body_param == 'allowEmptyValue':
                    body_param_required = True
                if body_param == 'type':
                    body_param_type = body_params.get(body_param)
                if body_param == 'name':
                    body_param_name = body_params.get(body_param)
            if body_param_type == 'string':
                body_param_example = 'string'
            elif body_param_type == 'integer':
                body_param_example = 0
            elif body_param_type == 'boolean':
                body_param_example = True
            elif body_param_type == 'array':
                body_param_node = True
                body_param_circulation = True
                try:
                    interface_body = InterfaceBody.objects.create(name=body_param_name,
                                                                  describe=body_param_description,
                                                                  required=body_param_required,
                                                                  example='',
                                                                  node=body_param_node,
                                                                  circulation=body_param_circulation,
                                                                  type=body_param_type,
                                                                  parent=parent,
                                                                  belong_interface=interface)
                    body_param_items = body_params.get("items", '')
                    # 非父分类节点
                    self.schema_analyse(body_param_items, definitions_list, parent=interface_body.id,
                                        interface=interface)
                except:
                    body_param_example = ''
                    # print(body_param_name)
            if body_param_type != 'array':
                interface_body = InterfaceBody.objects.create(name=body_param_name,
                                                              describe=body_param_description,
                                                              required=body_param_required,
                                                              example=body_param_example,
                                                              node=False,
                                                              circulation=False,
                                                              type=body_param_type,
                                                              parent=parent,
                                                              belong_interface=interface)


class InterfaceTree(generics.ListAPIView):
    serializer_class = InterfaceTreeSerializer
    queryset = Projects.objects.all()
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
            return Response(response.get_dic)


class InterfaceClassSelector(generics.ListAPIView):
    queryset = Projects.objects.all()
    serializer_class = InterfaceClassSelectorSerializer
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
            return Response(response.get_dic)


class InterfaceSelector(StandardListAPI):
    queryset = InterfaceClass.objects.all()
    serializer_class = InterfaceClassSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = InterfaceClassFilter
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
                name = data['name']
                project = data['project']
                data['class_name'] = name + '(' + str(Projects.objects.get(pk=project).name) + ')'
                data_list.append(data)
            response = ResponseStandard()
            response.data["items"] = data_list
            response.msg = '操作成功'
            # print(response.get_dic)
            return Response(response.get_dic)


class ProjectInterfaceDelete(generics.DestroyAPIView):
    queryset = Projects.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        interface_class = InterfaceClass.objects.filter(project=project)
        interface_class.delete()
        response = ResponseStandard()
        return Response(response.get_dic)


class UpdateInterfaceStatus(generics.UpdateAPIView):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        interface = self.get_object()
        interface.status = not interface.status
        interface.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class InterfaceTestHistory(generics.ListAPIView):
    queryset = InterfaceTest.objects.all()
    serializer_class = InterfaceTestHistorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = InterfaceTestFilter
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
                interface_param = data['interface_param']
                interface_body = data['interface_body']
                if interface_body != '':
                    data['interface_body'] = json.loads(interface_body)
                else:
                    data['interface_body'] = []
                if interface_param != '':
                    data['interface_param'] = json.loads(interface_param)
                else:
                    data['interface_param'] = []
                data_list.append(data)
            response.data["items"] = data_list
            response.msg = '操作成功'
            return Response(response.get_dic)


class InterfaceCallBackParamsCreateList(generics.ListCreateAPIView):
    queryset = InterfaceCallBackParams.objects.filter(delete=False)
    serializer_class = InterfaceCallBackParamsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = InterfaceCallBackParamsFilter
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
        if serializer.is_valid():
            self.perform_create(serializer)
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return JsonResponse(response.get_dic)
        return JsonResponse(response.get_dic, status=status.HTTP_201_CREATED)


class InterfaceCallBackParamsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = InterfaceCallBackParams.objects.all()
    serializer_class = InterfaceCallBackParamsSerializer
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


def body_example_json_generate(interface):
    body_params = InterfaceBody.objects.filter(belong_interface=interface, parent=-1)
    body_json = {}
    for body_param in body_params:
        if body_param.type != 'array':
            if body_param.example == 'True':
                example = True
            elif body_param.example == '0':
                example = 0
            else:
                example = body_param.example

            body_json[body_param.name] = example
        else:
            body_json[body_param.name] = []
            children = InterfaceBody.objects.filter(parent=body_param.id)
            child_items = {}
            for child in children:
                if child.type != 'array':
                    if child.name is not None:
                        if child.example == 'True':
                            example = True
                        elif child.example == '0':
                            example = 0
                        else:
                            example = child.example
                        child_items[child.name] = example
                    else:
                        body_json[body_param.name].append(child.example)
                else:
                    child_items[child.name] = []
                    child_body = body_json_generate(parent=child.id)
                    if type(child_body) is dict:
                        child_items[child.name].append(child_body)
                    elif type(child_body) is list:
                        child_items[child.name] = child_body
            if len(child_items) != 0:
                body_json[body_param.name].append(child_items)
    return body_json


def body_json_generate(parent):
    children = InterfaceBody.objects.filter(parent=parent)
    child_items = {}
    child_list = []
    for child in children:
        if child.type != 'array':
            if child.name != '':
                if child.example == 'True':
                    example = True
                elif child.example == '0':
                    example = 0
                else:
                    example = child.example
                child_items[child.name] = example
            else:
                child_list.append(child.example)
        else:
            child_items[child.name] = []
            child_children = body_json_generate(parent=child.id)
            child_items[child.name].append(child_children)
    if len(child_items) != 0:
        return child_items
    else:
        return child_list


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


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result
