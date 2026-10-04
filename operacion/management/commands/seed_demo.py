from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from operacion.models import Perfil

USUARIOS_DEMO = [
    ("funcionario1", "sgr-demo-2026", Perfil.Rol.FUNCIONARIO),
    ("verificador1", "sgr-demo-2026", Perfil.Rol.VERIFICADOR),
]


class Command(BaseCommand):
    help = "Crea/restaura los usuarios de demo (funcionario1, verificador1) con su Perfil correspondiente."

    def handle(self, *args, **options):
        for username, password, rol in USUARIOS_DEMO:
            user, creado = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.save()
            Perfil.objects.update_or_create(usuario=user, defaults={"rol": rol})
            estado = "creado" if creado else "actualizado"
            self.stdout.write(self.style.SUCCESS(f"{username} {estado} (rol={rol})"))
