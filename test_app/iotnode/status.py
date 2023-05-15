""" API to indicate the status of UI in the application.

The application is currently used to get the following information:

 1. Data From IoT Node Interface
 2. Connection Status
"""

import queue
import time

from enum import Enum


class Status(Enum):
    GOOD = 0
    FAULTY = 1
    NOT_CONNECTED = 2


class StatusIndicator:
    """Indicates the status of the UI."""
    STATUS_GOOD = 5
    STATUS_FAULT = 3
    MAX_SIZE = 10

    def __init__(self, cb):
        self._get_poll_period_cb = cb
        self._dataqueue = queue.Queue(maxsize = self.MAX_SIZE)

    def collect_data(self, data: dict, timestamp: float):
        """Collect data from the IoT interface

        Args:
           data: data received on IoT interface, part of callback spec
           timestamp: current timestamp, in seconds
        """

        if self._dataqueue.full():
            self._dataqueue.get()
        self._dataqueue.put(timestamp)

    def get_connection_status(self) -> Status:
        """Provides the status of connection to UI.

        Returns:
            Status of connection
        """

        current_time = time.time()
        poll_period = self._get_poll_period_cb()

        for timestamp in list(self._dataqueue.queue):
            if (current_time - (poll_period * 10)) <= timestamp:
                break
            self._dataqueue.get()

        qsize = self._dataqueue.qsize()
        if qsize >= self.STATUS_GOOD:
            return  Status.GOOD
        if qsize >= self.STATUS_FAULT:
            return Status.FAULTY

        return Status.NOT_CONNECTED
