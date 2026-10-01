from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Design, DesignImage


@receiver(post_delete, sender=Design)
def delete_design_preview_file(sender, instance, **kwargs):
    if instance.preview_image:
        instance.preview_image.delete(save=False)


@receiver(post_delete, sender=DesignImage)
def delete_design_image_files(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
    if instance.preview:
        instance.preview.delete(save=False)
