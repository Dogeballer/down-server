from django.db import models


# Create your models here.


class Projects(models.Model):
    """
    项目表
    """
    name = models.CharField(max_length=50, verbose_name="项目名称", unique=True)
    describe = models.TextField(default="", null=True, blank=True, verbose_name="项目简介")
    status = models.BooleanField(default=1, verbose_name="项目状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '项目管理'
        verbose_name_plural = '项目管理'

    def __str__(self):
        return self.name


class Modules(models.Model):
    """
    模块表
    """
    project = models.ForeignKey(Projects, related_name='modules_project', on_delete=models.CASCADE, verbose_name="所属项目")
    name = models.CharField(max_length=50, null=False, verbose_name="模块名称", unique=True)
    describe = models.TextField(default="", null=True, blank=True, verbose_name="模块简介")
    tester = models.CharField(max_length=200, verbose_name="测试人员")
    developer = models.CharField(max_length=100, blank=True, verbose_name="开发人员")
    status = models.BooleanField(default=1, verbose_name="模块状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '模块管理'
        verbose_name_plural = '模块管理'

    def __str__(self):
        return self.name


class AuthenticationEnvironment(models.Model):
    """
    鉴权环境管理
    """
    name = models.CharField(max_length=50, null=False, verbose_name="环境名称", unique=True)
    code = models.CharField(max_length=20, verbose_name="标识码", unique=True)
    is_func_call = models.BooleanField(default=1, verbose_name="是否函数调用")
    func_call = models.CharField(max_length=500, null=True, verbose_name="函数表达式")
    is_redis = models.BooleanField(default=1, verbose_name="是否缓存redis")
    timeout = models.IntegerField(null=True, verbose_name="超时时间")
    header_value = models.TextField(null=True, blank=True, verbose_name="请求头存储")
    execution_result = models.BooleanField(default=0, verbose_name="上次执行是否正常")
    error_log = models.TextField(null=True, blank=True, verbose_name="异常日志")
    status = models.BooleanField(default=1, verbose_name="状态")
    remark = models.TextField(null=True, blank=True, verbose_name="remark")
    last_time = models.DateTimeField(auto_now_add=True, verbose_name="上次执行时间")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '鉴权环境管理'
        verbose_name_plural = '鉴权环境管理'

    def __str__(self):
        return self.name


class Environment(models.Model):
    """
    环境url存储
    """
    # uac_url_list = (
    #     (0, '测试环境'),  # 测试环境
    #     (1, '开发环境'),  # 开发环境
    #     (2, '预生产环境'),  # 预生产环境
    #     (3, 'HMO测试环境'),  # HMO-UAC测试环境
    #     (4, 'HMO开发环境'),  # HMO-UAC开发环境
    # )
    project = models.ForeignKey(Projects, related_name='environment', on_delete=models.CASCADE, verbose_name="所属项目")
    authentication_environment = models.ForeignKey(AuthenticationEnvironment,
                                                   related_name='authentication_environment',
                                                   on_delete=models.CASCADE, verbose_name="鉴权环境")
    name = models.CharField(max_length=50, null=False, verbose_name="环境名称", unique=True)
    url = models.URLField(null=False, verbose_name="url", unique=True, default='')
    # uac_url = models.IntegerField(choices=uac_url_list, null=False, verbose_name="uac地址ip+port", default=0)
    describe = models.TextField(default="", null=True, blank=True, verbose_name="环境描述")
    status = models.BooleanField(default=1, verbose_name="环境状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '环境管理'
        verbose_name_plural = '环境管理'

    def __str__(self):
        return self.name
