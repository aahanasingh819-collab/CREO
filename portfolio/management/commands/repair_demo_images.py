from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from creators.models import CreatorProfile
from portfolio.models import PortfolioItem


class Command(BaseCommand):
    help = "Restore missing demo portfolio images"

    def handle(self, *args, **options):
        repaired = 0

        for i in range(14):
            username = f"demo_creator_{i + 1:02}"

            profile = CreatorProfile.objects.filter(
                user__username=username,
                is_demo=True
            ).first()

            if not profile:
                continue

            items = list(
                PortfolioItem.objects.filter(
                    creator=profile,
                    is_demo=True
                ).order_by("pk")
            )

            for j, item in enumerate(items[:2]):
                if item.image and item.image.storage.exists(item.image.name):
                    continue

                asset = (
                    Path(settings.BASE_DIR)
                    / "static"
                    / "img"
                    / f"demo-{i:02}-{j}.jpg"
                )

                if not asset.exists():
                    self.stdout.write(f"Missing source: {asset}")
                    continue

                item.image.save(
                    asset.name,
                    ContentFile(asset.read_bytes()),
                    save=True
                )

                repaired += 1

        self.stdout.write(
            self.style.SUCCESS(f"Restored {repaired} images.")
        )