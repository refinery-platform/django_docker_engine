# django_docker_engine 

![PyPI version](https://badge.fury.io/py/django-docker-engine.svg)](https://pypi.python.org/pypi/django-docker-engine)
    
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
- [for users of the library](README-USERS.md)
- [for developers of the library](README-DEVS.md)
- [background motivations and future directions](README-PROVENANCE.md)
