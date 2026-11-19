import json
import re

from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import ContactForm, GalleryImageEditForm, GalleryImageUploadForm
from .management.commands.import_gallery import GALLERY_FILES
from .models import (
    DEFAULT_SECTION_ORDER,
    GalleryImage,
    HeroSlide,
    SECTION_META,
    SiteSettings,
    SiteText,
    VIDEO_EXTENSIONS,
)
from .ratelimit import get_client_ip, is_rate_limited

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
ALLOWED_CAROUSEL_EXTENSIONS = IMAGE_EXTENSIONS + VIDEO_EXTENSIONS

SERVICES = [
    {
        "icon": "website/icons/ruler.svg",
        "title": "Diseño y construcción",
        "category": "fachadas",
        "description": "Proyectos a medida, desde el diseño hasta la construcción completa.",
    },
    {
        "icon": "website/icons/refresh.svg",
        "title": "Remodelaciones",
        "category": "remodelaciones",
        "description": "Remodelaciones interiores y exteriores, ampliaciones y obras menores.",
    },
    {
        "icon": "website/icons/cabinet.svg",
        "title": "Cocinas y muebles",
        "category": "cocinas",
        "description": "Cocinas, cubiertas y muebles personalizados a tu estilo.",
    },
    {
        "icon": "website/icons/layers.svg",
        "title": "Revestimientos y fachadas",
        "category": "fachadas",
        "description": "Revestimiento interior / exterior y fachadas con terminaciones premium.",
    },
    {
        "icon": "website/icons/pergola.svg",
        "title": "Pérgolas y terrazas",
        "category": "pergolas",
        "description": "Pérgolas, jardineras y terrazas personalizadas para tu jardín.",
    },
    {
        "icon": "website/icons/tv.svg",
        "title": "Salas de TV modernas",
        "category": "salas-tv",
        "description": "Diseño de salas de TV funcionales y de estilo vanguardista.",
    },
    {
        "icon": "website/icons/mirror.svg",
        "title": "Paneles y espejos LED",
        "category": "espejos",
        "description": "Paneles, espejos e iluminación LED para tus espacios comunes.",
    },
    {
        "icon": "website/icons/roller.svg",
        "title": "Pintura",
        "category": "pintura",
        "description": "Pintura interior y exterior, fachadas, anticorrosivos y barnizado.",
    },
    {
        "icon": "website/icons/grid.svg",
        "title": "Pavimentos",
        "category": "pavimentos",
        "description": "Pavimentos y estampados para pisos de hormigón.",
    },
    {
        "icon": "website/icons/truss.svg",
        "title": "Estructuras metálicas",
        "category": "estructuras",
        "description": "Estructuras metálicas seguras y eficientes para diversas edificaciones.",
    },
    {
        "icon": "website/icons/network.svg",
        "title": "Ley de Ductos (RIT)",
        "description": "Cumplimiento de la Ley N° 20.808: salas técnicas (SOTI/SOTS/SOTU), canalizaciones, tendido de fibra óptica y tramitación del Informe Favorable de Telecomunicaciones.",
        "slug": "ley-ductos",
    },
    {
        "icon": "website/icons/shield.svg",
        "title": "Corrientes débiles y seguridad (CCDD)",
        "description": "CCTV, control de acceso, citofonía y videoporteros, detección de incendios y redes de datos para una conectividad y seguridad 100% integradas.",
        "slug": "ccdd",
    },
]

