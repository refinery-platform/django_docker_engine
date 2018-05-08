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


class AuthMiddlewareCallable():
    def __init__(self, get_response):
        self.get_response = get_response
        self.middleware = AuthMiddleware()

    def __call__(self, request):
        self.middleware.process_request(request)
        return self.get_response(request)
