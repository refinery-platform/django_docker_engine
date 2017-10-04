# User documentation

## Configuring Django

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


## Docker

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

You also need a Docker container listening on some port: `DockerContainerSpec` makes this easy to manage programatically,
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


## Launching Containers

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