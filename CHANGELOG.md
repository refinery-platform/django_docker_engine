# Change Log

## [v.0.1.0](https://pypi.org/project/django-docker-engine/0.1.1/) (Sep 24, 2018)

* Remove the option for passing inputs via file mounting.
* Start measuring test coverage: Minimum can be improved over time.
* Support Python 3.7.

## [v.0.1.0](https://pypi.org/project/django-docker-engine/0.1.0/) (Sep 19, 2018)

With this release there's a big philosophical change: Instead of leaving the
user responsible for cleaning up older containers, now `django_docker_engine`
will see how much memory is required for a new container, and kill older
containers until the required space has been freed.
To do this, it needs to know how much total memory is available to Docker, and
how much memory should be reserved for a given container. The purge methods
are still available, but may be removed in a future release if this approach
proves workable.


## [v0.0.62](https://pypi.org/project/django-docker-engine/0.0.62/) (Aug 21, 2018)

* Allow remote URLs as demo inputs, and not just local files.
* Add is_live().
* Add tools to demo.
* Documentation for tool authors.


## [v0.0.61](https://pypi.org/project/django-docker-engine/0.0.61/) (Aug 1, 2018)

* Tool parameters can be specified in demo.
* Sensible defaults provided for demo tools.


## [v0.0.60](https://pypi.org/project/django-docker-engine/0.0.60/) (Jul 23, 2018)

* Make log exposure optional.
* In the demo, allow containers to be launched with multiple input files.


## [v0.0.59](https://pypi.org/project/django-docker-engine/0.0.59/) (Jul 10, 2018)

* Expose logs in UI.


## [v0.0.58](https://pypi.org/project/django-docker-engine/0.0.58/) (Jun 14, 2018)

* Avoid session cookie collisions. Expose logs in API.


## [v0.0.57](https://pypi.org/project/django-docker-engine/0.0.57/) (May 11, 2018)

* Demonstrate interactions with Django sessions.
