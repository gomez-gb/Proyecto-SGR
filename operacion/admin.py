from django.contrib import admin

from .models import Actividad, Compromiso, Evidencia, Perfil, Validacion


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol")


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ("id", "funcionario", "fecha", "item", "estado")
    list_filter = ("estado", "item", "agenda_colectiva")


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "actividad", "estado_revision", "fecha_registro")
    list_filter = ("estado_revision",)
    readonly_fields = ("codigo",)


@admin.register(Validacion)
class ValidacionAdmin(admin.ModelAdmin):
    list_display = ("evidencia", "verificador", "decision", "fecha_validacion")
    list_filter = ("decision",)


@admin.register(Compromiso)
class CompromisoAdmin(admin.ModelAdmin):
    list_display = ("id", "descripcion", "responsable", "estado", "fecha_compromiso")
    list_filter = ("estado",)
