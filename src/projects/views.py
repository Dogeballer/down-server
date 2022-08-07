from collections import OrderedDict
from datetime import datetime

from rest_framework.permissions import IsAuthenticated

from down.CommonStandards import StandardPagination, list_return, ResponseStandard
from django.shortcuts import render, HttpResponse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, generics, filters, permissions
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response
from executor.script_execution import DebugCode, udf_execute_setup, udf_execute
from executor.sql_executor import SqlExecutor
from projects.models import Projects, Modules, Environment
from .serializers import *
from django.db.models import Q
from rest_framework.viewsets import ViewSetMixin, mixins
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .filter import ProjectsFilter, ModulesFilter, EnvironmentFilter
from rest_framework_simplejwt import authentication
import json
import logging
from rest_framework import status
from down.CommonStandards import *

# 生成一个以当前文件名为名字的 logger实例
logger = logging.getLogger()
# 生成一个名字为collect的日志实例
web_logger = logging.getLogger('web.log')


class ProjectsList(generics.ListCreateAPIView):
    """
    查看接口列表
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer
    permission_classes = (IsAuthenticated,)

    # pagination_class = StandardPagination
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

    def create(self, request, *args, **kwargs):
        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            response.data = serializer.data
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return Response(response.get_dic)
        return Response(response.get_dic, status=status.HTTP_201_CREATED, headers=headers)


class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    查看接口详细
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response = ResponseStandard()
        return Response(response.get_dic)


class ModulesList(generics.ListAPIView):
    """
    查看接口列表
    """
    queryset = Modules.objects.all()
    serializer_class = ModuleListSerializer
    pagination_class = StandardPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = ModulesFilter
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            # response = self.list_return(data_list)
            # return Response(response.get_dic)
            # data_list = serializer.data
            # response = self.list_return(data_list)
            # return Response(response.get_dic)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = list_return(serializer.data)
            return Response(response.get_dic)


class ModuleCreate(generics.CreateAPIView):
    serializer_class = ModulesSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):

        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            response.data = serializer.data
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return Response(response.get_dic)
        return Response(response.get_dic, status=status.HTTP_201_CREATED, headers=headers)


class ModuleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    查看接口详细
    """
    queryset = Modules.objects.all()
    serializer_class = ModulesSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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
        self.perform_destroy(instance)
        response = ResponseStandard()
        return Response(response.get_dic)

    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        response.data = data
        return Response(response.get_dic)


class EnvironmentList(generics.ListAPIView):
    """
    查看接口列表
    """
    queryset = Environment.objects.all()
    serializer_class = EnvironmentListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EnvironmentFilter

    # permission_classes = (IsAuthenticated,)

    # pagination_class = StandardPagination
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


class EnvironmentCreate(generics.CreateAPIView):
    serializer_class = EnvironmentSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):

        response = ResponseStandard()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            response.data = serializer.data
            response.msg = '操作成功'
        else:
            response.code = 3000
            response.msg = str(serializer.errors).replace('{', '').replace('}', '')
            return Response(response.get_dic)
        return Response(response.get_dic, status=status.HTTP_201_CREATED, headers=headers)


class EnvironmentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    查看接口详细
    """
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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
        self.perform_destroy(instance)
        response = ResponseStandard()
        return Response(response.get_dic)


class UpdateEnvironmentStatus(generics.UpdateAPIView):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        environment = self.get_object()
        environment.status = not environment.status
        environment.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class Pros(ViewSetMixin, APIView):
    def get_all(self, request):
        response = ResponseStandard()
        pros = Projects.objects.all()
        ret = ProjectsSerializer(instance=pros, many=True)
        response.msg = '查询成功'
        response.data = ret.data
        return JsonResponse(response.get_dic, safe=False)


class ProModulesSerializer(generics.GenericAPIView):
    queryset = Projects.objects.all()
    serializer_class = ProModulesSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = ProjectsFilter
    ordering_fields = ['create_time']
    ordering = ['-create_time']
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        response = ResponseStandard()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        response.data = serializer.data
        print(serializer.data[0]['name'])
        for project in serializer.data:
            print(project['name'])
        response.msg = '查询成功'
        logger.info('查询成功')
        return JsonResponse(response.get_dic, safe=False)

    def post(self, request):
        response = ResponseStandard()
        serializer_class = self.serializer_class(data=request.data)
        if serializer_class.is_valid():
            serializer_class.save()
            response.data = serializer_class.data
            response.msg = '写入成功'
            return JsonResponse(response.get_dic, safe=False)
        else:
            response.code = 3000
            response.msg = '写入失败,' + str(serializer_class.errors)
            return JsonResponse(response.get_dic, safe=False)


class ProModulesSelector(StandardListAPI):
    queryset = Projects.objects.filter(status=True)
    serializer_class = ProModulesSelectorSerializer
    permission_classes = (IsAuthenticated,)


class AuthEnvironmentList(StandardListAPI):
    """
    查看鉴权环境列表
    """
    queryset = AuthenticationEnvironment.objects.all()
    serializer_class = AuthenticationEnvironmentSerializer
    permission_classes = (IsAuthenticated,)


class AuthEnvironmentCreate(StandardCreateAPI):
    """
    创建鉴权环境
    """
    queryset = AuthenticationEnvironment.objects.all()
    serializer_class = AuthenticationEnvironmentSerializer
    permission_classes = (IsAuthenticated,)


class AuthEnvironmentUpdate(StandardUpdateAPI):
    """
    修改鉴权环境
    """
    queryset = AuthenticationEnvironment.objects.all()
    serializer_class = AuthenticationEnvironmentSerializer
    permission_classes = (IsAuthenticated,)


class UpdateAuthEnvironmentStatus(generics.UpdateAPIView):
    """
    修改鉴权环境状态
    """
    queryset = AuthenticationEnvironment.objects.all()
    serializer_class = AuthenticationEnvironmentSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        environment = self.get_object()
        environment.status = not environment.status
        environment.save()
        response = ResponseStandard()
        return Response(response.get_dic)


class AuthEnvironmentDelete(StandardDeleteAPI):
    """
    删除鉴权环境状态
    """
    queryset = AuthenticationEnvironment.objects.all()
    serializer_class = AuthenticationEnvironmentSerializer
    permission_classes = (IsAuthenticated,)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        response = ResponseStandard()
        return Response(response.get_dic)
