"""down URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from system_settings.views import ConsumerTokenGet, ConsumerTokenRefresh

schema_view = get_schema_view(
    openapi.Info(
        title="Down测试平台API",
        default_version='v2.0',
        description="Down测试平台接口文档",
        terms_of_service="https://www.google.com/",
        contact=openapi.Contact(email="down-data"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# django-admin setting
admin.site.site_header = 'down django-admin'  # default: "Django Administration"
admin.site.index_title = 'down'  # default: "Site administration"
admin.site.site_title = 'down'  # default: "Django site admin"

urlpatterns = [
    # django-admin
    path('admin/', admin.site.urls),
    # rest framework doc
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # 配置django-rest-framwork API路由
    path(r'system_settings/', include('system_settings.urls', namespace='system_settings')),
    path(r'projects/', include('projects.urls', namespace='projects')),
    path(r'interfaces/', include('interfaces.urls', namespace='interfaces')),
    path(r'usecases/', include('usecases.urls', namespace='usecases')),
    path(r'testSuite/', include('test_suite.urls', namespace='test_suite')),

    # 配置drf-yasg路由
    path('^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('api/token', ConsumerTokenGet.as_view()),
    path('api/token/refresh', ConsumerTokenRefresh.as_view()),
]
