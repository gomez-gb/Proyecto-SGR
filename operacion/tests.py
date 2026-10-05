import datetime
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Actividad, Auditoria, Compromiso, Evidencia, Perfil


def _archivo_jpg(nombre="evidencia.jpg"):
    return SimpleUploadedFile(nombre, b"contenido-de-prueba", content_type="image/jpeg")


class RegistrarActividadTests(TestCase):
    """HU-01/HU-09/HU-10: registro de actividad + evidencia en una sola pantalla (Wireframe1)."""

    def setUp(self):
        self.funcionario = User.objects.create_user("func_test", password="x")
        Perfil.objects.create(usuario=self.funcionario, rol=Perfil.Rol.FUNCIONARIO)
        self.client.force_login(self.funcionario)
        self.datos_validos = {
            "fecha": "2026-10-04",
            "item": "OTRO",
            "solicitud_problema": "Descripción de prueba",
            "accion_realizada": "Acción de prueba",
            "contacto": "",
            "telefono": "",
        }

    def test_registro_valido_crea_actividad_y_evidencia(self):
        respuesta = self.client.post(
            reverse("operacion:registrar_actividad"),
            {**self.datos_validos, "archivo": _archivo_jpg()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("redirect", json.loads(respuesta.content))
        self.assertEqual(Actividad.objects.count(), 1)
        actividad = Actividad.objects.first()
        self.assertTrue(actividad.evidencia.archivo)
        self.assertTrue(actividad.evidencia.codigo)

    def test_fecha_invalida_no_crea_nada_y_devuelve_error_json(self):
        datos = {**self.datos_validos, "fecha": "0009-09-09", "archivo": _archivo_jpg()}
        respuesta = self.client.post(
            reverse("operacion:registrar_actividad"), datos, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(respuesta.status_code, 400)
        errores = json.loads(respuesta.content)["errors"]
        self.assertIn("fecha", errores)
        self.assertEqual(Actividad.objects.count(), 0)

    def test_extension_no_permitida_no_crea_nada(self):
        archivo_malo = SimpleUploadedFile("malware.exe", b"x", content_type="application/octet-stream")
        respuesta = self.client.post(
            reverse("operacion:registrar_actividad"),
            {**self.datos_validos, "archivo": archivo_malo},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("archivo", json.loads(respuesta.content)["errors"])
        self.assertEqual(Actividad.objects.count(), 0)

    def test_verificador_no_puede_registrar_actividad(self):
        verificador = User.objects.create_user("verif_test", password="x")
        Perfil.objects.create(usuario=verificador, rol=Perfil.Rol.VERIFICADOR)
        self.client.force_login(verificador)
        respuesta = self.client.get(reverse("operacion:registrar_actividad"))
        self.assertEqual(respuesta.status_code, 403)


class ValidarEvidenciaTests(TestCase):
    """HU-11: validación de evidencia por el Verificador."""

    def setUp(self):
        funcionario = User.objects.create_user("func_test2", password="x")
        Perfil.objects.create(usuario=funcionario, rol=Perfil.Rol.FUNCIONARIO)
        self.verificador = User.objects.create_user("verif_test2", password="x")
        Perfil.objects.create(usuario=self.verificador, rol=Perfil.Rol.VERIFICADOR)

        self.actividad = Actividad.objects.create(
            funcionario=funcionario,
            fecha=datetime.date(2026, 10, 4),
            item=Actividad.Item.OTRO,
            solicitud_problema="x",
            accion_realizada="x",
        )
        self.evidencia = Evidencia.objects.create(actividad=self.actividad, archivo=_archivo_jpg(), estado_revision="pendiente")

    def test_pantalla_de_validacion_no_tiene_opcion_en_blanco(self):
        # Django genera automaticamente una opcion vacia para ChoiceField sin
        # default ("- Select an option -"); decision se declara explicito en
        # el form justamente para que esto no vuelva a aparecer.
        self.client.force_login(self.verificador)
        respuesta = self.client.get(reverse("operacion:validar_evidencia", args=[self.evidencia.pk]))
        self.assertNotContains(respuesta, "Select an option")
        self.assertContains(respuesta, 'value="APROBADO"')

    def test_rechazar_sin_observacion_falla(self):
        self.client.force_login(self.verificador)
        respuesta = self.client.post(
            reverse("operacion:validar_evidencia", args=[self.evidencia.pk]),
            {"decision": "RECHAZADO", "observacion": ""},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.evidencia.refresh_from_db()
        self.assertEqual(self.evidencia.estado_revision, "pendiente")

    def test_aprobar_actualiza_estados(self):
        self.client.force_login(self.verificador)
        respuesta = self.client.post(
            reverse("operacion:validar_evidencia", args=[self.evidencia.pk]),
            {"decision": "APROBADO", "observacion": ""},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.evidencia.refresh_from_db()
        self.actividad.refresh_from_db()
        self.assertEqual(self.evidencia.estado_revision, "aprobada")
        self.assertEqual(self.actividad.estado, "validada")

    def test_aprobar_registra_auditoria(self):
        self.client.force_login(self.verificador)
        self.client.post(
            reverse("operacion:validar_evidencia", args=[self.evidencia.pk]),
            {"decision": "APROBADO", "observacion": ""},
        )
        evento = Auditoria.objects.filter(entidad_afectada="Evidencia", id_registro=str(self.evidencia.pk)).first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.valor_nuevo, "aprobada")


class AgendaCompartidaTests(TestCase):
    """HU-12 (agenda compartida), HU-13 (cambio de estado con historial), HU-14 (seguimiento)."""

    def setUp(self):
        self.func1 = User.objects.create_user("agenda_func1", password="x")
        Perfil.objects.create(usuario=self.func1, rol=Perfil.Rol.FUNCIONARIO)
        self.func2 = User.objects.create_user("agenda_func2", password="x")
        Perfil.objects.create(usuario=self.func2, rol=Perfil.Rol.FUNCIONARIO)

        self.compromiso_ajeno = Compromiso.objects.create(
            responsable=self.func2,
            descripcion="Compromiso de otro funcionario",
            solicitante="Vecino",
            fecha_compromiso=datetime.date(2026, 10, 10),
        )

    def test_agenda_compartida_muestra_compromisos_de_todos(self):
        self.client.force_login(self.func1)
        respuesta = self.client.get(reverse("operacion:agenda_compartida"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Compromiso de otro funcionario")

    def test_cambiar_estado_de_compromiso_ajeno_y_queda_auditado(self):
        self.client.force_login(self.func1)
        respuesta = self.client.post(
            reverse("operacion:actualizar_estado_compromiso", args=[self.compromiso_ajeno.pk]),
            {"estado": "EN_PROCESO"},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.compromiso_ajeno.refresh_from_db()
        self.assertEqual(self.compromiso_ajeno.estado, "EN_PROCESO")

        evento = Auditoria.objects.filter(entidad_afectada="Compromiso", id_registro=str(self.compromiso_ajeno.pk)).first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.usuario, self.func1)
        self.assertEqual(evento.valor_anterior, "INGRESADO")
        self.assertEqual(evento.valor_nuevo, "EN_PROCESO")

    def test_verificador_no_accede_a_agenda_compartida(self):
        verificador = User.objects.create_user("agenda_verif", password="x")
        Perfil.objects.create(usuario=verificador, rol=Perfil.Rol.VERIFICADOR)
        self.client.force_login(verificador)
        respuesta = self.client.get(reverse("operacion:agenda_compartida"))
        self.assertEqual(respuesta.status_code, 403)


class InicioRedirectTests(TestCase):
    """Un usuario sin Perfil (ej. superusuario interno 'admin') no debe caer en un 403 confuso."""

    def test_staff_sin_perfil_va_al_admin_de_django(self):
        staff = User.objects.create_user("staff_sin_perfil", password="x", is_staff=True)
        self.client.force_login(staff)
        respuesta = self.client.get(reverse("operacion:inicio"), follow=True)
        self.assertEqual(respuesta.redirect_chain[-1][0], "/admin/")

    def test_usuario_sin_perfil_ni_staff_recibe_403_explicado(self):
        usuario = User.objects.create_user("sin_rol", password="x")
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("operacion:inicio"))
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_va_al_historial_de_auditoria(self):
        usuario = User.objects.create_user("inicio_admin_rol", password="x")
        Perfil.objects.create(usuario=usuario, rol=Perfil.Rol.ADMINISTRADOR)
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("operacion:inicio"), follow=True)
        self.assertEqual(respuesta.redirect_chain[-1][0], reverse("operacion:historial_auditoria"))


class HistorialAuditoriaTests(TestCase):
    """Pantalla propia del prototipo para 'Auditoría de cambios' (rol Administrador) — no el admin de Django."""

    def setUp(self):
        self.administrador = User.objects.create_user("auditor_admin", password="x")
        Perfil.objects.create(usuario=self.administrador, rol=Perfil.Rol.ADMINISTRADOR)
        self.funcionario = User.objects.create_user("auditor_func", password="x")
        Perfil.objects.create(usuario=self.funcionario, rol=Perfil.Rol.FUNCIONARIO)
        Auditoria.objects.create(
            usuario=self.funcionario,
            evento="alta",
            origen="test",
            entidad_afectada="Actividad",
            id_registro="1",
            valor_nuevo="registrada",
        )

    def test_administrador_ve_el_historial(self):
        self.client.force_login(self.administrador)
        respuesta = self.client.get(reverse("operacion:historial_auditoria"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "auditor_func")

    def test_staff_interno_sin_rol_administrador_no_accede(self):
        # 'admin' es de uso interno, no sustituye al rol Administrador del prototipo
        staff_interno = User.objects.create_user("staff_interno", password="x", is_staff=True)
        self.client.force_login(staff_interno)
        respuesta = self.client.get(reverse("operacion:historial_auditoria"))
        self.assertEqual(respuesta.status_code, 403)

    def test_funcionario_no_accede_al_historial(self):
        self.client.force_login(self.funcionario)
        respuesta = self.client.get(reverse("operacion:historial_auditoria"))
        self.assertEqual(respuesta.status_code, 403)
