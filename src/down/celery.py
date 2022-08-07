import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'down.settings')

app = Celery('down')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# broker setting
# 格式redis://:password@hostname:port/db_number
app.conf.broker_url = 'redis://localhost:6379/0'
# app.conf.broker_url = 'redis://:test123@101.32.191.136:6379/1'
app.conf.broker_transport_options = {'visibility_timeout': 3600}  # 1 hour.
# 时区
app.conf.timezone = "Asia/shanghai"
# 任务超时时间
app.conf.task_time_limit = 2 * 60 * 60
app.conf.task_track_started = True
# 任务执行结果序列化方式
app.conf.result_backend = 'django-db'
# 序列化方式
app.conf.result_serializers = 'json'

# celery队列设置
default_exchange = Exchange('default', type='direct')
consumer_exchange = Exchange('consumer', type='direct')
app.conf.task_queues = (
    Queue('default', default_exchange, routing_key='default'),
    Queue("consumer", consumer_exchange, routing_key="consumer")
)
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# 队列启动命令
# celery -A down worker -P eventlet -c 2 -l info -Q default
