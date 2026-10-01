import uuid

from django.contrib.auth.models import User
from django.db import models

from common.utils import rename_image, validate_image_extension, validate_image_size


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    avatar = models.ImageField(
        upload_to=rename_image,
        validators=[validate_image_size, validate_image_extension],
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username
