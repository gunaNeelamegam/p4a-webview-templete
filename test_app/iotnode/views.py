"""Widgets that supports Dynamic changes in UI"""

import os
from typing import NamedTuple, Tuple
from typing import Any, Dict, List
import webbrowser
import re

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty  # pylint: disable=no-name-in-module
from kivy.properties import ListProperty  # pylint: disable=no-name-in-module
from kivy.properties import NumericProperty  # pylint: disable=no-name-in-module
from kivy.properties import StringProperty  # pylint: disable=no-name-in-module
from kivy.properties import ObjectProperty  # pylint: disable=no-name-in-module
from kivy.properties import DictProperty  # pylint: disable=no-name-in-module
from kivy.properties import ColorProperty  # pylint: disable=no-name-in-module
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.togglebutton import ToggleButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.checkbox import CheckBox
from kivy.metrics import dp, sp

from .cut_chart_fetcher import CutchartFetchInputParam
from .cut_chart_fetcher import CutChartFetcherError
from .cut_chart_fetcher import CutChartParam
from .psvalue import ProcessValueFormatter
from .faults import FCCM, FDMC, FDPC
from .configuration import Configuration

class Filler(Label):
    """Default Kivy Label"""
    pass


class IoTButton(Button):
    """Button with name when pressed triggers an event with button name."""
    name = StringProperty()
    """Button name for handling the button specific events"""
    event_data = None
    """Data to send along with the events"""
    reverse = BooleanProperty(False)
    """App to change its transistion direction"""


class CommandButton(IoTButton):
    """Button with modified dimensions and color."""
    pass


class MenuButton(IoTButton):
    pass


class Theme(Widget):
    """Widget, theme (color) of it can be changed."""
    theme = StringProperty()
    """Widget color in hex code"""

class RoundedButton(Button):
    down_color = ColorProperty()
    normal_color = ColorProperty()

class LabelButton(ButtonBehavior, Label, Theme):
    """Label with button and theme properties"""
    name = StringProperty()
    """Button name for handling the button specific events"""
    event_data = None
    """Data to send along with the events"""
    reverse = BooleanProperty(False)
    """App to change its transistion direction"""


class PopupWidget(Popup):
    """Popup with modified theme."""
    pass


class IotNodeImage(BoxLayout, Theme):
    """IotNode Image boxlayout"""

    @staticmethod
    def open_link(url: str):
        """Opens the link with the browser"""
        webbrowser.open(url)


class LinkButton(MenuButton):
    link = StringProperty()

    def on_press(self, *args):
        """Opens the link with the browser"""
        if self.link:
            webbrowser.open(self.link)


class NetworkSettingsInputBox(BoxLayout):
    pass


class StaticSwitch(ToggleButtonBehavior, Image):
    """Switch for choosing DHCP or static network"""
    active = BooleanProperty(False)
    scroll = ObjectProperty()
    sta_params = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'images/switch-off.png'

    def on_sta_params(self, instance: "StaticSwitch", sta_params: List["NetworkSettingsInputBox"]):
        self.on_state(self, "normal")

    def on_state(self, widget: "StaticSwitch", value: str):
        if value == "down":
            self.active = True
            self.scroll.do_scroll = True
            self.source = 'images/switch-on.png'
        else:
            self.active = False
            self.scroll.scroll_y = 1
            self.scroll.do_scroll = False
            self.source = 'images/switch-off.png'

        for obj in self.sta_params:
            obj.disabled = not self.active

        for obj in self.sta_params:
            obj.opacity = 1 if self.active else 0


class AlertPopup(PopupWidget):
    """Popup widget for confirmation."""

    def add_buttons(self, buttons: Dict[str, str] = None) -> None:
        """Creates button widgets with name and text, and adds it to popup.

        Args:
          buttons: buttons to be created.
        """
        btn_widgets = []
        if buttons is None:
            buttons = {"dismiss_button": "OK"}

        if len(buttons) < 2:
            btn_widgets.append(Filler())

        for btn_name, btn_text in buttons.items():
            btn_args = {
                "text": btn_text,
                "reverse": False if btn_name != 'cancel_button' else True,
                "name": btn_name,
                "font_size": "15sp",
                "on_press": self.dismiss,
            }
            btn = CommandButton(**btn_args)
            btn_widgets.append(btn)
            btn_widgets.append(Filler())

        btn_widgets.pop()  # pop last filler
        for widget in btn_widgets:
            self.ids.buttons.add_widget(widget)


class ValveCheckPopup(PopupWidget):
    """Popup widget for valve check authentication"""

    valid_password = StringProperty("pmcs1")

    authenticated = BooleanProperty(False)

    incorrect_message = StringProperty()

    def authenticate(self):
        password = self.ids.password
        entered_password = password.input_text
        password.input_text = ""
        if entered_password != self.valid_password:
            self.incorrect_message = "Incorrect Password!"
            return False
        self.authenticated = True
        return True


class IotBaseLabel(Label):
    """Label with modified attributes(color, size etc..)."""
    pass

class NoMaintainLabel(Label):
    """Label with modified attributes(color, size etc..)."""
    pass

class MaintenanceLayout(BoxLayout):
    text = StringProperty()

class MaintenanceItem(BoxLayout):
    text = StringProperty()

