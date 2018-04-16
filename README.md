# django_docker_engine 

[![Build Status](https://travis-ci.org/refinery-platform/django_docker_engine.svg?branch=master)](https://travis-ci.org/refinery-platform/django_docker_engine)
[![PyPI version](https://badge.fury.io/py/django-docker-engine.svg)](https://pypi.org/project/django-docker-engine/)
![Python versions](https://img.shields.io/pypi/pyversions/django_docker_engine.svg)
![Django versions](https://img.shields.io/pypi/djversions/django_docker_engine.svg)
    
This Django app manages and proxies requests to Docker containers.
The primary goal has been to provide a visualization framework for the
[Refinery Project](https://github.com/refinery-platform/refinery-platform),
but nothing should prevent its use in other contexts, as well.

In order for a Docker container to work with this package it must:

- listen on some port for HTTP connections, and
- accept a single JSON file as input.

The Refinery team maintains a [registry](https://github.com/refinery-platform/visualization-tools)
of Docker images which can be plugged in to this framework. It includes:

- [refinery-higlass-docker](https://github.com/refinery-platform/refinery-higlass-docker):
A wrapper for [HiGlass](http://higlass.io/), for exploring genomic contact 
matrices and tracks.
- [heatmap-scatter-dash](https://github.com/refinery-platform/heatmap-scatter-dash):
A Plotly Dash app for understanding differential expression data.
- [lineup-refinery-docker](https://github.com/refinery-platform/lineup-refinery-docker):
A wrapper for [Caleydo LineUp](http://caleydo.org/tools/lineup/), for visualizing
rankings based on heterogeneous attributes

More information:
- [for users of the library](https://github.com/refinery-platform/django_docker_engine/blob/master/README-USERS.md)
- [for developers of the library](https://github.com/refinery-platform/django_docker_engine/blob/master/README-DEVS.md)
- [background motivations and future directions](https://github.com/refinery-platform/django_docker_engine/blob/master/README-PROVENANCE.md)
- [API documentation](https://www.pydoc.io/pypi/django-docker-engine-0.0.48/)
