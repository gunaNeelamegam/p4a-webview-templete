import time

import unittest
from unittest import mock

from .status import StatusIndicator, Status

class StatusIndicatorTestCase(unittest.TestCase):
    def setUp(self):
        self.get_poll_period_cb = mock.Mock()
        self.get_poll_period_cb.return_value = 0.5

        self.status_ind = StatusIndicator(self.get_poll_period_cb)

    def test_connection_status_bad_on_empty_queue(self):
        out = self.status_ind.get_connection_status()

        self.assertEqual(Status.NOT_CONNECTED, out)

    def test_connection_status_bad_after_good(self):
        now = time.time()
        last = now - (self.get_poll_period_cb() * 30)

        for i in range(12):
            self.status_ind.collect_data(None, last + (i))

        out = self.status_ind.get_connection_status()

        self.assertEqual(Status.NOT_CONNECTED, out)

    def test_connection_status_good(self):
        now = time.time()

        for _ in range(5):
            self.status_ind.collect_data(None, now)

        out = self.status_ind.get_connection_status()

        self.assertEqual(Status.GOOD, out)

    def test_connection_status_faulty(self):
        now = time.time()

        for _ in range(3):
            self.status_ind.collect_data(None, now)

        out = self.status_ind.get_connection_status()

        self.assertEqual(Status.FAULTY, out)
