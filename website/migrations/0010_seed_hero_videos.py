from django.db import migrations

VIDEOS = [
    "hero_carousel/hero-video-1.mp4",
    "hero_carousel/hero-video-2.mp4",
    "hero_carousel/hero-video-3.mp4",
]


def add_videos(apps, schema_editor):
    HeroSlide = apps.get_model("website", "HeroSlide")
    last = HeroSlide.objects.order_by("-order").values_list("order", flat=True).first()
    order = (last if last is not None else -1) + 1
    for name in VIDEOS:
        if HeroSlide.objects.filter(media=name).exists():
            continue
        HeroSlide.objects.create(media=name, order=order, is_active=True)
        order += 1


def remove_videos(apps, schema_editor):
    HeroSlide = apps.get_model("website", "HeroSlide")
    HeroSlide.objects.filter(media__in=VIDEOS).delete()


class Migration(migrations.Migration):
    dependencies = [("website", "0009_sitesettings_extra")]
    operations = [migrations.RunPython(add_videos, remove_videos)]
