#!/usr/bin/env bash
set -o errexit

./manage.py migrate
./manage.py shell --command '
from django.contrib.auth.models import User
if not User.objects.count():
    User.objects.create_user("fake-username", "fake@example.com", "fake-password")
'