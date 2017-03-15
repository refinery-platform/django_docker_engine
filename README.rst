====================
django_docker_engine
====================

A Django app which manages and proxies requests to Docker containers.

-------
Install
-------

In either environment, Docker Engine needs to be installed and running.

via pip
-------

::

    pip install git+https://github.com/mccalluc/django_docker_engine.git@master

TODO: tag releases, and push to pypi when reasonably stable.

for development
---------------

::

    git clone https://github.com/mccalluc/django_docker_engine.git
    cd django_docker_engine
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py test --verbosity=2
    # python manage.py runserver &
    # TODO: What does the server do?

-----
Usage
-----

Add django_docker_engine to your dependencies, and then add something like this to your urls.py::

    url(r'^docker/', include('django_docker_engine.urls')
    
With that in place, incoming requests will be proxied to Docker containers by name. For instance::

    http://locahost:8080/docker/your-container-name/your-path?your=parameter
    
The server will try to locate a Docker container with the name "your-container-name", and will
proxy to it on port 80 a request for "/your-path?your=parameter".

When to start and stop containers is left to your application, but DockerContainerSpec may make
it easier: Look at test_container_spec for an example.

------------
Dependencies
------------

- `docker-py <https://github.com/docker/docker-py>`_: The official
  Python SDK for Docker. It uses much the same vocabulary as the CLI,
  but with `tricky differences <https://github.com/docker/docker-py/issues/1510>`_
  in meaning. The alternatives are calling
  the CLI commands as subprocesses, or hitting the socket API directly.

- `django-http-proxy <https://github.com/yvandermeer/django-http-proxy>`_:
  Makes Django into a proxy server. It looks like this package has thought about
  some of the edge cases, like rewriting absolute URLs in the body content.

----------------
Related projects
----------------

- `sidomo <https://github.com/deepgram/sidomo>`_: Wrap containers
  as python objects, but assumes input -> output, rather than a
  long-running process.
