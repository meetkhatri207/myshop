from django.db import models
from django.contrib.auth.models import User


class ImportHistory(models.Model):

    STATUS_CHOICES = (

        ('processing', 'Processing'),

        ('completed', 'Completed'),

        ('failed', 'Failed'),

    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    file_name = models.CharField(
        max_length=255
    )

    total_rows = models.IntegerField(
        default=0
    )

    success_rows = models.IntegerField(
        default=0
    )

    failed_rows = models.IntegerField(
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )

    error_message = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.file_name} - {self.status}"