import time
from collections import OrderedDict
from datetime import datetime
from django.http import JsonResponse
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import viewsets, generics, filters, permissions, status, serializers


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 1000

    def get_paginated_response(self, data):
        for item in data:
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


class ResponseStandard:
    def __init__(self):
        self.code = 0
        self.msg = None
        self.data = {'items': []}

    @property
    def get_dic(self):
        return self.__dict__


def list_return(data_list):
    response = ResponseStandard()
    for data in data_list:
        create_time = datetime.strptime(data['create_time'], "%Y-%m-%d %H:%M:%S")
        update_time = datetime.strptime(data['update_time'], "%Y-%m-%d %H:%M:%S")
        data['create_time'] = time.mktime(create_time.timetuple()) * 1000
        data['update_time'] = time.mktime(update_time.timetuple()) * 1000
    response.data["items"] = data_list
    response.msg = '操作成功'
    return response


class StandardCreateAPI(generics.CreateAPIView):
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


class StandardListAPI(generics.ListAPIView):
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


class StandardUpdateAPI(generics.UpdateAPIView):
    def update(self, request, *args, **kwargs):
        response = ResponseStandard()
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
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


class StandardDeleteAPI(generics.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete = True
        instance.save(update_fields=['delete'])
        response = ResponseStandard()
        response.msg = '操作成功'
        return Response(response.get_dic)


class StandardRetrieveAPI(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        response = ResponseStandard()
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        response.data = data
        return Response(response.get_dic)


class ChoicesSerializerField(serializers.SerializerMethodField):
    """
    A read-only field that return the representation of a model field with choices.
    """

    def to_representation(self, value):
        # sample: 'get_XXXX_display'
        method_name = 'get_{field_name}_display'.format(field_name=self.field_name)
        # retrieve instance method
        method = getattr(value, method_name)
        # finally use instance method to return result of get_XXXX_display()
        return method()
