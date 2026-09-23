from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from website.models import GalleryImage

SOURCE_DIR = Path(settings.BASE_DIR) / "static" / "img" / "gallery"

CATEGORY_LABELS = dict(GalleryImage.CATEGORY_CHOICES)

GALLERY_FILES = [
    ("fachadas-1.jpg", "fachadas", "Fachadas y Exteriores"),
    ("fachadas-2.jpg", "fachadas", "Fachadas y Exteriores"),
    ("fachadas-3.jpg", "fachadas", "Fachadas y Exteriores"),
    ("salas-tv-1.jpg", "salas-tv", "Salas de TV"),
    ("salas-tv-2.jpg", "salas-tv", "Salas de TV"),
    ("quinchos-1.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("quinchos-2.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("estructuras-1.jpg", "estructuras", "Estructuras y Carpintería"),
    ("estructuras-2.jpg", "estructuras", "Estructuras y Carpintería"),
    ("estructuras-3.jpg", "estructuras", "Estructuras y Carpintería"),
    ("pavimentos-1.jpg", "pavimentos", "Pavimentos"),
    ("pavimentos-2.jpg", "pavimentos", "Pavimentos"),
]

BUILD_PANEL_FILES = [
    ("fachadas-1.jpg", "fachadas", "build_project", "Un proyecto nuevo"),
    ("quinchos-1.jpg", "quinchos", "build_remodel", "Una remodelación"),
    ("pavimentos-1.jpg", "pavimentos", "build_quote", "Una cotización"),
]


class Command(BaseCommand):
    help = "One-off import of the curated static gallery photos into the GalleryImage table."

    def handle(self, *args, **options):
        if GalleryImage.objects.exists():
            self.stdout.write("GalleryImage table is not empty, skipping import.")
            return

        order = 0
        for filename, category, label in GALLERY_FILES:
            path = SOURCE_DIR / filename
            if not path.exists():
                self.stderr.write(f"Missing {path}, skipping")
                continue
            with open(path, "rb") as f:
                obj = GalleryImage(
                    title=label,
                    category=category,
                    placement="gallery",
                    is_active=True,
                    order=order,
                )
                obj.image.save(filename, File(f), save=True)
            order += 1
            self.stdout.write(f"Imported {filename} -> gallery/{category}")

        for filename, category, placement, label in BUILD_PANEL_FILES:
            path = SOURCE_DIR / filename
            if not path.exists():
                self.stderr.write(f"Missing {path}, skipping")
                continue
            with open(path, "rb") as f:
                obj = GalleryImage(
                    title=label,
                    category=category,
                    placement=placement,
                    is_active=True,
                    order=0,
                )
                obj.image.save(f"panel-{filename}", File(f), save=True)
            self.stdout.write(f"Imported {filename} -> {placement}")

        hero_path = SOURCE_DIR / "hero.jpg"
        if hero_path.exists():
            with open(hero_path, "rb") as f:
                obj = GalleryImage(
                    title="Fondo del hero",
                    category="fachadas",
                    placement="hero_bg",
                    is_active=True,
                    order=0,
                )
                obj.image.save("hero.jpg", File(f), save=True)
            self.stdout.write("Imported hero.jpg -> hero_bg")

        self.stdout.write(self.style.SUCCESS("Gallery import complete."))
