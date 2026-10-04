from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActividadForm, CompromisoForm, EvidenciaForm
from .models import Actividad, Compromiso, Evidencia


@login_required
def registrar_actividad(request):
    if request.method == "POST":
        actividad_form = ActividadForm(request.POST)
        if actividad_form.is_valid():
            actividad = actividad_form.save(commit=False)
            actividad.funcionario = request.user
            actividad.save()
            Evidencia.objects.create(actividad=actividad)
            messages.info(request, "Actividad registrada. Ahora adjunta la evidencia.")
            return redirect("operacion:subir_evidencia", pk=actividad.pk)
    else:
        actividad_form = ActividadForm()
    return render(request, "operacion/registrar_actividad.html", {"actividad_form": actividad_form})


@login_required
def subir_evidencia(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk, funcionario=request.user)
    evidencia = actividad.evidencia
    if request.method == "POST":
        form = EvidenciaForm(request.POST, request.FILES, instance=evidencia)
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.estado_revision = "pendiente"
            evidencia.save()
            messages.success(request, "Evidencia adjuntada correctamente.")
            return redirect("operacion:detalle_actividad", pk=actividad.pk)
    else:
        form = EvidenciaForm(instance=evidencia)
    return render(request, "operacion/subir_evidencia.html", {"form": form, "actividad": actividad})


@login_required
def detalle_actividad(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if actividad.funcionario_id != request.user.id and not request.user.is_staff:
        return render(request, "operacion/sin_permiso.html", status=403)
    return render(request, "operacion/detalle_actividad.html", {"actividad": actividad})


@login_required
def lista_actividades(request):
    actividades = Actividad.objects.filter(funcionario=request.user).select_related("evidencia").order_by("-fecha")
    return render(request, "operacion/lista_actividades.html", {"actividades": actividades})


@login_required
def registrar_compromiso(request):
    if request.method == "POST":
        form = CompromisoForm(request.POST)
        if form.is_valid():
            compromiso = form.save(commit=False)
            compromiso.responsable = request.user
            compromiso.save()
            return redirect("operacion:lista_compromisos")
    else:
        form = CompromisoForm()
    return render(request, "operacion/registrar_compromiso.html", {"form": form})


@login_required
def lista_compromisos(request):
    compromisos = Compromiso.objects.filter(responsable=request.user).order_by("fecha_compromiso")
    return render(request, "operacion/lista_compromisos.html", {"compromisos": compromisos})
