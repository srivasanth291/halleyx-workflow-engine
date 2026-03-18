import uuid
from django.db import models
from apps.workflows.models import Workflow

class Step(models.Model):
    TYPE_CHOICES = (
        ('task', 'Task'),
        ('approval', 'Approval'),
        ('notification', 'Notification'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    name = models.CharField(max_length=255)
    step_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    order = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.name} ({self.step_type})'
