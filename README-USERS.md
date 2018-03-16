# User documentation

## Install

Use pip to install `django_docker_engine`, either adding a line to your `requirements.txt`
or on the commandline:
```
$ pip install django_docker_engine
```

## Choices you need to make

### `input.json`: mounted file vs. envvar vs. envvar url

There are essentially two ways of passing input to a container on startup:
By mounting a file from the host filesystem and by passing environment variables.
The method used depend on the parameters you use for `DockerClientSpec`.

`do_input_json_file` (boolean):
- Input is serialized to a JSON file and saved in a tmp directory.
- If Docker Engine is on a remote host, requires SSH access.

`do_input_json_envvar` (boolean):
- Instead of writing a file, JSON is stored in an environment variable.
- There is limit to the size of environment variables: Typically 2M, but it could be lower.

`input_json_url` (string):
- This option requires the caller to have already made the data available at some URL.
- Managing access and cleaning up this resource is the caller's responsibility.


### Path vs. hostname routing

There are two ways to map incoming requests to containers.
The default is path-based routing, but domain-name routing
can also be used.

[Path-based routing](demo_path_routing):
- is simpler, but
- it requires a prefix on every path passed to the containerized webapp.
- ie: You may not use any paths starting with "/".

[Hostname-based routing](demo_host_routing):
- is more complex, because it requires `HostnameRoutingMiddleware`,
- and you will need to set up a wildcard entry in DNS to capture all subdomains.
- but the webapp can use paths starting with "/".


## Docker

`django_docker_engine` tries to abstract away the differences between different ways of running Docker.


### Local Docker Engine

Typically, Docker Engine will be installed and running on the same machine as Django:
Review their [docs](https://docs.docker.com/engine/installation/) for the best information,
and then [download](https://store.docker.com/search?offering=community&type=edition) and install.


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
>>> DockerClientWrapper('/tmp/docker', do_input_json_file=True).run(
      DockerContainerSpec(
        image_name='nginx:1.10.3-alpine',
        container_name='my-server',
        container_input_path='/tmp/hello.txt'
      )
    )
$ python manage.py runserver
$ curl http://localhost:8000/docker/my-server/hello.txt
Hello World
```

For more detail, consult the [generated documentation](docs.md).