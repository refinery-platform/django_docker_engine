#!/usr/bin/env bash

# For now, this is good enough.

pydoc django_docker_engine.docker_utils \
  | perl -ne 'if (/^\s+class|\|/) {s/^\s+//; s/^class/\n## class/; s/\|//; s/^  (\w+)/### $1/; s/^\s+//; print}' \
  | grep -v 'defined here' | grep -v '\-----'