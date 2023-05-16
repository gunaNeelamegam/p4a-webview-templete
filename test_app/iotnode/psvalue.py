"""API to format the process values for the UI display."""
from iotnode.faults import FCCM, FDMC, FDPC


GAS = {
    (30, 1, 1): ("15/32", "-"),
    (50, 1, 5): ("6/14", "12/26"),
    (70, 1, 5): ("10/21", "25/52"),
    (100, 1, 5): ("16/35", "27/58"),
    (130, 1, 5): ("17/36", "26/55"),
    (150, 1, 5): ("59/126", "81/171"),
    (200, 1, 5): ("42/89", "133/281"),
    (250, 1, 5): ("36/76", "132/279"),
    (300, 1, 5): ("27/58", "160/340"),
    (400, 1, 5): ("33/70", "203/430"),
    (15, 1, 1): ("8/18", "-"),
    (30, 5, 5): ("40/85", "-"),
    (30, 6, 10): ("28/58", "5/19"),
    (50, 5, 5): ("49/104", "-"),
    (50, 6, 10): ("18/38", "4/15"),
    (70, 5, 5): ("52/110", "-"),
    (70, 6, 10): ("8/17", "5/19"),
    (100, 3, 6): ("24/51", "51/107"),
    (100, 6, 10): ("14/29", "7/26"),
    (130, 3, 6): ("45/90", "26/55"),
    (130, 6, 10): ("20/42", "7.4/28"),
    (150, 3, 6): ("16/33", "37/78"),
    (150, 6, 10): ("16/35", "8/30"),
    (200, 3, 6): ("35/74", "49/103"),
    (200, 6, 10): ("25/53", "5/19"),
    (300, 3, 6): ("44/93", "51/108"),
    (300, 6, 10): ("63/134", "8/30"),
    (400, 3, 6): ("47/100", "173/367"),
    (400, 6, 10): ("72/153", "8/30"),
    (600, 3, 6): ("94/200", "31/65"),
    (600, 6, 10): ("78/165", "7/27"),
    (800, 3, 6): ("101/213", "85-217/18-460"),
    (800, 6, 10): ("98/207", "7/27"),
    (600, 6, 6): ("117/248", "-"),
    (800, 6, 6): ("115/244", "-"),
}

# Predefined Enumerated values
ENUM_MAP = {
    "dccm": {
        0: "Power up",
        1: "Idle",
        2: "Priming",
        3: "Pre-flowing",
        4: "Waiting for CNC start",
        5: "Holding Pilot Ignition",
        6: "Ignition Delay",
        7: "Igniting",
        8: "Piloting",
        9: "Ramping",
        10: "Cutting or Marking",
        11: "Stopping",
        12: "Auto Pilot Delaying",
        13: "Plasma Disabled",
    },
    "ddmc": {0: "Plasma Disabled", 1: "Idle", 2: "Purging", 3: "Active"},
    "ddpc": {
        0: "Plasma Disabled",
        1: "Idle",
        2: "Active",
        3: "Direct Mode",
        4: "Power Up",
    },
    "ds": {
        0: "OK",
        1: "Disabled",
        2: "Fault",
        3: "Busy",
        4: "Device Not Ready",
        5: "Reserved for future use",
    },
    "fccm": FCCM,
    "fdmc": FDMC,
    "fdpc": FDPC,
    "lccm": FCCM,
    "ldmc": FDMC,
    "ldpc": FDPC,
    "pm": {0: "Standalone", 1: "PS1", 2: "PS2"},
    "pg": {1: "Oxygen", 3: "H35", 5: "Air", 6: "Nitrogen", 9: "Argon", 12: "Auxillary"},
    "sf": {1: "Oxygen", 5: "Air", 6: "Nitrogen", 10: "H2O"},
}


