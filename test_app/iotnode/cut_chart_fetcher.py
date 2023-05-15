import os
from .cut_chart import CutChart, InputParams, Error
import re
from typing import NamedTuple, Optional, Union, List

def get_cutchart_path():
    """Returns the absolute path of the cut chart csv file"""
    dir_path = os.path.abspath(os.path.dirname(__file__))
    file_path = os.path.join(dir_path, CutchartFetchInputParam.FILE_NAME)
    return file_path


class CutChartFetcherError(Exception):
    """Raised to indicate a error when executing a query with cut chart"""
    pass

class Thickness(NamedTuple):
    """Represents thickness value in the csv file as it is 
    and canonicalize the data standard (inch).
    """

    value: str
    """thickness value"""

    in_inch: float
    """thickness in inch value for comparison operation"""



class CutchartFetchInputParam:
    """Loads and stores cut chart data in user readable format

    Args:
        use_metric: using metric measurement of system

    Attributes:
        cutting_quality_map: segregated cutting quality values
        material_map: segregated material values
        gas_plasma_map: segregated gas plasma values
        gas_shield_map: segregated gas shield values
        gas_selection_list: combined gas plasma and gas shield values
        cutting_quality_selection_list: segregated cutting quality value
        material_selection_list: segregated material values
        thickness_selection_list: segregated thickness values
        amperage_selection_list: segregated amperage values
        cutchart_obj: perform query values on the cut chart file
        rows: rows of values loaded from the cut chart
        is_metric: apply filter based on the unit of measure selected
        selected_param: target column and value as key value pair to apply filter
    """
    FILE_NAME = "cutchart.csv"

    def __init__(self, use_metric: bool) -> None:
        # User-friendly value of cutchart param
        self.cutting_quality_map = {"B": "Best",
                                    "F": "Fastest",
                                    "M": "Max Pierce",
                                    "E": "Edge Start",
                                    "R": "Robotic/Bevel",
                                    "U": "Under Water",
                                    "V": "Bevel",
                                    "UV": "Under Water Bevel",
                                    "QP": "Quick Pierce",
                                    "QPB": "Quick Pierce Best",
                                    "QPB": "Quick Pierce Fastest",
                                    "QPBU": "Quick Pierce Best Underwater",
                                    "QPE": "Quick Pierce Edge",
                                    "QPFU": "Quick Pierce Fastest Underwater",
                                    "UVE": "Under Water Bevel Edge",
                                    "VE": "Bevel Edge"}
        self.material_map = {"0": "Mild Steel",
                             "2": "Aluminium",
                             "1": "Stainless Steel"}
        self.gas_plasma_map = {"1": "Oxygen",
                               "3": "H35",
                               "5": "Air",
                               "6": "Nitrogen",
                               "9": "Argon",
                               "12": "Auxiliary"}
        self.gas_shield_map = {"1": "Oxygen",
                               "5": "Air",
                               "6": "Nitrogen",
                               "10": "H2O"}

        self.gas_selection_list = []
        self.cutting_quality_selection_list = []
        self.material_selection_list = []
        self.thickness_selection_list = []
        self.amperage_selection_list = []

        self.cutchart_obj = CutChart(get_cutchart_path())
        self.rows = self.cutchart_obj.load_process_list()

        #
        # FIXME: We need to use the metric / imperial column to select between the two.
        # Because there are other units that used in case of imperial, apart from inches, like gauge.
        #
        self.is_metric = use_metric
        self.update_input_params()
        self.selected_param = {}

    def update_input_params(self):
        """
        Stores the input params to its individual parameter and
        converts cutchart format to required (user-friendly) format.
        """

        def is_valid_row(row: InputParams):
            mm_check = ("1" if self.is_metric else "0") in row.is_thickness_inch
            cutting_quality_check = (
                row.cutting_quality in self.cutting_quality_map)
            return cutting_quality_check and mm_check

        filtered_rows = filter(is_valid_row, self.rows)
        inp_params_by_col = zip(*filtered_rows)
        inp_params_by_name = dict(zip(InputParams._fields, inp_params_by_col))

        material_list = set(inp_params_by_name["material"])
        self.material_selection_list = [
            self.material_map[m] for m in material_list]

        thickness_set = inp_params_by_name["thickness"]
        thickness_inch_set = inp_params_by_name["thickness_inch"]
        thickness = set(zip(thickness_set, thickness_inch_set))
        thickness_list = [Thickness(value, float(in_inch)) for value, in_inch in thickness]
        thickness_list.sort(key=lambda item: item.in_inch, reverse=False)
        thickness_selection_list = []
        for thickness in thickness_list:
            if thickness.value not in thickness_selection_list:
                thickness_selection_list.append(thickness.value)
        self.thickness_selection_list = thickness_selection_list


        cutting_quality_list = set(inp_params_by_name["cutting_quality"])
        self.cutting_quality_selection_list.clear()
        # cutting quality selection list order should be same as cutting_quality_map
        for key, val in self.cutting_quality_map.items():
            if key in cutting_quality_list:
                self.cutting_quality_selection_list.append(val)

        plasma_gas_list = inp_params_by_name["plasma_gas"]
        shield_gas_list = inp_params_by_name["shield_gas"]
        gas_pairs = zip(plasma_gas_list, shield_gas_list)
        self.gas_selection_list = set(f"{self.gas_plasma_map[p]} / {self.gas_shield_map[s]}"
                                      for p, s in gas_pairs)

        amp_lst = {*inp_params_by_name["amperage"]}
        self.amperage_selection_list = sorted(amp_lst, key=int)

    def reduce_row(self):
        """Filters the applicable row from the selected parameters"""
        # for the selected param we are reducing the self.rows
        self.rows = self.cutchart_obj.query_with_process_param(
            self.rows, **self.selected_param)
        self.update_input_params()

    def gas_selected(self, text: str):
        """Updates the selected parameter when gas field is selected

        Args:
            text: gas value (ex: {plasma_gas} / {shield_gas})
        """
        [plasma, shield] = text.split(" / ")
        self.selected_param.clear()
        for key, val in self.gas_shield_map.items():
            if shield == val:
                self.selected_param["shield_gas"] = key
                break
        for key, val in self.gas_plasma_map.items():
            if plasma == val:
                self.selected_param["plasma_gas"] = key
                break
        self.reduce_row()

    def thickness_selected(self, text: str):
        """Updates the selected parameter when thickness field is selected

        Args:
            text: thickness value
        """
        self.selected_param = {"thickness": text}
        self.reduce_row()

    def material_selected(self, text: str):
        """Updates the selected parameter when material field is selected

        Args:
            text: material value
        """
        for key, val in self.material_map.items():
            if val == text:
                self.selected_param = {"material": key}
                self.reduce_row()
                return

    def cutting_quality_selected(self, text: str):
        """Updates the selected parameter when cutting quality field is selected

        Args:
            text: cutting quality value
        """
        for key, val in self.cutting_quality_map.items():
            if val == text:
                self.selected_param = {"cutting_quality": key}
                self.reduce_row()
                return

    def amperage_selected(self, text: str):
        """Updates the selected parameter when amperage field is selected

        Args:
            text: amperage value
        """
        self.selected_param = {"amperage": text}
        self.reduce_row()


