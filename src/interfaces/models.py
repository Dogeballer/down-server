from django.db import models
from projects.models import Projects


# Create your models here.
class InterfaceClass(models.Model):
    """
    接口分类表
    """
    project = models.ForeignKey(Projects, related_name='project', on_delete=models.CASCADE, verbose_name="所属项目")
    class_name = models.CharField(max_length=200, verbose_name="接口分类名称")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="接口分类简介")
    status = models.BooleanField(default=1, verbose_name="分类状态")
    delete = models.BooleanField(default=False, verbose_name="是否删除")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")


class Interface(models.Model):
    """
    接口表
    """
    method_type = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
        ('OPTIONS', 'OPTIONS'),
    )
    body_type_choice = (
        (0, 'none'),
        (1, 'form-data'),
        (2, 'x-www-form-urlencoded'),
        (3, 'raw'),
        (4, 'binary'),
        (5, 'GraphQL'),
    )
    name = models.CharField(max_length=200, verbose_name="接口名称")
    method = models.CharField(max_length=50, choices=method_type, null=False)
    path = models.CharField(max_length=200, verbose_name="接口路径", null=False)
    body_type = models.IntegerField(choices=body_type_choice, null=True, default=3)
    version = models.CharField(max_length=50, verbose_name="版本号", null=True)
    interface_class = models.ForeignKey(InterfaceClass, related_name='interface_class', on_delete=models.CASCADE,
                                        verbose_name="所属分类", default=None)
    status = models.BooleanField(default=1, verbose_name="接口状态")
    describe = models.TextField(default="", null=True, blank=True, verbose_name="接口信息简介")
    tags = models.CharField(max_length=200, verbose_name="接口标签", default="")
    body_example_json = models.TextField(verbose_name="json消息体示例", default='')

    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '接口管理'
        verbose_name_plural = '接口管理'

    def __str__(self):
        return self.name


class InterfaceParam(models.Model):
    """
    接口参数表
    """
    param_in_type = (
        ('path', 'path'),
        ('query', 'query'),
        ('header', 'header'),
    )
    name = models.CharField(max_length=200, verbose_name="参数名")
    describe = models.CharField(max_length=200, verbose_name="参数描述", null=True)
    required = models.BooleanField(default=0, verbose_name="是否必填")
    example = models.CharField(max_length=200, verbose_name="示例值", null=True)
    param_in = models.CharField(max_length=50, choices=param_in_type, null=False, default='query')
    type = models.CharField(max_length=50, verbose_name="参数位置")
    interface = models.ForeignKey(Interface, related_name='interface', on_delete=models.CASCADE, verbose_name="所属接口",
                                  null=True)
    version = models.CharField(max_length=50, verbose_name="版本号", null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '接口参数管理'
        verbose_name_plural = '接口参数管理'

    def __str__(self):
        return self.name


class InterfaceBody(models.Model):
    param_type = (
        ('object', 'object'),
        ('array', 'array'),
        ('string', 'string'),
        ('integer', 'integer'),
        ('boolean', 'boolean'),
        ('number', 'number'),
        ('null', 'null'),
        ('any', 'any'),
    )
    name = models.CharField(max_length=200, verbose_name="参数名")
    describe = models.CharField(max_length=200, verbose_name="参数描述")
    belong_interface = models.ForeignKey(Interface, related_name='belong_interface', on_delete=models.CASCADE,
                                         verbose_name="所属接口", default='')
    required = models.BooleanField(default=0, verbose_name="是否必填")
    example = models.CharField(max_length=200, verbose_name="示例值")
    node = models.BooleanField(default=0, verbose_name="是否节点")
    circulation = models.BooleanField(default=0, verbose_name="是否循环")
    type = models.CharField(max_length=200, choices=param_type, null=False)
    parent = models.IntegerField(verbose_name="上级节点id")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")

    class Meta:
        verbose_name = '接口参数体管理'
        verbose_name_plural = '接口参数体管理'

    def __str__(self):
        return self.name


class InterfaceTest(models.Model):
    test_interface = models.ForeignKey(Interface, related_name='test_interface', on_delete=models.CASCADE,
                                       verbose_name="测试接口", default='')
    interface_param = models.TextField(verbose_name="消息参数存储", default='')
    interface_body = models.TextField(verbose_name="消息体存储", default='')

    class Meta:
        verbose_name = '接口测试参数管理'
        verbose_name_plural = '接口测试参数管理'

    def __str__(self):
        return self.test_interface


class InterfaceCallBackParams(models.Model):
    type = (
        (0, '字符串'),
        (1, '列表'),
        # (2, '列表长度'),
        # (3, '对象'),
    )
    return_interface = models.ForeignKey(Interface, related_name='return_interface', on_delete=models.CASCADE,
                                         verbose_name="返回接口", default='')
    name = models.CharField(max_length=50, verbose_name="参数名")
    param_name = models.CharField(max_length=50, verbose_name="参数调用名")
    json_path = models.CharField(max_length=100, verbose_name="json路径")
    type = models.IntegerField(choices=type, null=False, verbose_name="取值类型", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
    delete = models.BooleanField(verbose_name="是否删除", default=False)


class UacTokenRecord(models.Model):
    uac_url = models.IntegerField(null=False, verbose_name="uac地址", default=0)
    token = models.CharField(max_length=100, default="", verbose_name="token值存储", blank=True, null=True)
    token_update_time = models.DateTimeField(auto_now_add=True, verbose_name="token更新时间")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    update_time = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name="修改时间")
