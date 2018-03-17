#!/usr/bin/env bash
set -o errexit

start() { echo travis_fold':'start:$1; echo $1; }
end() { echo travis_fold':'end:$1; }
die() { set +v; echo "$*" 1>&2 ; exit 1; }

ping -c1 container-name.docker.localhost > /dev/null  # Prereq for hostname-based dispatch.
docker info | grep 'Operating System'  # Are we able to connect to Docker, and what OS is it?

start test
./manage.py test --verbosity=2
end test

start format
flake8 --exclude build . || die "Run 'autopep8 --in-place -r .'"
end format

start isort
isort --recursive . --verbose --check-only --skip django_docker_engine/cloudformation_utils.py || die "Run 'isort --recursive .'"
end isort

start egg
python setup.py bdist_egg
end egg

# TODO: No output on travis: Is pydoc installed?
# start docs;        diff <(./docs.sh) docs.md; end docs