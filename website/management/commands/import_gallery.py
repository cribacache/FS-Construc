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
    ("cocinas-1.jpg", "cocinas", "Cocinas y Muebles"),
    ("cocinas-2.jpg", "cocinas", "Cocinas y Muebles"),
    ("cocinas-3.jpg", "cocinas", "Cocinas y Muebles"),
    ("cocinas-4.jpg", "cocinas", "Cocinas y Muebles"),
    ("cocinas-5.jpg", "cocinas", "Cocinas y Muebles"),
    ("cocinas-6.jpg", "cocinas", "Cocinas y Muebles"),
    ("salas-tv-1.jpg", "salas-tv", "Salas de TV"),
    ("salas-tv-2.jpg", "salas-tv", "Salas de TV"),
    ("salas-tv-3.jpg", "salas-tv", "Salas de TV"),
    ("salas-tv-4.jpg", "salas-tv", "Salas de TV"),
    ("pergolas-1.jpg", "pergolas", "Pérgolas y Terrazas"),
    ("pergolas-2.jpg", "pergolas", "Pérgolas y Terrazas"),
    ("pergolas-3.jpg", "pergolas", "Pérgolas y Terrazas"),
    ("pergolas-4.jpg", "pergolas", "Pérgolas y Terrazas"),
    ("espejos-1.jpg", "espejos", "Paneles y Espejos LED"),
    ("espejos-2.jpg", "espejos", "Paneles y Espejos LED"),
    ("espejos-3.jpg", "espejos", "Paneles y Espejos LED"),
    ("espejos-4.jpg", "espejos", "Paneles y Espejos LED"),
    ("quinchos-1.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("quinchos-2.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("quinchos-3.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("quinchos-4.jpg", "quinchos", "Quinchos y Cocinas Exteriores"),
    ("estructuras-1.jpg", "estructuras", "Estructuras y Carpintería"),
    ("estructuras-2.jpg", "estructuras", "Estructuras y Carpintería"),
    ("estructuras-3.jpg", "estructuras", "Estructuras y Carpintería"),
    ("estructuras-4.jpg", "estructuras", "Estructuras y Carpintería"),
    ("pintura-1.jpg", "pintura", "Pintura"),
    ("pintura-2.jpg", "pintura", "Pintura"),
    ("pintura-3.jpg", "pintura", "Pintura"),
    ("pintura-4.jpg", "pintura", "Pintura"),
    ("remodelaciones-1.jpg", "remodelaciones", "Remodelaciones"),
    ("remodelaciones-2.jpg", "remodelaciones", "Remodelaciones"),
    ("remodelaciones-3.jpg", "remodelaciones", "Remodelaciones"),
    ("pavimentos-1.jpg", "pavimentos", "Pavimentos"),
    ("pavimentos-2.jpg", "pavimentos", "Pavimentos"),
    ("pavimentos-3.jpg", "pavimentos", "Pavimentos"),
    ("pavimentos-4.jpg", "pavimentos", "Pavimentos"),
]

BUILD_PANEL_FILES = [
    ("fachadas-2.jpg", "fachadas", "build_project", "Un proyecto nuevo"),
    ("remodelaciones-1.jpg", "remodelaciones", "build_remodel", "Una remodelación"),
    ("pavimentos-1.jpg", "pavimentos", "build_quote", "Una cotización"),
]


class Command(BaseCommand):
    help = "Import the curated static gallery photos into the GalleryImage table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete all existing GalleryImage rows first, then import the current curated set.",
        )

    def handle(self, *args, **options):
        if GalleryImage.objects.exists():
            if not options["force"]:
                self.stdout.write("GalleryImage table is not empty, skipping import.")
                return
            deleted, _ = GalleryImage.objects.all().delete()
            self.stdout.write(f"--force: deleted {deleted} existing rows.")

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
