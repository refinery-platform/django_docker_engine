from django.conf.urls import include, url

urlpatterns = [url(r'^docker/', include('demo_path_routing.proxy_url_patterns'))]
