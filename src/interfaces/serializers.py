from rest_framework import serializers
from rest_framework.fields import URLField, IntegerField

from projects.models import Projects
from projects.serializers import *
from .models import *


class InterfaceParamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceParam
        fields = "__all__"


class InterfaceBodyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceBody
        fields = ['name', 'describe', 'required', 'example', 'node', 'circulation', 'parent', 'type']


class InterfaceBodyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceBody
        fields = ['name', 'describe', 'required', 'example', 'node', 'circulation', 'parent', 'belong_interface',
                  'type']


class InterfaceSerializer(serializers.ModelSerializer):
    interface_param = InterfaceParamCreateSerializer(many=True, allow_empty=True)
    interface_body = InterfaceBodyCreateSerializer(many=True, allow_empty=True)

    class Meta:
        model = Interface
        fields = "__all__"

    def create(self, validated_data):
        interface_param_data = validated_data.pop('interface_param')
        interface_body_data = validated_data.pop('interface_body')
        interface = Interface.objects.create(**validated_data)
        for data in interface_param_data:
            InterfaceParam.objects.create(interface=interface, **data)
        for data in interface_body_data:
            InterfaceBody.objects.create(belong_interface=interface, **data)
        interface = Interface.objects.get(pk=interface.id).__dict__
        interface['interface_param'] = []
        interface['interface_body'] = []
        # print(interface)
        return interface

    def update(self, instance, validated_data):
        interface_param_data = validated_data.pop('interface_param')
        interface_body_data = validated_data.pop('interface_body')
        instance.name = validated_data.get('name', instance.name)
        instance.method = validated_data.get('method', instance.method)
        instance.path = validated_data.get('path', instance.path)
        instance.interface_class = validated_data.get('interface_class', instance.interface_class)
        instance.status = validated_data.get('status', instance.status)
        instance.describe = validated_data.get('describe', instance.describe)
        instance.save()
        # print(interface_param_data)
        # try:
        #     history = InterfaceTest.objects.get(test_interface=instance.id)
        #     history.delete()
        # except:
        #     pass
        # interface_params = InterfaceParam.objects.filter(interface_id=instance.id)
        # # interface_bodys = InterfaceBody.objects.filter(belong_interface_id=instance.id)
        # for interface_param in interface_params:
        #     interface_param.delete()
        # # for interface_body in interface_bodys:
        # #     interface_body.delete()
        # for data in interface_param_data:
        #     InterfaceParam.objects.create(interface_id=instance.id, **data)
        # # for data in interface_body_data:
        # #     InterfaceBody.objects.create(belong_interface_id=instance.id, **data)
        return instance


class InterfaceParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceParam
        fields = "__all__"


class InterfaceBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceBody
        fields = "__all__"


class InterfaceClassProjectSerializer(serializers.ModelSerializer):
    name = serializers.ModelField(InterfaceClass._meta.get_field('class_name'))

    class Meta:
        model = InterfaceClass
        fields = ['id', 'name', 'project']


class InterfaceGetSerializer(serializers.ModelSerializer):
    interface_param = InterfaceParamSerializer(source='interface', many=True)
    interface_body = InterfaceBodySerializer(source='belong_interface', many=True)

    class Meta:
        model = Interface
        fields = ['name', 'method', 'path', 'interface_class', 'status', 'describe', 'tags',
                  'interface_param', 'interface_body', 'version']


class SwaggerAnalysisSerializer(serializers.Serializer):
    swagger_url = URLField(max_length=200, min_length=None, allow_blank=False)
    project_id = serializers.IntegerField()
    version = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class InterfaceTestParamSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    param_in = serializers.CharField()
    value = serializers.CharField()


class InterfaceTestSerializer(serializers.Serializer):
    environmentId = serializers.IntegerField()
    interfaceId = serializers.IntegerField()
    params = InterfaceTestParamSerializer(many=True)
    body = serializers.JSONField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class InterfaceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = "__all__"


class InterfaceClassSerializer(serializers.ModelSerializer):
    name = serializers.ModelField(InterfaceClass._meta.get_field('class_name'))
    children = InterfaceListSerializer(source='interface_class', many=True)

    class Meta:
        model = InterfaceClass
        fields = ['id', 'name', 'status', 'describe', 'project', 'create_time', 'update_time', 'children']


class InterfaceTreeSerializer(serializers.ModelSerializer):
    children = InterfaceClassSerializer(source='project', many=True)

    class Meta:
        model = Projects
        fields = ['id', 'name', 'status', 'describe', 'create_time', 'update_time', 'status', 'children']


class InterfaceClassListSerializer(serializers.ModelSerializer):
    project = ProjectsSerializer(many=False)

    class Meta:
        model = InterfaceClass
        fields = "__all__"


class InterfaceClassCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceClass
        fields = "__all__"


class InterfaceClassSelectorSerializer(serializers.ModelSerializer):
    interface_class = InterfaceClassListSerializer(source='project', many=True)

    class Meta:
        model = Projects
        fields = ['id', 'name', 'status', 'describe', 'create_time', 'update_time', 'status', 'interface_class']


class InterfaceTestHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceTest
        fields = "__all__"


class InterfaceCallBackParamsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterfaceCallBackParams
        fields = "__all__"
