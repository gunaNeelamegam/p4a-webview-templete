import unittest

from .presenter import MachineState

class MachineStateTestCase(unittest.TestCase):
    def setUp(self):
        self.machine_state = MachineState()

    def test_set_values(self):
        name = "Machine 1"
        ip = "127.0.0.1"
        port = 9000
        hose_length = "23 m"
        torch_style = "21"
        machine = {"name": name, "ip": ip, "port": port, "hose_length": hose_length, "torch_style": torch_style}

        self.machine_state.set_values(machine)

        self.assertEqual(self.machine_state.name, name)
        self.assertEqual(self.machine_state.ip, ip)
        self.assertEqual(self.machine_state.port, port)
        self.assertEqual(self.machine_state.hose_length, hose_length)
        self.assertEqual(self.machine_state.torch_style, torch_style)

    def test_set_values_fail(self):
        machine = {"name": "Machine 1", "ipv4": "127.0.0.1", "port": "9000"}

        self.assertRaises(AttributeError, self.machine_state.set_values, machine)

    def test_get_values_for_ui(self):
        name = "Machine 1"
        ip = "127.0.0.1"
        port = "9000"
        hose_length = "23 m"
        torch_style = "21"
        is_add = False
        machine = {"name": name, "ip": ip, "port": port, "hose_length": hose_length, "torch_style": torch_style, "is_add": is_add}
        exp = {"machine_name": name, "ip": ip, "port": port, "hose_length": hose_length, "torch_style": torch_style, "is_add": is_add}
        self.machine_state.set_values(machine)

        out = self.machine_state.get_values_ui()

        self.assertEqual(exp, out)

    def test_get_values(self):
        name = "Machine 1"
        ip = "127.0.0.1"
        port = 9000
        hose_length = "23 m"
        torch_style = "21"
        machine = {"name": name, "ip": ip, "port": port, "hose_length": hose_length, "torch_style": torch_style}
        self.machine_state.set_values(machine)

        out = self.machine_state.get_values_config()

        self.assertEqual(machine, out)
