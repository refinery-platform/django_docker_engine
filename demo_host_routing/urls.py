from django.conf.urls import include, url


urlpatterns = [
    url(r'^docker/', include(__package__ + '.proxy_url_patterns'))
]