SERVICE_DETAILS = {
    "ley-ductos": {
        "title": "Ley de Ductos (RIT)",
        "eyebrow": "Cumplimiento Ley N° 20.808",
        "hero_image": "img/gallery/estructuras-4.jpg",
        "intro": [
            "Ofrecemos una solución “llave en mano” para el cumplimiento estricto de la "
            "normativa de telecomunicaciones (RIT), unificando la ejecución de la obra civil "
            "con el despliegue tecnológico.",
            "Nos aseguramos de que su proyecto avance sin retrasos operativos ni multas "
            "normativas, garantizando la conectividad desde las bases.",
        ],
        "steps": [
            {
                "icon": "website/icons/truss.svg",
                "title": "Infraestructura física y metalmecánica",
                "description": (
                    "Construcción y habilitación de salas técnicas obligatorias (SOTI, SOTS, "
                    "SOTU) y fabricación e instalación de canalizaciones verticales, "
                    "escalerillas porta-conductores y bandejas de distribución en acero."
                ),
            },
            {
                "icon": "website/icons/network.svg",
                "title": "Despliegue de redes internas",
                "description": (
                    "Diseño y tendido de cableado estructurado y fibra óptica de alta "
                    "capacidad hacia cada departamento o vivienda, asegurando el libre "
                    "acceso de múltiples operadores."
                ),
            },
            {
                "icon": "website/icons/badge.svg",
                "title": "Certificación y gestión",
                "description": (
                    "Pruebas de conectividad y mediciones técnicas, tramitación y obtención "
                    "del Informe Favorable de Telecomunicaciones ante la municipalidad."
                ),
            },
        ],
    },
    "ccdd": {
        "title": "Corrientes Débiles y Seguridad (CCDD)",
        "eyebrow": "Tecnología, conectividad y seguridad avanzada",
        "hero_image": "img/gallery/pintura-4.jpg",
        "intro": [
            "Dotamos a sus proyectos inmobiliarios de la inteligencia, automatización y "
            "protección que el mercado residencial y corporativo exige en la actualidad.",
            "Diseñamos e implementamos sistemas integrales que aseguran la continuidad "
            "operacional y el control total de los recintos.",
        ],
        "steps": [
            {
                "icon": "website/icons/shield.svg",
                "title": "Seguridad electrónica y control de acceso",
                "description": (
                    "CCTV con cámaras IP de alta definición y monitoreo centralizado, "
                    "control de acceso peatonal y vehicular automatizado, citofonía "
                    "digital y videoporteros."
                ),
            },
            {
                "icon": "website/icons/alert.svg",
                "title": "Prevención de incendios",
                "description": (
                    "Redes de detección temprana de humo y calor mediante paneles "
                    "centralizados inteligentes, cumpliendo rigurosamente con la "
                    "normativa vigente."
                ),
            },
            {
                "icon": "website/icons/network.svg",
                "title": "Conectividad y redes de datos",
                "description": (
                    "Iluminación WiFi de alta velocidad para áreas comunes, quinchos y "
                    "zonas de cowork; infraestructura de networking y telefonía IP de "
                    "estándar corporativo."
                ),
            },
        ],
    },
}

VALUES = [
    {
        "title": "Garantía",
        "description": "Respaldamos cada trabajo con materiales de calidad y mano de obra certificada.",
    },
    {
        "title": "Compromiso",
        "description": "Cumplimos plazos y acuerdos, manteniéndote informado en cada etapa.",
    },
    {
        "title": "Profesionalismo",
        "description": "Equipo técnico especializado en diseño, construcción y remodelación.",
    },
    {
        "title": "Dedicación",
        "description": "Personalizamos cada proyecto según tus gustos y necesidades reales.",
    },
]

PROCESS_STEPS = [
    {
        "title": "Contacto",
        "description": "Nos cuentas tu proyecto a través del formulario, correo o WhatsApp.",
    },
    {
        "title": "Diseño y cotización",
        "description": "Evaluamos el espacio y te entregamos una propuesta a medida.",
    },
    {
        "title": "Construcción",
        "description": "Ejecutamos con materiales de primera y técnicas avanzadas.",
    },
    {
        "title": "Entrega",
        "description": "Revisamos contigo cada detalle antes de la entrega final.",
    },
]

FALLBACK_STATIC = {
    "hero_bg": "img/gallery/hero.jpg",
    "build_project": "img/gallery/fachadas-2.jpg",
    "build_remodel": "img/gallery/remodelaciones-1.jpg",
    "build_quote": "img/gallery/pavimentos-1.jpg",
}

