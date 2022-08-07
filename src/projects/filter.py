from django_filters import rest_framework as filters
from django.db.models import Q

from interfaces.models import Interface
from .models import Projects, Modules, Environment


class ProjectsFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    describe = filters.CharFilter(field_name='describe', lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='status')

    class Meta:
        model = Projects
        fields = ['name', 'status', 'describe']


class ModulesFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    project = filters.CharFilter(field_name='project')
    status = filters.BooleanFilter(field_name='status')

    class Meta:
        model = Modules
        fields = ['name', 'project', 'status']


class EnvironmentFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    project = filters.CharFilter(field_name='project')
    status = filters.BooleanFilter(field_name='status')
    interface = filters.NumberFilter(field_name='interface', method='filter_interface')

    def filter_interface(self, queryset, name, value):
        interface_id = self.request.query_params.get('interface')
        try:
            interface = Interface.objects.get(pk=interface_id)
            project = interface.interface_class.project
            queryset = Environment.objects.filter(project=project)
        except:
            queryset = Environment.objects.filter(status=True)

        return queryset

    class Meta:
        model = Environment
        fields = ['name', 'project', 'status', 'interface']
