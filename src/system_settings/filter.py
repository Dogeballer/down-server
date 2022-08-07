from django_filters import rest_framework as filters
from django.db.models import Q
from .models import DataSource, Udf, UdfArgs


class DataSourceFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    host = filters.CharFilter(field_name='host', lookup_expr='icontains')
    database = filters.CharFilter(field_name='database', lookup_expr='icontains')
    database_type = filters.NumberFilter(field_name='database_type')
    status = filters.BooleanFilter(field_name='status')

    class Meta:
        model = DataSource
        fields = ['name', 'database_type', 'host', 'database', 'status']


class UdfFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    zh_name = filters.CharFilter(field_name='zh_name', lookup_expr='icontains')
    user = filters.CharFilter(field_name='user', lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='status')

    class Meta:
        model = Udf
        fields = ['name', 'zh_name', 'user', 'status']


class UdfArgsFilter(filters.FilterSet):
    udf = filters.NumberFilter(field_name='udf')

    class Meta:
        model = UdfArgs
        fields = ['udf']
