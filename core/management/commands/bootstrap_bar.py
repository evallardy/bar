from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea roles base y el usuario administrador inicial del sistema.'

    def handle(self, *args, **options):
        for group_name in ['administrador', 'empleados']:
            Group.objects.get_or_create(name=group_name)

        user_model = get_user_model()
        admin_user, created = user_model.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'admin@bar.local',
            },
        )
        if created:
            admin_user.set_password('Admin12345!')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Usuario admin creado.'))
        else:
            self.stdout.write(self.style.WARNING('El usuario admin ya existia.'))

        admin_group = Group.objects.get(name='administrador')
        admin_user.groups.add(admin_group)
        self.stdout.write(self.style.SUCCESS('Roles base verificados correctamente.'))