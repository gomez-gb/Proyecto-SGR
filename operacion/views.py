from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActividadForm, CompromisoForm, EvidenciaForm
from .models import Actividad, Compromiso


@login_required
def registrar_actividad(request):
    if request.method == "POST":
        actividad_form = ActividadForm(request.POST)
        evidencia_form = EvidenciaForm(request.POST, request.FILES)
        if actividad_form.is_valid() and evidencia_form.is_valid():
            with transaction.atomic():
                actividad = actividad_form.save(commit=False)
                actividad.funcionario = request.user
                actividad.save()
                evidencia = evidencia_form.save(commit=False)
                evidencia.actividad = actividad
                evidencia.save()
            return redirect("operacion:detalle_actividad", pk=actividad.pk)
    else:
        actividad_form = ActividadForm()
        evidencia_form = EvidenciaForm()
    return render(
        request,
        "operacion/registrar_actividad.html",
        {"actividad_form": actividad_form, "evidencia_form": evidencia_form},
    )


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
