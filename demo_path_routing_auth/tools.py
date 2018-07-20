tools = {
    'debugger': {
        'image': 'scottx611x/refinery-developer-vis-tool:v0.0.7',
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'lineup': {
        'image': 'mccalluc/lineup_refinery:v0.0.8',
        'input': lambda urls, prefix: {'file_relationships': urls}
    },
    'higlass': {
        'image': 'scottx611x/refinery-higlass-docker:v0.3.2',
        'input': lambda urls, prefix: {
            'node_info': {
                'fake-uuid-{}'.format(i): {'file_url': url}
                for (i, url) in enumerate(urls)
            },
            'extra_directories': ['/refinery-data/']
        }
    },
    'heatmap': {
        'image': 'mccalluc/heatmap_scatter_dash:v0.1.8',
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
