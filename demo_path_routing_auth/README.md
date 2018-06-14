# Path-based routing + user authentication

This demo adds user authentication to the basic
[path-based routing](../demo_path_routing_no_auth).

```bash
$ demo_path_routing_auth/setup-db.sh
  # Does migrations and user creation.
$ ./manage_auth.py runserver
  # The same as "manage.py", except it points here.
```

`django_docker_engine` itself has no
functionality related to users, but if a proxy is incorrectly configured,
sessions cookies can be lost: This demo gives us a place to make sure that
does not happen.

Symlinks from the other demos point here only because this has more files than
the others, but the choice is essentially arbitrary: This one should not be
taken as a default or anything like that.