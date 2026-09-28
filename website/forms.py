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
    ("ley-ductos", "Ley de Ductos (RIT)"),
    ("ccdd", "Corrientes débiles y seguridad (CCDD)"),
    ("otro", "Otro"),
]


class ContactForm(forms.ModelForm):
    service = forms.ChoiceField(
        label="Servicio de interés", choices=SERVICE_CHOICES, required=False
    )
    # Honeypot: hidden from real visitors via CSS, so only bots fill it in.
    # A non-empty value marks the submission as spam without tipping off
    # the bot (the view still shows the normal "thanks" message).
    website = forms.CharField(required=False, widget=forms.HiddenInput())

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

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))


MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


class GalleryImageUploadForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["image", "title", "category", "placement"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej: Fachada casa Vitacura"}),
        }

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError("La foto no puede pesar más de 10 MB.")
        return image


class GalleryImageEditForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["title", "category", "placement", "is_active", "order"]
