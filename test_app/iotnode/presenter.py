"""
Provides API to store and retrieve state of machine being modified.
"""


from typing import Any, Dict
from .utils import validate_ip


class MachineState:
    """Transient state of Machine interface.

    Attributes:
      name: str, machine's name.
      ip: str, machine's ip.
      port: str, machine's port
      is_add: bool, is machine being added.
    """

    def __init__(self) -> None:
        self.name = ""
        self.ip = ""
        self.port = ""
        self.hose_length = ""
        self.torch_style = ""
        self.is_add = False
        self.scan = False

    def set_values(self, values: Dict[str, Any]) -> None:
        """Set the attributes from the values.

        Args:
          values: atrributes to be set from key, value pair.

        Raises:
          AttributeError: if attribute does not match.
        """
        for key, value in values.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                err = "'MachineState' object has no attribute '{}'".format(key)
                raise AttributeError(err)

    def get_values_ui(self) -> Dict[str, Any]:
        """Provide machine attributes for ui."""
        values = {
            "ip": self.ip,
            "machine_name": self.name[:20],
            "port": str(self.port),
            "hose_length": str(self.hose_length),
            "torch_style": str(self.torch_style),
            "is_add": self.is_add,
        }
        return values

    def get_values_config(self) -> Dict[str, Any]:
        """Provide machine attributes for config."""
        values = {
            "ip": self.ip,
            "name": self.name,
            "port": int(self.port),
            "hose_length": str(self.hose_length),
            "torch_style": str(self.torch_style),
        }
        return values

    def make_initial_machine(self, name: str, ip: str = "") -> Dict[str, Any]:
        """Provide machine attributes for config.
            Hose length value was in meters """
        default_machine = {
            "ip": "192.168.4.1",
            "name": name,
            "port": 8080,
            "hose_length": "23 m",
            "torch_style": "21",
            "is_add": True,
        }
        if ip:
            default_machine["ip"] = ip
        self.set_values(default_machine)
        return default_machine
