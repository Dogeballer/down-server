from django.urls import path, re_path
from system_settings import views
from rest_framework.routers import DefaultRouter

app_name = "system_settings"
urlpatterns = [
    path('dataSource/list', views.DataSourceList.as_view()),
    path('dataSource/create', views.DataSourceCreate.as_view()),
    path('dataSource/get/<int:pk>', views.DataSourceDetail.as_view()),
    path('dataSource/update/<int:pk>', views.DataSourceUpdate.as_view()),
    path('dataSource/delete/<int:pk>', views.DataSourceDelete.as_view()),
    path('dataSource/dataSourceTest', views.DataSourceTest.as_view()),
    path('dataSource/updateStatus/<int:pk>', views.UpdateDataSourceStatus.as_view()),
    path('udf/onlineDebug', views.UdfOnlineDebug.as_view()),
    path('udf/list', views.UdfPageList.as_view()),
    path('udf/create', views.UdfCreate.as_view()),
    path('udf/get/<int:pk>', views.UdfRetrieve.as_view()),
    path('udf/update/<int:pk>', views.UdfUpdate.as_view()),
    path('udf/delete/<int:pk>', views.UdfDelete.as_view()),
    path('udf/updateStatus/<int:pk>', views.UpdateUdfStatus.as_view()),
    path('udf/udfArgs/list', views.UdfArgsList.as_view()),
    path('udf/udfArgs/create', views.UdfArgsCreate.as_view()),
    path('udf/udfArgs/update/<int:pk>', views.UdfArgsUpdate.as_view()),
    path('udf/udfArgs/delete/<int:pk>', views.UdfArgsDelete.as_view()),
]
