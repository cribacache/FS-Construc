from django.db import models

VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".m4v", ".ogg")

DEFAULT_SECTION_ORDER = ["choose", "portfolio", "tech", "services", "why"]
SECTION_META = {
    "choose": {"label": "¿Qué quieres construir?", "span": 1},
    "portfolio": {"label": "Proyectos ejecutados", "span": 1},
    "tech": {"label": "Bloques técnicos (Ley de Ductos / CCDD)", "span": 2},
    "services": {"label": "Nuestros servicios", "span": 1},
    "why": {"label": "Por qué elegirnos", "span": 1},
    }


def default_section_order():
    return list(DEFAULT_SECTION_ORDER)


class GalleryImage(models.Model):
    CATEGORY_CHOICES = [
        ("fachadas", "Fachadas y Exteriores"),
        ("cocinas", "Cocinas y Muebles"),
        ("salas-tv", "Salas de TV"),
        ("pergolas", "Pérgolas y Terrazas"),
        ("piscinas", "Piscinas"),
        ("espejos", "Paneles y Espejos LED"),
        ("quinchos", "Quinchos y Cocinas Exteriores"),
        ("estructuras", "Estructuras y Carpintería"),
        ("pintura", "Pintura"),
        ("pavimentos", "Pavimentos"),
        ("remodelaciones", "Remodelaciones"),
    ]
    PLACEMENT_CHOICES = [
        ("gallery", "Galería de portafolio"),
        ("hero_bg", "Fondo del hero (portada)"),
        ("build_project", 'Panel "¿Qué quieres construir?" — Un proyecto nuevo'),
        ("build_remodel", 'Panel "¿Qué quieres construir?" — Una remodelación'),
        ("build_quote", 'Panel "¿Qué quieres construir?" — Una cotización'),
        ("detail_ley_ductos", "Banner de Ley de Ductos (RIT)"),
        ("detail_ccdd", "Banner de Corrientes débiles (CCDD)"),
    ]

    image = models.FileField("Archivo (foto o video)", upload_to="gallery/")
    title = models.CharField("Título / descripción corta", max_length=120, blank=True)
    category = models.CharField(
        "Categoría", max_length=20, choices=CATEGORY_CHOICES, default="fachadas"
    )
    placement = models.CharField(
        "Dónde se muestra", max_length=20, choices=PLACEMENT_CHOICES, default="gallery"
    )
    is_active = models.BooleanField("Visible en el sitio", default=True)
    order = models.PositiveIntegerField(
        "Orden", default=0, help_text="Menor número aparece primero."
    )
    created_at = models.DateTimeField("Subida el", auto_now_add=True)

    class Meta:
        verbose_name = "Foto o video"
        verbose_name_plural = "Fotos y videos"
        ordering = ["order", "-created_at"]

    @property
    def is_video(self):
        name = (self.image.name or "").lower()
        return name.endswith(VIDEO_EXTENSIONS)

    def __str__(self):
        return self.title or f"Archivo #{self.pk}"


class ContactMessage(models.Model):
    name = models.CharField("Nombre", max_length=120)
    email = models.EmailField("Correo electrónico")
    phone = models.CharField("Teléfono", max_length=30, blank=True)
    service = models.CharField("Servicio de interés", max_length=120, blank=True)
    message = models.TextField("Mensaje")
    created_at = models.DateTimeField("Fecha de envío", auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje de contacto"
        verbose_name_plural = "Mensajes de contacto"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.created_at:%d-%m-%Y %H:%M})"


class SiteText(models.Model):
    """A text of the home page that was edited from the visual editor.
    Texts that were never edited have no row and show the default written
    in the template."""

    key = models.CharField("Clave", max_length=80, unique=True)
    value = models.TextField("Texto")
    updated_at = models.DateTimeField("Editado el", auto_now=True)

    class Meta:
        verbose_name = "Texto del sitio"
        verbose_name_plural = "Textos del sitio"
        ordering = ["key"]

    def __str__(self):
        return self.key


class HeroSlide(models.Model):
    TRANSITION_CHOICES = [
        ("fade", "Disolvencia cinematográfica"),
        ("slide", "Deslizamiento lateral"),
        ("curtain", "Cortina arquitectónica"),
        ("zoom", "Zoom profundo"),
    ]

    title = models.CharField("Etiqueta / Ubicación opcional", max_length=140, blank=True)
    media = models.FileField("Imagen o video", upload_to="hero_carousel/")
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Diapositiva de portada"
        verbose_name_plural = "Diapositivas de portada"

    @property
    def is_video(self):
        name = (self.media.name or "").lower()
        return name.endswith(VIDEO_EXTENSIONS)

    def __str__(self):
        return self.title or f"Slide #{self.pk}"


