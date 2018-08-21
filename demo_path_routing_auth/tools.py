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
        'image': 'mccalluc/intervene:v0.0.4',
        'description': 'Set intersection visualizations',
        'default_parameters': [],
        'default_files': ['fruit.txt', 'green.txt', 'sweet.txt', 'vegetable.txt'],
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'igv-js': {
        'image': 'gehlenborglab/docker_igv_js:v0.0.9',
        'description': 'Our wrapper for IGV.js',
        'default_parameters': [
            {'name': 'Genome Build',
             'value': 'hg19'}
        ],
        'default_files': ['3x3.csv'],
        'input': lambda urls, prefix: {'file_relationships': urls}
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
            'file_relationships': [urls, []],
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
            'file_relationships': [urls, []],
            'extra_directories': ['/data/']
        }
    }
}
