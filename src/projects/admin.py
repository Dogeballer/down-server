from django.contrib import admin
from .models import Projects, Modules, AuthenticationEnvironment


# Register your models here.

class ProjectsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'describe', 'status', 'create_time')


class ModulesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'describe', 'create_time', 'project', 'tester')


class AuthenticationEnvironmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'func_call', 'is_redis', 'timeout', 'header_value', 'execution_result', 'error_log',
                    'status', 'remark', 'last_time')
    list_exclude = []
    list_filter = ('name', 'is_redis', 'execution_result', 'status')


# admin.site.register(Projects, ProjectsAdmin)
# admin.site.register(Modules, ModulesAdmin)
admin.site.register(Projects, ProjectsAdmin)
admin.site.register(Modules, ModulesAdmin)
admin.site.register(AuthenticationEnvironment, AuthenticationEnvironmentAdmin)
