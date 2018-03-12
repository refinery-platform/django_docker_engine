import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'not-so-secret'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = [
    # This needs to allow the root server, and any
    # subdomains which are mapped to containers.
    # Leaving it as '*' is not good for security!
    # https://docs.djangoproject.com/en/1.11/ref/settings/#allowed-hosts
    '*'
]

INSTALLED_APPS = (
    'django_docker_engine',
    'httpproxy'
)

MIDDLEWARE_CLASSES = (
    # REMEMBER to keep a trailing comma so this will be a tuple.
    'django_docker_engine.middleware.request_debugging.RequestDebuggingMiddleware',
    'django_docker_engine.middleware.hostname_routing.HostnameRoutingMiddleware',
    'django_docker_engine.middleware.request_debugging.RequestDebuggingMiddleware',
)

ROOT_URLCONF = 'demo_host_routing.urls'
WSGI_APPLICATION = 'demo_host_routing.wsgi.application'

DJANGO_DOCKER_HOST_SUFFIX = '.docker.localhost'
DJANGO_DOCKER_PATH_PREFIX = '/docker/'

DATABASES = {}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
