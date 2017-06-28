from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class BackupStorage(S3BotoStorage):
    access_key = getattr(settings, 'BACKUP_BUCKET_AWS_ACCESS_KEY_ID')
    secret_key = getattr(settings, 'BACKUP_BUCKET_AWS_SECRET_ACCESS_KEY')
    bucket_name = getattr(settings, 'BACKUP_BUCKET_BUCKET_NAME')
    location = getattr(settings, 'BACKUP_BUCKET_LOCATION')