class MenuCheckBox(CheckBox):
    """Label with modified attributes(color, size etc..)."""
    text = StringProperty()

class NoMaintenaceBoxLayout(BoxLayout):
    pass

class MaintenanceBaseLabel(Label):
    pass

class TitleLabel(IotBaseLabel, Theme):
    """Label with title theme."""
    pass

class NoMaintenanceHint(BoxLayout):
    pass

class NodeAPConfigHint(BoxLayout):
    """Hint Label on AP config screen."""
    pass


class MaintenanceSchedulerHint(BoxLayout):
    """Hint Label on Maintenance Scheduler screen."""
    pass

class MachineEditScreen(Screen):

    def torch_data(self):
        values = ["21", "22"]
        return values

class MachineListItem(ButtonBehavior, BoxLayout):
    """Touchable Machine item which shows the machine details."""
    machine_name = StringProperty()
    """Machine name"""
    ip = StringProperty()
    """Machine IP"""
    port = StringProperty()
    """Machine Port"""
    hose_length = StringProperty()
    """Machine Hose Length"""
    torch_style = StringProperty()
    """Machine Torch Style"""

class MaintenanceListItem(BoxLayout):
    """Touchable Machine item which shows the machine details."""
    maintenance_name = StringProperty()
class MachineAddButton(BoxLayout):
    """Button to add a machine."""
    pass


class MachineScanAddButton(BoxLayout):
    """Button to scan and add a machine."""
    pass


class MachineScanScreen(Screen):
    machines = ListProperty()

    def on_machines(self, instance, machines):
        list_view = self.ids.list_view
        list_view.clear_widgets()
        list_view.parent.scroll_y = 1

        list_view.height = (len(self.machines) * sp(50)) + sp(50)
        for machine_values in self.machines:
            machine = MachineListItem()
            machine.machine_name = machine_values.name
            machine.ip = machine_values.ip
            machine.port = str(machine_values.port)
            machine.hose_length = str(machine_values.hose_length)
            machine.torch_style = str(machine_values.torch_style)
            list_view.add_widget(machine)

    def on_leave(self, *args):
        self.machines.clear()
        return super().on_leave(*args)


class MaintenanceScreen(Screen):
    maintenance_link = DictProperty()

    def on_maintenance_link(self, instance: "MaintenanceScreen", maintenance:Dict[str, str]):
        maintenance_link_menu = self.ids.maintenance_link_menu
        maintenance_link_menu.clear_widgets()
        maintenance_link_menu.parent.scroll_y = 1
        for name, link in self.maintenance_link.items():
            button = LinkButton()
            button.text = name
            button.link = link
            maintenance_link_menu.add_widget(button)


class MaintenanceScheduleScreen(Screen):
    current_notifications = DictProperty()
    count = NumericProperty()

    def on_current_notifications(self, instance: "MaintenanceScheduleScreen", schedules: Dict[str,List[str]]):
        list_view = self.ids.list_view
        list_view.clear_widgets()
        list_view.parent.scroll_y = 1
        result = any(self.current_notifications.values())

        if not result:
            hint = IotBaseLabel(text="No maintenace notification available")
            list_view.add_widget(hint)
            return

        lheight = sp(0)
        self.count = 0
        for hrs, notifications in self.current_notifications.items():
            hrs_boxlayout = MaintenanceLayout(text=hrs, orientation="vertical", height=(len(notifications) * sp(60)), size_hint_y=None)
            for notification in notifications:
                self.count+=1
                notify_boxlayout = MaintenanceItem(text=notification, orientation="horizontal")
                left_boxlayout = MaintenanceItem(text="left", orientation="vertical", size_hint_x=0.80)
                right_boxlayout = MaintenanceItem(text="right", orientation="vertical", size_hint_x=0.20)
                left_boxlayout.add_widget(NoMaintainLabel(text=notification))
                menu = MenuCheckBox(text=notification)
                self.ids[notification] = menu
                right_boxlayout.add_widget(menu)
                notify_boxlayout.add_widget(left_boxlayout)
                notify_boxlayout.add_widget(right_boxlayout)
                hrs_boxlayout.add_widget(notify_boxlayout)
            lheight += hrs_boxlayout.height
            list_view.add_widget(hrs_boxlayout)

        list_view.height = lheight

    def get_marked_notifications(self):
        marked_notifications = {}
        for hrs, notifications in self.current_notifications.items():
            for notification in notifications:
                if self.ids[notification].active:
                    if hrs not in marked_notifications:
                        marked_notifications[hrs] = [notification]
                    else:
                        marked_notifications[hrs].append(notification)
        return marked_notifications

    def on_leave(self, *args):
        self.current_notifications.clear()
        return super().on_leave(*args)

