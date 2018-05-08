class AuthBackend():
    def authenticate(self, username=None, password=None):
        return 'fake-user'


class _User():
    def __init__(self):
        self.is_active = True

    def get_username(self):
        return 'fake-username'


class AuthMiddleware():
    def process_request(self, request):
        request.user = _User()
