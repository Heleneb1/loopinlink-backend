import uuid

from django.conf import settings
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

class TermsAcceptance(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="terms_acceptances",
    )
    version = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "version"], name="unique_terms_per_user_version")
        ]

    def __str__(self):
        return f"{self.user_id} a accepté {self.version} le {self.accepted_at:%Y-%m-%d}"