class MachinesListScreen(Screen):
    """Screen to display list of machines."""
    machines = ListProperty()
    """Machine List

       Machine type: Dict [Name, IP, Port]
    """
    is_metric = BooleanProperty(False)

    def on_pre_enter(self, *args):
        if not self.machines:
            self.on_machines(self, self.machines)
        return super().on_pre_enter(*args)

    def _get_hose_len(self, hose_len):
        if self.is_metric:
            return hose_len
        else:
            return Configuration.HOSE_LENGTH_MET2IMP[hose_len]

    def _update(self):
        list_view = self.ids.list_view
        list_view.clear_widgets()
        list_view.parent.scroll_y = 1

        list_view.height = (len(self.machines) * sp(50)) + sp(50)
        for machine_values in self.machines:
            machine = MachineListItem()
            machine.machine_name = machine_values["name"]
            machine.ip = machine_values["ip"]
            machine.port = str(machine_values["port"])
            machine.hose_length = self._get_hose_len(machine_values["hose_length"])
            machine.torch_style = str(machine_values["torch_style"])
            list_view.add_widget(machine)

        list_view.add_widget(MachineAddButton())
        list_view.add_widget(Filler())


    def on_machines(self, instance: "MachinesListScreen", machines: List[Dict[str, Any]]):
        """Triggered when machine list changed.

        When machine list is changed, clear the widgets from instance
        and creates MachineListItem from the modified machines list.

        Args:
          instance: screen object
          machines: list of machine dicts

        """
        self._update()

    def on_is_metric(self, *args):
        self._update()

    def on_leave(self, *args):
        self.machines.clear()
        return super().on_leave(*args)


class AccessPointBox(ButtonBehavior, BoxLayout):
    """Touchable access point item which shows the AP summary."""
    ssid = StringProperty("Netgear 2.4G")
    """SSID of the WiFi AP"""
    bssid = StringProperty("24:12:d3:ff:3d")
    """BSSID of the WiFi AP"""
    rssi = NumericProperty(-70)
    """RSSI of the WiFi AP"""
    encrypt_type = StringProperty("WPA2")
    """Encryption type of the WiFi AP"""
    hidden = NumericProperty()
    """Hidden status of the WiFi AP"""
    channel = NumericProperty()
    """Channel number of the WiFi AP"""
    current = NumericProperty()
    """Connection status to the WiFi AP"""
    padding = [20, 0, 0, 0]

# FIXME: We might have to provide a mechanism to refresh the list
# from within the screen. Given the APs are dynamic.
class NodeAPConfigScreen(Screen):
    """Screen to display list of AP"""

    ap_list = ListProperty()
    """List of Access points"""
    scanning = BooleanProperty(False)
    """Scanning status"""

    def on_scanning(self, instance: "NodeAPConfigScreen", scanning: bool):
        self.update()

    def on_ap_list(self, instance: "NodeAPConfigScreen", ap_list: List[Dict[str, Any]]):
        self.update()

    def update(self):
        """Triggered when ap_list or scanning property changes.

        When the property is changed, clears the widgets in AP screen,
        creates AP items from the ap list.
        """
        list_view = self.ids.list_view
        list_view.clear_widgets()
        list_view.parent.scroll_y = 1

        if self.scanning:
            hint = NodeAPConfigHint(text="Scanning networks ...", scanning=True)
            list_view.add_widget(hint)
            return

        if not self.ap_list:
            hint = NodeAPConfigHint(text="No networks available")
            list_view.add_widget(hint)
            return

        list_view.height = len(self.ap_list) * sp(50) + sp(50)

        hint = NodeAPConfigHint(text="Select a network to configure the node.")
        list_view.add_widget(hint)

        for ap in self.ap_list:
            ap_box = AccessPointBox()
            ap_box.ssid = ap["ssid"]
            ap_box.bssid = ap["bssid"]
            ap_box.encrypt_type = ap["encrypt_type"]
            ap_box.hidden = ap["hidden"]
            ap_box.rssi = ap["rssi"]
            ap_box.channel = ap["channel"]
            ap_box.current = ap["current"]
            list_view.add_widget(ap_box)

    def on_leave(self, *args):
        self.ap_list.clear()
        return super().on_leave(*args)


class LimitedCharTextInput(TextInput):
    """TextInput with limited characters"""
    char_limit = NumericProperty(64)
    """Maximum character limit"""
    filter_regex = StringProperty("")
    """Characters to be filtered as specified in regex format"""
    prefix_string = StringProperty("")
    """String that is prefixed to be read only"""

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if self.prefix_string and len(self.text) < (len(self.prefix_string) + 1) and keycode == (8, 'backspace'):
            self.text += self.prefix_string[-1]
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def insert_text(self, substring, from_undo=False):
        if len(self.text) >= self.char_limit:
            substring = ""
        if self.filter_regex and not re.match(self.filter_regex, substring):
            substring = ""
        return super().insert_text(substring, from_undo)



class ErrorsScreen(Screen):
    fault_codes = ListProperty()

    def __init__(self, **kw):
        fault_data = {**FCCM,**FDMC, **FDPC}
        self.fault_codes = [code for code, *_ in fault_data.values()]
        super().__init__(**kw)


class HomeScreen(Screen):
    status = NumericProperty(0)
    machines = ListProperty()
    curr_machine = StringProperty()
    data = DictProperty()
    service_text = StringProperty()
    fault_code = StringProperty()


class ServiceMenu(Screen):
    status = NumericProperty(0)
    machines = ListProperty()
    curr_machine = StringProperty()
    data = DictProperty()
    error_text = StringProperty()
    fault_code = StringProperty()


