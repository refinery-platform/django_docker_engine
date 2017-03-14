# django_docker_engine

Through Django, manage docker images and route requests to
running containers. This repo defines a minimal project, and
a reusable app which can be added to other Django projects.
(TODO!)

## Install

For development:
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test --verbosity=2
python manage.py runserver &
# TODO: What does the server do?
```

For use in other projects: TODO

## Related projects

- [sidomo](https://github.com/deepgram/sidomo): Wrap containers
as python objects, but assumes input -> output, rather than a
long-running process.

- [docker-py](https://github.com/docker/docker-py): The official
Python SDK for Docker. It uses much the same vocabulary as the CLI,
but with subtle differences in mean. Using it right now, but
mixed feelings.