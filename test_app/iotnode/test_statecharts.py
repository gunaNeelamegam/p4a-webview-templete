import os
import copy
import unittest
import platform

from unittest.mock import MagicMock, Mock

from sismic.io import import_from_yaml
from sismic.interpreter import Interpreter
from sismic import testing

from . import configuration
from . import cut_chart
from . import maintenance_menu
from . import presenter
from .netparams import NetworkParams
from .configuration import UnitType

def statechart_interpreter():
    statechart = import_from_yaml(filepath=os.path.join(os.path.dirname(__file__), "statecharts", "main.yml"))
    interpreter = Interpreter(statechart)
    interpreter.clock.start()
    return interpreter

def home_screen(it, config):
    config.get_poll_period = Mock(return_value=1)
    it.execute()

def service_menu_screen(it, config):
    config.get_poll_period = Mock(return_value=1)
    it.execute()
    it.queue("service_menu_button_pressed").execute()

def settings_screen(it, config):
    config.get_poll_period = Mock(return_value=1)
    it.execute()
    it.queue("settings_button_pressed").execute()

def process_setup_input_screen(it, config):
    config.get_poll_period = Mock(return_value=1)
    config.get_current_unit_type = Mock(return_value=UnitType.METRIC)
    it.execute()
    it.queue("process_setup_button_pressed").execute()

def service_feature_screen(it, config):
    home_screen(it, config)
    it.queue("service_menu_button_pressed").execute()
    it.queue("service_button_pressed").execute()
    it.queue("valve_check_button_pressed", value={"authenticated": True}).execute()

SAMPLE_MACHINE_1 = {"name": "sample_1", "ip": "192.168.4.1", "port": 5000, "hose_length": "23 m", "torch_style": "21"}
SAMPLE_MACHINE_2 = {"name": "sample_2", "ip": "192.168.4.1", "port": 5000, "hose_length": "23 m", "torch_style": "21"}
CUTCHART_FNAME = "cutchart.csv"
MAINTENANCE_FNAME = "maintenance.csv"

class IoTNodeStatechartTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.initial_it = statechart_interpreter()

    def setUp(self):
        self.ui = Mock()
        self.status = Mock()
        self.rpc = Mock()
        self.psvalue = MagicMock()
        self.conf_file = Mock()
        self.lsm = Mock()
        self.lmh = Mock()
        self.machine_discover = Mock()
        self.maintenance_scheduler = Mock()
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self.cutchart_file = os.path.join(self.dir_path,CUTCHART_FNAME)
        self.cutchart = cut_chart.CutChart(self.cutchart_file)
        self.config = configuration.Configuration()
        self.config.machines.add(SAMPLE_MACHINE_1)
        self.config.machines.add(SAMPLE_MACHINE_2)
        self.config.curr_machine = "sample_1"
        self.machine_state = presenter.MachineState()
        self.it = copy.deepcopy(self.initial_it)
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self.maintenance_link = os.path.join(self.dir_path,MAINTENANCE_FNAME)
        self.maintenance_menu = maintenance_menu.MaintenanceMenu(self.maintenance_link)
        self.it.context["ui"] = self.ui
        self.it.context["config"] = self.config
        self.it.context["cutchart"] = self.cutchart
        self.it.context["status"] = self.status
        self.it.context["rpc"] = self.rpc
        self.it.context["machine_state"] = self.machine_state
        self.it.context["machine_discover"] = self.machine_discover
        self.it.context["maintenance_scheduler"] = self.maintenance_scheduler
        self.it.context["psvalue"] = self.psvalue
        self.it.context["CONF_FNAME"] = self.conf_file
        self.it.context["maintenance_menu"] = self.maintenance_menu
        self.it.context["LSM_FNAME"] = self.lsm
        self.it.context["LMH_FNAME"] = self.lmh
        self.it.context["UnitType"] = UnitType
        self.it.context["is_android"] = platform.system != "Darwin"

    def test_home_screen(self):
        status = Mock()
        status.value = 0
        self.status.get_connection_status.return_value = status
        self.config.curr_machine = ""
        self.config.get_poll_period = Mock(return_value=1)
        self.config.get_current_unit_type = Mock(return_value=UnitType.METRIC)
        self.psvalue.data = None
        self.ui.get_app_version.return_value = "0.1.0"
        self.psvalue.get_fault_code.return_value = ("", "")
        val = {"status": 0, "machines": ["sample_1", "sample_2"], "curr_machine": "","data":None, "app_version": "0.1.0", "fault_code": ""}

        steps = self.it.execute()
        self.ui.switch.assert_called_with("home_screen", val)
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_home_screen_back(self):
        self.config.get_poll_period = Mock(return_value=1)
        self.it.execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.ui.stop.assert_called()

    def test_start_rpc_client(self):
        self.config.get_poll_period = Mock(return_value=1)
        steps = self.it.execute()

        self.rpc.try_connect_start.assert_called_with(retry_period=3)
        self.assertTrue(testing.state_is_entered(steps, "rpc_started"))

    def test_rpc_started(self):
        self.config.get_poll_period = Mock(return_value=1)
        steps = self.it.queue("app_resumed").execute()

        self.assertTrue(testing.state_is_entered(steps, "start_rpc_client"))

    def test_machine_select(self):
        home_screen(self.it, self.config)
        self.config.update_last_selected_machine = Mock(return_value=None)
        steps = self.it.queue("machine_selected", value="sample_1").execute()

        self.assertTrue(testing.state_is_entered(steps, "iotnode"))
        self.config.update_last_selected_machine.assert_called_with(self.lsm)

    def test_cutting_process_view_screen(self):
        home_screen(self.it, self.config)
        steps = self.it.queue("cutting_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutting"))

    def test_service_process_view_screen(self):
        home_screen(self.it, self.config)
        self.it.queue("service_menu_button_pressed").execute()
        steps = self.it.queue("service_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))

    def test_process_setup_input_screen(self):
        home_screen(self.it, self.config)
        steps = self.it.queue("process_setup_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_input"))

    def test_maintenance_schedule_screen(self):
        self.psvalue.data = {"ah": 0}

        service_menu_screen(self.it, self.config)
        self.it.queue("maintenance_button_pressed").execute()
        steps = self.it.queue("maintenance_schedule_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "maintenance_schedule"))

    def test_cutting_screen_back(self):
        home_screen(self.it, self.config)
        self.it.queue("cutting_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_settings_screen(self):
        home_screen(self.it, self.config)
        steps = self.it.queue("settings_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "settings"))

    def test_settings_screen_back(self):
        home_screen(self.it, self.config)
        self.it.queue("settings_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_machine_config_screen(self):
        val = {"machines": [SAMPLE_MACHINE_1, SAMPLE_MACHINE_2],
               "is_metric": self.config.get_current_unit_type() == UnitType.METRIC}

        settings_screen(self.it, self.config)
        steps = self.it.queue("machine_config_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "machines"))
        self.ui.switch.assert_called_with("machine_config_screen", val)

    def test_machine_config_screen_back(self):
        settings_screen(self.it, self.config)
        self.it.queue("machine_config_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "settings"))

    def test_add_machine_pass(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": True}
        expected_machine = {"name":"sample_3", "ip": "192.168.4.1", "port": 5000, "hose_length": "23 m", "torch_style": "21"}

        self.config.save = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        step_1 = self.it.queue("machine_edit_button_pressed", value=val).execute()
        self.assertTrue(testing.state_is_entered(step_1, "machine_edit"))
        step_2 = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step_2, "machines"))
        self.config.save.assert_called_with(self.conf_file)
        self.assertEqual(self.config.machines.get("sample_3"), expected_machine)

    def test_add_machine_pass_with_valid_ipv6(self):
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": ipv6, "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": True}
        expected_machine = {"name":"sample_3", "ip": ipv6, "port": 5000, "hose_length": "23 m", "torch_style": "21"}

        self.config.save = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        step_1 = self.it.queue("machine_edit_button_pressed", value=val).execute()
        self.assertTrue(testing.state_is_entered(step_1, "machine_edit"))
        step_2 = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step_2, "machines"))
        self.config.save.assert_called_with(self.conf_file)
        self.assertEqual(self.config.machines.get("sample_3"), expected_machine)

    def test_add_machine_back(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}

        settings_screen(self.it, self.config)
        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "machines_mode"))

    def test_add_machine_fail_with_invalid_name(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": True}
        expected_err = "Machine name should have a minimum of 4 characters."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_add_machine_fail_with_invalid_ip(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": "192", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": True}
        expected_err = "Machine IP '192' is not an IPv4 or IPv6 address."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_add_machine_fail_with_invalid_port(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": "192.168.4.1", "port": '0', "hose_length": "23 m", "torch_style": "21", "is_add": True}
        expected_err = "Port should be between 1 and 65535."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_add_machine_fail_with_invalid_hose_length(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "0", "torch_style": "21", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": "192.168.4.1", "port": '8080', "hose_length": "0", "torch_style": "21", "is_add": True}
        expected_err = "Hose length is none of these values 3.0, 4.6, 7.6, 10.6, 15.2, 23, 30.5, 38.0, 45.6, 53.3."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_add_machine_fail_with_invalid_torch_style(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "0", "is_add": True, "scan": False}
        data = { "name": "sample_3", "ip": "192.168.4.1", "port": '8080', "hose_length": "23 m", "torch_style": "0", "is_add": True}
        expected_err = "Torch Style is none of these values 21, 22."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_add_machine_scan_state_not_change(self):
        val = {"name": "", "ip": "", "port": "", "is_add": True, "scan": True}
        list_machine_data = [{}]
        self.config.save = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step_1 = self.it.queue("list_of_machines_resp", value=list_machine_data).execute()
        self.assertFalse(testing.state_is_exited(step_1, "machine_scan"))

    def test_add_machine_scan_back(self):
        val = {"name": "", "ip": "", "port": "", "hose_length": "23 m", "torch_style": "21", "is_add": True, "scan": True}

        settings_screen(self.it, self.config)
        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("add_machine_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "machines"))

    def test_help_screen_maintenance(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("help_button_pressed").execute()
        steps = self.it.queue("maintenance_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "maintenance"))

    def test_help_screen_cut_quality_tips(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("help_button_pressed").execute()
        steps = self.it.queue("cut_quality_tips_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "cut_quality_tips"))

    def test_help_screen_errors(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("help_button_pressed").execute()
        steps = self.it.queue("errors_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "errors"))

    def test_maintenance_screen_back(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("maintenance_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service_menu"))

    def test_cut_quality_tips_screen_back(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("cut_quality_tips_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service_menu"))

    def test_errors_screen_back(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("errors_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service_menu"))

    def test_errors_screen_submit(self):
        data = 104

        service_menu_screen(self.it, self.config)
        self.it.queue("errors_button_pressed").execute()
        self.it.queue("error_submit_button_pressed", value=data).execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "errors"))

    def test_error_information_screen_back(self):
        data = 402

        service_menu_screen(self.it, self.config)
        self.it.queue("errors_button_pressed").execute()
        steps = self.it.queue("back_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "service_menu"))

    def test_process_setup_input_screen_back(self):
        process_setup_input_screen(self.it, self.config)
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_process_setup_input_screen_ok(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        steps = self.it.queue("submit_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_thc"))

    def test_process_setup_preview_screen_back(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_input"))

    def test_process_setup_thc_screen_back(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        steps = self.it.queue("back_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_input"))

    def test_process_setup_thc_screen_download(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("marking_button_pressed", value=data).execute()
        steps = self.it.queue("download_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_export"))

    def test_process_setup_thc_screen_marking(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        steps = self.it.queue("marking_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "marking_process"))

    def test_process_setup_thc_screen_consumable(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        steps = self.it.queue("consumable_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_consumables"))

    def test_process_setup_consumables_screen_back(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        steps = self.it.queue("back_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_thc"))

    def test_process_setup_consumables_screen_download(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        steps = self.it.queue("download_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_export"))

    def test_cutchart_export_screen_back(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        self.it.queue("download_button_pressed", value=data).execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_thc"))

    def test_cutchart_export_screen_error(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        self.it.queue("download_button_pressed", value=data).execute()
        steps = self.it.queue("error").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_export_retry"))

    def test_cutchart_export_retry_popup_cancel(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        self.it.queue("download_button_pressed", value=data).execute()
        self.it.queue("error", value=data).execute()
        steps = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "process_setup_thc"))

    def test_cutchart_export_retry_popup_retry(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        self.it.queue("download_button_pressed", value=data).execute()
        self.it.queue("error", value=data).execute()
        steps = self.it.queue("retry_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_export"))

    def test_cutchart_export_screen_sent_param_list(self):
        data = []

        process_setup_input_screen(self.it, self.config)
        self.it.queue("submit_button_pressed", value=data).execute()
        self.it.queue("consumable_button_pressed", value=data).execute()
        self.it.queue("download_button_pressed", value=data).execute()
        steps = self.it.queue("sent_param_list").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_download"))

    def test_cutting_screen_machine_selected(self):
        data = "sample2"

        home_screen(self.it, self.config)
        self.config.update_last_selected_machine = Mock(return_value=None)
        steps = self.it.queue("cutting_button_pressed").execute()
        self.it.queue("machine_selected", value=data).execute()
        self.assertFalse(testing.state_is_exited(steps, "cutting"))

    def test_cutting_screen_after_poll_period(self):
        data = ""

        home_screen(self.it, self.config)
        steps = self.it.queue("cutting_button_pressed").execute()
        self.it.clock.time += self.config.get_poll_period()
        self.it.execute_once()
        self.assertFalse(testing.state_is_exited(steps, "cutting"))

    def test_process_view_screen_cutchart_verify(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        steps = self.it.queue("cutchart_verify_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_compare"))

    def test_process_view_screen_cutchart_valve_check_authenticated_true(self):
        data = {"authenticated": True}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        steps = self.it.queue("valve_check_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "service_feature"))

    def test_process_view_screen_cutchart_valve_check_authenticated_false(self):
        data = {"authenticated": False}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        steps = self.it.queue("valve_check_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "authenticate_valve_check"))

    def test_authenticate_valve_check_popup_cancel(self):
        data = {"authenticated": False}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("valve_check_button_pressed", value=data).execute()
        steps = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))


    def test_node_ap_config_screen_with_no_machine(self):
        val = {"name": "sample_2", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        expected_msg = "Please select a machine to configure AP."
        self.config.curr_machine = ""

        self.config.save = Mock(return_value=None)
        self.config.update_last_selected_machine = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        self.it.queue("remove_machine_button_pressed").execute()
        self.it.queue("ok_button_pressed").execute()
        self.it.queue("back_button_pressed").execute()
        steps = self.it.queue("node_ap_config_button_pressed").execute()
        self.ui.show_popup.assert_called_with("Alert!", expected_msg)
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_authenticate_valve_check_popup_confirm_success_false(self):
        data = {"authenticated": False}
        data1 = {"success": False}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("valve_check_button_pressed", value=data).execute()
        steps = self.it.queue("confirm_button_pressed", value=data1).execute()
        self.assertFalse(testing.state_is_entered(steps, "authenticate_valve_check"))

    def test_authenticate_valve_check_popup_confirm_success_true(self):
        data = {"authenticated": False}
        data1 = {"success": True}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("valve_check_button_pressed", value=data).execute()
        steps = self.it.queue("confirm_button_pressed", value=data1).execute()
        self.assertTrue(testing.state_is_entered(steps, "service_feature"))

    def test_cutchart_compare_screen_back(self):
        data = []

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        steps = self.it.queue("back_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))

    def test_cutchart_compare_screen_got_param_list(self):
        data = []
        called_args = ("cutchart_verify_loading_screen", {"obtained": data})

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        self.it.queue("got_param_list", value=data).execute()
        self.ui.switch.assert_called_with(*called_args)

    def test_cutchart_compare_screen_got_process_id(self):
        data = []
        called_args = ("cutchart_verify_loading_screen", {"process_id": data})

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        self.it.queue("got_process_id", value=data).execute()
        self.ui.switch.assert_called_with(*called_args)

    def test_cutchart_compare_screen_get_param_list(self):
        data = []

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        self.it.queue("get_param_list", value=data).execute()
        self.rpc.get_param_list_start.assert_called_with(data)

    def test_cutchart_compare_screen_error(self):
        err_msg = "Error receiving cutchart comparison values.\nDo you want to retry?"
        buttons = {"cancel_button": "Cancel", "retry_button": "Retry"}

        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        steps = self.it.queue("error").execute()
        self.ui.show_popup.assert_called_with("Confirm", err_msg, buttons)
        self.assertTrue(testing.state_is_entered(steps, "cutting_compare_retry"))

    def test_cutting_compare_retry_popup_cancel(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        self.it.queue("error").execute()
        steps = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))

    def test_cutting_compare_retry_popup_retry(self):
        service_menu_screen(self.it, self.config)
        self.it.queue("service_button_pressed").execute()
        self.it.queue("cutchart_verify_button_pressed").execute()
        self.it.queue("error").execute()
        steps = self.it.queue("retry_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "cutchart_compare"))

    def test_service_feature_screen_back(self):
        service_feature_screen(self.it, self.config)
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))

    def test_service_feature_screen_param_change(self):
        data = []

        service_feature_screen(self.it, self.config)
        self.it.queue("param_change", value=data).execute()
        self.rpc.set_params_start.assert_called_with(data)

    def test_service_feature_screen_get_service(self):
        data = []

        service_feature_screen(self.it, self.config)
        self.it.queue("get_service", value=data).execute()
        self.rpc.get_params_start.assert_called_with(data)

    def test_service_feature_screen_got_service_data(self):
        data = []
        called_args = ("service_feature_screen", {'param_state': data})

        service_feature_screen(self.it, self.config)
        self.it.queue("got_service_data", value=data).execute()
        self.ui.switch.assert_called_with(*called_args)

    def test_cutchart_compare_screen_error(self):
        err_msg = "Error receiving service feature values.\nDo you want to retry?"
        buttons = {"cancel_button": "Cancel", "retry_button": "Retry"}

        service_feature_screen(self.it, self.config)
        steps = self.it.queue("error").execute()
        self.ui.show_popup.assert_called_with("Confirm", err_msg, buttons)
        self.assertTrue(testing.state_is_entered(steps, "service_feature_retry"))

    def test_service_feature_retry_popup_cancel(self):
        service_feature_screen(self.it, self.config)
        self.it.queue("error").execute()
        steps = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service"))

    def test_service_feature_retry_popup_retry(self):
        service_feature_screen(self.it, self.config)
        self.it.queue("error").execute()
        steps = self.it.queue("retry_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "service_feature"))

    def test_maintenance_schedule_screen_back(self):
        self.psvalue.data = {"ah": 0}

        service_menu_screen(self.it, self.config)
        self.it.queue("maintenance_schedule_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "home"))

    def test_maintenance_schedule_screen_mark_as_serviced(self):
        data = []
        self.psvalue.data = {"ah": 0}

        service_menu_screen(self.it, self.config)

        self.it.queue("maintenance_button_pressed").execute()
        self.it.queue("maintenance_schedule_button_pressed").execute()
        steps = self.it.queue("mark_as_serviced_button_pressed", value=data).execute()
        self.maintenance_scheduler.save.assert_called_with(self.lmh, data)
        self.assertTrue(testing.state_is_entered(steps, "maintenance_schedule"))

    def test_update_machine_pass(self):
        val = {"name": "sample_3", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        data = {"name": "sample_3", "ip": "192.168.4.1", "port": '6000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        expected_machine = {"name":"sample_3", "ip": "192.168.4.1", "port": 6000, "hose_length": "23 m", "torch_style": "21"}

        self.config.save = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machines"))
        self.config.save.assert_called_with(self.conf_file)
        self.assertEqual(self.config.machines.get("sample_3"), expected_machine)

    def test_update_machine_back(self):
        val = {"name": "sample_3", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}

        settings_screen(self.it, self.config)
        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "machines"))

    def test_update_machine_fail_with_invalid_ip(self):
        val = {"name": "sample_3", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        data = {"name": "sample_3", "ip": "192", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        expected_err = "Machine IP '192' is not an IPv4 or IPv6 address."

        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_update_machine_fail_with_invalid_port(self):
        val = {"name": "sample_3", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        data = {"name": "sample_3", "ip": "192.168.4.1", "port": '0', "hose_length": "23 m", "torch_style": "21", "is_add": False}
        expected_err = "Port should be between 1 and 65535."

        settings_screen(self.it, self.config)
        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step = self.it.queue("ok_button_pressed", value=data).execute()
        self.assertTrue(testing.state_is_entered(step, "machine_edit"))
        self.ui.show_popup.assert_called_with("Error", expected_err)

    def test_remove_machine_pass(self):
        val = {"name": "sample_2", "ip": "192.168.4.1", "port": '5000', "hose_length": "23 m", "torch_style": "21", "is_add": False}

        self.config.save = Mock(return_value=None)
        self.config.update_last_selected_machine = Mock(return_value=None)
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step_1 = self.it.queue("remove_machine_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step_1, "remove_machine"))
        step_2 = self.it.queue("ok_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step_2, "machines"))
        self.config.update_last_selected_machine.assert_called_with(self.lsm)
        self.config.save.assert_called_with(self.conf_file)
        self.assertEqual(self.config.machines.get("sample_2"), None)

    def test_remove_machine_cancel(self):
        val = {"name": "sample_1", "ip": "192.168.4.1", "port": "5000", "hose_length": "23 m", "torch_style": "21", "is_add": False}
        settings_screen(self.it, self.config)

        self.it.queue("machine_config_button_pressed").execute()
        self.it.queue("machine_edit_button_pressed", value=val).execute()
        step_1 = self.it.queue("remove_machine_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step_1, "remove_machine"))
        step_2 = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step_2, "machines"))
        self.assertEqual(self.config.machines.get("sample_1"), SAMPLE_MACHINE_1)

    def test_node_ap_config_screen(self):
        settings_screen(self.it, self.config)
        steps = self.it.queue("node_ap_config_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "get_ap_list_start_scan"))
        self.assertTrue(testing.state_is_entered(steps, "get_ap_list"))
        self.rpc.list_networks_start.assert_called()

    def test_node_ap_config_screen_back(self):
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()
        steps = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(steps, "settings"))

    def test_node_ap_list_network_resp(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        steps = self.it.queue("list_networks_resp", value=ap_list).execute()
        self.assertTrue(testing.state_is_entered(steps, "show_ap_list"))

    def test_node_ap_list_network_retry_ok(self):
        expected_msg = "Error receiving node AP list.\nDo you want to retry?"
        expected_btn = {"cancel_button": "Cancel", "retry_button": "Retry"}
        settings_screen(self.it, self.config)

        self.it.queue("node_ap_config_button_pressed").execute()
        step_1 = self.it.queue("error").execute()
        self.ui.show_popup.assert_called_with("Confirm", expected_msg, expected_btn)
        self.assertTrue(testing.state_is_entered(step_1, "list_network_retry_confirm"))
        step_2 = self.it.queue("retry_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step_2, "get_ap_list_start_scan"))

    def test_node_ap_list_network_retry_cancel(self):
        settings_screen(self.it, self.config)

        self.it.queue("node_ap_config_button_pressed").execute()
        self.it.queue("error").execute()
        step = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "settings"))

    def test_node_ap_show_ap_list_refresh(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        step = self.it.queue("refresh_button_pressed", value=ap_list).execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))

    def test_node_ap_show_ap_list_back(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        step = self.it.queue("back_button_pressed", value=ap_list).execute()
        self.assertTrue(testing.state_is_entered(step, "settings"))

    def test_node_ap_item_pressed(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        step = self.it.queue("ap_item_pressed", value=ap_list).execute()
        self.assertTrue(testing.state_is_entered(step, "enter_password"))

    def test_node_ap_enter_password_connect(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        ssid = ap_list[0]["ssid"]
        password = ""
        is_static = False
        ip = None
        subnet = None
        gateway = None
        ap_params = NetworkParams(bssid, ssid, password, is_static, ip, subnet, gateway)
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        step = self.it.queue("connect_button_pressed", value=ap_params).execute()
        self.assertTrue(testing.state_is_entered(step, "select_network"))

    def test_node_ap_enter_password_cancel(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        password = ""
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        step = self.it.queue("cancel_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))

    def test_node_ap_enter_password_back(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        step = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))

    def test_select_network_resp(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        ssid = ap_list[0]["ssid"]
        net_params = (bssid, ssid, "", False, None, None, None)
        ap_params = NetworkParams(*net_params)
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        self.it.queue("connect_button_pressed", value=ap_params).execute()
        step = self.it.queue("select_network_resp").execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))

    def test_wizard_configuration(self):
        ap_list = {
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }
        bssid = ap_list["bssid"]
        ssid = ap_list["ssid"]
        net_params = (bssid, ssid, "", False, None, None, None)
        machine = "1111"
        self.config.save = Mock(return_value=None)
        self.config.update_last_selected_machine = Mock(return_value=None)

        ap_params = NetworkParams(*net_params)
        settings_screen(self.it, self.config)
        self.it.queue("wizard_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("next_button_pressed", value=machine).execute()
        self.it.queue("next_button_pressed", value=machine).execute()
        self.it.queue("pong_received").execute()
        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        self.it.queue("connect_button_pressed", value=ap_params).execute()
        self.it.queue("select_network_resp").execute()
        step = self.it.queue("next_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "ap_reconnection"))


    def test_select_network_err(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        ssid = ap_list[0]["ssid"]
        net_params = (bssid, ssid, "", False, None, None, None)
        ap_params = NetworkParams(*net_params)
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        self.it.queue("connect_button_pressed", value=ap_params).execute()
        step = self.it.queue("error").execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))

    def test_select_network_back(self):
        ap_list = [{
            "ssid": "NetGear 2.4G",
            "encrypt_type": "wpa2",
            "rssi": -70,
            "bssid": "00:b4:23:56:3a:40",
            "channel": 0,
            "hidden": 0,
            "current": 1
        }]
        bssid = ap_list[0]["bssid"]
        ssid = ap_list[0]["ssid"]
        net_params = (bssid, ssid, "", False, None, None, None)
        ap_params = NetworkParams(*net_params)
        settings_screen(self.it, self.config)
        self.it.queue("node_ap_config_button_pressed").execute()

        self.it.clock.time += 5
        self.it.execute()

        self.it.queue("list_networks_resp", value=ap_list).execute()
        self.it.queue("ap_item_pressed", value=ap_list).execute()
        self.it.queue("connect_button_pressed", value=ap_params).execute()
        step = self.it.queue("back_button_pressed").execute()
        self.assertTrue(testing.state_is_entered(step, "get_ap_list"))