class ProcessSetupInputScreen(Screen):
    material_list = ListProperty()
    cutting_quality_list = ListProperty()
    gas_list = ListProperty()
    thickness_list = ListProperty()
    amperage_list = ListProperty()
    use_metric = BooleanProperty()

    def __init__(self, **kw):
        self.toggle = False
        self.material = None
        self.id_and_default_text = {"cutting_quality": "Select Cutting Quality",
                                    "thickness": "Select Thickness",
                                    "material": "Select Material",
                                    "gas": "Select Gas",
                                    "amperage": "Select Amperage"}
        self.fetcher = None
        self.filter_input_parmas = {}
        self.init_fetcher()
        super().__init__(**kw)

        self.previous_param = None
        self.previous_rows = None

    def init_fetcher(self):
        self.fetcher = CutchartFetchInputParam(self.use_metric)
        # When user selects a parameter call its filter method.
        self.filter_input_parmas = {"gas": self.fetcher.gas_selected,
                                    "material": self.fetcher.material_selected,
                                    "thickness": self.fetcher.thickness_selected,
                                    "cutting_quality": self.fetcher.cutting_quality_selected,
                                    "amperage": self.fetcher.amperage_selected}
        self.render_input_values()

    def on_use_metric(self, *args):
        self.reset_all_input()
        self.fetcher.is_metric = self.use_metric
        self.init_fetcher()

    def param_selected(self, selected_value: str, selected_param: str):
        """This method will get called when the user select a dropdown.

        Args:
            selected_value (str): Value of the selected parameter
            selected_param (str): Which parameter (say: 'thickness')
        """
        # Prevent default value from calling the filter function
        if selected_value in self.id_and_default_text.values():
            return

        # Check whether previous selected param is selected
        if self.previous_param == selected_param:
            self.fetcher.rows = self.previous_rows
        else:
            self.previous_param = selected_param
            self.previous_rows = self.fetcher.rows

        self.filter_input_parmas[selected_param](selected_value)
        self.render_input_values(selected_param)
        self.check_and_enable_ok_button()

    def render_input_values(self, last_selected_param=None):
        # Don't update last selected param
        if last_selected_param != "cutting_quality":
            self.cutting_quality_list.clear()
            selection_list = self.fetcher.cutting_quality_selection_list
            self.cutting_quality_list.extend(selection_list)
        if last_selected_param != "gas":
            self.gas_list.clear()
            self.gas_list.extend(self.fetcher.gas_selection_list)
        if last_selected_param != "material":
            self.material_list.clear()
            self.material_list.extend(self.fetcher.material_selection_list)
        if last_selected_param != "thickness":
            self.thickness_list.clear()
            self.thickness_list.extend(self.fetcher.thickness_selection_list)
        if last_selected_param != "amperage":
            self.amperage_list.clear()
            self.amperage_list.extend(self.fetcher.amperage_selection_list)

    def check_and_enable_ok_button(self):
        for input_id, default_text in self.id_and_default_text.items():
            if self.ids[input_id].text == default_text:
                self.ids.submit_button.disabled = True
                return
        self.ids.submit_button.disabled = False

    def reset_all_input(self):
        for key, val in self.id_and_default_text.items():
            self.ids[key].text = val
        self.ids.submit_button.disabled = True
        self.previous_param = None
        self.init_fetcher()

    def get_param_list(self):
        obj = CutChartParam()
        param_list = obj.get_cutting_marking_params(
            self.fetcher.rows[0].process_id)
        return param_list


class ProcessBoxBase(BoxLayout):
    ...


class ProcessBox(ProcessBoxBase):
    process_name = StringProperty()
    process_value = StringProperty()

class ProcessSetupTHCScreen(Screen):
    is_cutting = BooleanProperty(True)
    n_values = NumericProperty()
    param_name_and_col_no = {"Process Id": 2,
                             "Speed": 22,
                             "Kerf": 23,
                             "CNC Pierce Delay": 27,
                             "Arc Voltage": 29,
                             "Cut Height": 28,
                             "Elevation Height": 30,
                             "Control Delay": 31,
                             "Ignition Height": 34,
                             "THC Pierce Delay": 35,
                             "CNC Pierce Delay": 27,
                             "Pierce Height": 26}
    param_list = ListProperty()
    param_id_val_pair = ListProperty()
    use_metric = BooleanProperty()

    def on_is_cutting(self, instance:"ProcessSetupTHCScreen",is_cutting:bool):
            self.update()

    def on_param_list(self, instance:"ProcessSetupTHCScreen",is_cutting:bool):
        self.update()

    def update(self):
        if self.is_cutting:
            [cutting, _] = self.param_list
            self.n_values = len(self.param_name_and_col_no)
            self.mount(cutting)
        else:
            [_, marking] = self.param_list
            self.n_values = len(self.param_name_and_col_no)
            self.mount(marking)

    def mount(self, data):
        node = self.ids.output
        node.clear_widgets()
        mm_conversion = 25.4
        for attribute, idx in self.param_name_and_col_no.items():
            element = ProcessBox()
            element.process_name = attribute
            process_value = data[idx-1]
            units_map = {
                            "CNC Pierce Delay": ("sec", "sec"),
                            "THC Pierce Delay": ("sec", "sec"),
                            "Control Delay": ("sec", "sec"),
                            "Speed": ("mm/min", "ipm"),
                            "Arc Voltage": ("volts", "volts"),
                            "Kerf": ("mm", "inch"),
                            "Cut Height": ("mm", "inch"),
                            "Elevation Height": ("mm", "inch"),
                            "Ignition Height": ("mm", "inch"),
                            "Pierce Height": ("mm", "inch"),
                        }

            units = units_map.get(attribute, ("", ""))
            if self.use_metric:
                process_value = round(float(process_value) * mm_conversion, 2) if units[0] != units[1] else process_value
                process_value = f"{process_value} {units[0]}"
            else:
                process_value = f"{process_value} {units[1]}"

            element.process_value = process_value
            node.add_widget(element)

    def get_param_list(self):
        self.param_id_val_pair.clear()
        obj = CutChartParam()
        cutting, marking = self.param_list
        param_pair = obj.get_param_id_val_pair(cutting, marking)
        self.param_id_val_pair.extend(param_pair)