SLOT_NAMES = (
    "hero_bg",
    "build_project",
    "build_remodel",
    "build_quote",
    "detail_ley_ductos",
    "detail_ccdd",
)
DETAIL_SLOTS = {"ley-ductos": "detail_ley_ductos", "ccdd": "detail_ccdd"}


def _current_slot_image(placement):
    return (
        GalleryImage.objects.filter(placement=placement, is_active=True)
        .order_by("-created_at")
        .first()
    )


def _static_gallery():
    labels = dict(GalleryImage.CATEGORY_CHOICES)
    return [
        SimpleNamespace(
            pk="",
            category=category,
            title=label,
            is_video=False,
            image=SimpleNamespace(url=static(f"img/gallery/{filename}")),
            get_category_display=labels.get(category, label),
        )
        for filename, category, label in GALLERY_FILES
    ]


def _service_cards(by_category, details_by_slug):
    used = {}
    cards = []
    for service in SERVICES:
        slug = service.get("slug")
        if slug:
            detail = details_by_slug[slug]
            url = detail["bg_url"] or static(detail["hero_image"])
            is_video = bool(detail.get("bg_is_video"))
        else:
            category = service["category"]
            index = used.get(category, 0)
            used[category] = index + 1
            photos = by_category.get(category) or []
            if photos:
                chosen = photos[index % len(photos)]
                url = chosen.image.url
                is_video = bool(getattr(chosen, "is_video", False))
            else:
                url = static(f"img/gallery/{category}-{min(index + 1, 2)}.jpg")
                is_video = False
        cards.append({**service, "image_url": url, "is_video": is_video})
    return cards


def _studio_image_url(by_category):
    for category in ("espejos", "cocinas", "salas-tv"):
        photos = by_category.get(category)
        if photos:
            return photos[-1].image.url
    return static("img/gallery/espejos-4.jpg")


def home(request):
    if request.method == "POST":
        ip = get_client_ip(request)
        if settings.RATE_LIMIT_ACTIVE and is_rate_limited(
            f"contact:{ip}",
            settings.RATE_LIMIT_CONTACT_MAX,
            settings.RATE_LIMIT_CONTACT_WINDOW,
        ):
            messages.error(
                request,
                "Enviaste varios mensajes seguidos. Intenta de nuevo en un rato.",
            )
            return redirect("home")

        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            if not form.is_spam():
                form.save()
            messages.success(
                request,
                "¡Gracias por tu mensaje! Te contactaremos a la brevedad.",
            )
            return redirect("home")
    else:
        form = ContactForm()

    return render(request, "website/home.html", _site_context(form))


