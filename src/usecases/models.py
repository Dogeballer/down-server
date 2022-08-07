from django.db import models
from interfaces.models import Interface
from projects.models import Modules
from system_settings.models import DataSource, Udf


# Create your models here.


class UseCases(models.Model):
    """
    用例表
    """
    case_type = (
        (0, '正向用例'),
        (1, '异常用例'),
        (2, '场景用例'),
        (3, '流程用例'),
    )
    name = models.CharField(max_length=50, verbose_name="用例名称")
    type = models.IntegerField(choices=case_type, null=False, verbose_name="用例类型")
    modules = models.ForeignKey(Modules, related_name='modules', on_delete=models.CASCADE,
                                verbose_name="所属模块", default=None, null=True)
    data_source = models.ForeignKey(DataSource, related_name='case_data_source', null=True, on_delete=models.CASCADE,
                                    verbose_name="执行对应元数据")
    status = models.BooleanField(default=1, verbose_name="用例状态")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="用例信息简介")
    user = models.CharField(max_length=50, verbose_name="维护者", default="", null=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    global_params = models.CharField(max_length=1000, verbose_name="全局参数", default='{}')
    params = models.CharField(max_length=1000, verbose_name="用例参数", default='{}')
    delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        verbose_name = '用例管理'
        verbose_name_plural = '用例管理'

    def __str__(self):
        return self.name


class CaseSteps(models.Model):
    """
    用例步骤表
    """
    step_type = (
        (0, '执行接口'),
        (1, '等待时间'),
        (2, '轮巡接口'),
        (3, '回调列表循环'),
        (4, 'SQL查询'),
        (5, 'SQL执行'),
        (6, 'SQL轮询查询'),
        # (7, 'SQL轮询执行'),
        (8, 'SQL查询列表循环'),
        (9, 'SQL执行列表循环'),
    )
    name = models.CharField(max_length=50, verbose_name="步骤名称")
    use_case = models.ForeignKey(UseCases, related_name='use_case', on_delete=models.CASCADE, verbose_name="用例")
    case_interface = models.ForeignKey(Interface, related_name='case_interface', null=True, on_delete=models.CASCADE,
                                       verbose_name="对应接口")
    data_source = models.ForeignKey(DataSource, related_name='step_data_source', null=True, on_delete=models.CASCADE,
                                    verbose_name="执行对应元数据")
    param = models.TextField(verbose_name="消息参数存储", default='', null=True)
    body = models.TextField(verbose_name="消息体存储", default='', null=True)
    sql_script = models.TextField(verbose_name="sql脚本", default='', null=True, blank=True)
    type = models.IntegerField(choices=step_type, null=False, verbose_name="用例类型")
    sort = models.IntegerField(null=False, verbose_name="排序")
    status = models.BooleanField(default=1, verbose_name="步骤状态")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="步骤信息简介")
    wrap_count = models.IntegerField(null=True, verbose_name="轮询次数")
    polling_interval = models.IntegerField(null=True, verbose_name="轮询间隔")
    loop_parameter = models.TextField(default="", null=True, blank=True, verbose_name="循环参数")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        verbose_name = '用例步骤管理'
        verbose_name_plural = '用例步骤管理'

    def __str__(self):
        return self.case_interface


