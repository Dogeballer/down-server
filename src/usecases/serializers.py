import json
from rest_framework import serializers
from usecases.models import *
from projects.models import Projects, Modules


class UseCasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UseCases
        fields = "__all__"


class UseCaseCopySerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    caseId = serializers.IntegerField()


class CaseStepCopySerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    stepId = serializers.IntegerField()


class CaseStepsParamSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    id = serializers.IntegerField()
    name = serializers.CharField()
    param_in = serializers.CharField()
    value = serializers.CharField()


class CaseStepsCreateSerializer(serializers.ModelSerializer):
    param = CaseStepsParamSerializer(many=True, allow_null=False, required=False)
    body = serializers.JSONField(required=False)

    class Meta:
        model = CaseSteps
        fields = "__all__"

    def create(self, validated_data):
        param = json.dumps(validated_data.get('param', []))
        body = validated_data.get('body', '')
        validated_data['param'] = param
        validated_data['body'] = body
        case_step = CaseSteps.objects.create(**validated_data)
        if case_step.type in [0, 2, 3]:
            case_assert = CaseAssert.objects.create(name='返回码校验', type_from=1, assert_type=2, verify_value=200,
                                                    case_step=case_step)
        elif case_step.type in [4, 5, 6, 8, 9, 10, 11, 12]:
            case_assert = CaseAssert.objects.create(name='是否成功', type_from=0, value_statement='$.code', assert_type=2,
                                                    verify_value=0, case_step=case_step)
        return case_step

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.type = validated_data.get('type', instance.type)
        instance.sort = validated_data.get('sort', instance.sort)
        instance.describe = validated_data.get('describe', instance.describe)
        instance.status = validated_data.get('status', instance.status)
        # instance.use_case = validated_data.get('use_case', instance.use_case)
        instance.wrap_count = validated_data.get('wrap_count', instance.wrap_count)
        instance.polling_interval = validated_data.get('polling_interval', instance.polling_interval)
        instance.case_interface = validated_data.get('case_interface', instance.case_interface)
        instance.data_source = validated_data.get('data_source', instance.data_source)
        instance.sql_script = validated_data.get('sql_script', instance.sql_script)
        instance.param = json.dumps(validated_data.get('param', instance.param))
        instance.body = validated_data.get('body', instance.body)
        instance.topic = validated_data.get('topic', instance.topic)
        instance.qos = validated_data.get('qos', instance.qos)
        instance.save()
        return instance


class CaseStepsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseSteps
        fields = "__all__"


class CaseAssertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseAssert
        fields = "__all__"


class CaseStepPollSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStepPoll
        fields = "__all__"


class StepCircularKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = StepCircularKey
        fields = "__all__"


class StepForwardAfterOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepForwardAfterOperation
        fields = "__all__"


class ModulesCasesSerializer(serializers.ModelSerializer):
    queryset = UseCases.objects.filter(delete=False)
    children = UseCasesSerializer(source='modules', many=True)

    class Meta:
        model = Modules
        fields = ['id', 'name', 'status', 'describe', 'tester', 'project', 'create_time', 'update_time', 'children']


class UseCasesTreeSerializer(serializers.ModelSerializer):
    children = ModulesCasesSerializer(source='modules_project', many=True)

    class Meta:
        model = Projects
        fields = ['id', 'name', 'status', 'describe', 'create_time', 'update_time', 'children']


class TaskExecuteSerializer(serializers.Serializer):
    useCaseList = serializers.ListField()
    type = serializers.IntegerField()
    mode = serializers.IntegerField()
    executor = serializers.CharField()
    environment_id = serializers.IntegerField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class TaskLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLog
        fields = "__all__"


class CaseLogSerializer(serializers.ModelSerializer):
    use_case = UseCasesSerializer()

    class Meta:
        model = CaseLog
        fields = "__all__"


class StepLogSerializer(serializers.ModelSerializer):
    case_step = CaseStepsSerializer()

    class Meta:
        model = CaseStepLog
        fields = "__all__"


class UdfLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UdfLog
        fields = "__all__"


class InterfaceSaveCaseSerializer(serializers.ModelSerializer):
    case_interface = serializers.IntegerField()
    param = CaseStepsParamSerializer(many=True, allow_null=False)
    body = serializers.JSONField()

    class Meta:
        model = UseCases
        fields = ['name', 'type', 'modules', 'describe', 'user', 'param', 'body', 'case_interface']

    def create(self, validated_data):
        param = json.dumps(validated_data.pop('param'))
        body = json.dumps(validated_data.pop('body'))
        case_interface_id = validated_data.pop('case_interface')
        case_interface = Interface.objects.get(pk=case_interface_id)
        step_name = case_interface.name
        use_case = UseCases.objects.create(**validated_data, )
        case_step = CaseSteps.objects.create(name=step_name, use_case=use_case, case_interface=case_interface,
                                             param=param, body=body, type=0, sort=1)
        case_assert = CaseAssert.objects.create(name='返回码校验', type_from=1, assert_type=2, verify_value=200,
                                                case_step=case_step)
        return use_case


class CaseStepCallBackParamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepCallBackParams
        fields = "__all__"


class UseCaseSelectorSerializer(serializers.ModelSerializer):
    # children = UseCasesSerializer(source='modules', many=True)

    class Meta:
        model = Modules
        fields = "__all__"


class SqlScriptExecuteSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    data_source_id = serializers.IntegerField(required=False)
    use_case_id = serializers.IntegerField()
    step_type = serializers.IntegerField()
    sql_script = serializers.CharField()


class MqttPublishSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    mqtt_id = serializers.IntegerField(required=False)
    topic = serializers.CharField()
    qos = serializers.IntegerField()
    payload = serializers.CharField()


class MqttSubSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    mqtt_id = serializers.IntegerField(required=False)
    topic = serializers.CharField()
    qos = serializers.IntegerField()
