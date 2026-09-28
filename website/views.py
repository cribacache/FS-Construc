from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import ContactForm, GalleryImageEditForm, GalleryImageUploadForm
from .models import GalleryImage
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


def _singleton_image(placement):
    img = (
        GalleryImage.objects.filter(placement=placement, is_active=True)
        .order_by("-created_at")
        .first()
    )
    return img.image.url if img else None


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

    gallery_qs = GalleryImage.objects.filter(placement="gallery", is_active=True)
    category_labels = dict(GalleryImage.CATEGORY_CHOICES)
    gallery_categories = [
        {"slug": slug, "label": category_labels[slug]}
        for slug in gallery_qs.order_by().values_list("category", flat=True).distinct()
        if slug in category_labels
    ]
    gallery_categories.sort(key=lambda c: c["label"])

    context = {
        "form": form,
        "services": SERVICES,
        "service_details": SERVICE_DETAILS,
        "gallery": gallery_qs,
        "gallery_categories": gallery_categories,
        "hero_bg_url": _singleton_image("hero_bg"),
        "build_project_url": _singleton_image("build_project"),
        "build_remodel_url": _singleton_image("build_remodel"),
        "build_quote_url": _singleton_image("build_quote"),
        "fallback_static": FALLBACK_STATIC,
    }
    return render(request, "website/home.html", context)


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
    if request.method == "POST":
        upload_form = GalleryImageUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            upload_form.save()
            messages.success(request, "¡Foto subida con éxito!")
            return redirect("dashboard")
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
    return redirect("dashboard")


@login_required(login_url="dashboard_login")
@require_POST
def dashboard_delete(request, pk):
    photo = get_object_or_404(GalleryImage, pk=pk)
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "Foto eliminada.")
    return redirect("dashboard")
