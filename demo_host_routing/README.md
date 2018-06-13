# Hostname-based routing

This demonstrates hostname-based routing. This option is more complicated than
the default, [path-based routing](../demo_path_routing_no_auth) because

- it requires `HostnameRoutingMiddleware`,
- and you will need to set up a wildcard entry in DNS to capture all subdomains.
- but the webapp can use paths starting with "/".

Because of the dependency on DNS, this demo will not work out-of-the-box,
and it does not have a UI, but it is used by the tests.