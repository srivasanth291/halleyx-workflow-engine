"""
Execution model.
"""
import uuid
from django.db import models


class Execution(models.Model):
    """
    Tracks a single run of a workflow.
    Contains full audit log as JSON, supports loop prevention via
    iteration_count vs max_iterations.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        'workflows.Workflow',
        on_delete=models.CASCADE,
        related_name='executions',
    )
    workflow_version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    data = models.JSONField(default=dict)
    logs = models.JSONField(default=list)
    current_step_id = models.UUIDField(null=True, blank=True)
    retries = models.PositiveIntegerField(default=0)
    triggered_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_executions',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Loop prevention
    max_iterations = models.PositiveIntegerField(default=10)
    iteration_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Execution'
        verbose_name_plural = 'Executions'

    def __str__(self):
        return f'Execution {self.id} ({self.status})'
