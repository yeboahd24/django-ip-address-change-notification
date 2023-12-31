from celery import Celery
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_celery_email.settings")
app = Celery("django_celery_email")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.task(bind=True, ignore_result=True)
