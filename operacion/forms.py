from django import forms

from .models import Actividad, Compromiso, Evidencia

EXTENSIONES_PERMITIDAS = ("jpg", "jpeg", "png", "pdf")
TAMANO_MAXIMO_MB = 5


class EstiloBootstrapMixin:
    """Agrega clases de Bootstrap a cada campo — mismo formulario, mejor usabilidad/responsive."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-control")


class ActividadForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ["solicitud_problema", "accion_realizada", "contacto", "telefono", "servicio", "agenda_colectiva"]
        widgets = {
            "accion_realizada": forms.Textarea(attrs={"rows": 3}),
        }


class EvidenciaForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ["archivo"]

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        extension = archivo.name.rsplit(".", 1)[-1].lower()
        if extension not in EXTENSIONES_PERMITIDAS:
            raise forms.ValidationError(
                f"Formato no permitido (.{extension}). Usa: {', '.join(EXTENSIONES_PERMITIDAS)}."
            )
        if archivo.size > TAMANO_MAXIMO_MB * 1024 * 1024:
            raise forms.ValidationError(f"El archivo supera el máximo de {TAMANO_MAXIMO_MB} MB.")
        return archivo


class CompromisoForm(EstiloBootstrapMixin, forms.ModelForm):
    class Meta:
        model = Compromiso
        fields = ["descripcion", "solicitante", "territorio", "area_apoyo", "origen", "fecha_compromiso"]
        widgets = {
            "fecha_compromiso": forms.DateInput(attrs={"type": "date"}),
        }
