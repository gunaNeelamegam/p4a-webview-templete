from routes import flask_app
from sismic.interpreter import Interpreter
from iotnode.presenter import MachineState
from iotnode.psvalue import ProcessValueFormatter
from iotnode.status import StatusIndicator
from iotnode.rpc import IotNodeInterface
from iotnode.cut_chart import CutChart
from iotnode.discover import MachineDiscover
from iotnode.configuration import  UnitType


import platform
import os.path
import platform
from random import random
from typing import Dict, Any
import requests
from requests.exceptions import RequestException
from packaging import version


class UpdateError(Exception):
    pass


class IOTNodeFlaskApp:

    CONF_FNAME = "config.json"
    LSM_FNAME = "last_selected_machine"
    LMH_FNAME = "last_maintenanced_arc_hours.json"
    CUTCHART_FNAME = "cutchart.csv"
    MAINTENANCE_LINK_FNAME = "maintenance_link.csv"

    """
    Flask App
    """

    def init_flask_server(self):
        """
        Starting the flask Server
        port : 5000
        host_ip:localhost
        """
        from routes import flask_app

        flask_app.run(threaded=False,debug=False)

    def __init__(self, sismic_interperter: Interpreter, version: Any) -> None:
        self.init_flask_server()
        self.interperter = sismic_interperter
        self.conf_file = os.path.join(self.user_data_dir, self.CONF_FNAME)
        self.last_selected_machine_fname = os.path.join(
            self.user_data_dir, self.LSM_FNAME
        )
        self.dir_path = os.path.abspath(os.path.dirname(__file__))
        self._maintenance_link_path = os.path.join(
            self.dir_path, self.MAINTENANCE_LINK_FNAME
        )
        self.last_maintenanced_hrs_fname = os.path.join(
            self.user_data_dir, self.LMH_FNAME
        )
        self.cutchart_file = os.path.join(self.dir_path, self.CUTCHART_FNAME)
        self._reverse = False
        self._event_history = []
        self._version = version
        self._setup_client()

    def get_app_version(self):
        return self._version

    def check_for_updates(self):
        IOS_APPSTORE = "http://itunes.apple.com/lookup?bundleId="
        IOS_BUNDLEID = "com.esab.iotnodeapp"

        if platform.system() == "Darwin":
            try:
                response = requests.get("{}{}".format(IOS_APPSTORE, IOS_BUNDLEID))
            except RequestException as err:
                print("Error getting app version from appstore: {}".format(err))
                return

            try:
                appstore_version = response.json()["results"][0]["version"]
            except (KeyError, IndexError) as err:
                print("Error parsing the app version: {}".format(err))
                return

            if version.parse(appstore_version) > version.parse(self._version):
                title = "Update Available!"
                description = "New version of the app is available from App store. Install the latest version of the app, and get the latest updates and improvements."

                print(
                    "installed version = {}, appstore version = {}".format(
                        self._version, appstore_version
                    )
                )
                self.show_popup(
                    "{}".format(title),
                    "{}\n\nVersion: {}".format(description, appstore_version),
                )

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
        context = self.interperter.context
        context["ui"] = self
        context["machine_state"] = MachineState()
        context["cutchart"] = self.cutchart
        context["machine_discover"] = self.machine_discover
        context["maintenance_scheduler"] = self.maintenance_scheduler
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

    def switch(self, name: str, request_data: Dict[str,Any] = None):
        """Switches to the specified API template page.
        templates: for rendering the ui templates are stored inside the templates
        Args:
            name: name of the screen to switch to
            tmpl_data: Initial data for the screen

        Raises:
            ValueError: if data doesn't match the screen property
        """

        print(
            f"name of the screen : {name},rendering data to the screen {request_data}"
        )