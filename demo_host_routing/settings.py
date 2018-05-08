import django

from .settings_common import *  # noqa

ALLOWED_HOSTS = [
    # This needs to allow the root server, and any
    # subdomains which are mapped to containers.
    # Leaving it as '*' is not good for security!
    # https://docs.djangoproject.com/en/1.11/ref/settings/#allowed-hosts
    '*'
]

if django.VERSION >= (2, 0):
    MIDDLEWARE = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        __package__ + '.auth.AuthMiddleware',
        'django_docker_engine.middleware.hostname_routing.'
        'HostnameRoutingMiddlewareCallable',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        __package__ + '.auth.AuthMiddleware',
        'django_docker_engine.middleware.hostname_routing.'
        'HostnameRoutingMiddleware',
    )
