"""
This module contains the functionality needed for maintenance scheduler feature
"""

import os
import re
import json
import argparse

from typing import Dict, List
import jsonschema


Notifications = List[str]
LastMaintenancedHrs = Dict[str, Dict[str, int]]


class MaintenanceLoadError(Exception):
    """Raised to indicate a error in loading Maintenance."""

    pass


class Args(argparse.ArgumentParser):
    """Argparser method that is to be added is included in this protocol"""

    current_arc_hours: int


class MaintenanceScheduler:
    """Class to handle notification schedule maintenance

    Attributes:
        current_schedule: Stores current schedule.
        last_maintenace_schedule: Stores last maintened schedule.
    """

    SCHEMA = {
        "type": "object",
        "required": ["80", "160", "320", "480", "960", "2880", "3840", "4800"],
        "additionalProperties": False,
        "properties": {
            "80": {
                "type": "object",
                "required": ["LUBRICATE CARTRIGE O-RING", "LUBRICATE TORCH O-RING"],
                "additionalProperties": False,
                "properties": {
                    "LUBRICATE CARTRIGE O-RING": {"type": "integer"},
                    "LUBRICATE TORCH O-RING": {"type": "integer"},
                },
            },
            "160": {
                "type": "object",
                "required": ["CATRIDGE O-RING", "TORCH O-RING"],
                "additionalProperties": False,
                "properties": {
                    "CATRIDGE O-RING": {"type": "integer"},
                    "TORCH O-RING": {"type": "integer"},
                },
            },
            "320": {
                "type": "object",
                "required": [
                    "DO A COOLANT FLOW TEST",
                    "CLEAN RADIATOR",
                    "WASH COOLANT FILTER CARTRIDGE",
                ],
                "additionalProperties": False,
                "properties": {
                    "DO A COOLANT FLOW TEST": {"type": "integer"},
                    "CLEAN RADIATOR": {"type": "integer"},
                    "WASH COOLANT FILTER CARTRIDGE": {"type": "integer"},
                },
            },
            "480": {
                "type": "object",
                "required": [
                    "REPLACE COOLANT LIQUID",
                    "REPLACE DMC WATER MIST CATRIDGE",
                    "REPLACE H2O PUMP ACTIVE FILTER CATRIDGE",
                    "TORCH COOLANT TUBE",
                    "REPLACE CATRIDGE",
                    "CHECK FOR COLLANT LEAKS",
                    "CHECK FOR GAS LEAKS",
                ],
                "additionalProperties": False,
                "properties": {
                    "REPLACE COOLANT LIQUID": {"type": "integer"},
                    "REPLACE DMC WATER MIST CATRIDGE": {"type": "integer"},
                    "REPLACE H2O PUMP ACTIVE FILTER CATRIDGE": {"type": "integer"},
                    "TORCH COOLANT TUBE": {"type": "integer"},
                    "REPLACE CATRIDGE": {"type": "integer"},
                    "CHECK FOR COLLANT LEAKS": {"type": "integer"},
                    "CHECK FOR GAS LEAKS": {"type": "integer"},
                },
            },
            "960": {
                "type": "object",
                "required": ["REPLACE COOLANT FILTER CARTRIDGE"],
                "additionalProperties": False,
                "properties": {
                    "REPLACE COOLANT FILTER CARTRIDGE": {"type": "integer"},
                },
            },
            "2880": {
                "type": "object",
                "required": ["REPLACE TORCH HEAD"],
                "additionalProperties": False,
                "properties": {
                    "REPLACE TORCH HEAD": {"type": "integer"},
                },
            },
            "3840": {
                "type": "object",
                "required": ["REPLACE TORCH LEAD SET"],
                "additionalProperties": False,
                "properties": {
                    "REPLACE TORCH LEAD SET": {"type": "integer"},
                },
            },
            "4800": {
                "type": "object",
                "required": ["REPLACE GAS LEAD SET"],
                "additionalProperties": False,
                "properties": {
                    "REPLACE GAS LEAD SET": {"type": "integer"},
                },
            },
        },
    }

    def __init__(self):
        """Initiates file path, current_schedule, current arc hours"""
        self.current_schedule: LastMaintenancedHrs = {}
        self.last_maintenace_schedule: LastMaintenancedHrs = {}
        self._current_arc_hrs: int = 0

    def load(self, filepath: os.PathLike) -> None:
        """Loads last_maintenance_arc_hrs state.

        Args:
           filepath: File path of maintenance file.

        Raises:
            MaintenanceLoadError: Validation Error
            MaintenanceLoadError: JSON Decode Error
            MaintenanceLoadError: OS Error

        """
        self.last_maintenace_schedule = self._read_from_db(filepath)

    def save(
        self, filepath: os.PathLike, hrs_notifications: Dict[str, List[str]]
    ) -> None:
        """
        Loads the last_maintenance_arc_hrs state

        Args:
           filepath: File path of maintenance file.
           notifications: List of last updated hours.
        """
        for hrs, notifications in hrs_notifications.items():
            for notification in notifications:
                self.last_maintenace_schedule[hrs].update(
                    {notification: self._current_arc_hrs}
                )
        self._write_to_db(filepath, self.last_maintenace_schedule)

    @classmethod
    def _get_initial_db(cls) -> LastMaintenancedHrs:
        notifications_dict = cls.SCHEMA["properties"]
        arc_hours_list = cls.SCHEMA["required"]
        initial_db = {}

        for hours in arc_hours_list:
            notifications_data = {}
            for notification in notifications_dict[hours]["required"]:
                notifications_data[notification] = 0
            initial_db[hours] = notifications_data

        return initial_db

    @classmethod
    def _read_from_db(cls, filepath: os.PathLike) -> LastMaintenancedHrs:
        if not os.path.exists(filepath):
            cls._write_to_db(filepath, cls._get_initial_db())
        try:
            with open(filepath, "r") as jsonfile:
                last_maintenanced_arc_hours = json.load(jsonfile)
                jsonschema.validate(
                    last_maintenanced_arc_hours,
                    cls.SCHEMA,
                    format_checker=jsonschema.FormatChecker(),
                )
            return last_maintenanced_arc_hours
        except jsonschema.ValidationError as exc:
            raise MaintenanceLoadError("Validation error: {}".format(exc)) from exc
        except json.decoder.JSONDecodeError as exc:
            raise MaintenanceLoadError("Parsing failed: {}".format(exc)) from exc
        except OSError as exc:
            raise MaintenanceLoadError("Accessing file failed: {}".format(exc)) from exc

    @classmethod
    def _write_to_db(cls, filepath: os.PathLike, notifications: LastMaintenancedHrs):
        """
        Writes the last maintenanced arc hours for every maintenance arc hours cycle

        Parameters:
            current_schedule (LastMaintenancedHrs): To be serialized maintenance schedule
        """
        try:
            jsonschema.validate(
                notifications,
                cls.SCHEMA,
                format_checker=jsonschema.FormatChecker(),
            )
            with open(filepath, "w") as jsonfile:
                jsonfile.write(json.dumps(notifications, indent=4))
        except jsonschema.ValidationError as exc:
            with open(filepath, "w") as jsonfile:
                jsonfile.write(json.dumps(cls._get_initial_db(), indent=4))
                print("Writing failed: %s", exc)
            
        except OSError as err:
           print(err)

    @staticmethod
    def _get_hours_int(arc_hours: str) -> int:
        try:
            if re.search(r"hrs?$", arc_hours.strip(), flags=re.IGNORECASE):
                arc_hours, _ = arc_hours.strip().split()
            hrs = int(arc_hours)
        except ValueError:
            hrs = 0
        return hrs

    def notify(self, current_arc_hours: str):
        """Notifies user to maintenance the particulars

        Args:
           current_arc_hours: current arc hour

        Returns:
            Dict of Notification for Maintenance.
        """
        self._current_arc_hrs = self._get_hours_int(current_arc_hours)
        current_notifications = {}
        for schedule_period, final_data in self.last_maintenace_schedule.items():
            period_notifications = []
            for notification, last_arc_hrs in final_data.items():
                arc_hrs_elapsed = self._current_arc_hrs - last_arc_hrs
                schedule_due = (arc_hrs_elapsed) / int(schedule_period) >= 1
                if not schedule_due:
                    continue
                period_notifications.append(notification)
            current_notifications[schedule_period] = period_notifications
        return current_notifications


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "current_arc_hours",
        type=int,
        help="get the current arc hours to raise notification",
    )