class SiteSettings(models.Model):
    TRANSITION_CHOICES = HeroSlide.TRANSITION_CHOICES
    THEME_CHOICES = [
        ("navy", "Azul Marino Editorial (Original)"),
        ("slate", "Grafito & Acero Industrial"),
        ("sand", "Arena, Travertino & Bronce"),
        ("emerald", "Verde Bosque Arquitectónico"),
        ("obsidian", "Obsidiana & Oro Champán"),
        ("terracotta", "Terracota & Hormigón Visto"),
    ]
    FONT_CHOICES = [
        ("editorial", "Cormorant Garamond + Manrope (Editorial)"),
        ("modern", "Plus Jakarta Sans + Inter (Contemporáneo)"),
        ("brutalist", "Space Grotesk + DM Sans (Ingeniería)"),
    ]
    RADIUS_CHOICES = [
        ("pill", "Orgánico / Redondeado (Original)"),
        ("soft", "Suave / Moderno (10px)"),
        ("sharp", "Recto / Arquitectónico (2px)"),
    ]
    HERO_HEIGHT_CHOICES = [
        ("full", "Pantalla completa (100vh)"),
        ("tall", "Editorial amplio (85vh)"),
        ("compact", "Compacto (72vh)"),
    ]
    SPACING_CHOICES = [
        ("airy", "Amplio (Galería)"),
        ("normal", "Equilibrado (Original)"),
        ("compact", "Compacto"),
    ]

    # Carrusel
    carousel_transition = models.CharField(
        max_length=20, choices=TRANSITION_CHOICES, default="fade"
    )
    carousel_interval = models.PositiveIntegerField(
        "Segundos por diapositiva", default=6
    )
    carousel_kenburns = models.BooleanField(default=True)
    carousel_pause_hover = models.BooleanField(default=False)

    # Contacto y redes editables por el cliente
    phone_display = models.CharField(max_length=40, default="+56 9 3068 9483")
    phone_raw = models.CharField(max_length=30, default="+56930689483")
    whatsapp_number = models.CharField(max_length=30, default="56930689483")
    whatsapp_prefill = models.CharField(
        max_length=200,
        blank=True,
        default="Hola FS Construcciones, me gustaría cotizar un proyecto.",
    )
    email_primary = models.EmailField(default="contacto@fsconstrucciones.cl")
    email_sales = models.EmailField(default="ventas@fsconstrucciones.cl", blank=True)
    instagram_handle = models.CharField(max_length=60, default="@fdsconstrucciones")
    instagram_url = models.URLField(default="https://instagram.com/fdsconstrucciones")
    tiktok_handle = models.CharField(max_length=60, default="@fs.construcciones")
    tiktok_url = models.URLField(default="https://www.tiktok.com/@fs.construcciones")
    office_location = models.CharField(
        max_length=140, blank=True, default="Santiago, Región Metropolitana"
    )

    # Apariencia avanzada
    theme_preset = models.CharField(max_length=20, choices=THEME_CHOICES, default="navy")
    accent_color = models.CharField(max_length=20, blank=True, default="")
    font_preset = models.CharField(max_length=20, choices=FONT_CHOICES, default="editorial")
    radius_preset = models.CharField(max_length=20, choices=RADIUS_CHOICES, default="pill")
    hero_overlay = models.PositiveIntegerField(default=48)
    hero_height = models.CharField(max_length=20, choices=HERO_HEIGHT_CHOICES, default="full")
    section_spacing = models.CharField(max_length=20, choices=SPACING_CHOICES, default="normal")
    cta_label = models.CharField(max_length=40, default="Cotizar")

    # Visibilidad y orden de secciones
    show_marquee = models.BooleanField(default=True)
    show_floating_wa = models.BooleanField(default=True)
    show_choose = models.BooleanField(default=True)
    show_portfolio = models.BooleanField(default=True)
    show_tech = models.BooleanField(default=True)
    show_why = models.BooleanField(default=True)
    show_services = models.BooleanField(default=True)
    section_order = models.JSONField(default=default_section_order)

    # Opciones de diseño avanzadas (se guardan en un solo campo JSON)
    EXTRA_OPTIONS = {
        "hero_align": ("left", "center"),
        "content_width": ("narrow", "normal", "wide"),
        "header_style": ("auto", "solid"),
        "gallery_cols": ("2", "3", "4"),
        "gallery_tone": ("bw", "color"),
    }
    EXTRA_DEFAULTS = {
        "hero_align": "left",
        "content_width": "normal",
        "header_style": "auto",
        "gallery_cols": "3",
        "gallery_tone": "bw",
    }
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def get_extra(self):
        data = dict(self.EXTRA_DEFAULTS)
        for key, value in (self.extra or {}).items():
            if key in self.EXTRA_OPTIONS and value in self.EXTRA_OPTIONS[key]:
                data[key] = value
        return data

    def normalized_order(self):
        raw = self.section_order if isinstance(self.section_order, list) else []
        cleaned = [k for k in raw if k in SECTION_META]
        seen = set()
        unique = []
        for k in cleaned:
            if k not in seen:
                seen.add(k)
                unique.append(k)
        for k in DEFAULT_SECTION_ORDER:
            if k not in seen:
                unique.append(k)
        return unique

    def get_sections_layout(self):
        visibility = {
            "choose": self.show_choose,
            "services": self.show_services,
            "tech": self.show_tech,
            "why": self.show_why,
            "portfolio": self.show_portfolio,
        }
        num = 1
        items = []
        for key in self.normalized_order():
            meta = SECTION_META[key]
            vis = bool(visibility.get(key, True))
            if vis:
                num_str = f"{num:02d}"
                badge = f"{num:02d}–{num + 1:02d}" if meta["span"] == 2 else f"{num:02d}"
                start_idx = num - 1
                num += meta["span"]
            else:
                num_str = "--"
                badge = "Oculta"
                start_idx = 0
            items.append(
                {
                    "key": key,
                    "label": meta["label"],
                    "visible": vis,
                    "num": num_str,
                    "badge": badge,
                    "tech_base": start_idx,
                }
            )
        return items, f"{num:02d}"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
