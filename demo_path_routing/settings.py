from .settings_common import *  # noqa

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [__package__]
    },
]

STATIC_URL = '/static/'

# WARNING: Before running this on a public server,
# you should harden or remove the upload machinery.
ALLOWED_HOSTS = ['localhost', 'host.docker.internal']
MIDDLEWARE_CLASSES = ()
