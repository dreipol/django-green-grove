==================
django-green-grove
==================

Collection of helpers to back up Django projects that use a Postgres database and a S3 bucket as media storage.


Quickstart
----------

Install django-green-grove using pip.::

    pip install django-green-grove


Add the following to your `settings.py` module:::

    BACKUP_BUCKET_AWS_ACCESS_KEY_ID = ''
    BACKUP_BUCKET_AWS_SECRET_ACCESS_KEY = '
    BACKUP_BUCKET_BUCKET_NAME = ''
    BACKUP_BUCKET_LOCATION = ''


Backup Project
--------------

We suggest to use this management command as a cron tab:::

    python manage.py backup_project


This tutorial covers the steps that are needed to backup and restore a Django project that uses a Dokku hosting with a Postgres database and a S3 Bucket as media storage.

### Backup project
1.  Connect to your server
2.  Connect to the docker container: `dokku enter <project_name>`
3.  `python manage.py backup_project`

### Restore from backup
1.  Connect to your server
2.  Connect to the database: `dokku postgres:connect db`
3.  Drop the database: `DROP DATABASE <db_name>;`
4.  Recreate the database: `CREATE DATABASE <db_name>;`
5.  Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE <db_name> to <username>;`
6.  Exit the postgres console and the session on the server
7.  Download the database dump file from the bucket to your local machine: `s3cmd cp <path_of_dump_file> .`
8.  Move the dump file to the server: `scp <path_of_dump_file> <server>`
9.  Connect to your server
10. Import the dump: `cat <file_name> | sudo docker exec -i dokku.postgres.db psql -U <username> <db_name>`
11. Remove the media folder of your bucket (s3cmd or web interface)
12. Open up the terminal on your local machine
13. Copy the backup of the media folder back to the bucket:
    `s3cmd cp --recursive  --acl-public s3://backups/<project_name>/<timestamp>/media/ s3://<project_name>/media/`


Trivia
------

This package is named after the fictional retirement community where Tony Soprano, Paulie Gualtieri, and other Mafiosi admit their mothers, in The Sopranos.


Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
