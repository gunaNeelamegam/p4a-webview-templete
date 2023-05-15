from collections import namedtuple
import copy
import asyncio
from os import name

import unittest
from unittest import mock
from jsonrpc_base import ProtocolError, TransportError

from .rpc import IotNodeInterface


VALID_READ_DATA = {
    "pid": 112,
    "otm": 1,
    "po": 0,
    "ecc": 0,
    "ps": 1,
    "pe": 0,
    "mms": 0,
    "pref": 1,
    "dccm": 0,
    "ddmc": 0,
    "ddpc": 0,
    "ds": 0,
    "fccm": [4112, 1],
    "fdmc": [8192, 1],
    "fdpc": [12288, 1],
    "lccm": [4112, 2],
    "ldmc": [8192, 2],
    "ldpc": [12288, 2],
    "av": 10,
    "ptr": 20,
    "vs": 240,
    "app": 300,
    "asgp": 300,
    "ashf": 300,
    "cmip": 300,
    "pip": 300,
    "sip": 300,
    "sihp": 300,
    "fv": 0.1,
    "dss": 61680,
    "pm": 0,
    "hl": 240,
    "ah": 2,
    "cur": 30,
    "pg": 1,
    "sf": 1,
    "fr_maj_ccm": 0,
    "fr_min_ccm": 0,
    "fr_dev_ccm": 0,
    "fr_maj_dmc": 1,
    "fr_min_dmc": 1,
    "fr_dev_dmc": 1,
    "fr_maj_dpc": 2,
    "fr_min_dpc": 2,
    "fr_dev_dpc": 2,
}

VALID_NETWORKS = [
    {
        "ssid": "NetGear 2.4G",
        "encrypt_type": "wpa2",
        "rssi": -70,
        "bssid": "00:b4:23:56:3a:40",
        "channel": 0,
        "hidden": 0,
        "current": 1,
    },
    {
        "ssid": "ZTE 2.4G",
        "encrypt_type": "wpa2",
        "rssi": -60,
        "bssid": "00:b4:23:56:3a:40",
        "channel": 0,
        "hidden": 0,
        "current": 0,
    },
]

Value = namedtuple("value", "is_static ip subnet gateway")


