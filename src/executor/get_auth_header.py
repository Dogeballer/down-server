from redis import ConnectionPool, StrictRedis

from down.settings import redis_url
from executor.script_execution import udf_execute_setup, udf_execute
from system_settings.models import Udf
import django.utils.timezone as timezone


class GetAuthHeader(object):
    def __init__(self, authentication_environment):
        pool = ConnectionPool.from_url(redis_url)
        self.redis = StrictRedis(connection_pool=pool)
        self.authentication_environment = authentication_environment
        self.header_get_status = True

    def header_get(self):
        code = self.authentication_environment.code
        is_redis = self.authentication_environment.is_redis
        func_call = self.authentication_environment.func_call
        is_func_call = self.authentication_environment.is_func_call
        timeout = self.authentication_environment.timeout
        if is_redis:
            # 判断是否存在有效redis键
            if self.redis.exists(code):
                # redis缓存获取
                header_str = self.redis.get(code)
            else:
                # 如果设置为函数调用
                if is_func_call:
                    header_str = self.func_execute(func_call)
                else:
                    # 否者直接从库中取值
                    header_str = self.authentication_environment.header_value
                    if not header_str:
                        header_str = "{}"
                # 如果取值结果不为空，则保存在redis内存中
                if header_str != "{}" and header_str:
                    self.redis.set(name=code, value=header_str, ex=timeout * 60)
                    self.authentication_environment.last_time = timezone.now()
                    self.authentication_environment.save()
        else:
            # 不为redis取值，则本地数据库取值，先判断是否超时
            time_difference = timezone.now() - self.authentication_environment.last_time
            # 超时情况重新获取值
            if time_difference.total_seconds() >= 60 * timeout and not self.authentication_environment.header_value:
                if is_func_call:
                    header_str = self.func_execute(func_call)
                    self.authentication_environment.last_time = timezone.now()
                    self.authentication_environment.save()
                else:
                    header_str = self.authentication_environment.header_value
                    if not header_str:
                        header_str = "{}"
            # 未超时则直接本地取值
            else:
                header_str = self.authentication_environment.header_value
                if not header_str:
                    header_str = "{}"
                self.authentication_environment.last_time = timezone.now()
                self.authentication_environment.save()
            self.authentication_environment.header_value = header_str
            self.authentication_environment.save()
        return header_str, self.header_get_status

    # 请求头函数获取
    def func_execute(self, func_call):
        func_name, func_kwargs, execution_status, msg = udf_execute_setup(func_call)
        if execution_status:
            result, status, error_msg = udf_execute(func_name, func_kwargs)
            if status:
                remark = '执行结果为:%s' % str(result)
                self.authentication_environment.remark = remark
                self.authentication_environment.execution_result = True
                self.authentication_environment.error_log = ''
            else:
                # 函数执行异常处理
                remark = '报错信息为:%s' % error_msg
                self.authentication_environment.error_log = remark
                self.authentication_environment.remark = "函数执行异常"
                self.authentication_environment.execution_result = False
                self.header_get_status = False
            header_str = result
            self.authentication_environment.execution_result = status
            self.authentication_environment.save()
        else:
            # 函数表达式异常处理
            self.authentication_environment.execution_result = False
            self.authentication_environment.error_log = msg
            self.authentication_environment.remark = "函数表达式异常"
            self.authentication_environment.save()
            header_str = "{}"
            self.header_get_status = False
        return header_str
