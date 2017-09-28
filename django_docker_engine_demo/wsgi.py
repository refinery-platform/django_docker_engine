import os
import django.core.handlers.wsgi

# I don't have problems locally, but Travis fails without a wsgi.py?

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_docker_engine_demo.settings")
application = django.core.handlers.wsgi.WSGIHandler()
