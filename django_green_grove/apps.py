from django.apps import AppConfig
from django.conf import settings


class DjangoGreenGroveConfig(AppConfig):
    name = 'django_green_grove'

    def ready(self):
        """
        If there are bucket keys with no size, the `endElement` method of botos `Key` class fails with a ValueError.
        The errors aborts the management command and not a single file is backed up. To prevent this we set the size
        and log an error.
        """
        if hasattr(settings, 'DJANGO_GREEN_GROVE_EMPTY_S3_KEYS'):
            from boto.s3.key import Key

            def end_element(self, name, value, connection):
                if name == 'Key':
                    self.name = value
                elif name == 'ETag':
                    self.etag = value
                elif name == 'IsLatest':
                    if value == 'true':
                        self.is_latest = True
                    else:
                        self.is_latest = False
                elif name == 'LastModified':
                    self.last_modified = value
                elif name == 'Size':
                    try:
                        self.size = int(value)
                    except:
                        self.size = None
                elif name == 'StorageClass':
                    self.storage_class = value
                elif name == 'Owner':
                    pass
                elif name == 'VersionId':
                    self.version_id = value
                else:
                    setattr(self, name, value)

            Key.endElement = end_element
