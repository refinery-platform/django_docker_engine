# django_docker_engine 

[![Build Status](https://travis-ci.org/refinery-platform/django_docker_engine.svg?branch=master)](https://travis-ci.org/refinery-platform/django_docker_engine)
[![PyPI version](https://badge.fury.io/py/django-docker-engine.svg)](https://pypi.python.org/pypi/django-docker-engine)
![Python versions](https://img.shields.io/pypi/pyversions/django_docker_engine.svg)
![Django versions](https://img.shields.io/pypi/djversions/django_docker_engine.svg)
    
This Django app manages and proxies requests to Docker containers.
The primary goal has been to provide a visualization framework for the
[Refinery Project](https://github.com/refinery-platform/refinery-platform),
but nothing should prevent its use in other contexts, as well.

In order for a Docker container to work with this package it must:

- listen on some port for HTTP connections, and
- accept a single JSON file as input.

The following Docker projects have been designed to work with `django_docker_engine`:

- [docker_igv_js](https://github.com/refinery-platform/docker_igv_js)
- [refinery-higlass-docker](https://github.com/scottx611x/refinery-higlass-docker)
- [heatmap-scatter-dash](https://github.com/refinery-platform/heatmap-scatter-dash)

More information:
- [for users of the library](https://github.com/refinery-platform/django_docker_engine/blob/master/README-USERS.md)
- [for developers of the library](https://github.com/refinery-platform/django_docker_engine/blob/master/README-DEVS.md)
- [background motivations and future directions](https://github.com/refinery-platform/django_docker_engine/blob/master/README-PROVENANCE.md)
