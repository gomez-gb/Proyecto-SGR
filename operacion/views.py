import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ActividadForm, CompromisoForm, EvidenciaForm, ValidacionForm
from .models import Actividad, Compromiso, Evidencia, Perfil, registrar_evento


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


def _es_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@requiere_funcionario
def registrar_actividad(request):
    if request.method == "POST":
        actividad_form = ActividadForm(request.POST)
        evidencia_form = EvidenciaForm(request.POST, request.FILES)
        if actividad_form.is_valid() and evidencia_form.is_valid():
            actividad = actividad_form.save(commit=False)
            actividad.funcionario = request.user
            actividad.save()
            evidencia = evidencia_form.save(commit=False)
            evidencia.actividad = actividad
            evidencia.estado_revision = "pendiente"
            evidencia.save()
            registrar_evento(
                usuario=request.user,
                evento="alta",
                origen="registrar_actividad",
                entidad_afectada="Actividad",
                id_registro=actividad.pk,
                valor_nuevo=actividad.estado,
            )
            destino = reverse("operacion:detalle_actividad", args=[actividad.pk])
            if _es_ajax(request):
                return JsonResponse({"redirect": destino})
            messages.success(request, "Actividad y evidencia registradas correctamente.")
            return redirect(destino)
        if _es_ajax(request):
            errores = {**actividad_form.errors, **evidencia_form.errors}
            return JsonResponse({"errors": errores}, status=400)
    else:
        actividad_form = ActividadForm()
        evidencia_form = EvidenciaForm()
    return render(
        request,
        "operacion/registrar_actividad.html",
        {"actividad_form": actividad_form, "evidencia_form": evidencia_form},
    )


@requiere_funcionario
def subir_evidencia(request, pk):
    """Re-adjuntar evidencia cuando el Verificador solicitó corrección (HU-11)."""
    actividad = get_object_or_404(Actividad, pk=pk, funcionario=request.user)
    evidencia = actividad.evidencia
    if request.method == "POST":
        form = EvidenciaForm(request.POST, request.FILES, instance=evidencia)
        if form.is_valid():
            evidencia = form.save(commit=False)
            evidencia.estado_revision = "pendiente"
            evidencia.save()
            actividad.estado = "registrada"
            actividad.save()
            messages.success(request, "Evidencia actualizada correctamente.")
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


@requiere_funcionario
def agenda_compartida(request):
    """HU-12 (agenda compartida) + HU-14 (seguimiento): todos los compromisos, no solo los propios."""
    compromisos = Compromiso.objects.select_related("responsable").order_by("fecha_compromiso")

    estado = request.GET.get("estado")
    if estado:
        compromisos = compromisos.filter(estado=estado)

    hoy = timezone.localdate()
    proximos_dias = 3
    resumen = {
        "pendientes": compromisos.exclude(estado=Compromiso.Estado.REALIZADO).count(),
        "proximos_a_vencer": compromisos.filter(
            fecha_compromiso__gte=hoy,
            fecha_compromiso__lte=hoy + datetime.timedelta(days=proximos_dias),
        )
        .exclude(estado=Compromiso.Estado.REALIZADO)
        .count(),
        "vencidos": compromisos.filter(fecha_compromiso__lt=hoy).exclude(estado=Compromiso.Estado.REALIZADO).count(),
    }
    return render(
        request,
        "operacion/agenda_compartida.html",
        {"compromisos": compromisos, "resumen": resumen, "estados": Compromiso.Estado.choices, "estado_filtro": estado},
    )


@requiere_funcionario
def actualizar_estado_compromiso(request, pk):
    """HU-13: transición controlada de estados, con historial en Auditoria."""
    compromiso = get_object_or_404(Compromiso, pk=pk)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        estados_validos = dict(Compromiso.Estado.choices)
        if nuevo_estado in estados_validos:
            estado_anterior = compromiso.estado
            if estado_anterior != nuevo_estado:
                compromiso.estado = nuevo_estado
                compromiso.save()
                registrar_evento(
                    usuario=request.user,
                    evento="cambio_estado",
                    origen="actualizar_estado_compromiso",
                    entidad_afectada="Compromiso",
                    id_registro=compromiso.pk,
                    valor_anterior=estado_anterior,
                    valor_nuevo=nuevo_estado,
                )
                messages.success(request, f"Compromiso #{compromiso.pk}: {estados_validos[nuevo_estado]}.")
        else:
            messages.error(request, "Estado inválido.")
    return redirect("operacion:agenda_compartida")


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
            estado_anterior = evidencia.estado_revision
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
            registrar_evento(
                usuario=request.user,
                evento="validacion",
                origen="validar_evidencia",
                entidad_afectada="Evidencia",
                id_registro=evidencia.pk,
                valor_anterior=estado_anterior,
                valor_nuevo=evidencia.estado_revision,
            )

            messages.success(request, f"Evidencia {evidencia.codigo}: {validacion.get_decision_display()}.")
            return redirect("operacion:lista_pendientes_validacion")
    else:
        form = ValidacionForm()
    return render(request, "operacion/validar_evidencia.html", {"form": form, "evidencia": evidencia})
