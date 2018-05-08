from .settings_common import *  # noqa
from .utils import hostname

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [__package__]
    },
]

STATIC_URL = '/static/'

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', hostname()]
# hostname() allows the docker containers to
# get files from the upload directory on this server.

MIDDLEWARE_CLASSES = ()

AUTHENTICATION_BACKENDS = (__package__ + '.auth.AuthBackend')