class CutChartParam:
    """Defines method for fetching Cutting and Marking values

    Attributes:
        cutchart_obj: cut chart querying object
    """
    PARAM_ID_CCM_PROCESS_ID = 0x000B
    PARAM_ID_DMC_PROCESS_ID = 0x0111
    PARAM_ID_DPC_PROCESS_ID = 0x0211
    PARAM_ID_PROCESS_ID = PARAM_ID_CCM_PROCESS_ID
    PARAM_START_COL_NO = 36
    PROCESS_ID_IDX = 1

    def __init__(self) -> None:
        self.cutchart_obj = CutChart(get_cutchart_path())

    def get_cutting_marking_params(self, process_id: str):
        """Performs query with the given process id

        Args:
            process_id: apply filter based on process id value

        Returns:
            Result of the query based on process id

        Raises:
            CutChartFetcherError
        """
        try:
            return self.cutchart_obj.query_with_process_id(process_id)
        except Error as exc:
            raise CutChartFetcherError("Cutchart query failed") from exc

    def get_param_ids(self, need_filter: bool=False) -> List[str]:
        """Get the required parameter ids
        
        Returns:
            Param id list from the cut chart
        """
        return self.cutchart_obj.get_param_id_list(need_filter)

    def get_param_id_val_pair(self, cutting: List[str], marking: List[str]):
        """Groups cutting pairs and marking pairs for corresponding process id

        Args:
            cutting: list of cutting values
            marking: list of marking values

        Returns:
            Cutting pairs, Marking pairs, List of Process id as tuples
        """

        def is_value_empty(pair: str) -> bool:
            return not (pair[1].strip() == "" or pair[1] is None)

        def cast_int(string: str) -> int:
            try:
                return int(string)
            except ValueError:
                return int(float(string))

        cutting_param_id_list, marking_param_id_list = self.get_param_ids()
        process_id_list = [
            (self.PARAM_ID_CCM_PROCESS_ID, int(cutting[self.PROCESS_ID_IDX])),
            (self.PARAM_ID_DMC_PROCESS_ID, int(cutting[self.PROCESS_ID_IDX])),
            (self.PARAM_ID_DPC_PROCESS_ID, int(cutting[self.PROCESS_ID_IDX]))
        ]
        idx = self.PARAM_START_COL_NO-1
        # Pipeline to get Cutting pairs
        cutting_value_list = cutting[idx:]
        cutting_pairs = zip(cutting_param_id_list, cutting_value_list)
        cutting_pairs = filter(is_value_empty, cutting_pairs)
        cutting_pairs = [(k, cast_int(v)) for k, v in cutting_pairs]
        # Pipeline to get marking pairs
        marking_value_list = marking[idx:]
        marking_pairs = zip(marking_param_id_list, marking_value_list)
        marking_pairs = filter(is_value_empty, marking_pairs)
        marking_pairs = [(k, cast_int(v)) for k, v in marking_pairs]
        return (*cutting_pairs, *marking_pairs, *process_id_list)

    def get_cutting_marking_param_with_param_id(self, process_id: str):
        """Maps cutting and marking values pair into tuples

        Returns:
            Cutting and Marking parameter as key value pairs
        """
        e = self.get_param_id_val_pair(*self.get_cutting_marking_params(process_id))
        e = map(lambda a: (int(a[0]), a[1]), e)
        return dict(e)
