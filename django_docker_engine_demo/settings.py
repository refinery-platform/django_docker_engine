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