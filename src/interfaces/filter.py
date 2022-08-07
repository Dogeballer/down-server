from django_filters import rest_framework as filters
from django.db.models import Q
from .models import *


class InterfaceFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    path = filters.CharFilter(field_name='path', lookup_expr='icontains')
    method = filters.CharFilter(field_name='method')
    status = filters.BooleanFilter(field_name='status')
    interface_class = filters.NumberFilter(field_name='interface_class')
    # project = filters.CharFilter()
    tags = filters.CharFilter(field_name='tags')
    describe = filters.CharFilter(field_name='describe', lookup_expr='icontains')

    class Meta:
        model = Interface
        fields = ['name', 'method', 'status', 'interface_class', 'tags', 'describe']


class InterfaceClassFilter(filters.FilterSet):
    class_name = filters.CharFilter(field_name='class_name', lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='status')
    project = filters.NumberFilter(field_name='project')

    class Meta:
        model = InterfaceClass
        fields = ['class_name', 'status', 'project']


class InterfaceTestFilter(filters.FilterSet):
    test_interface = filters.NumberFilter(field_name='test_interface')

    class Meta:
        model = InterfaceTest
        fields = ['test_interface']


class InterfaceCallBackParamsFilter(filters.FilterSet):
    return_interface = filters.NumberFilter(field_name='return_interface')

    class Meta:
        model = InterfaceCallBackParams
        fields = ['return_interface']


class InterfaceSelectorFilter(filters.FilterSet):
    project = filters.NumberFilter(field_name='project')

    class Meta:
        model = InterfaceClass
        fields = ['project']
