import re
import unittest
from datetime import datetime
from time import sleep

from django_docker_engine.historian import FileHistorian


class FileHistorianTests(unittest.TestCase):

    def test_file_historian(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        id_1 = timestamp + '-1'
        id_2 = timestamp + '-2'
        id_3 = timestamp + '-3'
        id_4 = timestamp + '-4'

        historian = FileHistorian()
        historian.record(id_1, 'foo?')
        historian.record(id_2, 'bar?')
        historian.record(id_1, 'FOO!')

        sleep(1)
        # Can't rely on sub-second resolution being available,
        # and since we're looking at file-system modification dates,
        # using freezegun or mocking at a high-level wouldn't work.

        historian.record(id_2, 'BAR!')
        historian.record(id_3, 'zig')
        historian.record(id_4, 'zag')

        self.assertEqual(
            ['/foo?', '/FOO!'],
            [pair[1] for pair in historian.list(id_1)]
        )

        self.assertGreater(
            historian._last_timestamp(id_2),
            historian._last_timestamp(id_1)
        )

        lru = historian.lru({id_1, id_2, id_3, id_4})
        self.assertEqual(lru, id_1)

        sleep(1)
        historian.record(id_1, 'no longer the least recent!')

        lru = historian.lru({id_1, id_2, id_3, id_4})
        self.assertNotEqual(lru, id_1)
