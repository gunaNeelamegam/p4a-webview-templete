"""
Client side API to establish communication between the mobile application and IoT Node.

The communication protocol used is JSON-RPC over websockets.
"""

from typing import Any, Callable
import time
import asyncio
import aiohttp

import jsonschema

try:
    from kivy.logger import Logger
except ModuleNotFoundError as e:
    pass
from jsonrpc_websocket import Server
from jsonrpc_base import TransportError, ProtocolError
from .cut_chart_fetcher import CutChartParam

from .utils import VResult, validate_ip


class IotNodeInterface:
    """Set up communication between mobile application and IoT Node."""

    CONN_TIMEOUT = aiohttp.ClientTimeout(10)
    RESP_TIMEOUT = 3

    REQUEST_TIMEOUT = 20
    # Chunk size of get and set params
    CHUNK_SIZE = 30

    lock_unlock_param_ids = (0x10, 0x110, 0x210)
    lock_param_val = 0
    unlock_param_val = 1

    NETWORKS_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "required": [
                "ssid",
                "encrypt_type",
                "rssi",
                "bssid",
                "channel",
                "hidden",
                "current",
            ],
            "properties": {
                "ssid": {"type": "string"},
                "encrypt_type": {
                    "type": "string",
                    "enum": ["wpa2/psk", "open", "wpa2"],
                },
                "rssi": {"type": "integer", "minimum": -100, "maximum": 0},
                "bssid": {"type": "string", "minLength": 17, "maxLength": 17},
                "channel": {"type": "integer"},
                "hidden": {"type": "integer", "minimum": 0, "maximum": 1},
                "current": {"type": "integer", "minimum": 0, "maximum": 1},
            },
        },
    }

    READ_DATA_SCHEMA = {
        "type": "object",
        "required": [
            "pid",
            "otm",
            "po",
            "ecc",
            "ps",
            "pe",
            "mms",
            "pref",
            "dccm",
            "ddmc",
            "ddpc",
            "ds",
            "fccm",
            "fdmc",
            "fdpc",
            "lccm",
            "ldmc",
            "ldpc",
            "av",
            "ptr",
            "vs",
            "app",
            "asgp",
            "ashf",
            "cmip",
            "pip",
            "sip",
            "sihp",
            "fv",
            "dss",
            "pm",
            "hl",
            "ah",
            "cur",
            "pg",
            "sf",
            "fr_maj_ccm",
            "fr_maj_dmc",
            "fr_maj_dpc",
            "fr_min_ccm",
            "fr_min_dmc",
            "fr_min_dpc",
            "fr_dev_ccm",
            "fr_dev_dmc",
            "fr_dev_dpc",
        ],
        "properties": {
            "pid": {"type": "integer"},
            "otm": {"type": "integer", "minimum": 0, "maximum": 1},
            "po": {"type": "integer", "minimum": 0, "maximum": 1},
            "ecc": {"type": "integer", "minimum": 0, "maximum": 1},
            "ps": {"type": "integer", "minimum": 0, "maximum": 1},
            "pe": {"type": "integer", "minimum": 0, "maximum": 1},
            "mms": {"type": "integer", "minimum": 0, "maximum": 1},
            "pref": {"type": "integer", "minimum": 0, "maximum": 1},
            "dccm": {"type": "integer"},
            "ddmc": {"type": "integer"},
            "ddpc": {"type": "integer"},
            "ds": {"type": "integer"},
            "fccm": {"type": "array", "items": {"type": "integer"}},
            "fdmc": {"type": "array", "items": {"type": "integer"}},
            "fdpc": {"type": "array", "items": {"type": "integer"}},
            "lccm": {"type": "array", "items": {"type": "integer"}},
            "ldmc": {"type": "array", "items": {"type": "integer"}},
            "ldpc": {"type": "array", "items": {"type": "integer"}},
            "av": {"type": "integer"},
            "ptr": {"type": "integer"},
            "vs": {"type": "integer"},
            "app": {"type": "integer"},
            "asgp": {"type": "integer"},
            "ashf": {"type": "integer"},
            "cmip": {"type": "integer"},
            "pip": {"type": "integer"},
            "sip": {"type": "integer"},
            "sihp": {"type": "integer"},
            "fv": {"type": "number"},
            "dss": {"type": "integer"},
            "pm": {"type": "integer"},
            "hl": {"type": "integer"},
            "ah": {"type": "integer"},
            "cur": {"type": "integer"},
            "pg": {"type": "integer"},
            "sf": {"type": "integer"},
            "fr_maj_ccm": {"type": "integer"},
            "fr_maj_dmc": {"type": "integer"},
            "fr_maj_dpc": {"type": "integer"},
            "fr_min_ccm": {"type": "integer"},
            "fr_min_dmc": {"type": "integer"},
            "fr_min_dpc": {"type": "integer"},
            "fr_dev_ccm": {"type": "integer"},
            "fr_dev_dmc": {"type": "integer"},
            "fr_dev_dpc": {"type": "integer"},
        },
    }

    NETWORKS_VALIDATOR = jsonschema.Draft7Validator(NETWORKS_SCHEMA)
    READ_DATA_VALIDATOR = jsonschema.Draft7Validator(READ_DATA_SCHEMA)

    def __init__(self, config, send_event_cb):
        self._config = config
        self._callbacks = []
        self._send_event_cb = send_event_cb
        self._ws_client = None
        self._session = None
        self._try_conn_task = None
        self._version = 0
        self._read_paused = False

    @staticmethod
    def run() -> bool:
        """Helper function to ease the testing."""
        return True

    def register_callback(self, cb: Callable[[dict, float], None]) -> None:
        """Registers callbacks which will be triggered on response.

        Args:
          cb: callback function
        """
        self._callbacks.append(cb)

    def _get_url(self):
        ip, port = self._config.get_machine_ip_and_port()
        if not ip:
            return None

        url = "ws://{}:{}".format(ip, port)
        return url

    def is_connected(self):
        return self._ws_client and self._ws_client.connected

    def pause_read_data(self, state: bool):
        self._read_paused = state

    async def _close(self):
        if self._ws_client:
            await self._ws_client.close()
            self._ws_client = None

        if self._session:
            await self._session.close()
            self._session = None

    def _is_valid_client(self):
        url = self._get_url()

        if url is None:
            return False

        if (
            self._ws_client
            and self._ws_client._url == url
            and self._ws_client.connected
        ):
            return True

        return False

    async def _init_and_connect_client(self):
        url = self._get_url()
        if not url:
            await self._close()
            return False

        self._session = aiohttp.ClientSession(timeout=self.CONN_TIMEOUT)
        self._ws_client = Server(url, session=self._session, timeout=self.RESP_TIMEOUT)

        try:
            await self._ws_client.ws_connect()
        except (ProtocolError, TransportError, ConnectionError) as exc:
            await self._close()
            return False
        return self._ws_client.connected

    async def _validate_and_reinit_client(self):
        is_valid = self._is_valid_client()

        if not is_valid:
            await self._close()
            return await self._init_and_connect_client()

        return True

    async def check_connection(self):
        good_status = await self._validate_reinit_else_send_error()
        if not good_status:
            return None

        await self._send_server_req(self._ws_client.ping)
        self._send_event_cb("pong_received")

    def run_check_connection_task(self):
        asyncio.ensure_future(self.check_connection())

    def try_connect_start(self, retry_period: int) -> None:
        """Run the try_connect as a task.

        Args:
          retry_period: connection retry period in seconds.
        """
        if self._try_conn_task and not self._try_conn_task.cancelled():
            asyncio.ensure_future(self._close())
        else:
            self._try_conn_task = asyncio.ensure_future(self.try_connect(retry_period))

    async def try_connect(self, retry_period: int) -> None:
        """Retry connection for every retry_period.

        Tries to connect to websocket server for every retry
        period. Once connected, sends rpc requests - ping, get_version
        and read_data.

        Args:
          retry_period: connection retry period in seconds.
        """
        while self.run():
            connected = await self._validate_and_reinit_client()
            if not connected:
                await asyncio.sleep(retry_period)
                continue

            try:
                await self._ws_client.ping()
                hose_length_value = self._config.get_hose_length_download()
                hose_length_id = 11776
                hose_length = [(hose_length_id, hose_length_value)]
                await self._ws_client.set_params(pv_list=hose_length)
                version = await self._ws_client.get_version()
            except (ProtocolError, TransportError, ConnectionError):
                await self._close()
                await asyncio.sleep(retry_period)
            else:
                if isinstance(version, int):
                    self._version = version
                else:
                    try:
                        Logger.warning(
                            "Received invalid version type %s", type(version)
                        )
                    except ModuleNotFoundError as e:
                        pass
                await self.read_data()

    def _process_read_data(self, data):
        try:
            self.READ_DATA_VALIDATOR.validate(data, self.READ_DATA_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            err_path = "/".join(str(i) for i in exc.absolute_path)
            err = "Read data validation failed at /{}".format(err_path)
            try:
                Logger.warning(err)
            except ModuleNotFoundError as err:
                pass
        else:
            self._trigger_cbs(data)

    async def read_data(self) -> None:
        """Read data from WebSocket for every Poll Period."""
        while self.run():
            await asyncio.sleep(self._config.get_poll_period())
            connected = await self._validate_and_reinit_client()
            if not connected:
                return

            if self._read_paused:
                continue

            # read data
            try:
                data = await self._ws_client.read_data()
            except (ProtocolError, TransportError, ConnectionError) as exc:
                try:
                    Logger.warning(exc)
                except ModuleNotFoundError as e:
                    pass
                await self._close()
                return

            self._process_read_data(data)

    def get_version(self) -> None:
        """Returns the version of WebSocket Protocol."""
        return self._version

    def list_networks_start(self) -> None:
        """Run the list network as a task."""
        asyncio.ensure_future(self.list_networks())

    async def _send_server_req(self, send_req_func, *args, **kwargs):
        try:
            res = await send_req_func(*args, **kwargs)
            return res
        except ProtocolError:
            self._send_event_cb("error")
        except (TransportError, ConnectionError):
            await self._close()
            self._send_event_cb("error")

    async def _list_networks(self):
        good_status = await self._validate_reinit_else_send_error()
        if not good_status:
            return None

        networks = await self._send_server_req(self._ws_client.list_networks)

        try:
            self.NETWORKS_VALIDATOR.validate(networks, self.NETWORKS_SCHEMA)
        except jsonschema.exceptions.ValidationError as exc:
            err_path = "/".join(str(i) for i in exc.absolute_path)
            err = "List networks validation failed at /{}".format(err_path)
            try:
                Logger.warning(err)
            except ModuleNotFoundError as e:
                pass
            self._send_event_cb("error")
        else:
            self._send_event_cb("list_networks_resp", value=networks)

    async def list_networks(self) -> None:
        """Send the list networks as a request."""
        await self._list_networks()

    async def _validate_reinit_else_send_error(self) -> bool:
        """Send the 'error' event in case."""
        await self._validate_and_reinit_client()
        if not self._ws_client or not self._ws_client.connected:
            self._send_event_cb("error")
            return False
        return True

    @staticmethod
    def validate_select_network_args(args: Any) -> VResult:
        if not args.is_static:
            return VResult(True, "")

        vres = validate_ip(args.ip, "IP")
        if not vres.valid:
            return vres
        vres = validate_ip(args.subnet, "Subnet")
        if not vres.valid:
            return vres
        vres = validate_ip(args.gateway, "Gateway")
        return vres

    def get_node_ip_start(self, name: str):
        """Run the station ip request as a task."""
        asyncio.ensure_future(self.get_node_ip(name))

    async def get_node_ip(self, name: str):
        await self._get_node_ip(name)

    async def _get_node_ip(self, name: str):
        good_status = await self._validate_reinit_else_send_error()
        if not good_status:
            return None

        response = await self._send_server_req(self._ws_client.get_node_ip)

        try:
            jsonschema.validate(
                response,
                {
                    "type": "object",
                    "required": ["IP"],
                    "additionalProperties": False,
                    "properties": {"IP": {"type": "string"}},
                },
            )
        except jsonschema.exceptions.ValidationError as exc:
            err_path = "/".join(str(i) for i in exc.absolute_path)
            err = "Dynamic IP Response JSON Validation failed{}".format(err_path)
            try:
                Logger.warning(err)
            except ModuleNotFoundError as e:
                pass
            self._send_event_cb("error")
        else:
            ip = response["IP"]
            vres = validate_ip(ip, name)
            if vres.valid:
                self._send_event_cb("get_node_ip_resp", value=ip)
            else:
                self._send_event_cb("error", value=vres.reason)

    def select_network_start(
        self,
        bssid: str,
        password: str = None,
        is_static: bool = False,
        ip: str = None,
        subnet: str = None,
        gateway: str = None,
    ) -> None:
        """Run select_network as a task.

        Args:
          bssid: bssid of the network to be connected
          password: password of the network to be connected.
        """
        asyncio.ensure_future(
            self.select_network(bssid, password, is_static, ip, subnet, gateway)
        )

    async def select_network(
        self,
        bssid: str,
        password: str = None,
        is_static: bool = False,
        sta_ip: str = None,
        sta_subnet: str = None,
        sta_gateway: str = None,
    ) -> None:
        """Send select network as a request.

        Args:
          bssid: bssid of the network to be connected
          password: password of the network to be connected.
        """
        kwargs = {"bssid": bssid, "sta_dhcp": not is_static}
        if password:
            kwargs["password"] = password

        if is_static:
            kwargs["sta_ip"] = sta_ip
            kwargs["sta_subnet"] = sta_subnet
            kwargs["sta_gateway"] = sta_gateway

        good_status = await self._validate_reinit_else_send_error()
        if not good_status:
            return None

        result = await self._send_server_req(self._ws_client.select_network, **kwargs)
        self._send_event_cb("select_network_resp")

    def _trigger_cbs(self, data):
        timestamp = time.time()
        for cb in self._callbacks:
            cb(data, timestamp)

    def chunks(self, lst):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), self.CHUNK_SIZE):
            yield lst[i : i + self.CHUNK_SIZE]

    async def _set_params(self, data: list):
        async def main():
            for chunk in self.chunks(data):
                good_status = await self._validate_reinit_else_send_error()
                if not good_status:
                    return None
                await self._ws_client.set_params(pv_list=chunk)

        await self._send_server_req(main)

    async def _unlock_sequence(self):
        pv_list = [
            (param, self.unlock_param_val) for param in self.lock_unlock_param_ids
        ]
        await self._set_params(pv_list)

    async def _lock_sequence(self):
        pv_list = [(param, self.lock_param_val) for param in self.lock_unlock_param_ids]
        await self._set_params(pv_list)

    def get_process_id(self):
        async def main():
            good_status = await self._validate_reinit_else_send_error()
            if not good_status:
                return None
            res = await self._ws_client.get_params(
                pid=[CutChartParam.PARAM_ID_PROCESS_ID]
            )
            # FIXME: Need to validate results?
            # FIXME: Need to handle Exceptions?
            process_id_value = res[0][1]
            self._send_event_cb("got_process_id", value=process_id_value)

        asyncio.ensure_future(self._send_server_req(main))

    def get_param_list_start(self, param_id_list: list):
        param_list = []

        async def get_param_list():
            for chunk in self.chunks(param_id_list):
                good_status = await self._validate_reinit_else_send_error()
                if not good_status:
                    return None
                res = await self._ws_client.get_params(pid=chunk)
                # FIXME: Need to validate results?
                # FIXME: Need to handle Exceptions?
                param_list.extend(res)

        async def main():
            await self._send_server_req(get_param_list)
            self._send_event_cb("got_param_list", dict(param_list))

        asyncio.ensure_future(main())

    def set_params_start(self, data: list, locked: bool = True):
        asyncio.ensure_future(self.set_params(data, locked))

    async def set_params(self, data: list, locked: bool = True):
        try:
            if locked:
                await self._unlock_sequence()
            await self._set_params(data)
        finally:
            if locked:
                await self._lock_sequence()

        self._send_event_cb("sent_param_list")

    def get_params_start(self, data: list):
        async def main():
            temp = []
            for chunck in self.chunks(data):
                good_status = await self._validate_reinit_else_send_error()
                if not good_status:
                    return None
                res = await self._send_server_req(
                    self._ws_client.get_params, pid=chunck
                )
                if res:
                    temp.extend(res)
            self._send_event_cb("got_service_data", value=dict(temp))

        asyncio.ensure_future(self._send_server_req(main))