def _site_context(form, edit_mode=False):
    gallery = list(GalleryImage.objects.filter(placement="gallery", is_active=True))
    if (
        not gallery
        and not edit_mode
        and not GalleryImage.objects.filter(placement="gallery").exists()
    ):
        gallery = _static_gallery()
    category_labels = dict(GalleryImage.CATEGORY_CHOICES)
    by_category = {}
    for photo in gallery:
        by_category.setdefault(photo.category, []).append(photo)

    counts = {slug: len(photos) for slug, photos in by_category.items() if slug in category_labels}
    for slug in category_labels:
        counts.setdefault(slug, 0)
    gallery_categories = sorted(
        (
            {"slug": slug, "label": category_labels[slug], "count": count}
            for slug, count in counts.items()
        ),
        key=lambda c: (c["count"] == 0, c["count"], c["label"]),
    )
    non_empty = [c for c in gallery_categories if c["count"] > 0]
    gallery_start = (
        "all" if edit_mode or not non_empty else non_empty[0]["slug"]
    )

    slot_images = {name: _current_slot_image(name) for name in SLOT_NAMES}
    details = []
    for slug, detail in SERVICE_DETAILS.items():
        image = slot_images[DETAIL_SLOTS[slug]]
        details.append(
            {
                **detail,
                "slug": slug,
                "slot": DETAIL_SLOTS[slug],
                "photo_id": image.pk if image else "",
                "bg_url": image.image.url if image else None,
                "bg_is_video": bool(image.is_video) if image else False,
            }
        )
    details_by_slug = {detail["slug"]: detail for detail in details}

    site_cfg = SiteSettings.get_solo()
    sections_layout, contact_num = site_cfg.get_sections_layout()
    hero_slides_qs = (
        HeroSlide.objects.all() if edit_mode else HeroSlide.objects.filter(is_active=True)
    )

    return {
        "form": form,
        "site_cfg": site_cfg,
        "site_extra": site_cfg.get_extra(),
        "sections_layout": sections_layout,
        "contact_num": contact_num,
        "hero_slides": list(hero_slides_qs),
        "services": _service_cards(by_category, details_by_slug),
        "details": details,
        "values": VALUES,
        "process_steps": PROCESS_STEPS,
        "studio_image_url": _studio_image_url(by_category),
        "site_texts": dict(SiteText.objects.values_list("key", "value")),
        "gallery": gallery,
        "gallery_categories": gallery_categories,
        "gallery_start": gallery_start,
        "hero_bg_url": slot_images["hero_bg"].image.url if slot_images["hero_bg"] else None,
        "hero_bg_is_video": bool(slot_images["hero_bg"].is_video) if slot_images["hero_bg"] else False,
        "build_project_url": slot_images["build_project"].image.url if slot_images["build_project"] else None,
        "build_project_is_video": bool(slot_images["build_project"].is_video) if slot_images["build_project"] else False,
        "build_remodel_url": slot_images["build_remodel"].image.url if slot_images["build_remodel"] else None,
        "build_remodel_is_video": bool(slot_images["build_remodel"].is_video) if slot_images["build_remodel"] else False,
        "build_quote_url": slot_images["build_quote"].image.url if slot_images["build_quote"] else None,
        "build_quote_is_video": bool(slot_images["build_quote"].is_video) if slot_images["build_quote"] else False,
        "fallback_static": FALLBACK_STATIC,
        "edit_mode": edit_mode,
        "slot_ids": {name: (img.pk if img else "") for name, img in slot_images.items()},
        "category_choices": GalleryImage.CATEGORY_CHOICES,
    }


class RateLimitedLoginView(auth_views.LoginView):
    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        if settings.RATE_LIMIT_ACTIVE and is_rate_limited(
            f"dashboard-login:{ip}",
            settings.RATE_LIMIT_LOGIN_MAX,
            settings.RATE_LIMIT_LOGIN_WINDOW,
        ):
            return HttpResponse(
                "Demasiados intentos. Intenta de nuevo en unos minutos.",
                status=429,
            )
        return super().post(request, *args, **kwargs)


@never_cache
@login_required(login_url="dashboard_login")
def dashboard(request):
    return render(request, "website/home.html", _site_context(ContactForm(), edit_mode=True))


@never_cache
@login_required(login_url="dashboard_login")
def dashboard_list(request):
    if request.method == "POST":
        upload_form = GalleryImageUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_form.save()
            messages.success(request, "¡Archivo subido con éxito!")
            return redirect("dashboard_list")
    else:
        upload_form = GalleryImageUploadForm()

    photos = GalleryImage.objects.all().order_by("placement", "order", "-created_at")
    photo_rows = [(photo, GalleryImageEditForm(instance=photo)) for photo in photos]

    context = {
        "upload_form": upload_form,
        "photo_rows": photo_rows,
    }
    return render(request, "website/dashboard.html", context)


@login_required(login_url="dashboard_login")
@require_POST
def dashboard_update(request, pk):
    photo = get_object_or_404(GalleryImage, pk=pk)
    form = GalleryImageEditForm(request.POST, instance=photo)
    if form.is_valid():
        form.save()
        messages.success(request, "Cambios guardados.")
    else:
        messages.error(request, "No se pudo guardar: revisa los datos.")
    return redirect("dashboard_list")


@login_required(login_url="dashboard_login")
@require_POST
def dashboard_delete(request, pk):
    photo = get_object_or_404(GalleryImage, pk=pk)
    try:
        photo.image.delete(save=False)
    except OSError:
        pass
    photo.delete()
    messages.success(request, "Archivo eliminado.")
    return redirect("dashboard_list")


