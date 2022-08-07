import ast
import glob
import importlib
import io
import json
import shutil
import sys
import os
import subprocess
import tempfile
import types
import traceback

# 获取当前环境的python目录
from system_settings.models import Udf, UdfArgs

EXEC = sys.executable

if 'uwsgi' in EXEC:
    EXEC = '/usr/bin/python3'

debug_file_path = os.path.abspath(os.path.dirname(__file__))


class DebugCode(object):

    def __init__(self, code):
        self.__code = code
        self.resp = None
        # 创建一个临时文件
        self.temp = ''

    def run(self):
        """ 写入py文件
        """
        self.temp = tempfile.mkdtemp(prefix='DebugCode', dir=debug_file_path)
        try:
            file_path = os.path.join(self.temp, 'debug_code.py')
            dump_python_file(file_path, self.__code)
            # 创建一个子进程并返回子进程标准输出的输出结果，stderr=subprocess.STDOUT 把错误输出重定向到PIPE对应的标准输出
            self.resp = decode(
                subprocess.check_output([EXEC, file_path], stderr=subprocess.STDOUT, timeout=60))

        except subprocess.CalledProcessError as e:
            self.resp = decode(e.output)

        except subprocess.TimeoutExpired:
            self.resp = 'RunnerTimeOut'

        shutil.rmtree(self.temp)

    def check_function_name(self, func_name):
        file_path = os.path.join(debug_file_path, 'udf_py_file', func_name + '.py')
        dump_python_file(file_path, self.__code)
        sys.path.insert(0, file_path)
        module = importlib.import_module('executor.' + 'udf_py_file.' + func_name)
        # 修复重载bug
        importlib.reload(module)
        sys.path.pop(0)
        func_name_list = []
        # 获取当前源码中所有函数
        for name, item in vars(module).items():
            if is_function((name, item)):
                func_name_list.append(name)
            else:
                pass
        if func_name in func_name_list:
            result = True
        else:
            result = False
            os.remove(file_path)
        return result


def decode(s):
    try:
        return s.decode('utf-8')

    except UnicodeDecodeError:
        return s.decode('gbk')


def dump_python_file(python_file, data):
    """dump python file
    """
    with io.open(python_file, 'w', encoding='utf-8') as stream:
        stream.write(data)


def load_python_module(file_path):
    debugtalk_module = {
        "variables": {},
        "functions": {}
    }

    sys.path.insert(0, file_path)
    module = importlib.import_module("script")
    # 修复重载bug
    importlib.reload(module)
    sys.path.pop(0)

    for name, item in vars(module).items():
        if is_function((name, item)):
            debugtalk_module["functions"][name] = item
        elif is_variable((name, item)):
            if isinstance(item, tuple):
                continue
            debugtalk_module["variables"][name] = item
        else:
            pass

    func = getattr(module, 'gainerTest')

    arg = (1, 0, 2)

    result = func(*arg)

    return result


def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)


def is_variable(tup):
    """ Takes (name, object) tuple, returns True if it is a variable.
    """
    name, item = tup
    if callable(item):
        # function or class
        return False

    if isinstance(item, types.ModuleType):
        # imported module
        return False

    if name.startswith("_"):
        # private property
        return False

    return True


def udf_execute_setup(original_function_str):
    # 用例配置初始字符串提取函数和参数并判断是否符合参数条件
    # 示例为---"${funcName(str_args="string"||int_args=2||list_args=[1,2,3]||dict_args={"abc":"abc"}||boolean_args=True||float_args=0.01)}"
    func_name = ''
    args = ''
    func_name_slice_start = original_function_str.find('${')
    func_name_slice_end = original_function_str.find('(')
    args_slice_start = original_function_str.find('(')
    args_slice_end = original_function_str.rfind(')}')
    if func_name_slice_start == -1 or func_name_slice_end == -1 or args_slice_start == -1 or args_slice_end == -1:
        execution_status = False
        msg = "传入函数书写格式异常"
        return func_name, args, execution_status, msg
    func_name = original_function_str[func_name_slice_start + 2: func_name_slice_end]
    try:
        udf = Udf.objects.get(name=func_name)
    except Udf.DoesNotExist:
        execution_status = False
        msg = "未找到对应udf函数，请检查函数书写格式"
        return func_name, args, execution_status, msg
    args_str = original_function_str[args_slice_start + 1: args_slice_end]
    args_list = args_str.split('||')
    fun_args = UdfArgs.objects.filter(udf=udf)
    if len(args_list) != fun_args.count():
        execution_status = False
        msg = "传入参数校验异常，请检查函数传参"
        return func_name, args, execution_status, msg
    func_kwargs = {}
    try:
        for args in args_list:
            args_split_result = args.split('=')
            args_name = args_split_result[0]
            args_value = args_split_result[1]
            args_type = UdfArgs.objects.get(udf=udf, name=args_name).args_type
            if args_type == 0:  # int
                args_value = int(args_value)
            elif args_type == 1:  # str
                args_value = args_value.replace("'", '').replace('"', '')
            elif args_type == 2:  # list
                args_value = json.loads(args_value)
            elif args_type == 3:  # dict
                args_value = ast.literal_eval(args_value)
            elif args_type == 4:
                if args_value == "True":
                    args_value = True
                elif args_value == "False":
                    args_value = False
                else:
                    args_value = False
            elif args_type == 5:  # float
                args_value = float(args_value)
            func_kwargs[args_name] = args_value
    except Exception as e:
        execution_status = False
        msg = "传入参数转换异常，具体错误为-'%s'" % e
        return func_name, args, execution_status, msg
    execution_status = True
    msg = "函数转换成功"
    return func_name, func_kwargs, execution_status, msg


def udf_execute(func_name, kwargs):
    udf = Udf.objects.get(name=func_name)
    file_path = os.path.join(debug_file_path, 'udf_py_file', func_name + '.py')
    sys.path.insert(0, file_path)
    dump_python_file(file_path, udf.source_code)
    module = importlib.import_module('executor.' + 'udf_py_file.' + func_name)
    # 修复重载bug
    importlib.reload(module)
    sys.path.pop(0)
    func = getattr(module, func_name)
    result = ''
    error_msg = ''
    status = True
    try:
        result = func(**kwargs)
        return result, status, error_msg
    except Exception as e:
        status = False
        error_msg = str(traceback.format_exc())
        return result, status, error_msg


if __name__ == '__main__':
    # debug = DebugCode(['1'])
    # debug.run()
    # print(debug.resp)
    # print(udf_execute('gainerTest', {'test': 1}))
    print(udf_execute('args', {'test': 1}))
    # module_info = import_modules('udf_py_file/**.py')
    # print(module_info)
