from __future__ import print_function

import errno
import os
from datetime import datetime


class NullHistorian():
    """
    Satisfies the Historian interface, but does nothing.
    """

    def __init__(self):
        pass

    def record(self, container_id, url):
        pass

    def list(self, container_id):
        return []

    def last_timestamp(self, container_id):
        return 0


class FileHistorian():
    """
    Records incoming requests to a file, and provides access to the records
    in that file.
    """

    DIR = '/tmp/django-docker-file-historian'

    def __init__(self):
        # mkdir -p: https://stackoverflow.com/a/600612
        try:
            os.makedirs(FileHistorian.DIR)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(FileHistorian.DIR):
                pass
            else:
                raise

    def _path(self, container_id):
        return os.path.join(FileHistorian.DIR, container_id)

    def record(self, container_id, url):
        with open(self._path(container_id), 'a') as f:
            timestamp = datetime.now().isoformat()
            print('\t'.join([timestamp, '/' + url]), file=f)

    def list(self, container_id):
        with open(self._path(container_id)) as f:
            return [line.rstrip().split('\t') for line in f]

    def _last_timestamp(self, container_id):
        return os.path.getmtime(self._path(container_id))

    def sort_lru(self, container_id_set):
        '''
        Returns the container IDs sorted with the least-recently-used first.
        '''
        id_timestamp_pairs = [
            (id, self._last_timestamp(id)) for id in container_id_set
        ]
        return [
            pair[0] for pair in
            sorted(id_timestamp_pairs, key=lambda pair: pair[1])
        ]
