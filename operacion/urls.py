from django.urls import path

from . import views

app_name = "operacion"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("actividades/", views.lista_actividades, name="lista_actividades"),
    path("actividades/nueva/", views.registrar_actividad, name="registrar_actividad"),
    path("actividades/<int:pk>/", views.detalle_actividad, name="detalle_actividad"),
    path("actividades/<int:pk>/evidencia/", views.subir_evidencia, name="subir_evidencia"),
    path("compromisos/", views.lista_compromisos, name="lista_compromisos"),
    path("compromisos/nuevo/", views.registrar_compromiso, name="registrar_compromiso"),
    path("compromisos/agenda/", views.agenda_compartida, name="agenda_compartida"),
    path("compromisos/<int:pk>/estado/", views.actualizar_estado_compromiso, name="actualizar_estado_compromiso"),
    path("validaciones/", views.lista_pendientes_validacion, name="lista_pendientes_validacion"),
    path("validaciones/<int:pk>/", views.validar_evidencia, name="validar_evidencia"),
]
