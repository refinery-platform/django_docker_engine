tools = {
    'debugger': {
        'image': 'scottx611x/refinery-developer-vis-tool:v0.0.7',
        'description': 'Echos the user input',
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'lineup': {
        'image': 'mccalluc/lineup_refinery:v0.0.8',
        'description': 'Aggregate and sort heterogeneous data',
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'intervene': {
        'image': 'mccalluc/intervene:v0.0.4',
        'description': 'Variety of set intersection visualizations',
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'higlass': {
        'image': 'scottx611x/refinery-higlass-docker:v0.3.2',
        'description': '1-D and 2-D genomic data browser',
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
        'description': 'Heatmap and scatterplots for gene expression data',
        'input': lambda urls, prefix: {
            'file_relationships': [
                urls,  # Count data
                []  # Differential expression data
            ],
            'parameters': [],
            'api_prefix': prefix,
            'extra_directories': ['/refinery-data/']
        }
    }
}
