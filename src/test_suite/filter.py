from django_filters import rest_framework as filters
from django.db.models import Q
from .models import *


class TestSuiteFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    code = filters.CharFilter(field_name='code', lookup_expr='icontains')
    mode = filters.NumberFilter(field_name='mode')
    type = filters.NumberFilter(field_name='type')
    suite_class = filters.NumberFilter(field_name='suite_class')

    class Meta:
        model = TestSuite
        fields = ['name', 'mode', 'type', 'suite_class']
