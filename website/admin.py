from django.contrib import admin
from django.utils.html import format_html

from .models import ContactMessage, GalleryImage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "title", "category", "placement", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("category", "placement", "is_active")
    search_fields = ("title",)
    fields = ("image", "preview", "title", "category", "placement", "is_active", "order")
    readonly_fields = ("preview",)

    @admin.display(description="Foto")
    def thumbnail(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height:48px;width:64px;object-fit:cover;border-radius:4px;">',
            obj.image.url,
        )

    @admin.display(description="Vista previa")
    def preview(self, obj):
        if not obj.image:
            return "Sube una imagen y guarda para ver la vista previa."
        return format_html(
            '<img src="{}" style="max-height:280px;max-width:100%;border-radius:8px;">',
            obj.image.url,
        )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "service", "created_at")
    list_filter = ("service", "created_at")
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at",)
