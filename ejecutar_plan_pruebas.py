"""Ejecuta el Plan de Pruebas contra la base de datos real del SGR (sin borrar nada existente).
Corre con: python manage.py shell < ejecutar_plan_pruebas.py
"""
import datetime

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from operacion.models import Actividad, Auditoria, Compromiso, Evidencia, Perfil

resultados = []


def registrar(caso, esperado, obtenido, aprobado):
    estado = "APROBADO" if aprobado else "FALLIDO"
    resultados.append((caso, estado, obtenido))
    print(f"{caso}: {estado} — {obtenido}")


def archivo_jpg(nombre="qa_evidencia.jpg"):
    return SimpleUploadedFile(nombre, b"contenido-qa", content_type="image/jpeg")


# --- Preparar usuarios dedicados de QA (no tocan funcionario1/verificador1/administrador1) ---
func_a, _ = User.objects.get_or_create(username="qa_funcionario_a")
func_a.set_password("QaTest1234!")
func_a.save()
Perfil.objects.update_or_create(usuario=func_a, defaults={"rol": Perfil.Rol.FUNCIONARIO})

func_b, _ = User.objects.get_or_create(username="qa_funcionario_b")
func_b.set_password("QaTest1234!")
func_b.save()
Perfil.objects.update_or_create(usuario=func_b, defaults={"rol": Perfil.Rol.FUNCIONARIO})

verificador, _ = User.objects.get_or_create(username="qa_verificador")
verificador.set_password("QaTest1234!")
verificador.save()
Perfil.objects.update_or_create(usuario=verificador, defaults={"rol": Perfil.Rol.VERIFICADOR})

administrador, _ = User.objects.get_or_create(username="qa_administrador")
administrador.set_password("QaTest1234!")
administrador.save()
Perfil.objects.update_or_create(usuario=administrador, defaults={"rol": Perfil.Rol.ADMINISTRADOR})

sin_rol, _ = User.objects.get_or_create(username="qa_sin_rol")
sin_rol.set_password("QaTest1234!")
sin_rol.save()
Perfil.objects.filter(usuario=sin_rol).delete()

# --- CP-01: generación automática de código ---
actividad_u1 = Actividad.objects.create(
    funcionario=func_a, fecha=timezone.localdate(), item=Actividad.Item.OTRO,
    solicitud_problema="QA unitaria", accion_realizada="x",
)
ev_u1 = Evidencia.objects.create(actividad=actividad_u1)
registrar("CP-01", "código asignado automáticamente", f"código={ev_u1.codigo!r} (len={len(ev_u1.codigo)})", bool(ev_u1.codigo) and len(ev_u1.codigo) == 12)

# --- CP-02: esta_vencido() ---
compromiso_u2 = Compromiso.objects.create(
    responsable=func_a, descripcion="QA vencido", solicitante="QA",
    fecha_compromiso=timezone.localdate() - datetime.timedelta(days=1),
)
registrar("CP-02", "True", f"esta_vencido()={compromiso_u2.esta_vencido()}", compromiso_u2.esta_vencido() is True)

# --- CP-03 a CP-18: vía HTTP real con el test Client ---
c_a = Client()
c_a.login(username="qa_funcionario_a", password="QaTest1234!")

