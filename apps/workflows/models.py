import uuid
from django.db import models

class Workflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'authentication.Company',
        on_delete=models.CASCADE,
        related_name='workflows',
    )
    name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    input_schema = models.JSONField(default=dict)
    start_step_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} v{self.version}'
