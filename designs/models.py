import uuid

from django.contrib.auth.models import User
from django.db import models

from common.utils import rename_image, validate_image_extension, validate_image_size


class Design(models.Model):
    TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('feature', 'Feature'),
        ('carousel', 'Carousel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    data = models.JSONField()
    is_template = models.BooleanField(default=False)
    preview_image = models.ImageField(
        upload_to=rename_image,
        validators=[validate_image_size, validate_image_extension],
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['is_template']),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"


class DesignImage(models.Model):
    TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('feature', 'Feature'),
        ('carousel', 'Carousel'),
    ]

    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    element_id = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)

    file = models.ImageField(
        upload_to=rename_image,
        validators=[validate_image_size, validate_image_extension]
    )
    preview = models.ImageField(
        upload_to=rename_image,
        validators=[validate_image_size, validate_image_extension],
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image {self.element_id} pour {self.design.name}"
