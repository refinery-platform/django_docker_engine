# django_docker_engine

Through Django, manage docker images and route requests to
running containers. This repo defines a minimal project, and
a reusable app which can be added to other Django projects.
(TODO!)

## Install

For development, first install Docker, and then:
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test --verbosity=2
python manage.py runserver &
# TODO: What does the server do?
```

For use in other projects: TODO

## Dependencies

- [docker-py](https://github.com/docker/docker-py): The official
Python SDK for Docker. It uses much the same vocabulary as the CLI,
but with [subtle differences](https://github.com/docker/docker-py/issues/1510)
in meaning, and [bugs](https://github.com/docker/docker-py/issues/1380)
in what should be basic functionality. But the alternatives are calling
the CLI commands as subprocesses, or hitting the socket API directly.

- [django-http-proxy](https://github.com/yvandermeer/django-http-proxy):
Makes Django into a proxy server. It looks like this package has thought about
some of the edge cases, like rewriting absolute URLs in the body content.


## Related projects

- [sidomo](https://github.com/deepgram/sidomo): Wrap containers
as python objects, but assumes input -> output, rather than a
long-running process.
