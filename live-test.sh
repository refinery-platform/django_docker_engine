#!/usr/bin/env bash
set -o errexit

CONTAINER_NAME=my-container
BASE=http://127.0.0.1:8000

die() { echo "$@" 1>&2 ; exit 1; }

python manage.py runserver &
sleep 2 # TODO: wait loop
EXPECT_WAIT=`curl $BASE/docker/$CONTAINER_NAME/`
echo $EXPECT_WAIT | grep 'Please wait' || die "Not what I expected: '$EXPECT_WAIT'"

docker run --name $CONTAINER_NAME --publish 80 --detach nginx:1.10.3-alpine
sleep 2 # TODO: wait loop
EXPECT_NGINX=`curl $BASE/docker/$CONTAINER_NAME/`
echo $EXPECT_NGINX | grep 'Welcome to nginx' || die "Not what I expected: '$EXPECT_NGINX'"
