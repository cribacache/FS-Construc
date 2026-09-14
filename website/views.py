from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContactForm

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

GALLERY_CATEGORIES = [
    {"slug": "fachadas", "label": "Fachadas y Exteriores"},
    {"slug": "salas-tv", "label": "Salas de TV"},
    {"slug": "quinchos", "label": "Quinchos y Cocinas Exteriores"},
    {"slug": "estructuras", "label": "Estructuras y Carpintería"},
    {"slug": "pavimentos", "label": "Pavimentos"},
]

GALLERY = [
    {"image": "fachadas-1", "category": "fachadas", "label": "Fachadas y Exteriores"},
    {"image": "fachadas-2", "category": "fachadas", "label": "Fachadas y Exteriores"},
    {"image": "fachadas-3", "category": "fachadas", "label": "Fachadas y Exteriores"},
    {"image": "salas-tv-1", "category": "salas-tv", "label": "Salas de TV"},
    {"image": "salas-tv-2", "category": "salas-tv", "label": "Salas de TV"},
    {"image": "quinchos-1", "category": "quinchos", "label": "Quinchos y Cocinas Exteriores"},
    {"image": "quinchos-2", "category": "quinchos", "label": "Quinchos y Cocinas Exteriores"},
    {"image": "estructuras-1", "category": "estructuras", "label": "Estructuras y Carpintería"},
    {"image": "estructuras-2", "category": "estructuras", "label": "Estructuras y Carpintería"},
    {"image": "estructuras-3", "category": "estructuras", "label": "Estructuras y Carpintería"},
    {"image": "pavimentos-1", "category": "pavimentos", "label": "Pavimentos"},
    {"image": "pavimentos-2", "category": "pavimentos", "label": "Pavimentos"},
]


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

    context = {
        "form": form,
        "services": SERVICES,
        "gallery": GALLERY,
        "gallery_categories": GALLERY_CATEGORIES,
    }
    return render(request, "website/home.html", context)
