tools = {
    'debugger': {
        'image': 'scottx611x/refinery-developer-vis-tool:v0.0.7',
        'input': lambda url, prefix: {'file_relationships': [url]}
    },
    'lineup': {
        'image': 'mccalluc/lineup_refinery:v0.0.8',
        'input': lambda url, prefix: {'file_relationships': [url]}
    },
    'heatmap': {
        'image': 'mccalluc/heatmap_scatter_dash:v0.1.8',
        'input': lambda url, prefix: {
            'file_relationships': [
                [url],  # Count data
                []  # Differential expression data
            ],
            'parameters': [],
            'api_prefix': prefix,
            'extra_directories': '/refinery-data/'
        }
    }
}