class StepCallBackParams(models.Model):
    type = (
        (0, '字符串'),
        (1, '列表'),
        # (2, '列表长度'),
        # (3, '对象'),
    )
    step = models.ForeignKey(CaseSteps, related_name='stepCallBack', on_delete=models.CASCADE,
                             verbose_name="用例步骤", default='')
    name = models.CharField(max_length=50, verbose_name="参数名")
    param_name = models.CharField(max_length=50, verbose_name="参数调用名")
    json_path = models.CharField(max_length=100, verbose_name="json路径")
    type = models.IntegerField(choices=type, null=False, verbose_name="取值类型", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class StepForwardAfterOperation(models.Model):
    type_choice = (
        (0, '参数变更'),
    )
    mode_choice = (
        (0, '步骤前置操作'),
        (1, '步骤后置操作'),
    )
    step = models.ForeignKey(CaseSteps, related_name='stepForwardAfterOperation', on_delete=models.CASCADE,
                             verbose_name="用例步骤", default='')
    name = models.CharField(max_length=50, verbose_name="操作名")
    param_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="参数名")
    param_value = models.CharField(max_length=200, null=True, blank=True, verbose_name="变更值")
    operation_type = models.IntegerField(choices=type_choice, null=False, verbose_name="操作类型", default=0)
    mode = models.IntegerField(choices=mode_choice, null=False, verbose_name="前置/后置", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class StepCircularKey(models.Model):
    """
    步骤循环键
    """
    name = models.CharField(max_length=50, verbose_name="名称")
    case_step = models.ForeignKey(CaseSteps, related_name='step_circular_key', on_delete=models.CASCADE,
                                  verbose_name="步骤")
    key_name = models.CharField(max_length=50, verbose_name="替换值名")
    key = models.CharField(max_length=50, verbose_name="对象取值键")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '步骤循环键管理'
        verbose_name_plural = '步骤循环键管理'

    def __str__(self):
        return self.name


class CaseStepPoll(models.Model):
    """
    步骤轮巡表
    """
    type_from = (
        (0, '消息体校验'),
        (1, '返回码校验'),
        (2, '数据库校验'),
    )
    assert_mode = (
        (0, '包含'),
        (1, '不包含'),
        (2, '等于'),
        (3, '不等于'),
        (4, '大于'),
        (5, '小于'),
        (6, '大等于'),
        (7, '小等于'),
    )
    case_step = models.ForeignKey(CaseSteps, related_name='case_step_poll', on_delete=models.CASCADE, verbose_name="步骤")
    type_from = models.IntegerField(choices=type_from, null=False, verbose_name="取值类型")
    value_statement = models.CharField(max_length=500, verbose_name="取值语法", null=True)
    assert_type = models.IntegerField(choices=assert_mode, null=False, verbose_name="判断类型")
    verify_value = models.CharField(max_length=500, verbose_name="校验值")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class CaseAssert(models.Model):
    """
    步骤断言表
    """
    type_from = (
        (0, '消息体校验'),
        (1, '返回码校验'),
        (2, '数据库校验'),
    )
    assert_mode = (
        (0, '包含'),
        (1, '不包含'),
        (2, '等于'),
        (3, '不等于'),
        (4, '大于'),
        (5, '小于'),
        (6, '大等于'),
        (7, '小等于'),
    )
    name = models.CharField(max_length=50, verbose_name="断言名称")
    case_step = models.ForeignKey(CaseSteps, related_name='case_step', on_delete=models.CASCADE, verbose_name="步骤")
    type_from = models.IntegerField(choices=type_from, null=False, verbose_name="取值类型")
    value_statement = models.CharField(max_length=500, verbose_name="取值语法", null=True)
    assert_type = models.IntegerField(choices=assert_mode, null=False, verbose_name="断言类型")
    verify_value = models.CharField(max_length=500, verbose_name="校验值")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class TaskLog(models.Model):
    mode_type = (
        (0, '手动执行'),
        (1, '调度执行'),
        (2, 'CI/CD触发'),
    )
    execute_types = (
        (0, '执行用例'),
        (1, '执行用例集'),
    )
    status_type = (
        (0, '执行失败'),
        (1, '执行完成'),
        (2, '正在执行'),
    )
    job_id = models.CharField(max_length=50, verbose_name="任务job_id", null=True)
    name = models.CharField(max_length=50, verbose_name="任务名称")
    executor = models.CharField(max_length=50, verbose_name="执行者", default='')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间", null=True)
    execute_status = models.IntegerField(choices=status_type, null=False, verbose_name="执行状态")
    mode = models.IntegerField(choices=mode_type, null=False, verbose_name="执行方式", default=0)
    execute_type = models.IntegerField(choices=execute_types, null=False, verbose_name="执行类型", default=0)
    success_count = models.IntegerField(verbose_name="用例成功数")
    failed_count = models.IntegerField(verbose_name="用例失败数")
    spend_time = models.IntegerField(verbose_name="执行时间", null=True)
    execute_date = models.DateField(auto_now_add=True, verbose_name="执行日期")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    tags = models.TextField(verbose_name="任务标签", default='手动执行')
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class CaseLog(models.Model):
    """
    用例日志表
    """
    status_type = (
        (0, '执行失败'),
        (1, '执行成功'),
        (2, '正在执行'),
    )
    use_case = models.ForeignKey(UseCases, related_name='execute_use_case', on_delete=models.CASCADE, verbose_name="用例")
    task_log = models.ForeignKey(TaskLog, related_name='task_log', on_delete=models.CASCADE, verbose_name="任务",
                                 default='', null=True)
    global_parameter = models.TextField(verbose_name="全局参数存储", default='')
    callback_parameter = models.TextField(verbose_name="回调参数存储", default='')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间", null=True)
    execute_status = models.IntegerField(choices=status_type, null=False, verbose_name="执行状态")
    success_count = models.IntegerField(verbose_name="步骤成功数")
    failed_count = models.IntegerField(verbose_name="步骤失败数")
    spend_time = models.IntegerField(verbose_name="执行时间", null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    execute_date = models.DateField(auto_now_add=True, verbose_name="执行日期")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class CaseStepLog(models.Model):
    """
    用例步骤日志表
    """
    status_type = (
        (0, '执行失败'),
        (1, '执行成功'),
        (2, '未执行'),
    )
    case_log = models.ForeignKey(CaseLog, related_name='case_log', on_delete=models.CASCADE, verbose_name="用例日志")
    case_step = models.ForeignKey(CaseSteps, related_name='case_steps', on_delete=models.CASCADE, verbose_name="用例步骤",
                                  null=True)
    method = models.CharField(max_length=50, null=True)
    request_url = models.CharField(max_length=800, default='', null=True)
    param = models.TextField(verbose_name="测试消息参数存储", default='')
    body = models.TextField(verbose_name="测试消息体存储", default='')
    sql_script = models.TextField(verbose_name="sql脚本", default='', null=True, blank=True)
    step_body = models.TextField(verbose_name="返回消息体存储", default='')
    query_field = models.TextField(verbose_name="查询字段存储", default='')
    assert_result = models.TextField(verbose_name="断言结果存储", default='')
    poll_assert_result = models.TextField(verbose_name="断言结果存储", default='')
    execute_status = models.IntegerField(choices=status_type, null=True, verbose_name="执行状态")
    spend_time = models.IntegerField(verbose_name="执行时间", null=True, default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")


class UdfLog(models.Model):
    """
    Udf日志管理
    """
    udf = models.ForeignKey(Udf, related_name='udf_log', on_delete=models.CASCADE, verbose_name="所属函数", null=True,
                            blank=True)
    case_log = models.ForeignKey(CaseLog, related_name='case_udf_log', on_delete=models.CASCADE,
                                 verbose_name="用例日志")
    original_function_str = models.CharField(default="", max_length=200, null=False, verbose_name="原始调用函数字符串")
    udf_name = models.CharField(max_length=50, null=False, verbose_name="udf名称")
    udf_zh_name = models.CharField(max_length=50, null=False, verbose_name="udf中文名称")
    args = models.CharField(max_length=500, null=False, verbose_name="传入参数")
    execution_status = models.BooleanField(default=1, verbose_name="执行是否正常")
    remark = models.TextField(default="", null=True, blank=True, verbose_name="备注")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = 'Udf日志管理'
        verbose_name_plural = 'Udf日志管理'

    def __str__(self):
        return self.udf_name
