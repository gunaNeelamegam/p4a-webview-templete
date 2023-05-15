"""Main application implementation.

The IoTNodeApp class initializes the Kivy application, statechart
interpreter, action classes. Binds the Kivy application and the
statechart interpreter.
"""

import os.path
import platform
from random import random
from typing import Dict, Any
import requests
from requests.exceptions import RequestException
from packaging import version

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang.builder import Builder
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout

# We cannot do relative import as the application not runs as module
# but as script

# pylint: disable=import-error
from .views import MachinesListScreen  # pylint: disable=unused-import
from .views import AlertPopup  # pylint: disable=unused-import
from .presenter import MachineState
from .configuration import Configuration, ConfigLoadError, UnitType
from .psvalue import ProcessValueFormatter
from .status import StatusIndicator
from .rpc import IotNodeInterface
from .cut_chart import CutChart
from .maintenance_menu import MaintenanceMenu
from .discover import MachineDiscover
from .maintenance import MaintenanceScheduler, MaintenanceLoadError

CONF_FNAME = "config.json"
LSM_FNAME = "last_selected_machine"
LMH_FNAME = "last_maintenanced_arc_hours.json"
CUTCHART_FNAME = "cutchart.csv"
MAINTENANCE_LINK_FNAME= "maintenance_link.csv"


class Main(BoxLayout):
    """Toplevel (root widget) of the application."""
    pass


class UpdateError(Exception):
    pass


class IOTNodeApp(App):

    def __init__(self, it, version):
        super().__init__()
        self.conf_file = os.path.join(self.user_data_dir, CONF_FNAME)
        self.last_selected_machine_fname = os.path.join(self.user_data_dir, LSM_FNAME)
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self._maintenance_link_path = os.path.join(self.dir_path, MAINTENANCE_LINK_FNAME)
        self.last_maintenanced_hrs_fname = os.path.join(self.user_data_dir, LMH_FNAME)
        self.cutchart_file = os.path.join(self.dir_path,CUTCHART_FNAME)
        self.it = it
        self._setup_keyboard_hook()
        self._setup_config()
        self._setup_maintenance()
        self._setup_client()
        self._setup_interpreter()
        self._reverse = False
        self._event_history = []
        self._version = version

    def build(self):
        res_path = os.path.dirname(__file__)
        kivy.resources.resource_add_path(res_path)
        Builder.load_file("main.kv")
        self.root = Main()
        self.it.clock.start()
        Clock.schedule_interval(self.it.execute, 0.1)
        return self.root

    def on_resume(self):
        self.send_event("app_resumed")
        Logger.info("Application resumed")
        return True

    def _setup_keyboard_hook(self):
        Window.bind(on_keyboard=self._handle_esc)

    def _setup_config(self):
        self.config = Configuration()
        self.config.load_last_selected_machine(self.last_selected_machine_fname)
        try:
            self.config.load(self.conf_file)
        except ConfigLoadError as err:
            Logger.error(err)

    def _setup_maintenance(self):
        self.maintenance_menu = MaintenanceMenu(self._maintenance_link_path)
        self.maintenance_scheduler = MaintenanceScheduler()
        try:
            self.maintenance_scheduler.load(self.last_maintenanced_hrs_fname)
        except MaintenanceLoadError as err:
            Logger.error(err)

    def _setup_client(self):
        self.rpc = IotNodeInterface(self.config, self.send_event)
        self.psvalue = ProcessValueFormatter()
        self.cutchart = CutChart(self.cutchart_file)
        self.status = StatusIndicator(self.config.get_poll_period)
        self.machine_discover = MachineDiscover(self.send_event)

        # Register callbacks
        self.rpc.register_callback(self.psvalue.process_data)
        self.rpc.register_callback(self.status.collect_data)

    def _setup_interpreter(self):
        context = self.it.context
        context["ui"] = self
        context["machine_state"] = MachineState()
        context["cutchart"] = self.cutchart
        context["machine_discover"] =  self.machine_discover
        context["maintenance_scheduler"] =  self.maintenance_scheduler
        context["config"] = self.config
        context["maintenance_menu"] = self.maintenance_menu
        context["psvalue"] = self.psvalue
        context["rpc"] = self.rpc
        context["status"] = self.status
        context["CONF_FNAME"] = self.conf_file
        context["LSM_FNAME"] = self.last_selected_machine_fname
        context["LMH_FNAME"] = self.last_maintenanced_hrs_fname
        context["UnitType"] = UnitType
        context["is_android"] = platform.system() != "Darwin"

    def switch(self, name: str, tmpl_data: Dict[str, Any] = None):
        """Switches to the specified application screen.

        Args:
            name: name of the screen to switch to
            tmpl_data: Initial data for the screen

        Raises:
            ValueError: if data doesn't match the screen property
        """

        switcher = self.root.ids.switcher
        if not self._reverse:
            switcher.transition.direction = "left"
        else:
            switcher.transition.direction = "right"
        switcher.current = name

        if tmpl_data is None:
            tmpl_data = {}
        for key, value in tmpl_data.items():
            if hasattr(switcher.current_screen, key):
                setattr(switcher.current_screen, key, value)
            else:
                raise ValueError("invalid screen property '{}".format(key))

    def send_event(self, event: str, value: Dict[str, Any] = None, reverse_direction: bool = False):
        """Sends events to application statecharts interpreter.

        Args:
            event: event to be sent
            value: data associated with the event
        """
        if event.endswith("_pressed"):
            self._reverse = reverse_direction
        self.it.queue(event, value=value)

    def _handle_esc(self, window, key, *args):
        if key == 27:
            self.send_event("back_button_pressed", reverse_direction=True)
            return True
        return False

    @staticmethod
    def show_popup(title: str, err_msg: str, buttons: Dict[str, str] = None):
        """Displays a popup to show alert messages.

        Args:
            title: Popup title text
            err_msg: Detailed error message
            buttons: Mapping of button names to button text
        """
        # FIXME: Use List instead of dictionary to map
        # button names to button text
        alert = AlertPopup(title=title)
        alert.msg = err_msg
        alert.add_buttons(buttons)
        alert.open()

    @staticmethod
    def get_random_val():
        return random()

    def get_app_version(self):
        return self._version

    def check_for_updates(self):
        IOS_APPSTORE = "http://itunes.apple.com/lookup?bundleId="
        IOS_BUNDLEID = "com.esab.iotnodeapp"

        if platform.system() == "Darwin":
            try:
                response = requests.get("{}{}".format(IOS_APPSTORE, IOS_BUNDLEID))
            except RequestException as err:
                Logger.error("Error getting app version from appstore: {}".format(err))
                return

            try:
                appstore_version = response.json()["results"][0]["version"]
            except (KeyError, IndexError) as err:
                Logger.error("Error parsing the app version: {}".format(err))
                return

            if version.parse(appstore_version) > version.parse(self._version):
                title = "Update Available!"
                description = "New version of the app is available from App store. Install the latest version of the app, and get the latest updates and improvements."

                Logger.info("installed version = {}, appstore version = {}".format(self._version,
                                                                                   appstore_version))
                self.show_popup("{}".format(title), "{}\n\nVersion: {}".format(description, appstore_version))
