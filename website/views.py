import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import ContactForm, GalleryImageEditForm, GalleryImageUploadForm
from .models import GalleryImage, SiteText
from .ratelimit import get_client_ip, is_rate_limited

SERVICES = [
    {
        "icon": "website/icons/ruler.svg",
        "title": "Diseño y construcción",
        "description": "Proyectos a medida, desde el diseño hasta la construcción completa.",
    },
    {
        "icon": "website/icons/refresh.svg",
        "title": "Remodelaciones",
        "description": "Remodelaciones interiores y exteriores, ampliaciones y obras menores.",
    },
    {
        "icon": "website/icons/cabinet.svg",
        "title": "Cocinas y muebles",
        "description": "Cocinas, cubiertas y muebles personalizados a tu estilo.",
    },
    {
        "icon": "website/icons/layers.svg",
        "title": "Revestimientos y fachadas",
        "description": "Revestimiento interior / exterior y fachadas con terminaciones premium.",
    },
    {
        "icon": "website/icons/pergola.svg",
        "title": "Pérgolas y terrazas",
        "description": "Pérgolas, jardineras y terrazas personalizadas para tu jardín.",
    },
    {
        "icon": "website/icons/tv.svg",
        "title": "Salas de TV modernas",
        "description": "Diseño de salas de TV funcionales y de estilo vanguardista.",
    },
    {
        "icon": "website/icons/mirror.svg",
        "title": "Paneles y espejos LED",
        "description": "Paneles, espejos e iluminación LED para tus espacios comunes.",
    },
    {
        "icon": "website/icons/roller.svg",
        "title": "Pintura",
        "description": "Pintura interior y exterior, fachadas, anticorrosivos y barnizado.",
    },
    {
        "icon": "website/icons/grid.svg",
        "title": "Pavimentos",
        "description": "Pavimentos y estampados para pisos de hormigón.",
    },
    {
        "icon": "website/icons/truss.svg",
        "title": "Estructuras metálicas",
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

# Fallback static images, used only if nothing has been uploaded yet for that slot.
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

        form = ContactForm(request.POST)
        if form.is_valid():
            if not form.is_spam():
                form.save()
            # Same confirmation either way, so a bot can't tell its
            # submission was silently dropped.
            messages.success(
                request,
                "¡Gracias por tu mensaje! Te contactaremos a la brevedad.",
            )
            return redirect("home")
    else:
        form = ContactForm()

    return render(request, "website/home.html", _site_context(form))


def _site_context(form, edit_mode=False):
    gallery_qs = GalleryImage.objects.filter(placement="gallery", is_active=True)
    category_labels = dict(GalleryImage.CATEGORY_CHOICES)
    gallery_categories = [
        {"slug": slug, "label": category_labels[slug]}
        for slug in gallery_qs.order_by().values_list("category", flat=True).distinct()
        if slug in category_labels
    ]
    gallery_categories.sort(key=lambda c: c["label"])

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
            }
        )
    return {
        "form": form,
        "services": SERVICES,
        "details": details,
        "site_texts": dict(SiteText.objects.values_list("key", "value")),
        "gallery": gallery_qs,
        "gallery_categories": gallery_categories,
        "hero_bg_url": slot_images["hero_bg"].image.url if slot_images["hero_bg"] else None,
        "build_project_url": slot_images["build_project"].image.url if slot_images["build_project"] else None,
        "build_remodel_url": slot_images["build_remodel"].image.url if slot_images["build_remodel"] else None,
        "build_quote_url": slot_images["build_quote"].image.url if slot_images["build_quote"] else None,
        "fallback_static": FALLBACK_STATIC,
        "edit_mode": edit_mode,
        "slot_ids": {name: (img.pk if img else "") for name, img in slot_images.items()},
        "category_choices": GalleryImage.CATEGORY_CHOICES,
    }


class RateLimitedLoginView(auth_views.LoginView):
    """Same login view, but blocks an IP that's hammering the form before
    Django even validates the credentials."""

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
    """Visual editor: the real home page rendered in edit mode."""
    return render(request, "website/home.html", _site_context(ContactForm(), edit_mode=True))


@never_cache
@login_required(login_url="dashboard_login")
def dashboard_list(request):
    """Original list-style photo manager (title, category, hide, order)."""
    if request.method == "POST":
        upload_form = GalleryImageUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_form.save()
            messages.success(request, "¡Foto subida con éxito!")
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
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "Foto eliminada.")
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
    return "No se pudo guardar la foto."


def _make_current(slot, photo):
    """A singleton slot shows exactly one photo: hide any other active one."""
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
    data = request.POST.copy()
    data["placement"] = "gallery"
    form = GalleryImageUploadForm(data, request.FILES)
    if not form.is_valid():
        return _json_error(_form_error_message(form))
    last = GalleryImage.objects.filter(placement="gallery").aggregate(Max("order"))["order__max"]
    photo = form.save(commit=False)
    photo.order = 0 if last is None else last + 1
    photo.save()
    return JsonResponse({"ok": True, "id": photo.pk})


@login_required(login_url="dashboard_login")
@require_POST
def api_move(request):
    data = _json_body(request)
    photo = GalleryImage.objects.filter(pk=data.get("photo"), is_active=True).first()
    if photo is None:
        return _json_error("No encontré esa foto.", 404)

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
                return _json_error("No encontré esa foto.", 404)
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
    photo.image.delete(save=False)
    photo.delete()
    return JsonResponse({"ok": True})


TEXT_KEY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
MAX_TEXT_LENGTH = 3000


@login_required(login_url="dashboard_login")
@require_POST
def api_texts_save(request):
    """Save edited texts. An empty value restores the original text."""
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
