class RequestDebuggingMiddleware():
    def process_request(self, request):
        with open('/tmp/test-log.txt', 'a') as f:
            f.write(request.path + '\n')
        return None