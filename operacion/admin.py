from django.contrib import admin

from .models import Actividad, Auditoria, Compromiso, Evidencia, Perfil, Validacion


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


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "evento", "entidad_afectada", "id_registro", "valor_anterior", "valor_nuevo")
    list_filter = ("evento", "entidad_afectada")
    readonly_fields = [f.name for f in Auditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
