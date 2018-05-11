# Path-based routing + user authentication

This demo adds user authentication to the basic
[path-based routing](../demo_path_routing_no_auth).
The `setup-db.sh` script needs to be run before starting this demo: It runs
migrations and creates a test user.

`django_docker_engine` itself has no
functionality related to users, but if a proxy is incorrectly configured,
sessions cookies can be lost: This demo gives us a place to make sure that
does not happen.