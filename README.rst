====================
django_docker_engine
====================

This is a Django app which manages and proxies requests to Docker containers.
The primary goal has been to provide a visualization framework for the
`Refinery Project <https://github.com/refinery-platform/refinery-platform>`_,
but nothing should prevent its use in other contexts, as well.

In order for a Docker container to work with this package it must:

- listen on port 80 for HTTP connections, and
- accept a single json file as input.

The following Docker projects have been designed to work with ``django_docker_engine``:

- `docker_igv_js <https://github.com/refinery-platform/docker_igv_js>`_

-----
Usage: Configuring Django
-----

Use pip to install ``django_docker_engine``, either adding a line to ``requirements.txt``
or on the commandline::

    $ pip install git+https://github.com/refinery-platform/django_docker_engine.git@master

You will need to decide on a path that should be routed to Docker. A minimal ``urls.py`` could look like::

    from django.conf.urls import include, url
    import django_docker_engine

    urlpatterns = [ url(r'^docker/', include('django_docker_engine.urls')) ]

-----
Usage: Docker
-----

``django_docker_engine`` tries to abstract away the differences between different ways of running Docker.

.....
Local Docker Engine
.....

Typically, Docker Engine will be installed and running on the same machine as Django:
Review their `docs <https://docs.docker.com/engine/installation/>`_ for the best information,
but here is one way to install on Linux::

    $ sudo apt-get install libapparmor1
    $ DEB=docker-engine_1.13.0-0~ubuntu-precise_amd64.deb
    $ wget https://apt.dockerproject.org/repo/pool/main/d/docker-engine/$DEB
    $ sudo dpkg -i $DEB

You also need a Docker container with port 80 open: ``DockerContainerSpec`` makes this easy to manage programatically,
but for now let's start one by hand::

    $ docker run --name empty-server --publish 80 --detach nginx:1.10.3-alpine
    
Next, if you haven't already, start Django::

    $ python manage.py runserver
    
and visit: http://localhost:8000/docker/empty-server

You should see the Nginx welcome page: ``django_docker_engine`` has determined the port the container was assigned,
and has proxied your request. 

.....
Docker Engine on AWS-EC2
.....

TODO: It should be possible to do it almost exactly the same way,
except that the Docker instance is running on an EC2 instance.

.....
Docker Engine via AWS-ECS
.....

TODO: Instead of interacting directly with the Docker Engine,
use the AWS-ECS API.

For the AWS-ECS tests to work, a rather extensive set of permissions is necessary.
These can be assigned with the ``set_user_policy.py`` script.

-------
Usage: Launching Containers
-------

``DockerContainerSpec`` exposes a subset of Docker functionality so your application can launch containers as needed.
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

Note that this is only a Docker utility: You could persist this information in a database, but that is not a requirement.

For more detail, consult the `generated documentation <docs.md>`_.

-----------
Development
-----------

::

    git clone https://github.com/mccalluc/django_docker_engine.git
    cd django_docker_engine
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    python manage.py test --verbosity=2

TODO: The tests need to be better at cleaning up the resources they create.
Until then, keep an eye on the web console:

- `CloudFormation Stacks <https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filter=active>`_

When you delete a CloudFormation stack, it should also take care of the lower level resources:

- `Security Groups <https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#SecurityGroups:search=django_docker_;sort=groupId>`_
- `EC2 Instances <https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:search=django_docker_;sort=keyName>`_
- `Task Definitions <https://console.aws.amazon.com/ecs/home?region=us-east-1#/taskDefinitions>`_
- `Clusters <https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters>`_
- `Logs <https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logs:>`_

or use AWS-CLI (TODO: Better filtering so we delete only test ones, not the production ones.)::

    aws cloudformation list-stacks \
        --query 'StackSummaries[].[StackName]' \
        --output text | \
    grep django-docker | \
    xargs -n 1 aws cloudformation delete-stack --stack-name

... and, again, you can consider the lower level resources, though that shouldn't be necessary::

    aws ec2 describe-instances \
        --filters Name=tag:project,Values=django_docker_engine \
        --query 'Reservations[].Instances[].[InstanceId]' \
        --output text | \
    xargs aws ec2 terminate-instances --instance-ids

    aws ec2 describe-security-groups \
        --filters Name=description,Values='Security group for django_docker_engine' \
        --query 'SecurityGroups[].[GroupId]' \
        --output text | \
    xargs -n 1 aws ec2 delete-security-group --group-id

    aws ecs list-clusters \
        --query 'clusterArns' \
        --output text | \
    xargs -n 1 aws ecs delete-cluster --cluster

    aws logs describe-log-groups \
        --query 'logGroups[].[logGroupName]' \
        --output text | \
    xargs -n 1 aws logs delete-log-group --log-group-name

(It seems that tasks can not be deleted, they can only be "deregistered".)

---------
Debugging
---------


ssh -i ~/.ssh/django_docker_cloudformation.pem ec2-user@INSTANCE_IP

------------
Dependencies
------------

- `docker-py <https://github.com/docker/docker-py>`_: The official
  Python SDK for Docker. It uses much the same vocabulary as the CLI,
  but with some `subtle differences <https://github.com/docker/docker-py/issues/1510>`_
  in meaning. It's better than the alternatives: calling
  the CLI commands as subprocesses, or hitting the socket API directly.

- `boto <http://boto3.readthedocs.io/en/latest/>`_: AWS Python SDK.

- `django-http-proxy <https://github.com/yvandermeer/django-http-proxy>`_:
  Makes Django into a proxy server. It looks like this package has thought about
  some of the edge cases, like rewriting absolute URLs in the body content.

----------------
Related projects
----------------

- `sidomo <https://github.com/deepgram/sidomo>`_: Wrap containers
  as python objects, but assumes input -> output, rather than a
  long-running process.

- `Dockstore <https://dockstore.org/docs/about>`_:
  Docker containers described with CWL.

- `BioContainers <http://biocontainers.pro/docs/developer-manual/developer-intro/>`_:
  A set of best-practices, a community, and a registry of containers
  built for biology. Preference given to BioConda?
