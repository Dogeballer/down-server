from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_celery_beat.models import *
from down.celery import app
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

