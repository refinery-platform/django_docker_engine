# User input and containerized vidualizations

How do existing dockerized visualizations get their backing data? Are there idioms we can expect outside authors to follow?

Conclusions:
- Docker documentation is often an afterthought, though there are exceptions. Often just a copy of github docs.
- Surprised by the number of desktop applications.
- Mounting a /data volume is the usual approach to getting files in there, though we also see STDIN, sockets, and providing credentials for an API.


## Best Webapp Examples:

https://hub.docker.com/r/gehlenborglab/higlass/
	Data to be visualized must be in a mounted volume, and after boot ingest_tileset must be run. (I could imagine every file in the mounted volume being ingested on start up, with a mapping from filenames to uids, with the software also generating a plausible viewconf for a given set of files.)

https://hub.docker.com/r/vanessa/cogatvoxel/
	Visualizing Brain anatomy? Data is baked in?
	
https://hub.docker.com/r/tddv/superset/
	OLAP: Guess you provide connection info for DB somehow?
	
	

## Other Webapps:
	
https://hub.docker.com/r/centurylink/imagelayers-ui/ -> http://imagelayers.io
	Tool for examining shared dependencies between images. Seems broken right now, but I think the docker tag is passed as a URL parameter, and then it hits the dockerhub API.
	
https://hub.docker.com/r/ouven/akka-visual-mailbox-visualization/
	Visualize the state of a message passing system. (Reminds me of Erlang?) Web app, but another port is opened up where communication with the monitored system takes place.

https://hub.docker.com/r/jldowns/vatic-docker/
	Manage mechanical turk video annotation tasks. Mounted volumes for input and output files.
	
https://hub.docker.com/r/inistcnrs/ezvis/
	Visualization of natural language corpus. Example data hard coded?
	
https://hub.docker.com/r/centurylink/image-graph/
	Visualizing docker images. Mount the socket file to get information about the local Docker. Can either produce as output a PNG, or run as a webapp.
		
	
	
## Desktop:

https://hub.docker.com/r/nitnelave/deepvis/
	Visualizing deep learning on image data. Desktop app rather than web app: I guess it works with X Window client-server, or something like that?
	
https://hub.docker.com/r/jupedsim/jpsvis/
	Pedestrian behavior simulator. Visualize output trajectory files.
	
https://hub.docker.com/r/gtrafimenkov/logstalgia/
	Server log analysis. Mount the directory containing the log.
	
https://hub.docker.com/r/gtrafimenkov/codeswarm/
	Visualize software project history. Mount the repo to visualize. Output is non-interactive video, I think?
	
https://hub.docker.com/r/jonasrauber/c2s/
	Neuroscience signal processing and visualization. Mount a data directory
	
	

## Other / Unclear:


https://hub.docker.com/r/funkwerk/compose_plantuml/
	Generate UML from docker-compose specs. STDIN / STDOUT

https://hub.docker.com/r/3dechem/largevis/
	Sci-vis: high dimensional clustering. Mount a volume with the data on start. Produces output file.

https://hub.docker.com/r/stennie/ubuntu-mtools/

https://hub.docker.com/r/sevenbridges/maftools/
	An R package? Docker container installs R and libraries.

https://hub.docker.com/r/shopuz/alveo-visualization/
	Unclear / Broken? I think it relies on an outside API to provide metadata on a corpus of human language data.

https://hub.docker.com/r/ecomobi/visualization/
	Stub? The company is something like a web ad network for southeast Asia...
	
https://hub.docker.com/r/mathiask/weatherdb-visualization/
	Stub?
	
https://hub.docker.com/r/stefan125/sofia-service-osgi-visualization-ui/
	Stub?
	
https://hub.docker.com/r/kennethzfeng/pep-visualize/
	Not sure where the data comes from.