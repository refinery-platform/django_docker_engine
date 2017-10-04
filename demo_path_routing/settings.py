import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'not-so-secret'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django_docker_engine',
    'httpproxy'
)

MIDDLEWARE_CLASSES = ()

ROOT_URLCONF = 'demo_path_routing.urls'
WSGI_APPLICATION = 'demo_path_routing.wsgi.application'

# These are only really needed for hostname-based routing,
# but tests also use this settings.py. Fix?
DJANGO_DOCKER_HOST_SUFFIX = '.docker.localhost'
DJANGO_DOCKER_PATH_PREFIX = '/docker/'

DATABASES = {}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

PROXY_LOG = '/tmp/django_docker_engine.log'
