# config/celery.py
import os

from celery import Celery

# Устанавливаем переменную окружения по умолчанию для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Читаем конфигурацию из settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
