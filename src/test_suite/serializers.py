import json
import time
from datetime import datetime

from rest_framework import serializers
from usecases.models import *
from projects.models import *
from test_suite.models import *


class TestSuiteClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSuiteClass
        fields = "__all__"


class TestSuiteCasesSerializer(serializers.ModelSerializer):
    global_params = serializers.JSONField()

    class Meta:
        model = TestSuiteCases
        fields = "__all__"


class TestSuiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSuite
        fields = "__all__"


class TestSuiteCreateSerializer(serializers.ModelSerializer):
    global_params = serializers.JSONField()
    public_headers = serializers.JSONField()
    cases = TestSuiteCasesSerializer(many=True)

    class Meta:
        model = TestSuite
        fields = "__all__"

    def create(self, validated_data):
        cases_data = validated_data.pop('cases')
        public_headers = validated_data.pop('public_headers')
        global_params = validated_data.pop('global_params')
        timing = validated_data.get('timing')
        name = validated_data.get('name')
        timing = str(timing).split(':')
        hour = timing[0]
        minute = timing[1]
        crontab_schedule = CrontabSchedule.objects.create(minute=minute, hour=hour, timezone='Asia/Shanghai')
        periodic_task = PeriodicTask.objects.create(name=name, task='test_suite.tasks.dispatch_execute_test_suite',
                                                    crontab=crontab_schedule)
        periodic_task.kwargs = json.dumps({"name": name, "id": periodic_task.id})
        periodic_task.save()
        try:
            public_headers = json.dumps(public_headers)
        except:
            public_headers = []
        try:
            global_params = json.dumps(global_params)
        except:
            global_params = []
        test_suite = TestSuite.objects.create(**validated_data, public_headers=public_headers,
                                              global_params=global_params, crontab_schedule=crontab_schedule,
                                              periodic_task=periodic_task)
        for data in cases_data:
            try:
                global_params = json.dumps(data.get('global_params', []))
            except:
                global_params = json.dumps([])
            data['global_params'] = global_params
            TestSuiteCases.objects.create(test_suite=test_suite, **data)
        return test_suite

    def update(self, instance, validated_data):
        # print(instance)
        timing = validated_data.get('timing')
        name = validated_data.get('name')
        precondition_case = validated_data.get('precondition_case')
        cases_data = validated_data.pop('cases')
        cases = TestSuiteCases.objects.filter(test_suite=instance)
        cases.delete()
        timing = str(timing).split(':')
        hour = timing[0]
        minute = timing[1]
        crontab_schedule = instance.crontab_schedule
        crontab_schedule.minute = minute
        crontab_schedule.hour = hour
        crontab_schedule.save()
        periodic_task = instance.periodic_task
        periodic_task.name = name
        periodic_task.crontab = crontab_schedule
        periodic_task.kwargs = json.dumps({"name": name, "id": periodic_task.id})
        periodic_task.save()
        for data in cases_data:
            try:
                global_params = json.dumps(data.get('global_params', []))
            except:
                global_params = json.dumps([])
            data['global_params'] = global_params
            TestSuiteCases.objects.create(test_suite_id=instance.id, **data)
        public_headers = validated_data.pop('public_headers')
        global_params = validated_data.pop('global_params')
        try:
            public_headers = json.dumps(public_headers)
        except:
            public_headers = json.dumps([])
        try:
            global_params = json.dumps(global_params)
        except:
            global_params = json.dumps([])
        instance.name = validated_data.get('name', instance.name)
        instance.suite_class = validated_data.get('suite_class', instance.suite_class)
        instance.environment = validated_data.get('environment', instance.environment)
        instance.code = validated_data.get('code', instance.code)
        instance.mode = validated_data.get('mode', instance.mode)
        # instance.type = validated_data.get('type', instance.type)
        instance.execute_frequency = validated_data.get('execute_frequency', instance.execute_frequency)
        instance.timing = validated_data.get('timing', instance.timing)
        instance.public_headers = public_headers
        instance.global_params = global_params
        instance.precondition_case = precondition_case
        instance.save()
        return instance


class TestSuiteDetailSerializer(serializers.ModelSerializer):
    cases = TestSuiteCasesSerializer(source='suite', many=True)

    class Meta:
        model = TestSuite
        fields = "__all__"


class JenkinsTriggerExecuteSerializer(serializers.Serializer):
    ci_task_name = serializers.CharField()
    ci_task_build_id = serializers.IntegerField()
    ci_env = serializers.CharField()
    ci_branch = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
