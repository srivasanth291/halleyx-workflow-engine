"""
Rule model.
"""
import uuid
from django.db import models


class Rule(models.Model):
    """
    A routing rule for a step.
    Conditions are evaluated in priority order.
    'DEFAULT' condition always matches — used as fallback.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(
        'steps.Step',
        on_delete=models.CASCADE,
        related_name='rules',
    )
    condition = models.TextField()
    next_step_id = models.UUIDField(null=True, blank=True)
    priority = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority']
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'

    def __str__(self):
        return f'Rule P{self.priority}: {self.condition[:80]}'
