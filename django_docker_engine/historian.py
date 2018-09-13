from __future__ import print_function

from datetime import datetime
import os
from tempfile import mkdtemp


class NullHistorian():
    """
    Satisfies the Historian interface, but does nothing.
    """

    def __init__(self):
        pass

    def record(self, container_id, url):
        pass


class FileHistorian():
    """
    Records incoming requests to a file, and provides access to the records
    in that file.

    Not suitable for production use.
    """

    DIR = mkdtemp(suffix='-history')

    def __init__(self):
        pass

    def _path(self, container_id):
        return os.path.join(FileHistorian.DIR, container_id)

    def record(self, container_id, url):
        with open(self._path(container_id), 'a') as f:
            timestamp = datetime.now().isoformat()
            print('\t'.join([timestamp, url]), file=f)

    def list(self, container_id):
        with open(self._path(container_id)) as f:
            return f.readlines()

    def last_timestamp(self, container_id):
        return os.path.getmtime(self._path(container_id))