class ProcessSetupConsumablesScreen(Screen):
    n_values = NumericProperty()
    torch_style = StringProperty("21")
    param_name_and_col_no = {"Electrode": 11,
                             "Plasma Gas Distribution": 12,
                             "Tip": 13,
                             "SecGD": 14,
                             "ShieldCap": 15,
                             "Cartridge": 16,
                             "ShieldCup": 17}
    param_list = ListProperty()
    param_id_val_pair = ListProperty()

    def on_torch_style(self, *args):
        if self.param_list:
            [cutting, _] = self.param_list
            self.n_values = len(self.param_name_and_col_no)
            self.mount(cutting)

    def on_param_list(self, *args):
        [cutting, _] = self.param_list
        self.n_values = len(self.param_name_and_col_no)
        self.mount(cutting)

    def mount(self, cutting):
        node = self.ids.output
        node.clear_widgets()
        for attribute, idx in self.param_name_and_col_no.items():
            element = ProcessBox()
            element.process_name = attribute
            process_value = cutting[idx-1]
            if process_value == "None":
                element.process_value = process_value
            else:
                _, value =  process_value.split("-")
                element.process_value =  f"{self.torch_style}-{value}"
            node.add_widget(element)

    def get_param_list(self):
        self.param_id_val_pair.clear()
        obj = CutChartParam()
        cutting, marking = self.param_list
        param_pair = obj.get_param_id_val_pair(cutting, marking)
        self.param_id_val_pair.extend(param_pair)

class TestingApScreen(Screen):
    progress_timeout = 7
    progress = NumericProperty(0)
    display_text = StringProperty()

    def on_enter(self, *args):
        self.pb = self.ids.pb
        self.progress = 1

    def progress_run(self, *args):
        if self.progress:
            self.pb.value = 1
            Clock.unschedule(self.increment_progressbar)
            self.display_text="Testing Password....."
            Clock.schedule_interval(self.increment_progressbar, 0.5)

    def increment_progressbar(self, dt=0):
        self.pb.value += (100 / (self.progress_timeout * 2))
        if self.pb.value >= 100:
            Clock.unschedule(self.increment_progressbar)
            app = App.get_running_app()
            app.send_event("ap_test_password_timeout")

class ProcessSetupLoadingScreen(Screen):
    cutchart_export_timeout = 10
    progress = NumericProperty(0)
    param_data = ListProperty()
    display_text = StringProperty()

    def on_enter(self, *args):
        self.pb = self.ids.pb
        self.progress = 1

    def progress_run(self, *args):
        if self.progress:
            Clock.unschedule(self.increment_progressbar)
            self.pb.value = 1
            self.display_text="Downloading....."
            Clock.schedule_interval(self.increment_progressbar, 0.1)

    def increment_progressbar(self, dt=0):
        self.pb.value += (100 / (self.cutchart_export_timeout * 2.5))
        if self.pb.value >= 100:
            Clock.unschedule(self.increment_progressbar)
            self.display_text="Downloaded"

class CutchartVerifyLoadingScreen(Screen):
    cutchart_export_timeout = 25
    progress = NumericProperty(0)
    display_text = StringProperty()
    obtained = DictProperty()
    process_id = NumericProperty()
    param_id_list = ListProperty()
    param_id_val_dict = DictProperty()
    app = None

    def on_enter(self, *args):
        self.pb = self.ids.pb
        self.progress = 1

    def on_leave(self, *args):
        self.process_id = -1
        return super().on_leave(*args)

    def progress_run(self, *args):
        if self.progress:
            self.pb.value = 1
            Clock.unschedule(self.increment_progressbar)
            self.display_text="Uploading....."
            Clock.schedule_interval(self.increment_progressbar, 0.5)

    def increment_progressbar(self, dt=0):
        self.pb.value += (100 / (self.cutchart_export_timeout * 2))
        if self.pb.value >= 100:
            Clock.unschedule(self.increment_progressbar)
            self.display_text="Uploaded."

    def on_process_id(self, *args):
        self.app = App.get_running_app()
        self.obtained.clear()
        self.param_id_list.clear()

        if self.process_id == -1:
            return

        cutchart = CutChartParam()

        try:
            self.param_id_val_dict = cutchart.get_cutting_marking_param_with_param_id(
            str(self.process_id))
        except CutChartFetcherError as exc:
            # FIXME: Indicate to user fetching cutchart information failed
            pass

        cutting, marking = cutchart.get_param_ids(need_filter=True)
        self.param_id_list = (*cutting, *marking)
        self.app.send_event("get_param_list", self.param_id_list)

    def on_obtained(self, *args):
        if self.obtained:
            self.app.send_event("cutchart_compare_data_received", value=(self.param_id_val_dict, self.obtained))

    def load(self, instance:"CutchartVerifyLoadingScreen"):
        return


