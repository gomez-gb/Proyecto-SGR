import datetime

from django import forms
from django.utils import timezone

from .models import Actividad, Compromiso, Evidencia

EXTENSIONES_PERMITIDAS = ("jpg", "jpeg", "png", "pdf")
TAMANO_MAXIMO_MB = 5
FECHA_MINIMA = datetime.date(2020, 1, 1)


def _widget_fecha(minimo, maximo):
    return forms.DateInput(attrs={"type": "date", "min": minimo.isoformat(), "max": maximo.isoformat()})


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
        fields = ["fecha", "item", "solicitud_problema", "accion_realizada", "contacto", "telefono", "agenda_colectiva"]
        widgets = {
            "fecha": _widget_fecha(FECHA_MINIMA, timezone.localdate()),
            "solicitud_problema": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha < FECHA_MINIMA:
            raise forms.ValidationError(f"La fecha no puede ser anterior a {FECHA_MINIMA.strftime('%d/%m/%Y')}.")
        if fecha > timezone.localdate():
            raise forms.ValidationError("La fecha de una actividad no puede ser futura.")
        return fecha


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
            "fecha_compromiso": _widget_fecha(
                timezone.localdate() - datetime.timedelta(days=30),
                timezone.localdate() + datetime.timedelta(days=730),
            ),
        }

    def clean_fecha_compromiso(self):
        fecha = self.cleaned_data["fecha_compromiso"]
        minimo = timezone.localdate() - datetime.timedelta(days=30)
        maximo = timezone.localdate() + datetime.timedelta(days=730)
        if fecha < minimo or fecha > maximo:
            raise forms.ValidationError(
                f"La fecha debe estar entre {minimo.strftime('%d/%m/%Y')} y {maximo.strftime('%d/%m/%Y')}."
            )
        return fecha
