"""API to load and update application configuration.

The application configuration currently is used to store, the
following information:

  1. Poll Period
  2. Machine List
"""

import json
from collections import OrderedDict
from typing import NamedTuple
from typing import Optional
from typing import List
from typing import Tuple
from enum import Enum

import jsonschema
from kivy.logger import Logger

from .utils import VResult, validate_ip

class UnitType(Enum):
    IMPERIAL = 0
    METRIC = 1


class MachineInfo(NamedTuple):
    """Indicates the machine IP and port."""

    ip: Optional[str]
    """Indicates the machine IP address."""

    port: Optional[int]
    """Indicates the machine port."""


class ConfigLoadError(Exception):
    """Raised to indicate a error in loading configuration."""

    pass


class Machines:
    SCHEMA_v1 = {
        "type": "object",
        "required": ["name", "ip", "port"],
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 4, "maxLength": 20},
            # FIXME: I am not sure if we want to restrict this to IPv4
            # A hostname should also be valid. And may be IPv6 later on.
            "ip": {"type": "string", "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
        },
    }
    SCHEMA_v2 = SCHEMA_v1
    SCHEMA_v3 = {
        "type": "object",
        "required": ["name", "ip", "port", "hose_length"],
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 4, "maxLength": 20},
            # FIXME: I am not sure if we want to restrict this to IPv4
            # A hostname should also be valid. And may be IPv6 later on.
            "ip": {"type": "string", "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "hose_length": {"type": "string"},
        },
    }
    SCHEMA_v4 = {
        "type": "object",
        "required": ["name", "ip", "port", "hose_length"],
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 4, "maxLength": 20},
            # FIXME: I am not sure if we want to restrict this to IPv4
            # A hostname should also be valid. And may be IPv6 later on.
            # Hose length value was in meters
            "ip": {"type": "string", "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "hose_length": {"type": "string", "enum": ["3.0 m", "4.6 m", "7.6 m", "10.6 m", "15.2 m", "23 m", "30.5 m", "38.0 m", "45.6 m", "53.3 m"]},
            "torch_style": {"type": "string", "enum": ["21", "22"]},
        },
    }
    SCHEMA_v5 = {
        "type": "object",
        "required": ["name", "ip", "port", "hose_length", "torch_style"],
        "additionalProperties": False,
        "properties": {
            "name": {"type": "string", "minLength": 4, "maxLength": 20},
            # FIXME: I am not sure if we want to restrict this to IPv4
            # A hostname should also be valid. And may be IPv6 later on.
            # Hose length value was in meters
            "ip": {"type": "string", "anyOf": [{"format": "ipv4"}, {"format": "ipv6"}]},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "hose_length": {"type": "string", "enum": ["3.0 m", "4.6 m", "7.6 m", "10.6 m", "15.2 m", "23 m", "30.5 m", "38.0 m", "45.6 m", "53.3 m"]},
            "torch_style": {"type": "string", "enum": ["21", "22"]},
        },
    }

    V1_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v1, format_checker=jsonschema.FormatChecker())
    V2_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v2, format_checker=jsonschema.FormatChecker())
    V3_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v3, format_checker=jsonschema.FormatChecker())
    V4_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v4, format_checker=jsonschema.FormatChecker())
    V5_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v5, format_checker=jsonschema.FormatChecker())

    def __init__(self):
        self._machines = OrderedDict()

    def validate(self, machine: dict):
        """Validate a machine.

        Raises:
            jsonschema.exception.ValidationError: if validation fails.
        """
        self.V5_VALIDATOR.validate(machine)

    def add(self, machine: dict):
        """Adds machine to machine list.

        Args:
            machine: Machine to be added to the machine list

        Raises:
            ValueError: if already present in machine list
        """
        # Validation is for internal assertion only, the actual validation
        # for the configuration file, is done in load()
        self.validate(machine)

        name = machine["name"]
        if name in self._machines:
            raise ValueError("Duplicate machine '{}'".format(name))

        self._machines[name] = machine.copy()

    def update(self, machine: dict):
        """Updates the machine in the machine list.

        Args:
            machine: Machine to be updated

        FIXME: What if the validation fails?
        """
        self.validate(machine)
        self._machines[machine["name"]] = machine.copy()

    def get(self, name: str) -> dict:
        """Returns machine for the specified name.

        FIXME: What if the name is not present? We will return None in
        that case. The type hint needs to be updated accordingly.
        """
        return self._machines.get(name)

    def list(self) -> List[str]:
        """Returns machine names as a list.

        Returns:
            list of machine names
        """
        return list(self._machines)

    def get_machines(self) -> List[dict]:
        """Return all machines as a list.

        Returns:
            list of machines
        """
        machines = []
        for _, machine in self._machines.items():
            machines.append(machine.copy())
        return machines

    def remove(self, name: str):
        """Removes machine specified by the name.

        Args:
            name: Name of the machine to be removed.

        Raises:
            ValueError: Machine not in machine list.
        """
        if name in self._machines:
            del self._machines[name]
        else:
            raise ValueError("Invalid machine '{}'".format(name))