class ServiceBtn(ButtonBehavior, BoxLayout):
    ...


class ProcessCompareBox(ProcessBoxBase):
    process_name = StringProperty()
    process_value = StringProperty()
    process_value2 = StringProperty()


class CutchartCompareScreen(Screen):
    obtained = DictProperty()
    n_values = NumericProperty()
    param_id_val_dict = DictProperty()

    param_name_by_col_no = {6400: "AdvGas",
                            6401: "CCMReserved2",
                            6402: "CCMReserved3",
                            6403: "CCMReserved4",
                            6404: "PilotPeak",
                            6405: "PilotBackGround",
                            6406: "InverterAtPilot",
                            6407: "CCMReserved5",
                            6408: "CCMReserved6",
                            6409: "CCMReserved7",
                            6410: "RampType",
                            6411: "RampStart",
                            6412: "RampDelay",
                            6413: "RampLinearTime",
                            6414: "Exponent",
                            6415: "SwitchCutGas",
                            6416: "RampingShortedTorchVoltage",
                            6417: "PierceTime",
                            6418: "CCMReserved9",
                            6419: "CCMReserved10",
                            6420: "CuDemandAmps",
                            6421: "ShortedTorchVoltage",
                            6422: "CCMReserved11",
                            6423: "CCMReserved12",
                            6424: "CCMReserved13",
                            6425: "StopType",
                            6426: "StopTime",
                            6427: "StopLinearTime",
                            6428: "TimeConstant",
                            6429: "StopCurrent",
                            6430: "StopGasMode",
                            10496: "CutGas",
                            10497: "PilotGas",
                            10498: "ShieldGas",
                            10499: "PurgeOnTime",
                            10500: "PurgeOffTime",
                            10501: "NumberOfCycles",
                            10502: "DMCReserved1",
                            10503: "DMCReserved2",
                            10504: "DMCReserved3",
                            14656: "SetCutLowPressure",
                            14657: "CutLowPGain",
                            14658: "CutLowPGainScale",
                            14659: "CutLowIGain",
                            14660: "CutLowIGainScale",
                            14661: "CutLowBias",
                            14662: "CutLowPosSlewRate",
                            14663: "CutLowNegSlewRate",
                            14664: "CutLowTrackingErrorLimit",
                            14665: "CutLowTrackingDelayTime",
                            14666: "CutLowPiercePressure",
                            14667: "CutLowReserved2",
                            14668: "CutLowInletLowPSIG",
                            14669: "CutLowNominalFlowCurrent",
                            14670: "CutLowFlowTooHigh",
                            14671: "CutLowFlowTooLow",
                            14672: "CutLowReserved3",
                            14673: "CutLowReserved4",
                            14674: "CutLowDitherAmplitude",
                            14675: "CutLowReserved5",
                            14676: "CutLowReserved6",
                            14720: "SetCutPilotPressure",
                            14721: "CutPilotPGain",
                            14722: "CutPilotPGainScale",
                            14723: "CutPilotIGain",
                            14724: "CutPilotIGainScale",
                            14725: "CutPilotBias",
                            14726: "CutPilotPosSlewRate",
                            14727: "CutPilotNegSlewRate",
                            14728: "CutPilotTrackErrorLimit",
                            14729: "CutPilotTrackingDelayTime",
                            14730: "CutPilotReserved1",
                            14731: "CutPilotReserved2",
                            14732: "CutPilotInletLowPSIG",
                            14733: "CutPilotNominalFlowCurrent",
                            14734: "CutPilotFlowTooHigh",
                            14735: "CutPilotFlowTooLow",
                            14736: "CutPilotReserved3",
                            14737: "CutPilotReserved4",
                            14738: "CutPilotDitherAmplitude",
                            14739: "CutPilotReserved5",
                            14740: "CutPilotReserved6",
                            14784: "SetCutShieldGasPressure",
                            14785: "CutShieldGasPGain",
                            14786: "CutShieldGasPGainScale",
                            14787: "CutShieldGasIGain",
                            14788: "CutShieldGasIGainScale",
                            14789: "CutShieldGasBias",
                            14790: "CutShieldGasPosSlewRate",
                            14791: "CutShieldGasNegSlewRate",
                            14792: "CutShieldGasTrackingErrorLimit",
                            14793: "CutShieldGasTrackingDelayTime",
                            14794: "CutShieldGasReserved1",
                            14795: "CutShieldGasReserved2",
                            14796: "CutShieldGasInletLowPSIG",
                            14797: "CutShieldGasNominalFlowCurrent",
                            14798: "CutShieldGasFlowTooHigh",
                            14799: "CutShieldGasFlowTooLow",
                            14800: "CutShieldGasReserved3",
                            14801: "CutShieldGasReserved4",
                            14802: "CutShieldGasDitherAmplitude",
                            14803: "CutShieldGasReserved5",
                            14804: "CutShieldGasReserved6",
                            14856: "CutShieldH2OTrackingErrorLimit",
                            14857: "CutShieldH2OTrackingDelayTime",
                            14858: "CutShieldH2OReserved1",
                            14859: "CutShieldH2OReserved2",
                            14860: "CutShieldH20InletLowPSIG",
                            14861: "CutShieldH2OReserved3",
                            14862: "CutShieldH2OReserved4",
                            14863: "CutShieldH2OReserved5",
                            14864: "CutShieldH2OReserved6",
                            14865: "CutShieldH2OReserved7",
                            14866: "CutShieldH2ODitherAmplitude",
                            14867: "CutShieldH2OReserved8",
                            14868: "CutShieldH2OCommandScale", }

    idx_processid = 0
    min_process_id = 10000
    marking_param_id_offset = 0x200

    def __init__(self, **kw):
        super().__init__(**kw)

    def on_enter(self, *args):
        pass

    def on_leave(self, *args):
        self.ids.cutting.clear_widgets()
        self.ids.marking.clear_widgets()
        self.obtained.clear()
        self.param_id_val_dict.clear()
        self.n_values = 0
        return super().on_leave(*args)

    def _update(self):
        """Render the Chunk of cutting or marking data"""
        if not (self.obtained or self.param_id_val_dict):
            return

        for param_id, actual_param_val in self.obtained.items():
            factory_param_value = "-"
            if param_id in self.param_name_by_col_no:
                node = self.ids.cutting
                if self.param_id_val_dict and param_id in self.param_id_val_dict:
                    factory_param_value = self.param_id_val_dict[param_id]
            else:
                param_id -= self.marking_param_id_offset
                node = self.ids.marking
                if self.param_id_val_dict and param_id in self.param_id_val_dict:
                    factory_param_value = self.param_id_val_dict[param_id]

            if param_id in self.param_name_by_col_no:
                element = ProcessCompareBox()
                element.process_name = self.param_name_by_col_no[param_id]
                element.process_value = str(actual_param_val)
                element.process_value2 = str(factory_param_value)
                node.add_widget(element)
                self.n_values += 1

    def on_obtained(self, *args):
        self._update()

    def on_param_id_val_dict(self, *args):
        self._update()

