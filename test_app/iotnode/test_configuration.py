import copy
import json
import unittest
from io import StringIO
from unittest import mock

import jsonschema

from .configuration import Machines
from .configuration import Configuration, ConfigLoadError


class ConfigurationTestCase(unittest.TestCase):
    def setUp(self):
        self.valid_config = json.load(open("iotnode_app/iotnode/test_config.json"))
        self.config = Configuration()

    def fails(self, jconf):
        with mock.patch("iotnode.configuration.open", jconf):
            self.assertRaises(ConfigLoadError, self.config.load, "config.json")

    def load_config(self):
        self.config.load("iotnode_app/iotnode/test_config.json")

    def test_load_failed_reading_file(self):
        jconf = mock.Mock(side_effect=OSError)
        self.fails(jconf)

    def test_load_failed_parsing_json(self):
        jconf = mock.mock_open(read_data="")
        self.fails(jconf)

    def test_load_schema_validation_fail_empty(self):
        jconf = mock.mock_open(read_data="{}")
        self.fails(jconf)

        with mock.patch("iotnode.configuration.open", jconf):
            self.assertRaises(ConfigLoadError, self.config.load, "config.json")

    def test_load_schema_validation_fail_invalid_machine_name(self):
        self.valid_config["machines"][0]["name"] = ""
        jconf = mock.mock_open(read_data=json.dumps(self.valid_config))

        self.fails(jconf)

    def test_load_schema_validation_fail_invalid_machine_ip(self):
        self.valid_config["machines"][0]["ip"] = "100"
        jconf = mock.mock_open(read_data=json.dumps(self.valid_config))

        self.fails(jconf)

    def test_load_schema_validation_fail_invalid_machine_port(self):
        self.valid_config["machines"][0]["ip"] = "100"
        jconf = mock.mock_open(read_data=json.dumps(self.valid_config))

        self.fails(jconf)

    def test_load_schema_validation_fail_invalid_poll_period(self):
        self.valid_config["poll period"] = "500"
        jconf = mock.mock_open(read_data=json.dumps(self.valid_config))

        self.fails(jconf)


    def test_load_schema_validation_pass(self):
        self.load_config()

        self.assertEqual(self.valid_config["poll period"], self.config.poll_period)
        self.assertEqual(
            self.valid_config["machines"], self.config.machines.get_machines()
        )

    def test_save(self):
        self.load_config()
        _validate_config = mock.patch("iotnode.configuration.Configuration._validate_config")
        _validate_config.return_value = 1

        fp = StringIO()
        fp.close = lambda: None
        jconf = json.dumps(self.valid_config)

        with mock.patch("iotnode.configuration.open") as mock_open:
            mock_open.return_value = fp
            self.config.save("config.json")

        fp.seek(0)
        out = fp.getvalue()

        self.assertEqual(out, jconf)

    def test_get_poll_period(self):
        self.load_config()
        expected = self.config.poll_period / 1000

        out = self.config.get_poll_period()

        self.assertEqual(out, expected)

    def test_get_machine_ip_and_port_without_machine(self):
        expected = None, None

        out = self.config.get_machine_ip_and_port()

        self.assertEqual(out, expected)

    def test_get_machine_ip_and_port_with_machine(self):
        self.load_config()

        exp_ip = self.valid_config["machines"][0]["ip"]
        exp_port = self.valid_config["machines"][0]["port"]
        self.config.curr_machine = self.valid_config["machines"][0]["name"]

        out = self.config.get_machine_ip_and_port()

        self.assertEqual(out, (exp_ip, exp_port))

    def test_validate_machine_ip_empty_false(self):
        ip = ""
        exp = False, "Machine IP cannot be empty."
        machine = {"name": "Machine 1", "ip": ip, "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_ip_false(self):
        ip = "127.0.0"
        exp = False, "Machine IP '{}' is not an IPv4 or IPv6 address.".format(ip)
        machine = {"name": "Machine 1", "ip": ip, "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_name_false(self):
        machine = {"name": "Mac", "ip": "1.1.1.1", "port": 9000}
        exp = False, "Machine name should have a minimum of 4 characters."

        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_port_false(self):
        machine = {"name": "Machine 1", "ip": "1.1.1.1", "port": "", "hose_length": "23 m", "torch_style": "21"}
        exp = False, "Machine port cannot be empty."

        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_port_out_of_range_false(self):
        machine = {"name": "Machine 1", "ip": "1.1.1.1", "port": "65536", "hose_length": "23 m", "torch_style": "21"}
        exp = False, "Port should be between 1 and 65535."

        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_port_nan_false(self):
        machine = {"name": "Machine 1", "ip": "1.1.1.1", "port": "a436", "hose_length": "23 m", "torch_style": "21"}
        exp = False, "Port should be a number."

        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_machine_true(self):
        exp = True, ""
        machine = {"name": "Machine 1", "ip": "127.0.0.1", "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        out = self.config.validate_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_add_machine_duplicate_false(self):
        machine_name = "Machine 1"
        exp = False, "Machine with name '{}' already exists\n Do you want to overwrite it?".format(machine_name)
        machine = {"name": machine_name, "ip": "127.0.0.1", "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        self.config.machines.add(machine)

        out = self.config.validate_add_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_add_machine_duplicate_true(self):
        exp = True, ""
        machine = {"name": "Machine 1", "ip": "11.2.3.4", "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        out = self.config.validate_add_machine(machine)

        self.assertEqual(exp, out)

    def test_validate_add_machine_true(self):
        ip = "127.0.0"
        exp = False, "Machine IP '{}' is not an IPv4 or IPv6 address.".format(ip)
        machine = {"name": "Machine 1", "ip": ip, "port": 9000, "hose_length": "23 m", "torch_style": "21"}
        out = self.config.validate_add_machine(machine)
        print(out)
        self.assertEqual(exp, out)

    def test_validate_poll_period_more_than_5000(self):
        exp = False, "Poll period should be greater than 500ms and less than 5000ms."

        out = self.config.validate_poll_period("5100")

        self.assertEqual(exp, out)

    def test_validate_poll_period_less_than_500(self):
        exp = False, "Poll period should be greater than 500ms and less than 5000ms."

        out = self.config.validate_poll_period("400")

        self.assertEqual(exp, out)

    def test_validate_poll_period_empty(self):
        exp = False, "Poll period should not be empty."

        out = self.config.validate_poll_period("")

        self.assertEqual(exp, out)

    def test_validate_poll_period_pass(self):
        exp = True, ""

        out = self.config.validate_poll_period("500")

        self.assertEqual(exp, out)

    def test_load_last_selected_machine_pass(self):
        lsm = mock.mock_open(read_data="machine1")

        with mock.patch("iotnode.configuration.open", lsm):
            self.config.load_last_selected_machine("lsm")
            self.assertEqual(self.config.curr_machine, "machine1")

    def test_load_last_selected_machine_fails(self):
        lsm_fails = mock.Mock(side_effect=OSError)

        with mock.patch("iotnode.configuration.Logger") as mock_logger:
            with mock.patch("iotnode.configuration.open", lsm_fails):
                self.config.load_last_selected_machine("lsm")

            self.assertTrue(mock_logger.warning.called)


    def test_update_last_selected_machine_pass(self):
        lsm = mock.mock_open()
        self.config.curr_machine = "machine2"

        with mock.patch("iotnode.configuration.open", lsm):
            self.config.update_last_selected_machine("lsm")

        lsm().write.assert_called_once_with("machine2")

    def test_update_last_selected_machine_fails(self):
        lsm_fails = mock.Mock(side_effect=OSError)

        with mock.patch("iotnode.configuration.Logger") as mock_logger:
            with mock.patch("iotnode.configuration.open", lsm_fails):
                self.config.update_last_selected_machine("lsm")

            self.assertTrue(mock_logger.warning.called)


class MachinesTestCase(unittest.TestCase):
    def setUp(self):
        self.machines = Machines()
        self.valid_machines = json.load(open("iotnode_app/iotnode/test_config.json"))["machines"]

    def test_validate_machine(self):
        machine = self.valid_machines[0]

        self.machines.validate(machine)

    def test_validate_fail(self):
        machine = self.valid_machines[0]
        machine["ip"] = ""

        self.assertRaises(
            jsonschema.exceptions.ValidationError, self.machines.validate, machine
        )

    def test_add_pass(self):
        machine = self.valid_machines[0]
        machine_name = machine["name"]

        self.machines.add(machine)

        self.assertIn(machine_name, self.machines.list())


    def test_list(self):
        machine = self.valid_machines[0]
        machine_name = machine["name"]
        exp = [machine_name]
        self.machines.add(machine)

        mlist = self.machines.list()

        self.assertEqual(mlist, exp)

    def test_update(self):
        machine = self.valid_machines[0]
        machine_name = machine["name"]
        self.machines.add(machine)
        machine["ip"] = "10.10.1.14"

        self.machines.update(machine)

        self.assertEqual(machine, self.machines.get(machine_name))

    def test_get(self):
        machine = self.valid_machines[0]
        machine_name = machine["name"]
        self.machines.add(machine)

        out = self.machines.get(machine_name)

        self.assertEqual(out, machine)

    def test_get_machines(self):
        machine = self.valid_machines[0]
        self.machines.add(machine)

        out = self.machines.get_machines()

        self.assertEqual(out, [machine])

    def test_remove_machine(self):
        machine = self.valid_machines[0]
        machine_name = machine["name"]
        self.machines.add(machine)

        self.machines.remove(machine_name)

        self.assertEqual(self.machines.get_machines(), [])

    def test_remove_machine_invalid(self):
        self.assertRaises(ValueError, self.machines.remove, "invalid-machine")
