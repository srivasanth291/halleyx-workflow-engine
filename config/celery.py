"""
Celery application configuration for Halleyx Workflow Backend.
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('halleyx_workflow')

# Use Django settings for Celery configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task that prints the request.."""
    print(f'Request: {self.request!r}')
