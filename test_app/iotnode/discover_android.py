import asyncio
import logging
import re
import socket

from typing import Any, Callable, Dict, List, NamedTuple

from aiozeroconf import ServiceBrowser, ServiceStateChange, Zeroconf


class Machine(NamedTuple):
    """Specified the machine name, ip and port"""

    name: str
    ip: str
    port: int


class MachineDiscover:
    """Defines methods to discover nodes by Multicast DNS
    
    Args:
        send_event_cb: Append events to queue of interperter
    """

    def __init__(self,
                send_event_cb: Callable[[str, Dict[str, Any], bool], None] = None):
        self._machine_list = []
        self._send_event_cb = send_event_cb

    def _on_service_state_change(self,
                                 zero_config: Zeroconf,
                                 service_type: str,
                                 name: str,
                                 state_change: ServiceStateChange) -> None:
        logging.basicConfig(level=logging.INFO)
        logging.info("Service %s of type %s state changed: %s", name, service_type, state_change)
        if state_change is ServiceStateChange.Added:
            asyncio.ensure_future(self._on_service_state_change_process(zero_config,
                                                                        service_type,
                                                                        name))

    async def _on_service_state_change_process(self,
                                               zero_config: Zeroconf,
                                               service_type: str,
                                               name: str) -> None:
        info = await zero_config.get_service_info(service_type, name)
        if info:
            valid_name = re.search("^iotnode", name, flags=re.IGNORECASE)
            if valid_name:
                data = Machine(name, socket.inet_ntoa(info.address), info.port)
                self._machine_list.append(data)

    async def list_machine(self, timeout_value: int) -> List[Machine]:
        """Generates event with list of machines discovered through SD scan.

        Args:
           timeout_value: the no. of seconds to wait for services to be discovered

        Returns:
            list of machines discovered by the zeroconf using mdns
        """
        self._machine_list = []
        list_loop = asyncio.get_event_loop()
        list_loop.set_debug(True)
        zero_config = Zeroconf(list_loop)
        browser = ServiceBrowser(zero_config,
                                 "_http._tcp.local.",
                                 handlers=[self._on_service_state_change])
        await asyncio.sleep(timeout_value)
        browser.cancel()
        self._send_event_cb("list_of_machines_resp", value=self._machine_list)
        return self._machine_list

    def list_machine_start(self, timeout_value: int) -> None:
        """Run the list network as a task.

        Args:
           timeout_value: the no. of seconds to wait for services to be discovered
        """
        asyncio.ensure_future(self.list_machine(timeout_value))
