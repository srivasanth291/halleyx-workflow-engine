import uuid
from django.db import models
from apps.steps.models import Step

class Rule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(
        Step,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    condition = models.TextField()
    next_step_id = models.UUIDField(null=True, blank=True)
    priority = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority']

    def __str__(self):
        return f'Rule {self.priority} for {self.step}'
