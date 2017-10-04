# Developer documentation

## Development
```
$ git clone https://github.com/mccalluc/django_docker_engine.git
$ cd django_docker_engine
$ pip install -r requirements.txt
$ pip install -r requirements-dev.txt
$ ./manage.py test --verbosity=2
```

To run it end-to-end, use the included demo server:
```
$ ./manage.py runserver &
# In your browser, visit: http://127.0.0.1:8000/docker/my-container/
# You should get a "please wait" page: We're waiting for "my-container" to start.
$ docker run --name my-container --publish 80 --detach nginx:1.10.3-alpine \
  --label io.github.refinery-project.django_docker_engine.port=80
# In a second, you should get the nginx welcome page.
# If your container did something useful, then you'd be seeing that instead.
```

## Release Process

To make a new release, branch, increment the version number in `VERSION.txt`, and make a PR on github.
If it passes tests, merge to `master`, and Travis will push to PyPi.
(Travis will try pushing to PyPi on every merge to `master`,
but unless the version is new, the push will fail.)

## Key Dependencies

- [docker-py](https://github.com/docker/docker-py): The official
  Python SDK for Docker. It uses much the same vocabulary as the CLI,
  but with some [subtle differences](https://github.com/docker/docker-py/issues/1510)
  in meaning. It's better than the alternatives: calling
  the CLI commands as subprocesses, or hitting the socket API directly.

- [boto](http://boto3.readthedocs.io/en/latest/): AWS Python SDK.

- [django-http-proxy](https://github.com/yvandermeer/django-http-proxy):
  Makes Django into a proxy server. It looks like this package has thought about
  some of the edge cases, like rewriting absolute URLs in the body content.


## Related projects

- [sidomo](https://github.com/deepgram/sidomo): Wrap containers
  as python objects, but assumes input -> output, rather than a
  long-running process.

- [Dockstore](https://dockstore.org/docs/about):
  Docker containers described with CWL.

- [BioContainers](http://biocontainers.pro/docs/developer-manual/developer-intro/):
  A set of best-practices, a community, and a registry of containers
  built for biology. Preference given to BioConda?