class ErrorInformationScreen(Screen):
    code = StringProperty()
    information = StringProperty()
    remedy = StringProperty()
    document_link = StringProperty()
    video_link = StringProperty()
    fault_data = {}

    def __init__(self, **kw):
        for code, *fdata in (*FCCM.values(), *FDMC.values(), *FDPC.values()):
            self.fault_data[code] = fdata
        super().__init__(**kw)

    def on_code(self, instance, code):
        error_information = self.fault_data[self.code]
        self.information = error_information[0]
        self.remedy = error_information[2]
        self.document_link = f"{error_information[3]}?{error_information[4]}"
        self.video_link = error_information[5]


class ToggleSliderSwitch(ToggleButtonBehavior, Image):
    """Switch for choosing DHCP or static network"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'images/switch-off.png'

    def on_state(self, _, state: str):
        self.source = f'images/switch-{"on" if state == "down" else "off"}.png'


class NumericRangeInput(TextInput):
    """Maximum character limit"""
    enter_press = BooleanProperty(False)
    range = ListProperty([1, 100])

    def insert_text(self, substring, from_undo=False):
        if substring == "\n":
            self.enter_press = not self.enter_press
            return None
        result_text: str = self.text + substring
        min_range, max_range = self.range
        if not (result_text.isdigit() and
                min_range <= int(result_text) and
                max_range >= int(result_text)):
            substring = ""
        return super().insert_text(substring, from_undo)


class NameAndToggle(BoxLayout):
    name = StringProperty()
    param_id = NumericProperty()
    state = BooleanProperty(False)

class NameAndPush(BoxLayout):
    name = StringProperty()
    param_id = NumericProperty()
    state = BooleanProperty(False)


class NameAndTextInputBox(BoxLayout):
    name = StringProperty()
    param_id = NumericProperty()
    default_text = StringProperty()
    range = ListProperty()


class NameAndDropdown(BoxLayout):
    name = StringProperty()
    map = DictProperty()
    values = ListProperty()
    text = StringProperty()
    param_id = NumericProperty()


class ServiceLabel(IotBaseLabel):
    text = StringProperty()
    param_id = NumericProperty()


GAS_MAP = {"Oxygen": "1",
           "H35": "3",
           "Air": "5",
           "Nitrogen": "6",
           "Argon": "9",
           "Auxiliary": "12",
           "H2O": "10"}


class ControlToggleButton(NamedTuple):
    title: str
    param_id: int

    def get_element(self, state):
        return NameAndToggle(name=self.title,
                             param_id=self.param_id,
                             state=state)

class ControlPushButton(NamedTuple):
    title: str
    param_id: int

    def get_element(self, state):
        return NameAndPush(name=self.title,
                             param_id=self.param_id,
                             state=state)

class ControlTextInput(NamedTuple):
    title: str
    param_id: int
    range: Tuple[int]

    def get_element(self, state):
        state = str(state)
        return NameAndTextInputBox(name=self.title,
                                   param_id=self.param_id,
                                   range=self.range, default_text=state)


class ControlDropDownList(NamedTuple):
    title: str
    param_id: int
    values: List[str]

    def get_element(self, state):
        selected_text = ""
        for gas_name, gas_id in GAS_MAP.items():
            if gas_id == str(state):
                selected_text = gas_name
                break

        return NameAndDropdown(name=self.title, values=self.values,
                               param_id=self.param_id, text=selected_text,
                               map=GAS_MAP)


class ServiceFeatureScreen(Screen):
    services = {
        "Main Control": (
            ControlToggleButton(title="Plasma Enable", param_id=7808),
            ControlToggleButton(title="Preflow Enable", param_id=7809),
            ControlPushButton(title="Plasma Power Start", param_id=7810),
            ControlToggleButton(title="Cutting / Marking selection",
                                param_id=7811),
        ),
        "Cutting gas selection": (
            ControlDropDownList(title="Plasma Gas", param_id=11904,
                                values=["Oxygen", "H35", "Air", "Nitrogen", "Auxiliary"]),
            ControlDropDownList(title="Pre Flow Gas", param_id=11905,
                                values=["Oxygen", "Air", "Nitrogen"]),
            ControlDropDownList(title="Shield Fluid", param_id=11906,
                                values=["Oxygen", "Air", "Nitrogen", "H2O"])
        ),
        "Marking gas selection": (
            ControlDropDownList(title="Plasma Gas", param_id=11907,
                                values=["Air", "Nitrogen", "Argon", "Auxiliary"]),
            ControlDropDownList(title="Pre Flow Gas", param_id=11908,
                                values=["Oxygen", "Air", "Nitrogen"]),
            ControlDropDownList(title="Shield Fluid", param_id=11909,
                                values=["Oxygen", "Air", "Nitrogen", "H2O"]),
        ),
        "DMC Solenoid": (
            ControlToggleButton(title="S1(H35 PLASMA)", param_id=11901),
            ControlToggleButton(title="S2(O2 PLASMA)", param_id=11902),
            ControlToggleButton(title="S3 (AIR PLASMA)", param_id=11912),
            ControlToggleButton(title="S4 (N2 PLASMA)", param_id=11913),
            ControlToggleButton(title="S5(AUX PLASMA)", param_id=11914),
            ControlToggleButton(title="S6(O2 SHIELD)", param_id=11915),
            ControlToggleButton(title="S7(AIR SHIELD)", param_id=11916),
            ControlToggleButton(title="S8(N2 SHIELD)", param_id=11917),
            ControlToggleButton(title="S9(H2O SHIELD)", param_id=11918),
            ControlToggleButton(title="S10(O2 PREFLOW)", param_id=11919),
            ControlToggleButton(title="S11(AIR PREFLOW)", param_id=11920),
            ControlToggleButton(title="S12(N2 PREFLOW)", param_id=11921),
            ControlToggleButton(title="S13(ARGON MARKING)", param_id=11922),
            ControlToggleButton(title="S14(AIR MARKING)", param_id=11923),
            ControlToggleButton(title="S15(N2 MARKING)", param_id=11924)
        ),
        "DPC Solenoid": (
            ControlToggleButton(title="S1(PLASMA MARK)",param_id=16000),
            ControlToggleButton(title="S2(PLASMA VENT)",param_id=16001),
            ControlToggleButton(title="S3(PLASMA CUT)",param_id=16002),
        ),
        "DPC Propotional Valves": (
            ControlTextInput(title="V1(SHIELD GAS)",
                             param_id=16003, range=(0, 1450)),
            ControlTextInput(title="V2(SHIELD H2O)",
                             param_id=16004, range=(0, 1450)),
            ControlTextInput(title="V3(PREFLOW)",
                             param_id=16005, range=(0, 1450)),
            ControlTextInput(title="V4(PLASMA LOW)",
                             param_id=16006, range=(0, 1450)),
            ControlTextInput(title="V5(PLASMA HIGH)",
                             param_id=16007, range=(0, 1450)),
        ),

    }
    toggle_mount = BooleanProperty(False)
    param_state = DictProperty()  # Fetched data of param id(key) and its state(value)
    param_ids = ListProperty()
    lock_unlock_service = [("7696", toggle_mount),
                           ("11792", toggle_mount), ("15888", toggle_mount)]
    toggler_disabled = BooleanProperty(True)

    def on_toggle_mount(self, *args):
        if self.toggle_mount:
            self.mount()
        else:
            self.ids.node.clear_widgets()

    def on_enter(self, *args):
        temp = []
        for _, section_list in self.services.items():
            for section_item in section_list:
                temp.append(section_item.param_id)
        self.param_ids.extend(temp)
        return super().on_enter(*args)

    def on_param_state(self, *args):
        if self.toggle_mount:
            self.mount()

    def mount(self):
        if not self.param_state:
            return
        node = self.ids.node
        node.clear_widgets()
        for section_name, section_list in self.services.items():
            section_name_element = ServiceLabel(text=f"[b]{section_name.upper()}[/b]",
                                                halign="left", padding_x=20)
            node.add_widget(section_name_element)
            for section_item in section_list:
                state = self.param_state[section_item.param_id]
                section_item_element = section_item.get_element(state)
                node.add_widget(section_item_element)
