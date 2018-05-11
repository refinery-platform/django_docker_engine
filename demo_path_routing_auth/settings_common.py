import os as _os  # So we can "import *" and not get extra junk.

BASE_DIR = _os.path.dirname(_os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'not-so-secret'

DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS = (
    'django_docker_engine',
    'revproxy',
)

shared_middleware = (
    'django.middleware.csrf.CsrfViewMiddleware',
)

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

ROOT_URLCONF = __package__ + '.urls'
WSGI_APPLICATION = __package__ + '.wsgi.application'

# TODO: These are not needed in demo_path_routing_* ... except for tests?
DJANGO_DOCKER_HOST_SUFFIX = '.docker.localhost'
DJANGO_DOCKER_PATH_PREFIX = '/docker/'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
