from django import forms

from .models import ContactMessage, GalleryImage

SERVICE_CHOICES = [
    ("", "Selecciona un servicio"),
    ("diseno-construccion", "Diseño y construcción"),
    ("remodelaciones", "Remodelaciones interiores / exteriores"),
    ("cocinas-muebles", "Cocinas, cubiertas y muebles personalizados"),
    ("revestimientos", "Revestimientos y fachadas"),
    ("pergolas-terrazas", "Pérgolas, jardineras y terrazas"),
    ("pintura", "Pintura interior / exterior"),
    ("pavimentos", "Pavimentos y estampados de hormigón"),
    ("estructuras", "Estructuras metálicas"),
    ("otro", "Otro"),
]


class ContactForm(forms.ModelForm):
    service = forms.ChoiceField(
        label="Servicio de interés", choices=SERVICE_CHOICES, required=False
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "service", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Tu nombre"}),
            "email": forms.EmailInput(attrs={"placeholder": "tucorreo@ejemplo.com"}),
            "phone": forms.TextInput(attrs={"placeholder": "+56 9 1234 5678"}),
            "message": forms.Textarea(
                attrs={"placeholder": "Cuéntanos sobre tu proyecto...", "rows": 5}
            ),
        }


class GalleryImageUploadForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["image", "title", "category", "placement"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej: Fachada casa Vitacura"}),
        }


class GalleryImageEditForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["title", "category", "placement", "is_active", "order"]
        widgets = {
            "order": forms.NumberInput(attrs={"style": "width:70px"}),
        }
