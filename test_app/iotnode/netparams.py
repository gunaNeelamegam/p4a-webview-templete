"""API to load the access points network parameters."""

from typing import NamedTuple
from typing import Optional


class NetworkParams(NamedTuple):
    """Indicates the AP bssid, password and static or DHCP"""

    bssid: str
    """Indicates AP bssid"""

    ssid: str
    """Indicates AP Name"""

    password: Optional[str]
    """Indicates AP password"""

    is_static: bool
    """Indicates AP uses static IP"""

    ip: Optional[str]
    """On static IP usage, indicates AP IP address"""

    subnet: Optional[str]
    """On static IP usage, indicates AP subnet mask address"""

    gateway: Optional[str]
    """On static IP usage, indicates AP gateway address"""
