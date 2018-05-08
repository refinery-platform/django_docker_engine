class AuthBackend(object):
    def authenticate(self, username=None, password=None):
        return 'fake-user'
        # if username and password:
        #    try:
        #        response = my_auth_function(username, password)
        #        if response.status_code == 200:
        #            token = response.get('my_key')
        #            user = MyUser()
        #            return user
        #     except MyCustomException:
        #           return None