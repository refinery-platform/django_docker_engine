import os

import django.core.handlers.wsgi

# Locally, I don't need this, but Travis fails without a wsgi.py in place.
# Not sure why there's a difference.

os.environ.setdefault("DJANGO_SETTINGS_MODULE", __package__ + ".settings")
application = django.core.handlers.wsgi.WSGIHandler()
