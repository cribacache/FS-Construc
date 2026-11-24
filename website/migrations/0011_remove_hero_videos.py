from django.db import migrations

VIDEOS = [
    "hero_carousel/hero-video-1.mp4",
    "hero_carousel/hero-video-2.mp4",
    "hero_carousel/hero-video-3.mp4",
]


def remove_videos(apps, schema_editor):
    apps.get_model("website", "HeroSlide").objects.filter(media__in=VIDEOS).delete()


class Migration(migrations.Migration):
    dependencies = [("website", "0010_seed_hero_videos")]
    operations = [migrations.RunPython(remove_videos, migrations.RunPython.noop)]
