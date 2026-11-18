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
    ("consulta", "Consulta general"),
    ("trabajo", "Quiero trabajar con ustedes"),
    ("otro", "Otro"),
]

MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CV_EXTENSIONS = ("pdf", "doc", "docx")


class ContactForm(forms.ModelForm):
    service = forms.ChoiceField(
        label="Servicio de interés", choices=SERVICE_CHOICES, required=False
    )
    cv = forms.FileField(
        label="Currículum Vitae (Opcional)",
        required=False,
        widget=forms.FileInput(
            attrs={
                "accept": ".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            }
        ),
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

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")
        if not cv:
            return cv
        ext = cv.name.rsplit(".", 1)[-1].lower() if "." in cv.name else ""
        if ext not in ALLOWED_CV_EXTENSIONS:
            raise forms.ValidationError(
                "Formato no válido. Adjunta tu CV en PDF o Word (.pdf, .doc, .docx)."
            )
        if cv.size > MAX_CV_SIZE:
            raise forms.ValidationError("El CV no puede pesar más de 5 MB.")
        return cv

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))

    def save(self, commit=True):
        instance = super().save(commit=False)
        cv = self.cleaned_data.get("cv")
        if cv and hasattr(instance, "cv"):
            instance.cv = cv
        if commit:
            instance.save()
        return instance


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "webp", "avif", "gif")
ALLOWED_VIDEO_EXTENSIONS = ("mp4", "webm", "mov", "m4v", "ogg")


class GalleryImageUploadForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["image", "title", "category", "placement"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ej: Fachada casa Vitacura"}),
            "image": forms.FileInput(
                attrs={
                    "accept": "image/*,video/mp4,video/webm,video/quicktime,video/ogg",
                }
            ),
        }

    def clean_image(self):
        media = self.cleaned_data["image"]
        ext = media.name.rsplit(".", 1)[-1].lower() if "." in media.name else ""
        if ext in ALLOWED_VIDEO_EXTENSIONS:
            if media.size > MAX_VIDEO_SIZE:
                raise forms.ValidationError("El video no puede pesar más de 50 MB.")
            return media
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            if media.size > MAX_IMAGE_SIZE:
                raise forms.ValidationError("La foto no puede pesar más de 10 MB.")
            return media
        raise forms.ValidationError(
            "Formato no compatible. Usa imágenes (JPG, PNG, WebP) o videos (MP4, WebM, MOV)."
        )


class GalleryImageEditForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["title", "category", "placement", "is_active", "order"]