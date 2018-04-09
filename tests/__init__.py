NGINX_IMAGE = 'nginx:1.10.3-alpine'  # TODO: only use ECHO_IMAGE?
ALPINE_IMAGE = 'alpine:3.6'
ECHO_IMAGE = 'jmalloc/echo-server'  # TODO: pin version


class TestUser(object):
    is_active = True

    def get_username(self):
        return "test user"
