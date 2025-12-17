import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Создает резервную копию базы данных PostgreSQL.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем процесс резервного копирования...'))

        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')

        command = [
            'pg_dump',
            f'--dbname=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
            '-f',
            backup_file,
            '--clean',
            '--no-owner',
            '--no-privileges'
        ]

        try:
            process = subprocess.Popen(command)
            process.wait()

            if process.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f'Резервная копия успешно создана: {backup_file}'))
            else:
                self.stdout.write(self.style.ERROR('Произошла ошибка при создании резервной копии.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                'Ошибка: команда "pg_dump" не найдена. '
                'Убедитесь, что PostgreSQL установлен и путь к его bin-директории добавлен в системный PATH.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла непредвиденная ошибка: {e}'))