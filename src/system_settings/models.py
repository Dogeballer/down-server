from django.db import models


# Create your models here.


class DataSource(models.Model):
    """
    源数据管理
    """
    database_type_choice = (
        (0, 'Pg'),
        (1, 'SqlSever'),
        (2, 'Oracle'),
        (3, 'Mysql'),
    )

    name = models.CharField(max_length=50, null=False, verbose_name="元数据名")
    database_type = models.IntegerField(choices=database_type_choice, null=False, verbose_name="数据库类型",
                                        default=0)
    host = models.CharField(max_length=50, null=False, verbose_name="host", default='')
    port = models.IntegerField(null=False, verbose_name="port", default=0)
    username = models.CharField(max_length=50, null=False, verbose_name="username", default='')
    password = models.CharField(max_length=50, null=False, verbose_name="password", default='')
    database = models.CharField(max_length=50, null=False, verbose_name="database", default='')
    sid = models.CharField(max_length=50, null=True, blank=True, verbose_name="sid", default='')
    describe = models.TextField(default="", null=True, blank=True, verbose_name="元数据描述")
    status = models.BooleanField(default=1, verbose_name="状态")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '源数据管理'
        verbose_name_plural = '源数据管理'

    def __str__(self):
        return self.name


class Udf(models.Model):
    """
    自定义函数管理
    """
    name = models.CharField(max_length=50, null=False, verbose_name="函数名")
    zh_name = models.CharField(max_length=50, null=False, verbose_name="函数中文名")
    user = models.CharField(max_length=50, verbose_name="编辑人员")
    source_code = models.TextField(default="", null=True, blank=True, verbose_name="源码")
    returns_number_of = models.IntegerField(default=1, null=True, blank=True, verbose_name="返回值个数")
    expression = models.CharField(max_length=200, null=True, blank=True, verbose_name="函数表达式示例")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="函数信息简介")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    status = models.BooleanField(default=1, verbose_name="状态")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '自定义函数管理'
        verbose_name_plural = '自定义函数管理'

    def __str__(self):
        return self.name


class UdfArgs(models.Model):
    """
    UDF函数
    """
    args_type_choice = (
        (0, 'int'),
        (1, 'str'),
        (2, 'list'),
        (3, 'dict'),
        (4, 'boolean'),
        (5, 'float'),
    )

    udf = models.ForeignKey(Udf, related_name='udf_args', on_delete=models.CASCADE, verbose_name="所属函数")
    name = models.CharField(max_length=50, null=False, verbose_name="参数名")
    zh_name = models.CharField(max_length=50, null=False, verbose_name="参数中文名")
    args_type = models.IntegerField(choices=args_type_choice, null=False, verbose_name="参数类型", default=0)
    describe = models.TextField(default="", null=True, blank=True, verbose_name="参数简介")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = 'UDF参数管理'
        verbose_name_plural = 'UDF参数管理'

    def __str__(self):
        return self.name


class MQTTClient(models.Model):
    """
    mqtt客户端管理
    """
    name = models.CharField(max_length=50, null=False, verbose_name="客户端名称")
    broker = models.CharField(max_length=50, null=False, verbose_name="broker", default='')
    port = models.IntegerField(null=False, verbose_name="port", default=0)
    username = models.CharField(max_length=50, null=False, verbose_name="username", default='')
    password = models.CharField(max_length=50, null=False, blank=True, verbose_name="password", default='')
    describe = models.TextField(default="", null=True, blank=True, verbose_name="客户端备注")
    status = models.BooleanField(default=1, verbose_name="状态")
    delete = models.BooleanField(verbose_name="是否删除", default=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = 'mqtt客户端管理'
        verbose_name_plural = 'mqtt客户端管理'

    def __str__(self):
        return self.name + self.broker
