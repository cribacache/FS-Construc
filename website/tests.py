from django.test import RequestFactory, SimpleTestCase, override_settings

from .ratelimit import get_client_ip


class ClientIpTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, forwarded=None):
        extra = {"REMOTE_ADDR": "10.0.0.1"}
        if forwarded:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded
        return self.factory.get("/", **extra)

    @override_settings(TRUSTED_PROXY_HOPS=0)
    def test_legacy_mode_uses_first_entry(self):
        self.assertEqual(get_client_ip(self.request("1.1.1.1, 2.2.2.2")), "1.1.1.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_one_hop_uses_last_entry_so_spoofed_header_is_ignored(self):
        # nginx sets X-Forwarded-For to the real peer; anything a client
        # sent ahead of it must not be trusted.
        self.assertEqual(get_client_ip(self.request("6.6.6.6, 9.9.9.9")), "9.9.9.9")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_two_hops_uses_second_from_right(self):
        self.assertEqual(get_client_ip(self.request("6.6.6.6, 9.9.9.9, 3.3.3.3")), "9.9.9.9")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_fewer_entries_than_hops_falls_back_to_remote_addr(self):
        self.assertEqual(get_client_ip(self.request("9.9.9.9")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_no_header_falls_back_to_remote_addr(self):
        self.assertEqual(get_client_ip(self.request()), "10.0.0.1")


import json
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import GalleryImage

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00"
    b"\xfd\xd4\x9as\x00\x00\x00\x12IDATx\x9cc<\x91b\xc4\xc0\xc0\xc0\xc4\x00\x06\x00\x11(\x01b\xdau\xca\xa1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class EditorApiTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._media)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        get_user_model().objects.create_user("editor", password="pw-test-123")
        self.client.login(username="editor", password="pw-test-123")

    def photo(self, placement="gallery", order=0, title="x"):
        return GalleryImage.objects.create(
            image=SimpleUploadedFile("a.png", PNG, "image/png"),
            placement=placement,
            order=order,
            title=title,
        )

    def post_json(self, url, payload):
        return self.client.post(url, json.dumps(payload), content_type="application/json")

    def test_requires_login(self):
        self.client.logout()
        response = self.post_json("/mis-fotos/api/move/", {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/mis-fotos/").status_code, 302)

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    )
    def test_editor_renders_home_in_edit_mode(self):
        response = self.client.get("/mis-fotos/")
        self.assertContains(response, 'data-edit="1"')
        self.assertContains(response, 'data-slot="hero_bg"')

    def test_slot_upload_replaces_current_and_hides_old(self):
        old = self.photo("hero_bg")
        response = self.client.post(
            "/mis-fotos/api/slot/hero_bg/upload/",
            {"image": SimpleUploadedFile("n.png", PNG, "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        old.refresh_from_db()
        self.assertFalse(old.is_active)
        self.assertEqual(GalleryImage.objects.filter(placement="hero_bg", is_active=True).count(), 1)

    def test_unknown_slot_is_rejected(self):
        response = self.client.post(
            "/mis-fotos/api/slot/nope/upload/",
            {"image": SimpleUploadedFile("n.png", PNG, "image/png")},
        )
        self.assertEqual(response.status_code, 404)

    def test_gallery_photo_dropped_on_slot_swaps_with_current(self):
        hero = self.photo("hero_bg")
        tile = self.photo("gallery", order=3)
        self.post_json("/mis-fotos/api/move/", {"photo": tile.pk, "to_slot": "hero_bg"})
        hero.refresh_from_db()
        tile.refresh_from_db()
        self.assertEqual((tile.placement, hero.placement), ("hero_bg", "gallery"))
        self.assertEqual(hero.order, 3)

    def test_photo_moves_to_empty_slot(self):
        tile = self.photo("gallery")
        self.post_json("/mis-fotos/api/move/", {"photo": tile.pk, "to_slot": "build_quote"})
        tile.refresh_from_db()
        self.assertEqual(tile.placement, "build_quote")

    def test_slot_photo_swaps_with_gallery_tile(self):
        hero = self.photo("hero_bg")
        tile = self.photo("gallery", order=2)
        self.post_json("/mis-fotos/api/move/", {"photo": hero.pk, "with": tile.pk})
        hero.refresh_from_db()
        tile.refresh_from_db()
        self.assertEqual((hero.placement, tile.placement), ("gallery", "hero_bg"))

    def test_reorder_gallery(self):
        a, b, c = self.photo(order=0), self.photo(order=1), self.photo(order=2)
        self.post_json("/mis-fotos/api/gallery/reorder/", {"ids": [c.pk, a.pk, b.pk]})
        self.assertEqual(
            list(GalleryImage.objects.order_by("order").values_list("pk", flat=True)),
            [c.pk, a.pk, b.pk],
        )

    def test_reorder_rejects_bad_payload(self):
        response = self.post_json("/mis-fotos/api/gallery/reorder/", {"ids": ["x"]})
        self.assertEqual(response.status_code, 400)

    def test_gallery_upload_appends_and_delete_removes(self):
        self.photo(order=4)
        response = self.client.post(
            "/mis-fotos/api/gallery/upload/",
            {"image": SimpleUploadedFile("n.png", PNG, "image/png"), "category": "pintura"},
        )
        new = GalleryImage.objects.get(pk=response.json()["id"])
        self.assertEqual((new.placement, new.category, new.order), ("gallery", "pintura", 5))
        self.client.post(f"/mis-fotos/api/photo/{new.pk}/delete/")
        self.assertFalse(GalleryImage.objects.filter(pk=new.pk).exists())

    def test_rejects_non_image_upload(self):
        response = self.client.post(
            "/mis-fotos/api/gallery/upload/",
            {"image": SimpleUploadedFile("n.txt", b"hello", "text/plain"), "category": "pintura"},
        )
        self.assertEqual(response.status_code, 400)


from .models import SiteText

NO_MANIFEST = override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)


@NO_MANIFEST
class EditableTextTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user("editor", password="pw-test-123")

    def save(self, changes):
        return self.client.post(
            "/mis-fotos/api/texts/",
            json.dumps({"changes": changes}),
            content_type="application/json",
        )

    def login(self):
        self.client.login(username="editor", password="pw-test-123")

    def test_public_page_shows_defaults_without_editor_markup(self):
        response = self.client.get("/")
        self.assertContains(response, "Diseñamos, remodelamos,<br>construimos")
        self.assertContains(response, "Diseño &amp; Construcción a medida")
        self.assertNotContains(response, "data-text-key")
        self.assertNotContains(response, "ed-text")

    def test_texts_api_requires_login(self):
        self.assertEqual(self.save({"hero.title": "x"}).status_code, 302)
        self.assertEqual(SiteText.objects.count(), 0)

    def test_saved_text_replaces_default_on_public_page_and_is_escaped(self):
        self.login()
        self.assertEqual(self.save({"hero.title": "Hola\nMundo <b>"}).status_code, 200)
        page = self.client.get("/")
        self.assertContains(page, "Hola<br>Mundo &lt;b&gt;")
        self.assertNotContains(page, "Diseñamos, remodelamos,<br>construimos")

    def test_empty_value_restores_default(self):
        self.login()
        self.save({"hero.eyebrow": "Otro texto"})
        self.save({"hero.eyebrow": ""})
        self.assertFalse(SiteText.objects.filter(key="hero.eyebrow").exists())
        self.assertContains(self.client.get("/"), "Diseño &amp; Construcción a medida")

    def test_repeated_items_have_their_own_keys(self):
        self.login()
        self.save({"svc.0.title": "Servicio uno editado", "det.ccdd.step.1.title": "Paso editado"})
        page = self.client.get("/")
        self.assertContains(page, "Servicio uno editado")
        self.assertContains(page, "Paso editado")
        self.assertContains(page, "Remodelaciones")  # svc.1 untouched

    def test_editor_marks_texts_and_keeps_menus_in_sync(self):
        self.login()
        self.save({"svc.0.title": "Servicio uno editado"})
        page = self.client.get("/mis-fotos/")
        self.assertContains(page, 'data-text-key="svc.0.title"')
        self.assertContains(page, 'data-text-sync="svc.0.title">Servicio uno editado')
        self.assertContains(page, 'data-multiline="1"')  # hero title has a line break

    def test_rejects_bad_keys_and_values(self):
        self.login()
        self.assertEqual(self.save({"bad key!": "x"}).status_code, 400)
        self.assertEqual(self.save({"hero.title": "x" * 3001}).status_code, 400)
        self.assertEqual(self.save({"hero.title": 5}).status_code, 400)
        self.assertEqual(SiteText.objects.count(), 0)

    def test_detail_banner_is_a_photo_slot(self):
        self.login()
        page = self.client.get("/mis-fotos/")
        self.assertContains(page, 'data-slot="detail_ley_ductos"')
        self.assertContains(page, 'data-slot="detail_ccdd"')
