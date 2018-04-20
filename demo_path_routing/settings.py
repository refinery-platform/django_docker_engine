from .settings_common import *  # noqa

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [__package__]
    },
]

STATIC_URL = '/static/'

ALLOWED_HOSTS = ['docker.for.mac.localhost', 'host.docker.internal']
MIDDLEWARE_CLASSES = ()