class ProcessValueFormatter:
    """Process value formatter for displaying on the UI.

    Attributes:
        data (dict): the formatted process values
    """

    def __init__(self) -> None:
        self._process_value_map = {
            "pid": self._no_conv,
            "otm": self._no_conv,
            "po": self._no_conv,
            "ecc": self._no_conv,
            "ps": self._no_conv,
            "pe": self._no_conv,
            "mms": self._no_conv,
            "pref": self._no_conv,
            "dccm": self._enum_conv,
            "ddmc": self._enum_conv,
            "ddpc": self._enum_conv,
            "ds": self._enum_conv,
            "fccm": self._enum_conv,
            "fdmc": self._enum_conv,
            "fdpc": self._enum_conv,
            "lccm": self._enum_conv,
            "ldmc": self._enum_conv,
            "ldpc": self._enum_conv,
            "av": self._volt_conv,
            "ptr": self._sec_conv,
            "vs": self._valve_bitmask_conv,
            "app": self._psi_to_bar_conv,
            "asgp": self._psi_to_bar_conv,
            "ashf": self._gph_to_lpm_conv,
            "cmip": self._psi_to_bar_conv,
            "pip": self._psi_to_bar_conv,
            "sip": self._psi_to_bar_conv,
            "sihp": self._psi_to_bar_conv,
            "fv": self._no_conv,
            "dss": self._dss_bitmask_conv,
            "pm": self._enum_conv,
            "hl": self._inch_to_meter_conv,
            "ah": self._hr_conv,
            "pf": self._get_gas_flow,
            "sgf": self._get_gas_flow,
            "fr_ccm": self._firmware_revision,
            "fr_dmc": self._firmware_revision,
            "fr_dpc": self._firmware_revision,
            "pg": self._enum_conv,
            "sf": self._enum_conv,
            "kw": self._get_kw_output,
            "cur": self._format_current,
        }
        self.data = self._get_default_data()

    @staticmethod
    def _no_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        return {ps: str(val)}

    @staticmethod
    def _volt_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        res = "{} Volts".format(val)
        return {ps: res}

    @staticmethod
    def _sec_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        res = "{} Sec".format(val)
        return {ps: res}

    @staticmethod
    def _hr_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        res = "{} hr".format(val)
        return {ps: res}

    @staticmethod
    def _enum_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        if isinstance(val, list):
            val = tuple(val)
        res = ENUM_MAP[ps].get(val)
        if res is not None:
            return {ps: res}
        return {}

    @staticmethod
    def _valve_bitmask_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        vs_keys = ("phe", "ple", "pe", "sge", "she", "ve", "cse", "mse")
        vs_data = {}
        for i, key in enumerate(vs_keys):
            vs_data[key] = (val >> i) & 0x01
        return {ps: vs_data}

    @staticmethod
    def _dss_bitmask_conv(ps, data):
        if ps not in data:
            return {}

        val = data[ps]
        dss_data = {}
        pft_map = {0: "8 Sec", 1: "6 Sec", 2: "4 Sec", 3: "2 Sec"}
        pf_map = {0: "0 Sec", 1: "5 Sec", 2: "20 Sec", 3: "10 Sec"}
        apf_map = radc_map = rcmmc_map = {0: "Enabled", 1: "Disabled"}
        tr_map = {0: "Disabled", 1: "Enabled"}
        pt_map = {0: "3 s", 1: "85 ms"}  # long - 3s, short-85ms
        apt_map = {
            0: "2.0 Sec",
            1: "1.5 Sec",
            2: "1.0 Sec",
            3: "0.8 Sec",
            4: "0.4 Sec",
            5: "0.2 Sec",
            6: "0.1 Sec",
            7: "0.0 Sec",
        }

        dss_data["pft"] = pft_map[val & 0b11]  # bit0 & bit1
        dss_data["pf"] = pf_map[(val >> 2) & 0b11]  # bit2 & bit3
        dss_data["apf"] = apf_map[(val >> 8) & 0b1]  # bit8
        dss_data["apt"] = apt_map[(val >> 9) & 0b111]  # bit9-11
        dss_data["pt"] = pt_map[(val >> 12) & 0b1]  # bit12
        dss_data["radc"] = radc_map[(val >> 13) & 0b1]  # bit13
        dss_data["tr"] = tr_map[(val >> 14) & 0b1]  # bit14
        dss_data["rcmmc"] = rcmmc_map[(val >> 15) & 0b1]  # bit15
        return {ps: dss_data}

    @staticmethod
    def _psi_to_bar_conv(ps, data):
        if ps not in data:
            return {}

        psi = data[ps]
        psi_bar_const = 0.068947
        psi /= 10
        res_str = "{} PSI\n({:.1f} BAR)".format(psi, psi * psi_bar_const)
        return {ps: res_str}

    @staticmethod
    def _gph_to_lpm_conv(ps, data):
        if ps not in data:
            return {}

        gph = data[ps]
        gph_lpm_const = 0.0630902
        gph /= 10
        res_str = "{} GPH\n({:.1f} LPM)".format(gph, gph * gph_lpm_const)
        return {ps: res_str}

    @staticmethod
    def _inch_to_meter_conv(ps, data):
        if ps not in data:
            return {}

        inch = data[ps]
        inch_meter_const = 0.0254
        inch_ft_const = 1 / 12
        ft = inch * inch_ft_const
        meter = inch * inch_meter_const
        res_str = "{:.0f} ft\n({:.0f} m)".format(ft, meter)
        return {ps: res_str}

    @staticmethod
    def _get_default_data():
        # fmt: off
        data_keys = (
            "pid", "ps", "pe", "pref", "po", "otm", "av", "app", "dccm",
            "ddmc", "ddpc", "asgp", "ashf", "cmip", "mms", "fv", "ptr",
            "ecc", "hl", "pm", "ds", "pip", "pf", "sip", "sgf", "sihp", "ah",
            "fr_ccm", "fr_dmc", "fr_dpc", "pg", "sf", "kw", "cur"
        )
        # fmt: on
        fault_keys = ("fccm", "lccm", "fdmc", "ldmc", "fdpc", "ldpc")
        vs_keys = ("phe", "ple", "pe", "sge", "she", "ve", "cse", "mse")
        dss_keys = ("pft", "pf", "apf", "apt", "pit", "radc", "tr", "rcmmc")

        def set_defaults(keys, default="-"):
            return {key: default for key in keys}

        vs = set_defaults(vs_keys)
        dss = set_defaults(dss_keys)
        faults = set_defaults(fault_keys, ("-",) * 3)
        data = set_defaults(data_keys)
        data["vs"] = vs
        data["dss"] = dss
        data.update(faults)
        return data

    @staticmethod
    def _firmware_revision(ps, raw_dt):
        res = {}
        fr_map = {
            "fr_ccm": ("fr_maj_ccm", "fr_min_ccm", "fr_dev_ccm"),
            "fr_dmc": ("fr_maj_dmc", "fr_min_dmc", "fr_dev_dmc"),
            "fr_dpc": ("fr_maj_dpc", "fr_min_dpc", "fr_dev_dpc"),
        }
        fr_keys = fr_map[ps]
        if not all(fr_key in raw_dt for fr_key in fr_keys):
            return res

        fr = "{}.{}.{}".format(
            raw_dt[fr_keys[0]], raw_dt[fr_keys[1]], raw_dt[fr_keys[2]]
        )
        res[ps] = fr

        return res

    @staticmethod
    def _get_gas_flow(ps, raw_dt):
        flow_map_keys = {"cur", "pg", "sf"}
        flow_ord = {"pf": 0, "sgf": 1}
        res = {}
        if not all(fm_key in raw_dt for fm_key in flow_map_keys):
            return res

        cur = raw_dt["cur"]
        pg = raw_dt["pg"]
        sf = raw_dt["sf"]
        try:
            flow_value = GAS[(cur, pg, sf)]
        except KeyError:
            err_msg = "No mapping available for gas flow values: %s"
            print(err_msg)
            return res

        res[ps] = "{} slpm/scfh".format(flow_value[flow_ord[ps]])
        return res

    @staticmethod
    def _get_kw_output(ps, raw_dt):
        try:
            kw = (raw_dt["cur"] * raw_dt["av"]) / 1000
            return {"kw": "{:.3} kW".format(kw)}
        except KeyError:
            return {}

    @staticmethod
    def _format_current(ps, raw_dt):
        try:
            return {"cur": "{} A".format(raw_dt["cur"])}
        except KeyError:
            return {}

    def process_data(self, data: dict, timestamp: float = None) -> None:
        """Formats the process values and stores in data attribute.

        Args:
           data: process values to be formatted
           timestamp: timestamp of process values, in seconds
        """
        process_dt = self._get_default_data()

        for key in process_dt:
            conv = self._process_value_map[key](key, data)
            process_dt.update(conv)

        self.data = process_dt

    def get_fault_code(self, data: dict) -> (str, str):
        """Return CCM fault code"""
        fault_key = "fccm"
        fault = self.data.get(fault_key, "-")[0]
        code = fault.replace("CCM ", "")

        if fault != "-":
            return (code, fault)

        return ("", "")
