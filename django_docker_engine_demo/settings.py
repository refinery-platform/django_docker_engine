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
    'django_docker_engine.middleware.hostname_routing.HostnameRoutingMiddleware', # The comma makes it a tuple.
)

ROOT_URLCONF = 'django_docker_engine_demo.urls'
WSGI_APPLICATION = 'django_docker_engine_demo.wsgi.application'

DATABASES = {}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

PROXY_LOG = '/tmp/django_docker_engine.log'
