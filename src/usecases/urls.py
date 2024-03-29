from django.urls import path, re_path
from usecases import views
from rest_framework.routers import DefaultRouter

app_name = "useCases"
urlpatterns = [
    path('list', views.UseCasesList.as_view()),
    path('selector', views.UseCaseSelector.as_view()),
    path('suiteUseCasesList', views.SuiteUseCasesList.as_view()),
    path('create', views.UseCasesCreate.as_view()),
    path('copy', views.CopyUseCase.as_view()),
    path('get/<int:pk>', views.UseCasesDetail.as_view()),
    path('update/<int:pk>', views.UseCasesUpdate.as_view()),
    path('updateStatus/<int:pk>', views.UpdateUseCaseStatus.as_view()),
    path('delete/<int:pk>', views.UseCasesDelete.as_view()),
    path('caseSteps/list', views.CaseStepsList.as_view()),
    path('caseSteps/create', views.CaseStepsCreate.as_view()),
    path('caseSteps/get/<int:pk>', views.CaseStepsDetail.as_view()),
    path('caseSteps/update/<int:pk>', views.CaseStepsUpdate.as_view()),
    path('caseSteps/delete/<int:pk>', views.CaseStepsDelete.as_view()),
    path('caseSteps/copy', views.CopyCaseStep.as_view()),
    path('caseAssert/list', views.CaseAssertList.as_view()),
    path('caseAssert/create', views.CaseAssertCreate.as_view()),
    path('caseAssert/get/<int:pk>', views.CaseAssertDetail.as_view()),
    path('caseAssert/update/<int:pk>', views.CaseAssertUpdate.as_view()),
    path('caseAssert/delete/<int:pk>', views.CaseAssertDelete.as_view()),
    path('caseStepPoll/list', views.CaseStepPollList.as_view()),
    path('caseStepPoll/create', views.CaseStepPollCreate.as_view()),
    path('caseStepPoll/get/<int:pk>', views.CaseStepPollDetail.as_view()),
    path('caseStepPoll/update/<int:pk>', views.CaseStepPollUpdate.as_view()),
    path('caseStepPoll/delete/<int:pk>', views.CaseStepPollDelete.as_view()),
    path('stepCircularKey/list', views.StepCircularKeyList.as_view()),
    path('stepCircularKey/create', views.StepCircularKeyCreate.as_view()),
    path('stepCircularKey/get/<int:pk>', views.StepCircularKeyDetail.as_view()),
    path('stepCircularKey/update/<int:pk>', views.StepCircularKeyUpdate.as_view()),
    path('stepCircularKey/delete/<int:pk>', views.StepCircularKeyDelete.as_view()),
    path('stepForwardAfterOperation/list', views.StepForwardAfterOperationList.as_view()),
    path('stepForwardAfterOperation/create', views.StepForwardAfterOperationCreate.as_view()),
    path('stepForwardAfterOperation/get/<int:pk>', views.StepForwardAfterOperationDetail.as_view()),
    path('stepForwardAfterOperation/update/<int:pk>', views.StepForwardAfterOperationUpdate.as_view()),
    path('stepForwardAfterOperation/delete/<int:pk>', views.StepForwardAfterOperationDelete.as_view()),
    path('taskExecute', views.TaskExecute.as_view()),
    path('useCaseAsyncExecute', views.UseCaseAsyncExecute.as_view()),
    path('interfaceSaveCase', views.InterfaceSaveCase.as_view()),
    path('tree', views.UseCasesTree.as_view()),
    path('taskLogList', views.TaskLogList.as_view()),
    path('taskLogTree', views.TaskLogTree.as_view()),
    path('caseLogList', views.CaseLogList.as_view()),
    path('caseLogPageList', views.CaseLogPageList.as_view()),
    path('stepLogList', views.StepLogList.as_view()),
    path('udfLogList', views.UdfLogList.as_view()),
    path('casePollParamSelect/<int:pk>', views.CasePollParam.as_view()),
    path('stepCallBackParams', views.StepCallBackParamsCreateList.as_view()),
    path('stepCallBackParams/<int:pk>', views.StepCallBackParamsDetail.as_view()),
    path('sqlScriptExecute', views.SqlScriptExecute.as_view()),
]
