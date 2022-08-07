from django.urls import path, re_path
from test_suite import views
from rest_framework.routers import DefaultRouter

app_name = "testSuite"
urlpatterns = [
    path('testSuiteClass/list', views.TestSuiteClassList.as_view()),
    path('testSuiteClass/create', views.TestSuiteClassCreate.as_view()),
    path('testSuiteClass/get/<int:pk>', views.TestSuiteClassDetail.as_view()),
    path('testSuiteClass/update/<int:pk>', views.TestSuiteClassUpdate.as_view()),
    path('testSuiteClass/updateStatus/<int:pk>', views.UpdateTestSuiteClassStatus.as_view()),
    path('testSuiteClass/delete/<int:pk>', views.TestSuiteClassDelete.as_view()),
    path('list', views.TestSuiteList.as_view()),
    path('create', views.TestSuiteCreate.as_view()),
    path('get/<int:pk>', views.TestSuiteDetail.as_view()),
    path('update/<int:pk>', views.TestSuiteUpdate.as_view()),
    path('updateStatus/<int:pk>', views.UpdateTestSuiteStatus.as_view()),
    path('delete/<int:pk>', views.TestSuiteDelete.as_view()),
    path('batchDelete', views.TestSuiteBatchDelete.as_view()),
    path('suiteExecute', views.SuiteExecute.as_view()),
    path('asyncSuiteExecute', views.AsyncSuiteExecute.as_view()),
    path('jenkinsTrigger', views.JenkinsTrigger.as_view()),
]
