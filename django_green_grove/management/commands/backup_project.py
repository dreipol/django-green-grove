import logging
import os
import subprocess

import boto
from django.conf import settings
from django.core.management import BaseCommand
from django.utils.timezone import now

from ...backends import BackupStorage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backs up the database and bucket data to another S3 bucket.'
    timestamp = None
    temp_backup_path = ''

    def handle(self, *args, **options):
        # Set variables
        self.timestamp = now().strftime('%Y%m%d%H%M%S')
        self.temp_backup_path = 'tmp/backups/%s' % self.timestamp

        backup_storage = BackupStorage()

        self.prepare_backup()
        self.create_pgpass()

        try:
            self.back_up_database(backup_storage=backup_storage, temp_backup_path=self.temp_backup_path)
            self.back_up_bucket()
            logger.info('backup_project_success: Successfully backed up database and bucket.')
        except:
            pass

        self.cleanup_backup()

    def prepare_backup(self):
        os.makedirs(self.temp_backup_path, exist_ok=True)  # Set up the temporary directory.

    def cleanup_backup(self):
        # Cleanup all temporary files
        if os.path.exists(self.temp_backup_path):
            file_list = os.listdir(self.temp_backup_path)
            for file_name in file_list:
                file = os.path.join(self.temp_backup_path, file_name)
                os.remove(file)
            os.rmdir(self.temp_backup_path)

    def create_pgpass(self):
        file_path = '~/.pgpass'
        connection_string = '{hostname}:{port}:{database}:{username}:{password}'.format(
            hostname=settings.DATABASES['default']['HOST'],
            port='5432',
            database=settings.DATABASES['default']['NAME'],
            username=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD']
        )

        if os.path.exists(file_path):
            backup_pgpass_text = '.pgpass has changed. Back it up to make sure no data is lost.'

            # Prepare the check of the contents from the current version of the pgpass file.
            grep = 'grep -q "{connection_string}" {file_path}; test $? -eq 0 && echo "\c" || ' \
                   'echo "{backup_pgpass_text}\c"'.format(connection_string=connection_string, file_path=file_path,
                                                          backup_pgpass_text=backup_pgpass_text)

            # Backup the pgpass file if there is a difference.
            if str(subprocess.check_output(grep, shell=True), 'utf-8') == backup_pgpass_text:
                print(backup_pgpass_text)
                os.system('mv {file_path} {file_path}_{timestamp}'.format(file_path=file_path,
                                                                          timestamp=self.timestamp))

        # Save the connection string to the pgpass file.
        os.system('echo "{connection_string}\c" > {file_path} && chmod 600 {file_path}'.format(
            connection_string=connection_string,
            file_path=file_path
        ))

    def back_up_database(self, backup_storage, temp_backup_path):
        logger.info('Start backing up the database.')
        file_path = '{database}_{timestamp}.dump'.format(
            database=settings.DATABASES['default']['NAME'],
            timestamp=self.timestamp
        )
        temp_file_path = '{backup_path}/{file_path}'.format(backup_path=temp_backup_path, file_path=file_path)

        # Run the `pg_dump` command.
        os.system('pg_dump -h {host} -U {user} {database} > {file_path}'.format(
            host=settings.DATABASES['default']['HOST'],
            user=settings.DATABASES['default']['USER'],
            database=settings.DATABASES['default']['NAME'],
            file_path=temp_file_path
        ))

        # Store the dump file on the backup bucket.
        with open(temp_file_path, 'rb') as database_backup_file:
            target_file_path = '{timestamp}/{path}'.format(timestamp=self.timestamp, path=file_path)
            backup_storage.save(target_file_path, database_backup_file)
            logger.info('Database dump successfully copied to the target storage backend.')

    def back_up_bucket(self):
        logger.info('Start backing up the bucket data.')

        boto_connection = boto.connect_s3(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            host=settings.AWS_S3_HOST,
        )
        source_bucket = boto_connection.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        destination_bucket = boto_connection.get_bucket(settings.BACKUP_BUCKET_BUCKET_NAME)
        destination_sub_directory = '{location}/{timestamp}'.format(location=settings.BACKUP_BUCKET_LOCATION,
                                                                    timestamp=self.timestamp)

        for source_key in source_bucket.list():
            new_key_name = '{sub_directory}/{name}'.format(sub_directory=destination_sub_directory,
                                                           name=source_key.key)
            destination_bucket.copy_key(
                new_key_name=new_key_name,
                src_bucket_name=source_bucket.name,
                src_key_name=source_key.key
            )

        logger.info('Bucket data successfully copied to the target storage backend.')
