from django.db import models

# Create your models here.
from django_celery_beat.models import PeriodicTask, CrontabSchedule

from projects.models import *
from usecases.models import UseCases


class TestSuiteClass(models.Model):
    """
    测试套件分类表
    """
    name = models.CharField(max_length=50, verbose_name="测试套件分类名称")
    code = models.TextField(default="", null=True, blank=True, verbose_name="编码")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="测试套件分类简介")
    parent = models.IntegerField(verbose_name="上级节点id")
    status = models.BooleanField(default=1, verbose_name="状态")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '测试套件分类管理'
        verbose_name_plural = '测试套件分类管理'

    def __str__(self):
        return self.name


class TestSuite(models.Model):
    mode_options = (
        (0, '手动执行'),
        (1, '调度执行'),
    )
    type_options = (
        (0, '按项目'),
        (1, '按模块'),
        (2, '自定义'),
    )
    execute_frequency_options = (
        (0, '每日执行'),
        (1, '每周一次'),
    )
    name = models.CharField(max_length=50, verbose_name="测试套件分类名称")
    suite_class = models.ForeignKey(TestSuiteClass, related_name='suite_class', on_delete=models.CASCADE,
                                    verbose_name="套件分类", null=False)
    environment = models.ForeignKey(Environment, related_name='environment', on_delete=models.CASCADE,
                                    verbose_name="执行环境", null=False)
    code = models.TextField(default="", null=True, blank=True, verbose_name="编码")
    mode = models.IntegerField(choices=mode_options, null=False, verbose_name="执行方式")
    # type = models.IntegerField(choices=type_options, null=False, verbose_name="套件类型")
    # type_value = models.IntegerField(null=True, verbose_name="类型值")
    execute_frequency = models.IntegerField(default=0, choices=execute_frequency_options, null=False,
                                            verbose_name="执行频率")
    timing = models.TimeField(verbose_name="执行时间", null=True)
    thread_count = models.IntegerField(default=1, null=True, verbose_name="线程数")
    global_params = models.TextField(verbose_name="套件全局参数存储", default='[]', null=True)
    public_headers = models.TextField(verbose_name="套件公共header存储", default='[]', null=True)
    status = models.BooleanField(default=1, verbose_name="状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    periodic_task = models.ForeignKey(PeriodicTask, related_name='periodic_tasks', on_delete=models.CASCADE,
                                      verbose_name="关联调度任务", null=True, blank=True)
    precondition_case = models.ForeignKey(UseCases, related_name='precondition_case', on_delete=models.CASCADE,
                                          verbose_name="前置用例", null=True)
    crontab_schedule = models.ForeignKey(CrontabSchedule, related_name='crontab_schedule', on_delete=models.CASCADE,
                                         verbose_name="关联crontab", null=True, blank=True)
    suite_log_case = models.ForeignKey(UseCases, related_name='suite_log_case', on_delete=models.CASCADE,
                                       verbose_name="套件日志用例", null=True, blank=True)


class TestSuiteCases(models.Model):
    case = models.ForeignKey(UseCases, related_name='case', on_delete=models.CASCADE,
                             verbose_name="关联用例", null=False)
    test_suite = models.ForeignKey(TestSuite, related_name='suite', on_delete=models.CASCADE,
                                   verbose_name="用例套件", null=True)
    environment = models.ForeignKey(Environment, related_name='environment_id', on_delete=models.CASCADE,
                                    verbose_name="独立执行环境", null=True)
    global_params = models.TextField(verbose_name="用例全局参数存储", default='', null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
