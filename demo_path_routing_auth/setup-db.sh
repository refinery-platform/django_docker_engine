#!/usr/bin/env bash
set -o errexit

cd `dirname "$0"`
../manage_auth.py migrate
../manage_auth.py shell --command '
from django.contrib.auth.models import User
if not User.objects.count():
    User.objects.create_user("fake-username", "fake@example.com", "fake-password")
'