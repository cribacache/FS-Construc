from django.db import models


class GalleryImage(models.Model):
    CATEGORY_CHOICES = [
        ("fachadas", "Fachadas y Exteriores"),
        ("cocinas", "Cocinas y Muebles"),
        ("salas-tv", "Salas de TV"),
        ("pergolas", "Pérgolas y Terrazas"),
        ("espejos", "Paneles y Espejos LED"),
        ("quinchos", "Quinchos y Cocinas Exteriores"),
        ("estructuras", "Estructuras y Carpintería"),
        ("pintura", "Pintura"),
        ("pavimentos", "Pavimentos"),
    ]
    PLACEMENT_CHOICES = [
        ("gallery", "Galería de portafolio"),
        ("hero_bg", "Fondo del hero (portada)"),
        ("build_project", 'Panel "¿Qué quieres construir?" — Un proyecto nuevo'),
        ("build_remodel", 'Panel "¿Qué quieres construir?" — Una remodelación'),
        ("build_quote", 'Panel "¿Qué quieres construir?" — Una cotización'),
    ]

    image = models.ImageField("Foto", upload_to="gallery/")
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
        verbose_name = "Foto"
        verbose_name_plural = "Fotos"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title or f"Foto #{self.pk}"


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
