====================
django_docker_engine
====================

A Django app which manages and proxies requests to Docker containers.

-----
Usage: Configuring Django
-----

Typically, Docker Engine will be installed and running on the same machine as Django:
Read their `docs <https://docs.docker.com/engine/installation/>`_ for more information on Docker installation.

Use pip to install ``django_docker_engine``, either adding a line to ``requirements.txt``
or on the commandline::

    $ pip install git+https://github.com/mccalluc/django_docker_engine.git@master

You will need to decide on a path that should be routed to Docker. A minimal ``urls.py`` could look like::

    from django.conf.urls import patterns, include, url
    import django_docker_engine
    
    urlpatterns = patterns('',
        url(r'^docker/', include('django_docker_engine.urls'))
    )

You also need a Docker container with port 80 open: ``DockerContainerSpec`` makes this easy to manage programatically,
but for now let's start one by hand::

    $ docker run --name empty-server --publish 80 --detach nginx:1.10.3-alpine
    
Next, let's start Django::

    $ python manage.py runserver
    
and visit: http://localhost:8000/docker/empty-server

You should see the Nginx welcome page: ``django_docker_engine`` has determined the port the container was assigned,
and has proxied your request. 

-------
Usage: Launching Containers
-------

``DockerContainerSpec`` exposes a subset of Docker functionality so your application can easily launch containers as needed.
This is under active development and for now the best demonstrations of the functionality are in the test suite,
but here's a basic example::

    $ echo 'Hello World' > /tmp/hello.txt
    $ python
    >>> from django_docker_engine.docker_utils import DockerContainerSpec
    >>> DockerContainerSpec(
          image_name='nginx:1.10.3-alpine',
          container_name='my-content-server',
          input_mount='/usr/share/nginx/html',
          input_files=['/tmp/hello.txt']
       ).run()
    $ curl http://localhost:8000/docker/my-content-server/hello.txt
    Hello World

Note that this is only a Docker utility: it does not touch any Django models to record information about containers.

-----------
Development
-----------

::

    git clone https://github.com/mccalluc/django_docker_engine.git
    cd django_docker_engine
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python manage.py migrate
    python manage.py test --verbosity=2

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
