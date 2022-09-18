from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from system_settings.models import DataSource, Udf, UdfArgs, MQTTClient


class ConsumerTokenSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': attrs['password'],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)
        if self.user is None or not self.user.is_active:
            raise ValidationError(
                {'getTokenError': '用户名或密码错误'}
            )
        refresh = self.get_token(self.user)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
        return data


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = "__all__"


class UdfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Udf
        fields = "__all__"


class UdfArgsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UdfArgs
        fields = "__all__"


class UdfOnlineDebugSerializer(serializers.Serializer):
    SourceCode = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class MQTTClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = MQTTClient
        fields = "__all__"
