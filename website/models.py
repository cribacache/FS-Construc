from django.db import models


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
