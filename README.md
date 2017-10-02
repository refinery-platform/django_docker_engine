# django_docker_engine 

[![Build Status](https://travis-ci.org/refinery-platform/django_docker_engine.svg?branch=master)](https://travis-ci.org/refinery-platform/django_docker_engine)

[django_docker_engine on PyPi](https://pypi.python.org/pypi/django-docker-engine)
    
This Django app manages and proxies requests to Docker containers.
The primary goal has been to provide a visualization framework for the
[Refinery Project](https://github.com/refinery-platform/refinery-platform),
but nothing should prevent its use in other contexts, as well.

In order for a Docker container to work with this package it must:

- listen on port 80 for HTTP connections, and
- accept a single json file as input.

The following Docker projects have been designed to work with `django_docker_engine`:

- [docker_igv_js](https://github.com/refinery-platform/docker_igv_js)
- [refinery-higlass-docker](https://github.com/scottx611x/refinery-higlass-docker)

Write-ups on the background motivations and future directions:

- [Provenance](README-PROVENANCE.md)


## Usage: Configuring Django

Use pip to install `django_docker_engine`, either adding a line to `requirements.txt`
or on the commandline:
```
$ pip install django_docker_engine
```

You will need to decide on a path that should be routed to Docker. A minimal `urls.py` could look like:

```
from django.conf.urls import include, url
import django_docker_engine

urlpatterns = [ url(r'^docker/', include('django_docker_engine.urls')) ]
```


## Usage: Docker

`django_docker_engine` tries to abstract away the differences between different ways of running Docker.


### Local Docker Engine

Typically, Docker Engine will be installed and running on the same machine as Django:
Review their [docs](https://docs.docker.com/engine/installation/) for the best information,
but here is one way to install on Linux:

```
$ sudo apt-get install libapparmor1
$ DEB=docker-engine_1.13.0-0~ubuntu-precise_amd64.deb
$ wget https://apt.dockerproject.org/repo/pool/main/d/docker-engine/$DEB
$ sudo dpkg -i $DEB
```

You also need a Docker container with port 80 open: `DockerContainerSpec` makes this easy to manage programatically,
but for now let's start one by hand:

```
$ docker run --name empty-server --publish 80 --detach nginx:1.10.3-alpine
```
    
Next, if you haven't already, start Django:

```
$ python manage.py runserver
```

and visit: http://localhost:8000/docker/empty-server

You should see the Nginx welcome page: `django_docker_engine` has determined the port the container was assigned,
and has proxied your request. 


### Docker Engine on AWS-EC2

The Docker Engine can also be run on a remote machine. `cloudformation_util.py` can either be run
on the command-line, or it can be imported and called within Python to set up a new EC2 with appropriate
security. Once the EC2 is available, it can be provided when constructing `DockerEngineManager`,
either implicitly as an envvar, or explicitly via an instance of the SDK client.

If this will be done automatically, you can ensure that the user has the appropriate privs by running
`set_user_policy.py`.

[Notes on working with AWS](README-AWS.md) are available.


### AWS-ECS

TODO: AWS provides its own wrapper around Docker through ECS. We will need to abstract away what the
Docker SDK provides so that we can use either interface, as needed.


## Usage: Launching Containers

`DockerContainerSpec` exposes a subset of Docker functionality so your application can launch containers as needed:

```
$ echo 'Hello World' > /tmp/hello.txt
$ python
>>> from django_docker_engine.docker_utils import (DockerClientWrapper, DockerContainerSpec)
>>> DockerClientWrapper('/tmp/docker').run(
      DockerContainerSpec(
        image_name='nginx:1.10.3-alpine',
        container_name='my-server',
        input_mount='/usr/share/nginx/html',
        input_files=['/tmp/hello.txt']
      )
    )
$ curl http://localhost:8000/docker/my-server/hello.txt
Hello World
```

For more detail, consult the [generated documentation](docs.md).


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
# In a second, you should get the nginx welcom page.
# If your container did something useful, then you'd be seeing that instead.
```

### Release Process

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