# ---------- Visual editor: JSON API ----------

def _json_error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


def _json_body(request):
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _form_error_message(form):
    for errors in form.errors.values():
        return errors[0]
    return "No se pudo guardar el archivo."


def _make_current(slot, photo):
    GalleryImage.objects.filter(placement=slot, is_active=True).exclude(pk=photo.pk).update(
        is_active=False
    )


def _swap(a, b):
    a.placement, b.placement = b.placement, a.placement
    a.order, b.order = b.order, a.order
    a.save(update_fields=["placement", "order"])
    b.save(update_fields=["placement", "order"])
    for photo in (a, b):
        if photo.placement in SLOT_NAMES:
            _make_current(photo.placement, photo)


@login_required(login_url="dashboard_login")
@require_POST
def api_slot_upload(request, slot):
    if slot not in SLOT_NAMES:
        return _json_error("Ese espacio no existe.", 404)
    data = request.POST.copy()
    data["placement"] = slot
    data.setdefault("category", "fachadas")
    form = GalleryImageUploadForm(data, request.FILES)
    if not form.is_valid():
        return _json_error(_form_error_message(form))
    with transaction.atomic():
        photo = form.save()
        _make_current(slot, photo)
    return JsonResponse({"ok": True, "id": photo.pk})


@login_required(login_url="dashboard_login")
@require_POST
def api_gallery_upload(request):
    files = request.FILES.getlist("images") or request.FILES.getlist("image")
    if not files:
        return _json_error("Selecciona al menos una foto o video.")

    category = request.POST.get("category", "fachadas")
    title = request.POST.get("title", "").strip()[:120]
    last = GalleryImage.objects.filter(placement="gallery").aggregate(Max("order"))["order__max"]
    next_order = 0 if last is None else last + 1
    created_ids = []

    with transaction.atomic():
        for idx, uploaded in enumerate(files):
            form = GalleryImageUploadForm(
                {"placement": "gallery", "category": category, "title": title},
                {"image": uploaded},
            )
            if not form.is_valid():
                return _json_error(_form_error_message(form))
            photo = form.save(commit=False)
            photo.order = next_order + idx
            photo.save()
            created_ids.append(photo.pk)

    return JsonResponse({"ok": True, "ids": created_ids, "id": created_ids[0]})


@login_required(login_url="dashboard_login")
@require_POST
def api_move(request):
    data = _json_body(request)
    photo = GalleryImage.objects.filter(pk=data.get("photo"), is_active=True).first()
    if photo is None:
        return _json_error("No encontré ese archivo.", 404)

    with transaction.atomic():
        if "to_slot" in data:
            slot = data["to_slot"]
            if slot not in SLOT_NAMES:
                return _json_error("Ese espacio no existe.", 404)
            current = _current_slot_image(slot)
            if current is not None and current.pk == photo.pk:
                return JsonResponse({"ok": True})
            if current is not None:
                _swap(photo, current)
            else:
                photo.placement = slot
                photo.save(update_fields=["placement"])
                _make_current(slot, photo)
        elif "with" in data:
            other = GalleryImage.objects.filter(pk=data.get("with"), is_active=True).first()
            if other is None:
                return _json_error("No encontré ese archivo.", 404)
            if other.pk != photo.pk:
                _swap(photo, other)
        else:
            return _json_error("Falta el destino.")
    return JsonResponse({"ok": True})


@login_required(login_url="dashboard_login")
@require_POST
def api_gallery_reorder(request):
    ids = _json_body(request).get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return _json_error("Orden inválido.")
    with transaction.atomic():
        for index, pk in enumerate(ids):
            GalleryImage.objects.filter(pk=pk, placement="gallery").update(order=index)
    return JsonResponse({"ok": True})


@login_required(login_url="dashboard_login")
@require_POST
def api_photo_delete(request, pk):
    photo = get_object_or_404(GalleryImage, pk=pk)
    try:
        photo.image.delete(save=False)
    except OSError:
        pass
    photo.delete()
    return JsonResponse({"ok": True})


