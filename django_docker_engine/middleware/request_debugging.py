class RequestDebuggingMiddleware():
    def process_request(self, request):
        with open('/tmp/test-log.txt', 'a') as f:
            f.write(request.get_raw_uri() + '\n')
        return None