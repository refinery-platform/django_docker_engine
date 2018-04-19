from __future__ import print_function

from datetime import datetime


class NullHistorian():
    """
    Satisfies the Historian interface, but does nothing.
    """

    def __init__(self):
        pass

    def record(self, *args):
        pass


class FileHistorian():
    """
    Records incoming requests to a file, and provides access to the records
    in that file.

    Not suitable for production use.
    """

    def __init__(self, path):
        self.path = path

    def record(self, *args):
        with open(self.path, 'a') as f:
            timestamp = datetime.now().isoformat()
            args_list = list(args)
            args_list.insert(0, timestamp)
            print('\t'.join(args_list), file=f)

    def list(self):
        with open(self.path) as f:
            lines = f.readlines()
        return lines
