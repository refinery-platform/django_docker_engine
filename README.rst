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

TODO

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
