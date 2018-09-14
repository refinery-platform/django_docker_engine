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
            print('\t'.join([timestamp, url]), file=f)

    def list(self, container_id):
        with open(self._path(container_id)) as f:
            return f.readlines()

    def last_timestamp(self, container_id):
        return os.path.getmtime(self._path(container_id))
