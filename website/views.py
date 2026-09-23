from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContactForm
from .models import GalleryImage

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
]

# Fallback static images, used only if nothing has been uploaded yet for that slot.
FALLBACK_STATIC = {
    "hero_bg": "img/gallery/hero.jpg",
    "build_project": "img/gallery/fachadas-1.jpg",
    "build_remodel": "img/gallery/quinchos-1.jpg",
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
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
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
        "gallery": gallery_qs,
        "gallery_categories": gallery_categories,
        "hero_bg_url": _singleton_image("hero_bg"),
        "build_project_url": _singleton_image("build_project"),
        "build_remodel_url": _singleton_image("build_remodel"),
        "build_quote_url": _singleton_image("build_quote"),
        "fallback_static": FALLBACK_STATIC,
    }
    return render(request, "website/home.html", context)
