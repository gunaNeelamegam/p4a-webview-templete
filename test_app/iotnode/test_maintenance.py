import json
import unittest
from io import StringIO
from unittest import mock
import os
from jsonschema.exceptions import ValidationError
from typing import Dict

from .maintenance import MaintenanceScheduler
from .maintenance import MaintenanceLoadError


class MaintenanceSchedulerTestCase(unittest.TestCase):

    def get_file_path(self):
        dir_path = os.path.dirname(__file__)
        file_path = os.path.join(dir_path,  "last_maintenanced_arc_hours.json")
        return file_path

    def setUp(self):
        dir_path = os.path.dirname(__file__)
        file_path = os.path.join(dir_path,  "test_last_maintenanced_arc_hours.json")
        self.valid_config = json.load(open(file_path))
        self.maintain = MaintenanceScheduler()

    def load_config(self):
        dir_path = os.path.dirname(__file__)
        file_path = os.path.join(dir_path,  "test_last_maintenanced_arc_hours.json")
        self.maintain.load(file_path)

    def fails(self, jconf):
        with mock.patch("iotnode.maintenance.open", jconf):
            self.assertRaises(MaintenanceLoadError, self.maintain.load, self.get_file_path())

    def test_load_failed_read_file(self):
        jconf = mock.Mock(side_effect=OSError)
        self.fails(jconf)

    def test_load_failed_parsing_json(self):
        jconf = mock.mock_open(read_data="")
        self.fails(jconf)

    def test_load_schema_validation_fail_empty(self):
        jconf = mock.mock_open(read_data="{}")
        self.fails(jconf)

        with mock.patch("iotnode.maintenance.open", jconf):
            self.assertRaises(MaintenanceLoadError, self.maintain.load, self.get_file_path())

    def test_load_schema_validation_fail_invalid_arc_hours(self):
        self.valid_config["80"]= ""
        jconf = mock.mock_open(read_data=json.dumps(self.valid_config))
        self.fails(jconf)


    def test_update_last_selected_hours_fails(self):
        demo_data = {
                "80": {
                    "LUBRICATE CARTRIGE O-RING": 90,
                    "LUBRICATE TORCH O-RING": 0
                },
                "160": {
                    "CATRIDGE O-RING": 0,
                    "TORCH O-RING": 0
                },
                "320": {
                    "DO A COOLANT FLOW TEST": 0,
                    "CLEAN RADIATOR": 0,
                    "WASH COOLANT FILTER CARTRIDGE": 0
                },
                "480": {
                    "REPLACE COOLANT LIQUID": 0,
                    "REPLACE DMC WATER MIST CATRIDGE": 0,
                    "REPLACE H2O PUMP ACTIVE FILTER CATRIDGE": 0,
                    "TORCH COOLANT TUBE": 0,
                    "REPLACE CATRIDGE": 0,
                    "CHECK FOR COLLANT LEAKS": 0,
                    "CHECK FOR GAS LEAKS": 0
                },
                "960": {
                    "REPLACE COOLANT FILTER CARTRIDGE": 0
                },
                "2880": {
                    "REPLACE TORCH HEAD": 0
                },
                "3840": {
                    "REPLACE TORCH LEAD SET": 0
                },
                "4800": {
                    "REPLACE GAS LEAD SET": 0
                }
         }
        with mock.patch("iotnode.maintenance.Logger") as mock_logger:
            with mock.patch("iotnode.maintenance.open", side_effect=OSError):
                self.maintain._write_to_db(self.get_file_path(),demo_data)

            self.assertTrue(mock_logger.warning.called)

    def test_save(self):
        self.load_config()

        fp = StringIO()
        fp.close = lambda: None
        jconf = json.dumps(self.valid_config, indent=4)

        with mock.patch("iotnode.maintenance.open") as mock_open:
            mock_open.return_value = fp
            self.maintain.save(self.get_file_path(),{})

        fp.seek(0)
        out = fp.getvalue()

        self.assertEqual(out, jconf)

