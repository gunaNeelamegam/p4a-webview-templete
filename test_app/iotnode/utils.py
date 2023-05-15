import ipaddress
from typing import NamedTuple


class VResult(NamedTuple):
    """Indicates the result of validation."""

    valid: bool
    """Indicates if the validation was successful."""

    reason: str
    """On validation failure, indicates the reason for faliure."""

def validate_ip(ip: str, name: str) -> VResult:
    """Validates ip address."""
    if ip == "":
        return VResult(False, "{} cannot be empty.".format(name))
    try:
        ipaddress.IPv4Address(ip)
        return VResult(True, "")
    except ipaddress.AddressValueError:
        try:
            ipaddress.IPv6Address(ip)
            return VResult(True, "")
        except ipaddress.AddressValueError:
            msg = "{} '{}' is not an IPv4 or IPv6 address.".format(name, ip)
            return VResult(False, msg)
