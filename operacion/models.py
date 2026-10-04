import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Perfil(models.Model):
    class Rol(models.TextChoices):
        FUNCIONARIO = "FUNCIONARIO", "Funcionario"
        VERIFICADOR = "VERIFICADOR", "Verificador"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=20, choices=Rol.choices)

    def __str__(self):
        return f"{self.usuario.get_username()} ({self.get_rol_display()})"


class Actividad(models.Model):
    class Item(models.TextChoices):
        ALUMBRADO_PUBLICO = "ALUMBRADO_PUBLICO", "Alumbrado público"
        ATENCION_SOCIAL = "ATENCION_SOCIAL", "Atención social"
        INFRAESTRUCTURA = "INFRAESTRUCTURA", "Infraestructura y mantención"
        ASEO_ORNATO = "ASEO_ORNATO", "Aseo y ornato"
        OTRO = "OTRO", "Otro"

    funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="actividades")
    fecha = models.DateField(default=timezone.localdate)
    item = models.CharField(max_length=30, choices=Item.choices)
    solicitud_problema = models.TextField()
    accion_realizada = models.CharField(max_length=255)
    contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    servicio = models.CharField(max_length=100, blank=True)
    agenda_colectiva = models.BooleanField(default=False)
    estado = models.CharField(max_length=30, default="registrada")

    def __str__(self):
        return f"Actividad #{self.pk} — {self.solicitud_problema[:50]}"


class Evidencia(models.Model):
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, related_name="evidencia")
    codigo = models.CharField(max_length=12, unique=True, editable=False)
    archivo = models.FileField(upload_to="evidencias/%Y/%m/", blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado_revision = models.CharField(max_length=30, default="sin_archivo")
    metadatos = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidencia {self.codigo}"


class Validacion(models.Model):
    class Decision(models.TextChoices):
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        SOLICITA_CORRECCION = "SOLICITA_CORRECCION", "Solicita corrección"

    evidencia = models.ForeignKey(Evidencia, on_delete=models.CASCADE, related_name="validaciones")
    verificador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="validaciones_realizadas")
    decision = models.CharField(max_length=25, choices=Decision.choices)
    observacion = models.TextField(blank=True)
    fecha_validacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Validación de {self.evidencia.codigo} — {self.get_decision_display()}"


class Compromiso(models.Model):
    class Estado(models.TextChoices):
        INGRESADO = "INGRESADO", "Ingresado"
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        REALIZADO = "REALIZADO", "Realizado"

    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="compromisos")
    descripcion = models.CharField(max_length=255)
    solicitante = models.CharField(max_length=150)
    territorio = models.CharField(max_length=150, blank=True)
    area_apoyo = models.CharField(max_length=150, blank=True)
    origen = models.CharField(max_length=20, default="interna")
    fecha_compromiso = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.INGRESADO)
    observacion = models.TextField(blank=True)

    def esta_vencido(self):
        return self.estado != self.Estado.REALIZADO and self.fecha_compromiso < timezone.now().date()

    def __str__(self):
        return f"Compromiso #{self.pk} — {self.descripcion}"
