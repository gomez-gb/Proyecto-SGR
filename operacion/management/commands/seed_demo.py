from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from operacion.models import Perfil

USUARIOS_DEMO = [
    ("funcionario1", "Test1234!", Perfil.Rol.FUNCIONARIO),
    ("verificador1", "Test1234!", Perfil.Rol.VERIFICADOR),
    ("administrador1", "Test1234!", Perfil.Rol.ADMINISTRADOR),
]


class Command(BaseCommand):
    help = "Crea/restaura los usuarios de demo (funcionario1, verificador1, administrador1, admin) con su Perfil correspondiente."

    def handle(self, *args, **options):
        for username, password, rol in USUARIOS_DEMO:
            user, creado = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.save()
            Perfil.objects.update_or_create(usuario=user, defaults={"rol": rol})
            estado = "creado" if creado else "actualizado"
            self.stdout.write(self.style.SUCCESS(f"{username} {estado} (rol={rol})"))

        # 'admin' es de uso interno (Django admin, datos, pruebas) - no tiene Perfil
        # ni es el rol Administrador del prototipo, ese es 'administrador1' arriba.
        admin, creado = User.objects.get_or_create(username="admin")
        admin.set_password("Test1234!")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        estado = "creado" if creado else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"admin {estado} (superusuario interno, acceso a /admin/)"))
