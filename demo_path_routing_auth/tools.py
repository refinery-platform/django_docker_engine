class Tool():
    '''
    Tool definition, analogous to those in
    https://github.com/refinery-platform/visualization-tools

    image: Dockerhub image with version tag
    description: Displayed in UI
    default_parameters: In demo, user can edit JSON.
      (In Refinery, there is a UI.)
    default_files: Should match values in demo-data.csv.
      (Doesn't need to be every possible valid input from that file.)
    input_f: Lambda which returns a dict which becomes the INPUT_JSON.
    container_port: If the tool uses a port other than 80.
    mem_reservation_mb: Expected memory use in MB.
    '''
    # In 3.7, default values are supported for namedtuples. Until then:

    def __init__(self, image, description, mem_reservation_mb,
                 default_parameters=None, default_files=None,
                 container_port=None, input_f=None):
        self.image = image
        self.description = description
        self.mem_reservation_mb = mem_reservation_mb
        self.default_parameters = [] \
            if default_parameters is None else default_parameters
        self.default_files = ['3x3.csv'] \
            if default_files is None else default_files
        self.container_port = 80 \
            if container_port is None else container_port
        self.input_f = (lambda urls, prefix: {
            'file_relationships': urls,
            'extra_directories': []
        }) if input_f is None else input_f


tools = {
    'debugger': Tool(
        'scottx611x/refinery-developer-vis-tool:v0.0.7',
        'Echo the user input',
        mem_reservation_mb=15
    ),
    'lineup': Tool(
        'mccalluc/lineup_refinery:v0.0.8',
        'Aggregate and sort heterogeneous data',
        mem_reservation_mb=11
    ),
    'intervene': Tool(
        'mccalluc/intervene:v0.0.5',
        'Set intersection Shiny app',
        default_files=['mESC.genes', 'Myotube.genes',
                       'pro-B.genes', 'Th-cell.genes'],
        mem_reservation_mb=208
    ),
    'shiny-demo': Tool(
        'mccalluc/shiny-heatmap-refinery:v0.0.2',
        'Trivial Shiny app',
        container_port=3838,
        mem_reservation_mb=120
    ),
    'igv-js': Tool(
        'gehlenborglab/docker_igv_js:v0.0.9',
        'Our wrapper for IGV.js',
        default_parameters=[
            {'name': 'Genome Build',
             'value': 'hg19'}
        ],
        default_files=['NC_009084.gff'],
        input_f=lambda urls, prefix: {
            'extra_directories': [],
            'node_info': {
                'fake-uuid-{}'.format(i): {
                    'file_url': url,
                    'node_solr_info': {
                        'name': 'fake-name-{}'.format(i)
                    }
                }
                for (i, url) in enumerate(urls)
            },
        },
        mem_reservation_mb=15
    ),
    'higlass': Tool(
        'scottx611x/refinery-higlass-docker:v0.3.2',
        '1-D and 2-D genomic data browser',
        default_files=['gene_annotations.short.db', 'cnv_short.hibed'],
        input_f=lambda urls, prefix: {
            'node_info': {
                'fake-uuid-{}'.format(i): {'file_url': url}
                for (i, url) in enumerate(urls)
            },
            'extra_directories': ['/refinery-data/']
        },
        mem_reservation_mb=100  # Highly variable
    ),
    'rna-seq': Tool(
        'mccalluc/heatmap_scatter_dash:v0.1.15',
        'Linked visualization for gene expression',
        input_f=lambda urls, prefix: {
            'file_relationships': urls,
            'api_prefix': prefix,
            'extra_directories': ['/refinery-data/']
        },
        mem_reservation_mb=74
    ),
    'multiqc': Tool(
        'mccalluc/qualimap_multiqc_refinery:v0.0.7',
        'Wrapper for MultiQC',
        default_files=['raw_data_qualimapReport.zip'],
        input_f=lambda urls, prefix: {
            'file_relationships': urls,
            'extra_directories': ['/data/']
        },
        mem_reservation_mb=20
    )
}
