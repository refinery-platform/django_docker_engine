from demo_path_routing_auth.proxy import AuthProxy

urlpatterns = AuthProxy(logs_path='docker-logs').url_patterns()
