"""Provides API to read and filter rows from the cutchart stored in a CSV
file.
"""

# pylint: disable=import-error
from typing import NamedTuple, List, Tuple
from collections import OrderedDict
import csv


class Error(Exception):
    pass


class MatchParams(NamedTuple):
    """Parameter column name and parmater value, to match for rows in
    the cutchart CSV file.
    """

    param_name: str
    """Parameter CSV column number"""

    value: str
    """Required parameter value"""


class InputParams(NamedTuple):
    """Maps the row of values as tuple for the corresponding field"""

    process_id: str
    marking_process_id: str
    material: str
    thickness: str
    is_thickness_inch: str
    thickness_inch: str
    cutting_quality: str
    amperage: str
    plasma_gas: str
    shield_gas: str


class CutChart:
    """Defines methods to load and query the CSV file

    Args:
        filename: absolute filepath of cutchart csv
    """

    PARAM_COL_IDX = {
        "cutting_quality": 7,
        "thickness": 4,
        "is_thickness_inch": 5,
        "thickness_inch": 6,
        "material": 3,
        "plasma_gas": 69,
        "shield_gas": 71,
        "process_id": 1,
        "marking_process_id": 2,
        "amperage": 55,
    }
    FILTER_COL = 0
    PARAM_ID_COL_NO = 2
    PARAM_START_COL_NO = 36
    MARKING_PARAM_ID_OFFSET = 0x200
    PARAM_ID_SKIP_RANGES = ((14592, 14612),)

    def __init__(self, filename):
        self._filename = filename
        self.params_in_sorted_col_index = OrderedDict(
            sorted(CutChart.PARAM_COL_IDX.items(), key=lambda item: item[1])
        )
        self.cutchart_revision = self._get_cutchart_revision()

    def _get_cutchart_revision(self):
        try:
            with open(self._filename) as csvfile:
                data = csv.reader(csvfile)
                for row in data:
                    if row[0] == "h" and row[1] == "Rev":
                        return "{}.{}.{}".format(row[3], row[4], row[5])
        except OSError as exc:
            print(exc)

    def load_process_list(self) -> List[InputParams]:
        """Loads and filters cutting row values

        Returns:
            Records of cut chart data
        """

        def get_req_col(row):
            input_params = []
            for idx in self.params_in_sorted_col_index.values():
                input_params.append(row[idx])
            return InputParams(*input_params)

        def is_cutting_row(row):
            return row[CutChart.FILTER_COL] == "C"

        with open(self._filename, "r") as file:
            filtered_row = filter(is_cutting_row, csv.reader(file))
            return list(map(get_req_col, filtered_row))

    def query_with_process_param(
        self, process_list: List[InputParams], **kwargs
    ) -> list:
        """Get filtered process list

        Args:
            process_list: List of row column data to apply filter

        Keyword Args:
            column name: Target column name to query
            filter value: Target value to query

        Returns:
            Cutting and Marking parameter values
        """
        match_param_list = []

        for key, val in kwargs.items():
            if key not in self.PARAM_COL_IDX:
                raise ValueError(f"The given {key} not available")
            data = MatchParams(key, val)
            match_param_list.append(data)

        def match(input_params):
            for match_param in match_param_list:
                if input_params._asdict()[match_param.param_name] != match_param.value:
                    return False
            return True

        return list(filter(match, process_list))

    def query_with_process_id(self, process_id: str):
        """Gets cutting and marking parameters based on process id

        Args:
            process_id: target id to apply filter

        Returns:
            Cutting and Marking parameters for given process id
        """

        processid_index = CutChart.PARAM_COL_IDX["process_id"]
        marking_processid_index = CutChart.PARAM_COL_IDX["marking_process_id"]

        def is_process_id_match(row):
            if row[processid_index] == process_id:
                return True
            return False

        with open(self._filename, "r") as file:
            cutting_row = next(filter(is_process_id_match, csv.reader(file)), None)
            if cutting_row is None:
                raise Error("Invalid Process ID")
            process_id = cutting_row[marking_processid_index]

        with open(self._filename, "r") as file:
            marking_row = next(filter(is_process_id_match, csv.reader(file)), None)

        return cutting_row, marking_row

    def get_param_id_list(
        self, need_filter: bool = False
    ) -> Tuple[List[int], List[int]]:
        """Gets Param id and Marking param id values

        Returns:
            Param ids and Marking param ids as couple
        """

        def is_param_id_row(row):
            return row[CutChart.PARAM_ID_COL_NO - 1] == "ParamID"

        def skip_param_id_ranges(param_id_list):
            filtered_param_id = []
            for param_id in param_id_list:
                for skip_start, skip_end in CutChart.PARAM_ID_SKIP_RANGES:
                    if param_id < skip_start or param_id > skip_end:
                        filtered_param_id.append(param_id)

            return filtered_param_id

        with open(self._filename, "r") as file:
            row = next(filter(is_param_id_row, csv.reader(file)), None)
            idx = CutChart.PARAM_START_COL_NO - 1
            param_id_list = row[idx:-1]
            param_id_list = list(map(int, param_id_list))

            if need_filter:
                param_id_list = skip_param_id_ranges(param_id_list)

            def offset_func(a):
                return a + self.MARKING_PARAM_ID_OFFSET

            marking_param_id_list = list(map(offset_func, param_id_list))
            return (param_id_list, marking_param_id_list)