class Configuration:
    """Loads, validates and stores the configuration."""
    LATEST_VERSION = 5

    HOSE_LENGTH_MET2IMP = {
    "3.0 m":"10 ft",
    "4.6 m":"15 ft",
    "7.6 m":"25 ft",
    "10.6 m":"35 ft",
    "15.2 m":"50 ft",
    "23 m":"75 ft",
    "30.5 m":"100 ft",
    "38.0 m":"125 ft",
    "45.6 m":"150 ft",
    "53.3 m":"175 ft"}

    HOSE_LENGTH_IMP2MET = {
    "10 ft": "3.0 m",
    "15 ft": "4.6 m",
    "25 ft": "7.6 m",
    "35 ft": "10.6 m",
    "50 ft": "15.2 m",
    "75 ft": "23 m",
    "100 ft": "30.5 m",
    "125 ft": "38.0 m",
    "150 ft": "45.6 m",
    "175 ft": "53.3 m"
    }

    SCHEMA_v1 = {
        "type": "object",
        "required": ["poll period", "machines"],
        "additionalProperties": False,
        "properties": {
            "poll period": {"type": "integer"},
            "machines": {"type": "array", "items": Machines.SCHEMA_v1},
        },
    }
    SCHEMA_v2 = {
        "type": "object",
        "required": ["poll period", "machines", "version", "unit type"],
        "additionalProperties": False,
        "properties": {
            "version": {"type": "integer"},
            "poll period": {"type": "integer"},
            "machines": {"type": "array", "items": Machines.SCHEMA_v2},
            "unit type": {"type": "string", "enum": ["IMPERIAL", "METRIC"]},
        },
    }
    SCHEMA_v3 = {
        "type": "object",
        "required": ["poll period", "machines", "version", "unit type"],
        "additionalProperties": False,
        "properties": {
            "version": {"type": "integer"},
            "poll period": {"type": "integer"},
            "machines": {"type": "array", "items": Machines.SCHEMA_v3},
            "unit type": {"type": "string", "enum": ["IMPERIAL", "METRIC"]},
        },
    }
    SCHEMA_v4 = {
        "type": "object",
        "required": ["poll period", "machines", "version", "unit type"],
        "additionalProperties": False,
        "properties": {
            "version": {"type": "integer"},
            "poll period": {"type": "integer"},
            "machines": {"type": "array", "items": Machines.SCHEMA_v4},
            "unit type": {"type": "string", "enum": ["IMPERIAL", "METRIC"]},
        },
    }
    SCHEMA_v5 = {
        "type": "object",
        "required": ["poll period", "machines", "version", "unit type"],
        "additionalProperties": False,
        "properties": {
            "version": {"type": "integer"},
            "poll period": {"type": "integer"},
            "machines": {"type": "array", "items": Machines.SCHEMA_v5},
            "unit type": {"type": "string", "enum": ["IMPERIAL", "METRIC"]},
        },
    }

    V1_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v1, format_checker=jsonschema.FormatChecker())
    V2_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v2, format_checker=jsonschema.FormatChecker())
    V3_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v3, format_checker=jsonschema.FormatChecker())
    V4_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v4, format_checker=jsonschema.FormatChecker())
    V5_VALIDATOR = jsonschema.Draft7Validator(SCHEMA_v5, format_checker=jsonschema.FormatChecker())


    def __init__(self):
        self.poll_period = 500
        self.machines = Machines()
        self.curr_machine = ""
        self.current_unit_type = UnitType.METRIC
        self._version = 5

    def _load_machines(self, machines: List[dict]) -> None:
        for machine in machines:
            try:
                self.machines.add(machine)
            except KeyError as exc:
                raise ConfigLoadError("Machine {} not found".format(exc))
            except ValueError as exc:
                raise ConfigLoadError(exc)

    def _schema_validator(self, config: dict, version: int) -> VResult:
        """Returns the validation status of given schema version"""
        try:
            validator = getattr(self, f"V{version}_VALIDATOR")
            validator.validate(config)
            return VResult(True, "")
        except jsonschema.exceptions.ValidationError as exc:
            err_path = "/".join(str(i) for i in exc.absolute_path)
            return VResult(
                False,
                f"JSON validation failed at {err_path}",
            )

    def _validate_config(self, config: dict) -> int:
        """Returns the config version."""
        try:
            self.V5_VALIDATOR.validate(config)
        except jsonschema.exceptions.ValidationError as exc:
            err_path = "/".join(str(i) for i in exc.absolute_path)
            raise ConfigLoadError(f"JSON validation failed at {err_path}")

    def hose_data(self,is_metric):
        if is_metric:
            return list(map(str, self.HOSE_LENGTH_IMP2MET.values()))
        else:
            return list(map(str, self.HOSE_LENGTH_IMP2MET.keys()))

    def load(self, filename: str):
        """Loads configuration from the specified file.

        Args:
            filename: filename to load the configuration from

        Raises:
            ConfigLoadError: Raised if error accessing the file, error
                             parsing JSON, invalid configuration.
        """
        try:
            with open(filename) as fp:
                config = json.load(fp)
        except json.decoder.JSONDecodeError as exc:
            raise ConfigLoadError("Parsing failed: {}".format(exc))
        except OSError as exc:
            raise ConfigLoadError("Accessing file failed: {}".format(exc))
        self._validate_config(config)
        self.poll_period = config["poll period"]
        self._load_machines(config["machines"])

        if self._version != 1:
            self.set_current_unit_type(UnitType[config["unit type"]])

    def upgrade_lower_version_machines(self, machines: List[dict]):
        default_torch_style = "21"

        if self._version == 4:
            for machine in machines:
                if "torch_style" not in machine:
                    machine["torch_style"] = default_torch_style
                    self.machines.update(machine)
            self._version = 5

    def save(self, filename: str):
        """Saves the configuration to the specified file.

        Args:
            filename: filename to store configuration

        Raises:
            OSError: Error accessing file.
        """
        machines = self.machines.get_machines()
        self.upgrade_lower_version_machines(machines)

        config = {
            "poll period": self.poll_period,
            "machines": machines,
        }
        config["version"] = self.LATEST_VERSION
        config["unit type"] = self.current_unit_type.name

        with open(filename, "w") as fp:
            json.dump(config, fp)

    def get_poll_period(self) -> float:
        """Returns poll period in seconds."""
        return self.poll_period / 1000

    def get_machine_ip_and_port(self) -> MachineInfo:
        """Returns the current machine ip and port.

        Returns:
           If no machine is selected returns with ip and port, set to
           None.
        """
        curr_machine = self.machines.get(self.curr_machine)
        if not curr_machine:
            return MachineInfo(None, None)
        return MachineInfo(curr_machine["ip"], curr_machine["port"])

    def get_hose_length_download(self) -> str:
        """Returns the current machine hose length.

        Returns:
           If no machine is selected returns empty string.
        """
        curr_machine = self.machines.get(self.curr_machine)
        if not curr_machine:
            return ""

        hose_len = curr_machine["hose_length"]
        return int(self.HOSE_LENGTH_MET2IMP[hose_len].split()[0])

    def get_torch_style(self) -> str:
        """Returns the current machine torch style.

        Returns:
           If no machine is selected returns empty string.
        """
        curr_machine = self.machines.get(self.curr_machine)
        if not curr_machine:
            return ""
        return curr_machine["torch_style"]

    @staticmethod
    def _validate_machine_name(name: str) -> VResult:
        if len(name) < 4:
            return VResult(False, "Machine name should have a minimum of 4 characters.")

        if len(name) > 20:
            return VResult(
                False, "Machine name should have a maximum of 20 characters."
            )
        return VResult(True, "")

    def get_unit_types(self) -> List[Tuple[str, UnitType]]:
        return list(UnitType.__members__.items())

    def get_current_unit_type(self) -> UnitType:
        return self.current_unit_type

    def set_current_unit_type(self, unit_type: UnitType):
        self.current_unit_type = unit_type

    @staticmethod
    def _validate_machine_ip(ip: str) -> VResult:
        return validate_ip(ip, "Machine IP")

    @staticmethod
    def _validate_machine_port(port: str) -> VResult:
        port_range = range(1, 65536)
        if port == "":
            return VResult(False, "Machine port cannot be empty.")
        try:
            iport = int(port)
            if iport not in port_range:
                msg = "Port should be between {} and {}."
                msg = msg.format(port_range.start, port_range.stop - 1)
                return VResult(False, msg)

            return VResult(True, "")
        except ValueError:
            return VResult(False, "Port should be a number.")

    @staticmethod
    def _validate_machine_hose_length(length: str) -> VResult:
        # Hose length value was in meters
        if length not in ["3.0 m", "4.6 m", "7.6 m", "10.6 m", "15.2 m", "23 m", "30.5 m", "38.0 m", "45.6 m", "53.3 m"]:
            return VResult(False, "Hose length is none of these values 3.0, 4.6, 7.6, 10.6, 15.2, 23, 30.5, 38.0, 45.6, 53.3.")
        return VResult(True, "")

    @staticmethod
    def _validate_machine_torch_style(style: str) -> VResult:
        if style not in ["21", "22"]:
            return VResult(False, "Torch Style is none of these values 21, 22.")
        return VResult(True, "")

    def validate_machine(self, machine) -> VResult:
        v_name = self._validate_machine_name(machine["name"])
        if not v_name.valid:
            return v_name

        v_ip = self._validate_machine_ip(machine["ip"])
        if not v_ip.valid:
            return v_ip

        v_port = self._validate_machine_port(machine["port"])
        if not v_port.valid:
            return v_port

        v_hose_len = self._validate_machine_hose_length(machine["hose_length"])
        if not v_hose_len.valid:
            return v_hose_len

        v_torch = self._validate_machine_torch_style(machine["torch_style"])
        if not v_torch.valid:
            return v_torch

        return VResult(True, "")

    def validate_add_machine(self, machine) -> VResult:
        machine_list = self.machines.list()
        if machine["name"] in machine_list:
            msg = "Machine with name '{}' already exists\n Do you want to overwrite it?".format(machine["name"])
            return VResult(False, msg)
        return self.validate_machine(machine)

    @staticmethod
    def validate_poll_period(poll_period: int) -> VResult:
        """Validate the poll period range.

        Args:
          poll_period: poll period in ms

        Returns:
          Result of validation, indicating success or failure, and reason.
        """
        try:
            val = int(poll_period)
            if 500 <= val <= 5000:
                return VResult(True, "")
            return VResult(
                False, "Poll period should be greater than 500ms and less than 5000ms."
            )
        except ValueError:
            return VResult(False, "Poll period should not be empty.")

    def load_last_selected_machine(self, filename: str):
        try:
            with open(filename, "r") as fp:
                self.curr_machine = fp.read().strip()
        except OSError as err:
            Logger.warning("Loading failed: %s", err)

    def update_last_selected_machine(self, filename: str):
        try:
            with open(filename, "w") as fp:
                fp.write(self.curr_machine)
        except OSError as err:
            Logger.warning("Updating failed: %s", err)
