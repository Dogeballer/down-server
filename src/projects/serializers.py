from rest_framework import serializers

from down.CommonStandards import ChoicesSerializerField
from projects.models import Modules, Projects, Environment, AuthenticationEnvironment


class ProjectsSerializer(serializers.ModelSerializer):
    class Meta:
        # 指定要序列号的表模型是book
        model = Projects
        # 查询所有的列
        fields = "__all__"
        # 也可以传列表,指定取几个
        # fields=['name','authors','publish']
        # 除了nid都查
        # exclude = ['nid']
        # 查询的深度,如果有关联的表,会自动关联查询,深度为1的所有数据
        # depth = 1
        # fields和exclude不能同时用
        # depth指定深度，个人建议最多  用3
        # name = serializers.CharField(error_messages={'required': '该字段必填'})


class ModulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = "__all__"


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = "__all__"


class AuthenticationEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticationEnvironment
        fields = "__all__"


class ModuleListSerializer(serializers.ModelSerializer):
    project = ProjectsSerializer(many=False)

    class Meta:
        model = Modules
        fields = "__all__"


class EnvironmentListSerializer(serializers.ModelSerializer):
    project = ProjectsSerializer(many=False)
    authentication_environment = AuthenticationEnvironmentSerializer(many=False)

    # uac_url = serializers.CharField(source='get_uac_url_display')

    class Meta:
        model = Environment
        fields = "__all__"


class ModuleProSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modules
        fields = ['name', 'describe', 'tester', 'developer', 'status']


class ProModulesSelectorSerializer(serializers.ModelSerializer):
    modules = ModulesSerializer(source='modules_project', many=True)

    class Meta:
        model = Projects
        fields = ['id', 'name', 'modules', 'status', 'describe', 'create_time', 'update_time', 'status']


class ProModulesSerializer(serializers.ModelSerializer):
    modules = ModuleProSerializer(many=True)

    class Meta:
        model = Projects
        fields = ['name', 'describe', 'modules']

    def create(self, validated_data):
        modules_data = validated_data.pop('modules')
        project = Projects.objects.create(**validated_data)
        for module_data in modules_data:
            Modules.objects.create(project=project, **module_data)
        return project

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.describe = validated_data.get('describe', instance.describe)
        instance.save()
        return instance
