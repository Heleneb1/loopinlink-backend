from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from designs.models import DesignImage


class Command(BaseCommand):
    help = "Supprime les DesignImage orphelines (design=None) créées il y a plus d'1 heure."

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(hours=1)
        orphans = DesignImage.objects.filter(design__isnull=True, updated_at__lt=threshold)
        count = orphans.count()

        for img in orphans:
            img.delete()  # déclenche le signal post_delete -> supprime aussi le fichier physique

        self.stdout.write(self.style.SUCCESS(f"{count} DesignImage orpheline(s) supprimée(s)."))
