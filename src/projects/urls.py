from django.urls import path, re_path
from projects import views
from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register(r'projects', views.ProjectViewSet, basename='projects')
# urlpatterns = router.urls

app_name = "projects"
urlpatterns = [
    path('', views.ProjectsList.as_view()),
    path('<int:pk>', views.ProjectDetail.as_view()),
    path('selector', views.ProModulesSelector.as_view()),
    path('modules/list/', views.ModulesList.as_view()),
    path('modules', views.ModuleCreate.as_view()),
    path('modules/<int:pk>', views.ModuleDetail.as_view()),
    path('environment/list/', views.EnvironmentList.as_view()),
    path('environment', views.EnvironmentCreate.as_view()),
    path('environment/<int:pk>', views.EnvironmentDetail.as_view()),
    path('environment/updateStatus/<int:pk>', views.UpdateEnvironmentStatus.as_view()),
    path('authEnvironment/list', views.AuthEnvironmentList.as_view()),
    path('authEnvironment/create', views.AuthEnvironmentCreate.as_view()),
    path('authEnvironment/update/<int:pk>', views.AuthEnvironmentUpdate.as_view()),
    path('authEnvironment/updateStatus/<int:pk>', views.UpdateAuthEnvironmentStatus.as_view()),
    path('authEnvironment/delete/<int:pk>', views.AuthEnvironmentDelete.as_view()),
]