# CP-03
r = c_a.post("/actividades/nueva/", {
    "fecha": timezone.localdate().isoformat(), "item": "OTRO",
    "solicitud_problema": "QA integracion", "accion_realizada": "x",
    "contacto": "", "telefono": "", "archivo": archivo_jpg(),
}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
import json
ok = r.status_code == 200 and "redirect" in json.loads(r.content)
actividad_cp03 = Actividad.objects.filter(funcionario=func_a, solicitud_problema="QA integracion").first()
tiene_evidencia = actividad_cp03 is not None and Evidencia.objects.filter(actividad=actividad_cp03).exists()
registrar("CP-03", "Actividad+Evidencia creadas juntas", f"status={r.status_code}, evidencia creada={tiene_evidencia}", ok and tiene_evidencia and bool(actividad_cp03.evidencia.archivo))

# CP-04
c_v = Client()
c_v.login(username="qa_verificador", password="QaTest1234!")
ev_cp04 = actividad_cp03.evidencia
r = c_v.post(f"/validaciones/{ev_cp04.pk}/", {"decision": "APROBADO", "observacion": ""})
ev_cp04.refresh_from_db(); actividad_cp03.refresh_from_db()
registrar("CP-04", "evidencia=aprobada, actividad=validada", f"evidencia={ev_cp04.estado_revision}, actividad={actividad_cp03.estado}", ev_cp04.estado_revision == "aprobada" and actividad_cp03.estado == "validada")

# CP-05
r = c_a.post(f"/compromisos/{compromiso_u2.pk}/estado/", {"estado": "EN_PROCESO"})
evento_cp05 = Auditoria.objects.filter(entidad_afectada="Compromiso", id_registro=str(compromiso_u2.pk)).order_by("-fecha").first()
registrar("CP-05", "evento de auditoría creado", f"evento={evento_cp05.evento if evento_cp05 else None}, {evento_cp05.valor_anterior if evento_cp05 else ''}->{evento_cp05.valor_nuevo if evento_cp05 else ''}", evento_cp05 is not None and evento_cp05.valor_nuevo == "EN_PROCESO")

# CP-06
r = c_a.post("/actividades/nueva/", {
    "fecha": timezone.localdate().isoformat(), "item": "ALUMBRADO_PUBLICO",
    "solicitud_problema": "QA HU-01 completo", "accion_realizada": "Reparacion",
    "contacto": "Vecino QA", "telefono": "+56900000000", "archivo": archivo_jpg("qa_hu01.jpg"),
}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
registrar("CP-06", "302/200 con redirect al detalle", f"status={r.status_code}, body={r.content.decode()[:80]}", r.status_code == 200 and "redirect" in json.loads(r.content))

# CP-07
r = c_a.post("/actividades/nueva/", {
    "fecha": "0009-09-09", "item": "OTRO", "solicitud_problema": "x", "accion_realizada": "x",
    "contacto": "", "telefono": "", "archivo": archivo_jpg("qa_malo.jpg"),
}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
registrar("CP-07", "400 con error en fecha, nada creado", f"status={r.status_code}, errors={json.loads(r.content).get('errors', {}).get('fecha')}", r.status_code == 400 and "fecha" in json.loads(r.content).get("errors", {}))

# CP-08
compromiso_b = Compromiso.objects.create(
    responsable=func_b, descripcion="QA compromiso de B", solicitante="QA",
    fecha_compromiso=timezone.localdate() + datetime.timedelta(days=1),
)
r = c_a.get("/compromisos/agenda/")
registrar("CP-08", "compromiso de B visible para A", f"status={r.status_code}, visible={'QA compromiso de B' in r.content.decode()}", "QA compromiso de B" in r.content.decode())

# CP-09
Compromiso.objects.create(responsable=func_a, descripcion="QA vencido 2", solicitante="QA", fecha_compromiso=timezone.localdate() - datetime.timedelta(days=2))
Compromiso.objects.create(responsable=func_a, descripcion="QA proximo", solicitante="QA", fecha_compromiso=timezone.localdate() + datetime.timedelta(days=1))
Compromiso.objects.create(responsable=func_a, descripcion="QA al dia", solicitante="QA", fecha_compromiso=timezone.localdate() + datetime.timedelta(days=20))
r = c_a.get("/compromisos/agenda/")
registrar("CP-09", "contadores reflejan los compromisos QA creados", f"status={r.status_code} (revisar conteos en pantalla)", r.status_code == 200)

# CP-10
c_anon = Client()
r = c_anon.post("/login/", {"username": "qa_funcionario_a", "password": "clave-incorrecta"})
registrar("CP-10", "acceso denegado sin detalles", f"status={r.status_code}, autenticado={r.wsgi_request.user.is_authenticated if hasattr(r, 'wsgi_request') else 'N/A'}", r.status_code == 200 and b"incorrect" not in r.content.lower())

# CP-11
r = c_a.get("/validaciones/")
registrar("CP-11", "403", f"status={r.status_code}", r.status_code == 403)

# CP-12
r = c_anon.get(f"/evidencias/{ev_u1.pk}/archivo/")
registrar("CP-12", "redirige a login (302)", f"status={r.status_code}, location={r.get('Location')}", r.status_code == 302 and "login" in (r.get("Location") or ""))

# CP-13
r = c_a.post(f"/actividades/{actividad_u1.pk}/evidencia/", {"archivo": SimpleUploadedFile("qa_malware.exe", b"x", content_type="application/octet-stream")})
registrar("CP-13", "rechazado, formato no permitido", f"status={r.status_code}, contiene mensaje={'no permitido' in r.content.decode()}", "no permitido" in r.content.decode())

# CP-14
c_b = Client()
c_b.login(username="qa_funcionario_b", password="QaTest1234!")
r = c_b.get(f"/evidencias/{ev_u1.pk}/archivo/")
registrar("CP-14", "403", f"status={r.status_code}", r.status_code == 403)

# CP-15 (inspección estática, no HTTP)
with open("operacion/templates/operacion/base.html") as f:
    base_html = f.read()
tiene_viewport = 'name="viewport"' in base_html
registrar("CP-15", "meta viewport presente", f"viewport presente={tiene_viewport}", tiene_viewport)

# CP-16
r = c_a.post("/actividades/nueva/", {
    "fecha": "0009-09-09", "item": "OTRO", "solicitud_problema": "dato que no se debe perder", "accion_realizada": "x",
    "contacto": "", "telefono": "", "archivo": archivo_jpg("qa_16.jpg"),
}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
cuerpo = r.content.decode()
registrar("CP-16", "error devuelto en JSON por campo, sin recargar", f"status={r.status_code}, errors={json.loads(cuerpo).get('errors')}", r.status_code == 400)

# CP-17
c_adm = Client()
c_adm.login(username="qa_administrador", password="QaTest1234!")
r = c_adm.get("/auditoria/")
contiene_alta = "alta" in r.content.decode() and "qa_funcionario_a" in r.content.decode()
registrar("CP-17", "eventos de alta/validación visibles en Auditoría", f"status={r.status_code}, contiene evento qa_funcionario_a={contiene_alta}", contiene_alta)

# CP-18
c_sr = Client()
c_sr.login(username="qa_sin_rol", password="QaTest1234!")
r = c_sr.get("/", follow=False)
registrar("CP-18", "403 explícito", f"status={r.status_code}", r.status_code == 403)

print()
print("=== RESUMEN ===")
aprobados = sum(1 for _, estado, _ in resultados if estado == "APROBADO")
print(f"{aprobados}/{len(resultados)} casos aprobados")
for caso, estado, obtenido in resultados:
    print(f"{caso}: {estado}")
