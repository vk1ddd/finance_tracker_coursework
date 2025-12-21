import os
import requests
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Создает резервную копию БД и загружает ее на Яндекс.Диск.'

    def upload_to_yadisk(self, file_path):
        self.stdout.write(self.style.HTTP_INFO('Начинаем загрузку на Яндекс.Диск...'))

        token = settings.YADISK_TOKEN
        app_folder = settings.YADISK_APP_FOLDER
        file_name = os.path.basename(file_path)

        headers = {
            'Authorization': f'OAuth {token}'
        }

        try:
            folder_check_url = 'https://cloud-api.yandex.net/v1/disk/resources'
            folder_check_params = {'path': f'app:/{app_folder}'}
            response = requests.get(folder_check_url, headers=headers, params=folder_check_params)

            if response.status_code == 404:
                self.stdout.write(self.style.WARNING(f'Папка "{app_folder}" не найдена. Создаем...'))
                folder_create_url = 'https://cloud-api.yandex.net/v1/disk/resources'
                folder_create_params = {'path': f'app:/{app_folder}'}
                create_response = requests.put(folder_create_url, headers=headers, params=folder_create_params)
                create_response.raise_for_status()
                self.stdout.write(self.style.SUCCESS('Папка успешно создана.'))
            elif response.status_code != 200:
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при создании/проверке папки на Яндекс.Диске: {e}'))
            if e.response is not None:
                self.stdout.write(self.style.ERROR(f'Ответ сервера: {e.response.text}'))
            return

        yadisk_path = f'app:/{app_folder}/{file_name}'

        params = {'path': yadisk_path, 'overwrite': 'true'}
        try:
            response = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload', headers=headers,
                                    params=params)
            response.raise_for_status()
            upload_url = response.json().get('href')

            if not upload_url:
                self.stdout.write(self.style.ERROR('Не удалось получить URL для загрузки.'))
                return

            with open(file_path, 'rb') as f:
                upload_response = requests.put(upload_url, data=f)
                upload_response.raise_for_status()

            self.stdout.write(self.style.SUCCESS('Файл успешно загружен на Яндекс.Диск!'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при работе с API Яндекс.Диска: {e}'))
            if e.response is not None:
                self.stdout.write(self.style.ERROR(f'Ответ сервера: {e.response.status_code} - {e.response.text}'))
            else:
                self.stdout.write(self.style.ERROR('Нет ответа от сервера.'))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем процесс резервного копирования...'))

        db_settings = settings.DATABASES['default']
        db_name, db_user, db_password, db_host, db_port = (
            db_settings['NAME'], db_settings['USER'], db_settings['PASSWORD'],
            db_settings['HOST'], db_settings['PORT']
        )

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_file_path = os.path.join(backup_dir, f'backup_{timestamp}.sql')

        command = f'pg_dump --dbname=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name} -f {backup_file_path} --clean'

        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            self.stdout.write(self.style.SUCCESS(f'Локальная резервная копия успешно создана: {backup_file_path}'))

            self.upload_to_yadisk(backup_file_path)

            os.remove(backup_file_path)
            self.stdout.write(self.style.SUCCESS('Локальный файл бэкапа удален.'))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR('Произошла ошибка при создании локальной резервной копии.'))
            self.stdout.write(self.style.ERROR(e.stderr))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Ошибка: команда "pg_dump" не найдена.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла непредвиденная ошибка: {e}'))