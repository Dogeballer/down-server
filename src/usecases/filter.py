from django_filters import rest_framework as filters
from django.db.models import Q
from .models import *


class UseCasesFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    user = filters.CharFilter(field_name='user', lookup_expr='icontains')
    status = filters.BooleanFilter(field_name='status')
    modules = filters.NumberFilter(field_name='modules')
    type = filters.NumberFilter(field_name='type')
    # project = filters.CharFilter()
    describe = filters.CharFilter(field_name='describe', lookup_expr='icontains')

    class Meta:
        model = UseCases
        fields = ['name', 'user', 'status', 'modules', 'type', 'describe']


class CaseStepsFilter(filters.FilterSet):
    use_case = filters.NumberFilter(field_name='use_case')

    class Meta:
        model = CaseSteps
        fields = ['use_case']


class CaseAssertFilter(filters.FilterSet):
    case_step = filters.NumberFilter(field_name='case_step')

    class Meta:
        model = CaseAssert
        fields = ['case_step']


class CaseStepPollFilter(filters.FilterSet):
    case_step = filters.NumberFilter(field_name='case_step')

    class Meta:
        model = CaseStepPoll
        fields = ['case_step']


class StepCircularKeyFilter(filters.FilterSet):
    case_step = filters.NumberFilter(field_name='case_step')

    class Meta:
        model = StepCircularKey
        fields = ['case_step']


class StepForwardAfterOperationFilter(filters.FilterSet):
    step = filters.NumberFilter(field_name='step')

    class Meta:
        model = StepForwardAfterOperation
        fields = ['step']


class TaskLogFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    executor = filters.CharFilter(field_name='executor', lookup_expr='icontains')
    execute_date = filters.DateFilter(field_name='execute_date')
    mode = filters.NumberFilter(field_name='mode')
    execute_type = filters.NumberFilter(field_name='execute_type')
    execute_status = filters.NumberFilter(field_name='execute_status')
    job_id = filters.CharFilter(field_name='job_id')

    class Meta:
        model = TaskLog
        fields = ['name', 'executor', 'execute_date', 'mode', 'execute_type', 'execute_status', 'job_id']


class TaskLogTreeFilter(filters.FilterSet):
    execute_date = filters.DateFilter(field_name='execute_date')
    job_id = filters.CharFilter(field_name='job_id')

    class Meta:
        model = TaskLog
        fields = ['execute_date', 'job_id']


class CaseLogFilter(filters.FilterSet):
    execute_status = filters.NumberFilter(field_name='execute_status')
    use_case = filters.NumberFilter(field_name='use_case')
    task_log = filters.NumberFilter(field_name='task_log')

    class Meta:
        model = CaseLog
        fields = ['use_case', 'task_log', 'execute_status']


class StepLogFilter(filters.FilterSet):
    case_log = filters.NumberFilter(field_name='case_log')

    class Meta:
        model = CaseStepLog
        fields = ['case_log']


class UdfLogFilter(filters.FilterSet):
    case_log = filters.NumberFilter(field_name='case_log')
    udf = filters.NumberFilter(field_name='udf')
    udf_name = filters.CharFilter(field_name='udf_name', lookup_expr='icontains')
    udf_zh_name = filters.CharFilter(field_name='udf_zh_name', lookup_expr='icontains')

    class Meta:
        model = UdfLog
        fields = ['case_log', 'udf', 'udf_name', 'udf_zh_name']


class StepCallBackParamsFilter(filters.FilterSet):
    step = filters.NumberFilter(field_name='step')

    class Meta:
        model = StepCallBackParams
        fields = ['step']