@login_required(login_url="dashboard_login")
@require_POST
def api_photo_update(request, pk):
    photo = get_object_or_404(GalleryImage, pk=pk)
    data = _json_body(request)
    fields = []
    if isinstance(data.get("title"), str):
        photo.title = data["title"].strip()[:120]
        fields.append("title")
    valid_categories = {choice[0] for choice in GalleryImage.CATEGORY_CHOICES}
    if data.get("category") in valid_categories:
        photo.category = data["category"]
        fields.append("category")
    if fields:
        photo.save(update_fields=fields)
    return JsonResponse({"ok": True})


TEXT_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
MAX_TEXT_LENGTH = 3000


@login_required(login_url="dashboard_login")
@require_POST
def api_texts_save(request):
    changes = _json_body(request).get("changes")
    if not isinstance(changes, dict) or len(changes) > 300:
        return _json_error("Cambios inválidos.")
    cleaned = {}
    for key, value in changes.items():
        if not isinstance(key, str) or not TEXT_KEY_RE.match(key) or not isinstance(value, str):
            return _json_error("Cambios inválidos.")
        value = value.replace("\r", "").strip()
        if len(value) > MAX_TEXT_LENGTH:
            return _json_error("Uno de los textos es demasiado largo.")
        cleaned[key] = value
    with transaction.atomic():
        for key, value in cleaned.items():
            if value:
                SiteText.objects.update_or_create(key=key, defaults={"value": value})
            else:
                SiteText.objects.filter(key=key).delete()
    return JsonResponse({"ok": True})


# ---------- Carousel & SiteSettings API ----------


@login_required(login_url="dashboard_login")
@require_POST
def editor_carousel_add(request):
    files = request.FILES.getlist("media")
    title = request.POST.get("title", "").strip()[:140]
    if not files:
        return _json_error("Selecciona al menos una imagen o video.")

    for uploaded in files:
        filename = (uploaded.name or "").lower()
        if not filename.endswith(ALLOWED_CAROUSEL_EXTENSIONS):
            return _json_error(
                "Formato no compatible. Usa JPG, PNG, WEBP, MP4, WEBM o MOV."
            )

    last = HeroSlide.objects.aggregate(Max("order"))["order__max"]
    next_order = 0 if last is None else last + 1
    created = []
    with transaction.atomic():
        for idx, uploaded in enumerate(files):
            slide = HeroSlide.objects.create(
                title=title,
                media=uploaded,
                order=next_order + idx,
                is_active=True,
            )
            created.append(
                {
                    "id": slide.pk,
                    "title": slide.title,
                    "url": slide.media.url,
                    "is_video": slide.is_video,
                    "is_active": slide.is_active,
                }
            )
    return JsonResponse({"ok": True, "slides": created})


@login_required(login_url="dashboard_login")
@require_POST
def editor_carousel_reorder(request):
    ids = _json_body(request).get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return _json_error("Orden inválido.")
    with transaction.atomic():
        for idx, slide_id in enumerate(ids):
            HeroSlide.objects.filter(pk=slide_id).update(order=idx)
    return JsonResponse({"ok": True})


@login_required(login_url="dashboard_login")
@require_POST
def editor_carousel_toggle(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    slide.is_active = not slide.is_active
    slide.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "is_active": slide.is_active})


