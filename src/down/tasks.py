from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True)
def debug_tasker(self):
    # PeriodicTask.objects.create()
    print('Hello Celery, the task id is: ')
    # logger.info('Hello Celery, the task id is: ')
    return f'Hello Celery, the task id is: {self.request.id}'


@shared_task(bind=True)
def debug_task(self, name):
    print(f'Request: {self.request!r}')
    return f'Hello Celery, the task id is: {self.request.id}, {name}'
