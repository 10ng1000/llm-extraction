import os
import sys
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
app = Celery('mysite', broker='redis://localhost:6379', backend='redis://localhost:6379')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()