# Based on https://stackoverflow.com/a/32498408
class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class IoTNodeInterfaceTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("iotnode.rpc.Server")
        self.addCleanup(patcher.stop)
        self.mk_server = patcher.start()

        patcher = mock.patch("iotnode.rpc.aiohttp.ClientSession")
        self.addCleanup(patcher.stop)
        self.mk_session = patcher.start()

        patcher = mock.patch("iotnode.rpc.Logger")
        self.addCleanup(patcher.stop)
        self.logger = patcher.start()

        self._setup_ws_client()
        self._setup_client_session()

        self.valid_read_data = copy.deepcopy(VALID_READ_DATA)
        self.valid_networks = copy.deepcopy(VALID_NETWORKS)

        self.send_event_cb = mock.Mock()
        self.config = mock.Mock()
        self.config.get_poll_period.return_value = 0.1
        self.rpc = IotNodeInterface(self.config, self.send_event_cb)

    def _setup_ws_client(self):
        self.ws_client = self.mk_server()
        self.ws_client.ws_connect = AsyncMock()
        self.ws_client.ping = AsyncMock()
        self.ws_client.get_version = AsyncMock()
        self.ws_client.set_params = AsyncMock()
        self.ws_client.read_data = AsyncMock()
        self.ws_client.list_networks = AsyncMock()
        self.ws_client.select_network = AsyncMock()
        self.ws_client.close = AsyncMock()
        ip = "127.0.0.1"
        port = "9000"
        url = "ws://{}:{}".format(ip, port)
        self.ws_client._url = url

    def _setup_client_session(self):
        self.client_session = self.mk_session.return_value
        self.client_session.close = AsyncMock()

    @staticmethod
    def get_true_false(ntime):
        while True:
            yield ntime > 0
            if ntime > 0:
                ntime -= 1

    @staticmethod
    def run_and_close(seconds):
        loop = asyncio.get_event_loop()
        loop.call_later(seconds, loop.stop)
        loop.call_later(seconds + 0.01, loop.close)
        loop.run_forever()

    @staticmethod
    def run_until_complete(corotine):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(corotine)

    def set_ip_port_and_run(self, nrun):
        ip = "127.0.0.1"
        port = "9000"
        self.config.get_machine_ip_and_port.return_value = ip, port
        self.rpc.run = mock.Mock(side_effect=self.get_true_false(nrun))

    def test_register_callbacks(self):
        cb = mock.Mock()
        self.rpc.register_callback(cb)

        self.assertIn(cb, self.rpc._callbacks)

    def test_try_connect_start(self):
        self.config.get_machine_ip_and_port.return_value = None, None

        self.rpc.try_connect_start(1)
        self.run_and_close(0.2)

        self.assertIsInstance(self.rpc._try_conn_task, asyncio.Task)

    def test_try_connect_without_machine(self):
        self.rpc.run = mock.Mock(side_effect=self.get_true_false(1))
        self.config.get_machine_ip_and_port.return_value = None, None
        self.ws_client.ws_connect.side_effect = ConnectionError("")

        self.run_until_complete(self.rpc.try_connect(0.1))

        self.assertIsNone(self.rpc._ws_client)

    def test_try_connect_success(self):
        self.rpc.read_data = AsyncMock()
        self.set_ip_port_and_run(1)
        self.ws_client.get_version.return_value = "1.0"
        self.ws_client.read_data.return_value = {}

        self.run_until_complete(self.rpc.try_connect(0.1))

        called_func = [
            self.ws_client.ws_connect,
            self.ws_client.ping,
            self.ws_client.get_version,
            self.rpc.read_data,
        ]
        is_called = all(func.called for func in called_func)
        self.assertTrue(is_called)

    def test_try_connect_connection_failed(self):
        self.rpc.read_data = AsyncMock()
        self.ws_client.ws_connect.side_effect = TransportError("")
        self.set_ip_port_and_run(2)

        self.run_until_complete(self.rpc.try_connect(0.1))

        self.assertFalse(self.rpc.read_data.called)

    def test_try_connect_connection_reset(self):
        self.rpc.read_data = AsyncMock()
        self.ws_client.ws_connect.side_effect = ConnectionError("")
        self.set_ip_port_and_run(2)

        self.run_until_complete(self.rpc.try_connect(0.1))

        self.assertFalse(self.rpc.read_data.called)

    def test_try_connect_fail_not_implemented(self):
        self.rpc.read_data = AsyncMock()
        self.ws_client.get_version.side_effect = ProtocolError("")
        self.set_ip_port_and_run(2)

        self.run_until_complete(self.rpc.try_connect(0.1))

        self.assertFalse(self.rpc.read_data.called)

    def test_read_data(self):
        self.set_ip_port_and_run(2)
        cb = mock.Mock()
        self.rpc.register_callback(cb)
        self.ws_client.read_data.return_value = self.valid_read_data

        self.run_until_complete(self.rpc.read_data())

        self.assertTrue(cb.called)

    def test_read_data_invalid(self):
        self.set_ip_port_and_run(2)
        cb = mock.Mock()
        self.rpc.register_callback(cb)
        data = "data"
        self.ws_client.read_data.return_value = data

        self.run_until_complete(self.rpc.read_data())

        err_msg = "Read data validation failed at /"
        self.logger.warning.assert_called_with(err_msg)
        self.assertFalse(cb.called)

    def test_read_data_null(self):
        self.set_ip_port_and_run(2)
        cb = mock.Mock()
        self.rpc.register_callback(cb)
        self.ws_client.read_data.return_value = None

        self.run_until_complete(self.rpc.read_data())

        self.assertFalse(cb.called)

    def test_read_data_connection_closed(self):
        self.set_ip_port_and_run(2)
        self.ws_client.connected = False
        cb = mock.Mock()
        self.rpc.register_callback(cb)

        self.run_until_complete(self.rpc.read_data())

        self.assertFalse(cb.called)

    def test_read_data_fail(self):
        self.set_ip_port_and_run(2)
        self.ws_client.read_data.side_effect = TransportError("")
        cb = mock.Mock()
        self.rpc.register_callback(cb)

        self.run_until_complete(self.rpc.read_data())

        self.assertFalse(cb.called)

    def test_read_data_fail_conn_reset(self):
        self.set_ip_port_and_run(2)
        self.ws_client.read_data.side_effect = ConnectionError("")
        cb = mock.Mock()
        self.rpc.register_callback(cb)

        self.run_until_complete(self.rpc.read_data())

        self.assertFalse(cb.called)

    def test_invalid_version(self):
        self.set_ip_port_and_run(1)
        self.ws_client.get_version.return_value = "1"

        self.run_until_complete(self.rpc.try_connect(0.1))

        err_msg = ("Received invalid version type %s", str)
        self.logger.warning.assert_called_with(*err_msg)

    def test_get_version(self):
        version = 1
        self.set_ip_port_and_run(1)
        self.ws_client.get_version.return_value = version
        self.run_until_complete(self.rpc.try_connect(0.1))

        out = self.rpc.get_version()

        self.assertEqual(version, out)

    def test_list_networks_start(self):
        self.rpc.list_networks = AsyncMock()

        self.rpc.list_networks_start()
        self.run_and_close(0.1)

        self.assertTrue(self.rpc.list_networks.called)

    def test_list_networks_fail_connection_closed(self):
        self.set_ip_port_and_run(1)
        self.ws_client.connected = False

        self.run_until_complete(self.rpc.list_networks())

        self.send_event_cb.assert_called_with("error")

    def test_list_networks_fail_not_implemented(self):
        self.set_ip_port_and_run(1)
        self.ws_client.list_networks.side_effect = ProtocolError

        self.run_until_complete(self.rpc.list_networks())

        self.send_event_cb.assert_called_with("error")

    def test_list_networks_fail_transport_err(self):
        self.set_ip_port_and_run(1)
        self.ws_client.list_networks.side_effect = TransportError("")

        self.run_until_complete(self.rpc.list_networks())

        self.send_event_cb.assert_called_with("error")

    def test_list_networks_fail_conn_error(self):
        self.set_ip_port_and_run(1)
        self.ws_client.list_networks.side_effect = ConnectionError("")

        self.run_until_complete(self.rpc.list_networks())

        self.send_event_cb.assert_called_with("error")

    def test_list_networks_resp(self):
        self.set_ip_port_and_run(1)
        self.ws_client.list_networks.return_value = self.valid_networks

        self.run_until_complete(self.rpc.list_networks())

        self.send_event_cb.assert_called_with("list_networks_resp", value=self.valid_networks)

    def test_list_networks_resp_not_list(self):
        self.set_ip_port_and_run(1)
        self.ws_client.list_networks.return_value = self.valid_networks[0]

        self.run_until_complete(self.rpc.list_networks())

        err_msg = "List networks validation failed at /"
        self.logger.warning.assert_called_with(err_msg)
        self.send_event_cb.assert_called_with("error")

    def test_list_networks_resp_not_list_of_dict(self):
        self.set_ip_port_and_run(1)
        self.valid_networks[0] = []
        self.ws_client.list_networks.return_value = self.valid_networks

        self.run_until_complete(self.rpc.list_networks())

        err_msg = "List networks validation failed at /0"
        self.logger.warning.assert_called_with(err_msg)
        self.send_event_cb.assert_called_with("error")

    def test_select_network_start(self):
        self.set_ip_port_and_run(1)
        self.rpc.select_network = AsyncMock()
        bssid = "TestESP"
        psswd = "password"

        self.rpc.select_network_start(bssid, psswd)
        self.run_and_close(0.1)

        self.rpc.select_network.assert_called_with(bssid, psswd, False, None, None, None)

    def test_select_network_not_connected(self):
        self.set_ip_port_and_run(1)
        self.ws_client.connected = False
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        self.send_event_cb("error")

    def test_select_network_transport_err(self):
        self.set_ip_port_and_run(1)
        self.ws_client.select_network.side_effect = TransportError("")
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        # FIXME: 
        self.send_event_cb.assert_any_call("error")

    def test_select_network_conn_err(self):
        self.set_ip_port_and_run(1)
        self.ws_client.select_network.side_effect = ConnectionError("")
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        # FIXME: 
        self.send_event_cb.assert_any_call("error")

    def test_select_network_proto_err(self):
        self.set_ip_port_and_run(1)
        self.ws_client.select_network.side_effect = ProtocolError
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        # FIXME: 
        self.send_event_cb.assert_any_call("error")

    def test_select_network_success(self):
        self.set_ip_port_and_run(1)
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        self.send_event_cb.assert_called_with("select_network_resp")

    def test_reconnect_when_client_present(self):
        self.set_ip_port_and_run(1)
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        self.config.get_machine_ip_and_port.return_value = None, None
        self.rpc.try_connect_start(1)
        self.run_and_close(0.1)

        self.send_event_cb.assert_called_with("select_network_resp")

    def test_reconnect_when_url_differs(self):
        self.set_ip_port_and_run(1)
        self.ws_client._url = "ws://127.0.0.1:4444"
        self.config.get_machine_ip_and_port.return_value = "127.0.0.1", "1111"
        self.ws_client.get_version.return_value = "1.0"
        bssid = "TestESP"
        psswd = "password"

        self.run_until_complete(self.rpc.select_network(bssid, psswd))

        self.rpc.try_connect_start(1)
        self.run_and_close(0.1)

        self.send_event_cb.assert_called_with("select_network_resp")

    def test_reconnect_when_url_not_differs_but_client_not_connected(self):
        self.set_ip_port_and_run(1)
        self.ws_client._url = "ws://127.0.0.1:4444"
        self.ws_client.connected = False
        self.config.get_machine_ip_and_port.return_value = "127.0.0.1", "4444"
        self.ws_client.list_networks.return_value = [{}]
        self.ws_client.get_version.return_value = "1.0"

        self.run_until_complete(self.rpc.list_networks())

        self.rpc.try_connect_start(1)
        self.run_and_close(0.1)

        self.assertTrue(self.ws_client.close.called)
        self.assertTrue(self.client_session.close.called)

    def test_validate_select_network_args_empty_ip(self):
        value = Value(True, "", "", "")
        exp_reason = "IP cannot be empty."

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_invalid_ip(self):
        ip = "0"
        value = Value(True, ip, "", "")
        exp_reason = "IP '{}' is not an IPv4 or IPv6 address.".format(ip)

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_empty_subnet(self):
        value = Value(True, "1.1.1.1", "", "")
        exp_reason = "Subnet cannot be empty."

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_invalid_subnet(self):
        subnet = "0"
        value = Value(True, "1.1.1.1", subnet, "")
        exp_reason = "Subnet '{}' is not an IPv4 or IPv6 address.".format(subnet)

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_empty_gateway(self):
        value = Value(True, "1.1.1.1", "1.1.1.1", "")
        exp_reason = "Gateway cannot be empty."

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_invalid_gateway(self):
        gateway = "0"
        value = Value(True, "1.1.1.1", "1.1.1.1", gateway)
        exp_reason = "Gateway '{}' is not an IPv4 or IPv6 address.".format(gateway)

        res = self.rpc.validate_select_network_args(value)

        self.assertFalse(res.valid)
        self.assertEqual(exp_reason, res.reason)

    def test_validate_select_network_args_success(self):
        value = Value(True, "1.1.1.1", "1.1.1.1", "1.1.1.1")

        res = self.rpc.validate_select_network_args(value)

        self.assertTrue(res.valid)
        self.assertEqual("", res.reason)

    def test_validate_select_network_args_dhcp(self):
        value = Value(False, "", "", "")
        
        res = self.rpc.validate_select_network_args(value)

        self.assertTrue(res.valid)
        self.assertEqual("", res.reason)
