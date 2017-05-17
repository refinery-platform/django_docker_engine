from url_utils import proxy_url

urlpatterns = [
    proxy_url()

    # During development, it's useful to be able to test proxying,
    # without also needing to start a container.
    # url(r'^proxy_any_host/(?P<host>[^/]*)/(?P<url>.*)$',
    #     lambda request, host, url:
    #         HttpProxy.as_view(
    #             base_url='http://{}/'.format(host)
    #         )(request, url=url)
    # ),
]