@login_required(login_url="dashboard_login")
@require_POST
def editor_carousel_update(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    data = _json_body(request)
    if isinstance(data.get("title"), str):
        slide.title = data["title"].strip()[:140]
        slide.save(update_fields=["title"])
    return JsonResponse({"ok": True})


@login_required(login_url="dashboard_login")
@require_POST
def editor_carousel_delete(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    try:
        if slide.media:
            slide.media.delete(save=False)
    except OSError:
        pass
    slide.delete()
    return JsonResponse({"ok": True})


VALID_TRANSITIONS = {choice[0] for choice in SiteSettings.TRANSITION_CHOICES}
VALID_THEMES = {choice[0] for choice in SiteSettings.THEME_CHOICES}
VALID_FONTS = {choice[0] for choice in SiteSettings.FONT_CHOICES}
VALID_RADII = {choice[0] for choice in SiteSettings.RADIUS_CHOICES}
VALID_HERO_HEIGHTS = {choice[0] for choice in SiteSettings.HERO_HEIGHT_CHOICES}
VALID_SPACINGS = {choice[0] for choice in SiteSettings.SPACING_CHOICES}
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@login_required(login_url="dashboard_login")
@require_POST
def editor_settings_save(request):
    payload = _json_body(request)
    if not payload:
        return _json_error("Datos inválidos.")

    cfg = SiteSettings.get_solo()

    if payload.get("carousel_transition") in VALID_TRANSITIONS:
        cfg.carousel_transition = payload["carousel_transition"]

    if "carousel_interval" in payload:
        try:
            cfg.carousel_interval = max(3, min(20, int(payload["carousel_interval"])))
        except (TypeError, ValueError):
            pass

    if payload.get("theme_preset") in VALID_THEMES:
        cfg.theme_preset = payload["theme_preset"]

    if payload.get("font_preset") in VALID_FONTS:
        cfg.font_preset = payload["font_preset"]

    if payload.get("radius_preset") in VALID_RADII:
        cfg.radius_preset = payload["radius_preset"]

    if payload.get("hero_height") in VALID_HERO_HEIGHTS:
        cfg.hero_height = payload["hero_height"]

    if payload.get("section_spacing") in VALID_SPACINGS:
        cfg.section_spacing = payload["section_spacing"]

    if "hero_overlay" in payload:
        try:
            cfg.hero_overlay = max(15, min(85, int(payload["hero_overlay"])))
        except (TypeError, ValueError):
            pass

    if "accent_color" in payload and isinstance(payload["accent_color"], str):
        raw_color = payload["accent_color"].strip()
        if raw_color == "":
            cfg.accent_color = ""
        elif HEX_COLOR_RE.match(raw_color):
            cfg.accent_color = raw_color.lower()

    str_limits = {
        "phone_display": 40,
        "phone_raw": 30,
        "whatsapp_number": 30,
        "whatsapp_prefill": 200,
        "email_primary": 254,
        "email_sales": 254,
        "instagram_handle": 60,
        "instagram_url": 200,
        "tiktok_handle": 60,
        "tiktok_url": 200,
        "office_location": 140,
        "cta_label": 40,
    }
    for field, max_len in str_limits.items():
        if field in payload and isinstance(payload[field], str):
            val = payload[field].strip()[:max_len]
            if field == "whatsapp_number":
                val = re.sub(r"\D+", "", val)
            if field in ("email_primary", "cta_label") and not val:
                continue
            setattr(cfg, field, val)

    bool_fields = (
        "carousel_kenburns",
        "carousel_pause_hover",
        "show_marquee",
        "show_floating_wa",
        "show_choose",
        "show_portfolio",
        "show_tech",
        "show_why",
        "show_services",
    )
    for bool_field in bool_fields:
        if bool_field in payload:
            setattr(cfg, bool_field, bool(payload[bool_field]))

    if isinstance(payload.get("section_order"), list):
        valid_order = [k for k in payload["section_order"] if k in SECTION_META]
        seen = set()
        deduped = []
        for k in valid_order:
            if k not in seen:
                seen.add(k)
                deduped.append(k)
        for k in DEFAULT_SECTION_ORDER:
            if k not in seen:
                deduped.append(k)
        cfg.section_order = deduped

    extra_payload = payload.get("extra")
    if isinstance(extra_payload, dict):
        current_extra = dict(cfg.extra or {})
        for key, allowed in SiteSettings.EXTRA_OPTIONS.items():
            if extra_payload.get(key) in allowed:
                current_extra[key] = extra_payload[key]
        for key, max_len in SiteSettings.EXTRA_TEXT_LIMITS.items():
            if isinstance(extra_payload.get(key), str):
                current_extra[key] = extra_payload[key].strip()[:max_len]
        cfg.extra = current_extra

    cfg.save()
    return JsonResponse({"ok": True})