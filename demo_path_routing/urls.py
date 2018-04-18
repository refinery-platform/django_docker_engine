from django.conf.urls import include, url
import pdb; pdb.set_trace()
urlpatterns = [
    url(r'^docker/', include(__package__ + '.proxy_url_patterns'))]
