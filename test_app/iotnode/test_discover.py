"""
Test Case file for mdns scan
"""

import asyncio
from platform import machine
import socket
from unittest.mock import patch
from unittest.mock import Mock
from aiozeroconf import ServiceStateChange
import aiounittest
from .discover import MachineDiscover, Machine
from . import discover


class MdnsScanTestCase(aiounittest.AsyncTestCase):
    SLEEP_TIME = .00001

    def setUp(self):
        send_event_cb = Mock()
        self.machine_discover = MachineDiscover(send_event_cb)

    def mk_zeroconf_mock(self):
        patcher = patch("iotnode.discover_android.Zeroconf")
        zeroconf_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("iotnode.discover_android.ServiceBrowser")
        service_browser_mock = patcher.start()
        self.addCleanup(patcher.stop)

        return zeroconf_mock, service_browser_mock

    def notify_new_service(self, name, zeroconf_mock, service_browser_mock):
        on_service_state_change = service_browser_mock.call_args[1]["handlers"][0]
        on_service_state_change(zeroconf_mock, "", name, ServiceStateChange.Added)

    async def test_valid_data(self):
        """
        Method to check the mdns module returns the valid data
        """
        zeroconf_mock, service_browser_mock = self.mk_zeroconf_mock()

        machinelist_future = asyncio.ensure_future(self.machine_discover.list_machine(1))

        f1 = asyncio.Future()
        f1.set_result(Mock(address=socket.inet_aton("172.16.0.1"), port=80))
        f2 = asyncio.Future()
        f2.set_result(Mock(address=socket.inet_aton("172.16.2.0"), port=90))
        f3 = asyncio.Future()
        f3.set_result(Mock(address=socket.inet_aton("172.16.3.0"), port=90))
        f4 = asyncio.Future()
        f4.set_result(Mock(address=socket.inet_aton("172.16.4.0"), port=90))
        zeroconf_mock.get_service_info.side_effect = [f1, f2, f3, f4]
        await asyncio.sleep(self.SLEEP_TIME)

        self.notify_new_service("iotnode_00", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iotnode_01", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iotnode_02", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iotnode_03", zeroconf_mock, service_browser_mock)

        demodata = [
            Machine(name='iotnode_00', ip='172.16.0.1', port=80),
            Machine(name='iotnode_01', ip='172.16.2.0', port=90),
            Machine(name='iotnode_02', ip='172.16.3.0', port=90),
            Machine(name='iotnode_03', ip='172.16.4.0', port=90)
        ]

        await machinelist_future
        self.assertEqual(demodata, machinelist_future.result())


    async def test_invalid_data(self):
        """
        Method for checked with invalid data
        """
        zeroconf_mock, service_browser_mock = self.mk_zeroconf_mock()

        machinelist_future = asyncio.ensure_future(self.machine_discover.list_machine(1))

        f1 = asyncio.Future()
        f1.set_result(Mock(address=socket.inet_aton("172.14.0.1"), port=80))
        f2 = asyncio.Future()
        f2.set_result(Mock(address=socket.inet_aton("172.16.0.0"), port=90))
        zeroconf_mock.get_service_info.side_effect = [f1, f2]

        await asyncio.sleep(self.SLEEP_TIME)

        self.notify_new_service("iotnode", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iotnode", zeroconf_mock, service_browser_mock)

        demodata = [
            Machine(name='iotnode_00', ip='172.16.0.9', port = 80),
            Machine(name='iotnode_01', ip='172.16.2.8', port=90)
        ]
        await machinelist_future
        self.assertNotEqual(demodata, machinelist_future.result())

    async def test_mdns_filter(self):
        """
        Method for checked with invalid data
        """
        zeroconf_mock, service_browser_mock = self.mk_zeroconf_mock()

        machinelist_future = asyncio.ensure_future(self.machine_discover.list_machine(1))

        f1 = asyncio.Future()
        f1.set_result(Mock(address=socket.inet_aton("172.14.0.1"), port=80))
        f2 = asyncio.Future()
        f2.set_result(Mock(address=socket.inet_aton("172.16.0.0"), port=90))
        f3 = asyncio.Future()
        f3.set_result(Mock(address=socket.inet_aton("172.16.0.3"), port=70))
        zeroconf_mock.get_service_info.side_effect = [f1, f2, f3]

        await asyncio.sleep(self.SLEEP_TIME)

        self.notify_new_service("IoTNode", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iotNode", zeroconf_mock, service_browser_mock)
        self.notify_new_service("iiotnode", zeroconf_mock, service_browser_mock)

        demodata = [
            Machine(name='IoTNode', ip='172.14.0.1', port = 80),
            Machine(name='iotNode', ip='172.16.0.0', port = 90)
        ]
        await machinelist_future
        self.assertEqual(demodata, machinelist_future.result())

    async def test_with_None_data(self):
        """
        Method for checked with invalid data
        """
        zeroconf_mock, service_browser_mock = self.mk_zeroconf_mock()

        machinelist_future = asyncio.ensure_future(self.machine_discover.list_machine(1))

        f1 = asyncio.Future()
        f1.set_result(Mock(address=socket.inet_aton("172.14.0.1"), port=80))
        f2 = asyncio.Future()
        f2.set_result(Mock(address=socket.inet_aton("172.16.0.0"), port=90))
        zeroconf_mock.get_service_info.side_effect = [f1, f2]

        await asyncio.sleep(self.SLEEP_TIME)

        with self.assertRaises(AttributeError):
            self.notify_new_service("iotnode_00", None, None)
            self.notify_new_service("iotnode_01", None, None)
        await machinelist_future

    async def test_invalid_ip(self):
        """
        Method for checked with invalid data
        """
        zeroconf_mock, service_browser_mock = self.mk_zeroconf_mock()

        machinelist_future = asyncio.ensure_future(self.machine_discover.list_machine(1))

        with self.assertRaises(OSError):
            f1 = asyncio.Future()
            f1.set_result(Mock(address=socket.inet_aton("342.14.0.1"), port=80))
            f2 = asyncio.Future()
            f2.set_result(Mock(address=socket.inet_aton("172.16.0.0"), port=90))
            zeroconf_mock.get_service_info.side_effect = [f1, f2]

            await asyncio.sleep(self.SLEEP_TIME)

            self.notify_new_service("iotnode", zeroconf_mock, service_browser_mock)
            self.notify_new_service("iotnode", zeroconf_mock, service_browser_mock)

        demodata = [
            Machine(name='iotnode_00', ip='172.16.0.9', port = 80),
            Machine(name='iotnode_01', ip='172.16.2.8', port=90)
        ]
        await machinelist_future
        self.assertNotEqual(demodata, machinelist_future.result())