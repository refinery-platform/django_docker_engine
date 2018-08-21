# Visualization author documentation

`django_docker_engine` exists to make web-based visualizations reusable:
If you can wrap your visualization in a container image, and adhere to a few
conventions, your tool will remain useful and usable even when you've moved
on to other projects.

We'll outline here what a container image is and how to build one, what
particular conventions `django_docker_engine` requires, some gotchas to be aware
of, and how to publish your tool.

## Building the image

If you haven't worked with containers before, read this
[introduction to Docker](https://docs.docker.com/get-started/), and try the
examples in this [introcution to containers](https://docs.docker.com/get-started/part2/).
The container ecology is complicated, but you only need to focus on one part,
building your container and pushing it to a repository.
Hopefully you can base your work on one of our examples.

A `Dockerfile` gives step-by-step instructions for building an image, and
the first line gives the base image to build on top of: Base images are available
for every popular language and framework. After that you will add any additional
libraries you require, and finally the code for your particular project.
Here are samples from some of our projects:

- [Python](https://github.com/refinery-platform/heatmap-scatter-dash/blob/master/context/Dockerfile)
- [R Shiny](https://github.com/refinery-platform/intervene-refinery-docker/blob/master/context/Dockerfile)
- [JS](https://github.com/refinery-platform/lineup-refinery-docker/blob/master/context/Dockerfile)*

The JS example is different: The visualization is purely client-side, but because a
small script to process the input on startup is required, the base image is
actually Python.

It is best practice for your `Dockerfile` to be under version control, and to use
Travis to build and push your images on successful commits. Whether this is the same
repo as the rest of your source code will depend on your situation:
- If your visualization will be used primarily through `django_docker_engine`,
or if the code base and build process are relatively simple, it makes sense to
keep it all in one repo
- If there are other use cases for the visualization, if you are wrapping a
3rd party tool, or if the build process is already complicated, then it probably
makes more sense set up a separate repo.

## Inputs

When your container starts up, an environment variable will specify the inputs
for the tool. Either `INPUT_JSON` will be set to a JSON document,
or `INPUT_JSON_URL` will point to the document.
The document will look like [this](https://github.com/refinery-platform/docker_igv_js/blob/master/input_fixtures/good/input.json).
- Input files are provided as a list of URLs under `file_relationships`.
- Detailed metadata for each file in the dataset, not just your input, is provided
in `node_info`.
- User supplied strings or numbers are available in `parameters`.

## Development

To run your container locally, check out this project and add a description of your
tool to `tools.py`, and start the demo with `python ./manage.py runserver`.
The `image` field can reference images either on DockerHub or in your local cache.

## Gotchas

There are a few things to be careful about when wrapping your tool.

- **Port 80**: `django_docker_engine` assumes your tool will use port 80. 
(Other ports can be accomodated, but that requires additional configuration.)
- **Relocatable**: There will be a prefix in the path when your tool is served.
No URLs you use should begin with `/`. The prefix is available in the
`api_prefix` of your input.json.
- **Keep the cookies**: Your tool will ultimately be run inside django, so the django
session cookie needs to be preserved on any AJAX requests you make. Right now,
FF and Chrome have slightly different implementations of the HTML5 Fetch API
in this regard.
- **No WebSockets**: WebSockets are a step beyond HTTP, and won't work across plain
HTTP proxies like we use.
- **No server state**: There are no provisions right
now to preserve sessions or to make them available with restarts. Instead, try
to update the query portion of the URL.
- **Logging**: The Docker way to log is simply to output to STDOUT. If any files
are updated or created, they should be listed in the `extra_directories` of your spec.
*Warning*: The container itself has only limited disk space by default.
This space can be exhausted if you write large log files or create a database
outside `extra_directories`.
- **Friendly error page**: Until your tool has fully started, it should either
not reply, or reply with a non-200 response to requests for `/`. Once it has
started, a 200 should be returned. If your tool can't start for some reason,
please still respond with 200, but give an error message in the body instead.
Until requests for `/` return 200, `django_docker_engine` will keep a
please-wait page up.

## Pushing to DockerHub

DockerHub is the most prominent repository of docker images. It is our source
for base images, and we push our own containerized tools back there as well. Once
you have registered for an account, you could push images by hand, but it is better
to add encrypted credentials to your `.travis.yaml` and have Travis do it for you
on successful tagged builds. Here's a [script](https://github.com/refinery-platform/intervene-refinery-docker/blob/master/after_success.sh)
that many of our projects use.

## Publishing

Once you've pushed your image to DockerHub, you need to let the community know about it.
PRs to this repo which add to `tools.py` are welcome, and you should make a similar
addition to the [list of Refinery tools](https://github.com/refinery-platform/visualization-tools/tree/master/tool-annotations).