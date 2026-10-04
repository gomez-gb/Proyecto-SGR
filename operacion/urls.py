from django.urls import path

from . import views

app_name = "operacion"

urlpatterns = [
    path("actividades/", views.lista_actividades, name="lista_actividades"),
    path("actividades/nueva/", views.registrar_actividad, name="registrar_actividad"),
    path("actividades/<int:pk>/", views.detalle_actividad, name="detalle_actividad"),
    path("actividades/<int:pk>/evidencia/", views.subir_evidencia, name="subir_evidencia"),
    path("compromisos/", views.lista_compromisos, name="lista_compromisos"),
    path("compromisos/nuevo/", views.registrar_compromiso, name="registrar_compromiso"),
]
