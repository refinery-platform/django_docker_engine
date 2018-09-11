# The CSV also specifies which tool goes with each file... but I could imagine
# listing multiple incompatible input sets there. The default_files here can
# just be a simple, coherent example to start from.

tools = {
    'debugger': {
        'image': 'scottx611x/refinery-developer-vis-tool:v0.0.7',
        'description': 'Echo the user input',
        'default_parameters': [],
        'default_files': ['3x3.csv'],
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'lineup': {
        'image': 'mccalluc/lineup_refinery:v0.0.8',
        'description': 'Aggregate and sort heterogeneous data',
        'default_parameters': [],
        'default_files': ['3x3.csv'],
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'intervene': {
        'image': 'mccalluc/intervene:v0.0.5',
        'description': 'Set intersection Shiny app',
        'default_parameters': [],
        'default_files': ['mESC.genes', 'Myotube.genes', 'pro-B.genes', 'Th-cell.genes'],
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'shiny-demo': {
        'image': 'mccalluc/shiny-heatmap-refinery:v0.0.2',
        'description': 'Trivial Shiny app',
        'default_parameters': [],
        'default_files': ['3x3.csv'],
        'input': lambda urls, prefix: {'file_relationships': urls},
        'container_port': 3838
        # Not sure why it needs to be 3838...
        # but it's also good to exercise container_port.
        # https://github.com/refinery-platform/shiny-heatmap-refinery/issues/2
    },
    'igv-js': {
        'image': 'gehlenborglab/docker_igv_js:v0.0.9',
        'description': 'Our wrapper for IGV.js',
        'default_parameters': [
            {'name': 'Genome Build',
             'value': 'hg19'}
        ],
        'default_files': ['NC_009084.gff'],
        'input': lambda urls, prefix: {
            'node_info': {
                'fake-uuid-{}'.format(i): {
                    'file_url': url,
                    'node_solr_info': {
                        'name': 'fake-name-{}'.format(i)
                    }
                }
                for (i, url) in enumerate(urls)
            },
        }
    },
    'higlass': {
        'image': 'scottx611x/refinery-higlass-docker:v0.3.2',
        'description': '1-D and 2-D genomic data browser',
        'default_parameters': [],
        'default_files': ['gene_annotations.short.db', 'cnv_short.hibed'],
        'input': lambda urls, prefix: {
            'node_info': {
                'fake-uuid-{}'.format(i): {'file_url': url}
                for (i, url) in enumerate(urls)
            },
            'extra_directories': ['/refinery-data/']
        }
    },
    'rna-seq': {
        'image': 'mccalluc/heatmap_scatter_dash:v0.1.8',
        'description': 'Linked visualization for gene expression',
        'default_parameters': [],
        'default_files': ['3x3.csv'],
        'input': lambda urls, prefix: {
            'file_relationships': urls,
            'api_prefix': prefix,
            'extra_directories': ['/refinery-data/']
        }
    },
    'multiqc': {
        'image': 'mccalluc/qualimap_multiqc_refinery:v0.0.7',
        'description': 'Wrapper for MultiQC',
        'default_parameters': [],
        'default_files': ['raw_data_qualimapReport.zip'],
        'input': lambda urls, prefix: {
            'file_relationships': urls,
            'extra_directories': ['/data/']
        }
    }
}
