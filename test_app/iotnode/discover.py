"""Wrapper to discover mdns nodes
"""
import platform


if platform.system() == "Darwin":
    from .discover_ios import MachineDiscover
else:
    from .discover_android import MachineDiscover, Machine

