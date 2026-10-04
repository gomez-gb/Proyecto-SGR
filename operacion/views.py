from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActividadForm, CompromisoForm, EvidenciaForm, ValidacionForm
from .models import Actividad, Compromiso, Evidencia, Perfil


def _requiere_rol(rol_requerido):
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            perfil = getattr(request.user, "perfil", None)
            if not perfil or perfil.rol != rol_requerido:
                raise PermissionDenied(f"Esta acción requiere rol {rol_requerido}.")
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


requiere_funcionario = _requiere_rol(Perfil.Rol.FUNCIONARIO)
requiere_verificador = _requiere_rol(Perfil.Rol.VERIFICADOR)


@login_required
def inicio(request):
    perfil = getattr(request.user, "perfil", None)
    if perfil and perfil.rol == Perfil.Rol.VERIFICADOR:
        return redirect("operacion:lista_pendientes_validacion")
    return redirect("operacion:lista_actividades")


@requiere_funcionario
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


@requiere_funcionario
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


@requiere_funcionario
def lista_actividades(request):
    actividades = Actividad.objects.filter(funcionario=request.user).select_related("evidencia").order_by("-fecha")
    return render(request, "operacion/lista_actividades.html", {"actividades": actividades})


@requiere_funcionario
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


@requiere_funcionario
def lista_compromisos(request):
    compromisos = Compromiso.objects.filter(responsable=request.user).order_by("fecha_compromiso")
    return render(request, "operacion/lista_compromisos.html", {"compromisos": compromisos})


@requiere_verificador
def lista_pendientes_validacion(request):
    evidencias = (
        Evidencia.objects.filter(estado_revision="pendiente")
        .exclude(archivo="")
        .select_related("actividad", "actividad__funcionario")
        .order_by("fecha_registro")
    )
    return render(request, "operacion/lista_pendientes_validacion.html", {"evidencias": evidencias})


@requiere_verificador
def validar_evidencia(request, pk):
    evidencia = get_object_or_404(Evidencia, pk=pk)
    if not evidencia.archivo:
        messages.error(request, "Esta evidencia todavía no tiene archivo adjunto.")
        return redirect("operacion:lista_pendientes_validacion")

    if request.method == "POST":
        form = ValidacionForm(request.POST)
        if form.is_valid():
            validacion = form.save(commit=False)
            validacion.evidencia = evidencia
            validacion.verificador = request.user
            validacion.save()

            if validacion.decision == validacion.Decision.APROBADO:
                evidencia.estado_revision = "aprobada"
                evidencia.actividad.estado = "validada"
            elif validacion.decision == validacion.Decision.RECHAZADO:
                evidencia.estado_revision = "rechazada"
                evidencia.actividad.estado = "rechazada"
            else:
                evidencia.estado_revision = "correccion_solicitada"
                evidencia.actividad.estado = "correccion_solicitada"
            evidencia.save()
            evidencia.actividad.save()

            messages.success(request, f"Evidencia {evidencia.codigo}: {validacion.get_decision_display()}.")
            return redirect("operacion:lista_pendientes_validacion")
    else:
        form = ValidacionForm()
    return render(request, "operacion/validar_evidencia.html", {"form": form, "evidencia": evidencia})
