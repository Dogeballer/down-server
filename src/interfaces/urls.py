from django.urls import path, re_path
from interfaces import views

app_name = "projects"
urlpatterns = [
    path('', views.InterfaceCreate.as_view()),
    path('list', views.InterfaceList.as_view()),
    path('selector', views.InterfaceSelector.as_view()),
    path('interfaceClass/list', views.InterfaceClassList.as_view()),
    path('interfaceClass/create', views.InterfaceClassCreate.as_view()),
    path('interfaceClass/delete/<int:pk>', views.InterfaceClassDelete.as_view()),
    path('interfaceClass/update/<int:pk>', views.InterfaceClassUpdate.as_view()),
    path('interfaceParam/delete/<int:pk>', views.InterfaceParamDelete.as_view()),
    path('interfaceBody/list', views.InterfaceBodyList.as_view()),
    path('interfaceBody/create', views.InterfaceBodyCreate.as_view()),
    path('interfaceBody/delete/<int:pk>', views.InterfaceBodyDelete.as_view()),
    path('interfaceBody/update/<int:pk>', views.InterfaceBodyUpdate.as_view()),
    path('interfaceClass/selector', views.InterfaceClassSelector.as_view()),
    path('update/<int:pk>', views.InterfaceDetailUpdate.as_view()),
    path('updateStatus/<int:pk>', views.UpdateInterfaceStatus.as_view()),
    path('proDelete/<int:pk>', views.ProjectInterfaceDelete.as_view()),
    path('<int:pk>', views.InterfaceDetail.as_view()),
    path('SwaggerAnalysis', views.SwaggerAnalysisAPI.as_view()),
    path('interfaceTest', views.InterfaceTestApi.as_view()),
    path('interfaceTest/list', views.InterfaceTestHistory.as_view()),
    path('interfaceCallBackParams', views.InterfaceCallBackParamsCreateList.as_view()),
    path('interfaceCallBackParams/<int:pk>', views.InterfaceCallBackParamsDetail.as_view()),
    path('tree', views.InterfaceTree.as_view())
]
