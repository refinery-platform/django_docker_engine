# User documentation

## Install

Use pip to install `django_docker_engine`, either adding a line to your `requirements.txt`
or on the commandline:
```
$ pip install django_docker_engine
```

## Responsibilities

If the parent Django application has user sessions:
- Containers need to make sure that any AJAX requests back to the host
preserve session cookies. Any
[`fetch`](https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/fetch#Parameters)
or [`Request`](https://developer.mozilla.org/en-US/docs/Web/API/Request/Request#Parameters)
needs to include `credentials: "same-origin"`
- If the container is itself a Django application, either the container application
or the parent application needs to change `SESSION_COOKIE_NAME` to a non-default value
to avoid a collision.

## Choices

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

[Path-based routing](demo_path_routing_no_auth):
- is simpler, but
- it requires a prefix on every path passed to the containerized webapp.
- ie: You may not use any paths starting with "/".

[Hostname-based routing](demo_host_routing):
- is more complex, because it requires `HostnameRoutingMiddleware`,
- and you will need to set up a wildcard entry in DNS to capture all subdomains.
- but the webapp can use paths starting with "/".

### Local host vs. remote host

`django_docker_engine` tries to abstract away the differences between different ways of running Docker.

#### Local Docker Engine

Typically for development, Docker Engine will be installed and running on the same machine as Django:
Review their [docs](https://docs.docker.com/engine/installation/) for the best information,
and then [download](https://store.docker.com/search?offering=community&type=edition) and install.

But with more load, you'll probably want the containers on a separate machine
to avoid resource contention...

#### Docker Engine on AWS-EC2

In Refinery, the Docker Engine is running on on a separate EC2. You'll need to
provision the server, using boto, cloudformation, terraform, or some other libary,
and then set `DOCKER_HOST` to point at the EC2. 

#### AWS-ECS

TODO: AWS provides its own wrapper around Docker through ECS. We will need to abstract away what the
Docker SDK provides so that we can use either interface, as needed.


## Walk-throughs

### Basics

Here's a basic demo. (This script does start up our demo 
django instance: for that to work, you will need to checkout the repo and cd, 
and not just have installed it via pip.)

```
>>> from django_docker_engine.docker_utils import (
...     DockerClientRunWrapper, DockerClientSpec, DockerContainerSpec)
>>> client_spec = DockerClientSpec(None, do_input_json_envvar=True)
>>> client = DockerClientRunWrapper(client_spec)

# First, confirm no containers are already running:
>>> client.list()
[]

# Then start your own container:
>>> container_name = 'basic-nginx'
>>> from tests import NGINX_IMAGE
>>> container_spec = DockerContainerSpec(
...     image_name=NGINX_IMAGE,
...     container_name=container_name)
>>> container_url = client.run(container_spec)
>>> container_url  # doctest:+ELLIPSIS
'http://localhost:...'

# The nginx container is responding to requests:
>>> import requests
>>> text = requests.get(container_url).text
>>> ('Welcome to nginx' in text) or text
True

# Start Django as a subprocess, and give it a moment to start:
>>> import subprocess
>>> process = subprocess.Popen(
...     ['./manage.py', 'runserver'],
...     stdout=open('/dev/null', 'w'),
...     stderr=open('/dev/null', 'w'))
>>> django_url = 'http://localhost:8000'
>>> from time import sleep
>>> sleep(2)

# There is a homepage at '/':
>>> demo_home = requests.get(django_url).text
>>> ('django_docker_engine demo' in demo_home) or demo_home
True

# Under '/docker/, requests are proxied to containers by name:
>>> proxy_url = django_url + '/docker/' + container_name + '/'
>>> proxy_url
'http://localhost:8000/docker/basic-nginx/'
>>> nginx_welcome = requests.get(proxy_url).text
>>> ('Welcome to nginx' in nginx_welcome) or nginx_welcome
True

# The history of requests is available:
>>> hist = client.history(container_name)
>>> hist
TODO!!!

# and Docker logs are also available:
>>> api_logs = client.logs(container_name)
>>> (b'"GET / HTTP/1.1" 200' in api_logs) or api_logs
True

# ... or from the UI, if `logs_path` was provided as a kwarg to Proxy:
>>> ui_logs = requests.get(proxy_url + 'docker-logs').text
>>> ('"GET / HTTP/1.1" 200' in ui_logs) or ui_logs
True



```

### Please wait

By default, if the container is not yet responding to
requests, the proxy will return a "Please wait" page with both a 
JS- and a meta-reload. You can customize the content of this page, 
and the reload behavior.

Note, though, that there is no attempt to distinguish between a container
that is taking its time, and one that may never start up: In either case,
the user just gets the "Please wait" page by default, and it will continue
to refresh indefinitely.

```
# Make sure Django is still up:
>>> text = requests.get(django_url).text
>>> assert 'django_docker_engine demo' in text, 'unexpected: {}'.format(text)

# Try to get a container that doesn't exist:
>>> container_name = 'please-wait'
>>> proxy_url = django_url + '/docker/' + container_name + '/'
>>> proxy_url
'http://localhost:8000/docker/please-wait/'
>>> text = requests.get(proxy_url).text
>>> assert 'Please wait' in text, 'unexpected: {}'.format(text)
>>> assert 'http-equiv="refresh"' in text, 'unexpected: {}'.format(text)

```

### Historian

The `Historian` provides access to a record of the requests that have been
made through the Proxy. Its configuration, along with that for the "Please wait"
page needs to be made as part of your django configuration. The example here
shows how it can be configured:

```
>>> from os import environ
>>> environ['DJANGO_SETTINGS_MODULE'] = 'demo_path_routing_no_auth.settings'
>>> from django_docker_engine.historian import FileHistorian
>>> from django_docker_engine.proxy import Proxy
>>> from django.test import RequestFactory

>>> import django
>>> django.setup()

>>> historian = FileHistorian('/tmp/readme-doc-text.txt')
>>> proxy = Proxy(
...     historian=historian,
...     please_wait_title='<test-title>',
...     please_wait_body_html='<p>test-body</p>')
>>> urlpatterns = proxy.url_patterns()

# All of this would be handled by Django in practice:
>>> response = urlpatterns[-1].callback(
...     request=RequestFactory().get('/fake-url'),
...     container_name='fake-container',
...     url='fake-url')
>>> html = response.content.decode()
>>> assert '<title>&lt;test-title&gt;</title>' in html
>>> assert '<p>test-body</p>' in html
>>> assert 'fake-container\tfake-url' in historian.list()[-1] 

```