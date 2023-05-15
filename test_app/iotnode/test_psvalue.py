import unittest

from .psvalue import ProcessValueFormatter
from .psvalue import ENUM_MAP, GAS


class ProcessValueTestCase(unittest.TestCase):
    def setUp(self):
        self.ps_value = ProcessValueFormatter()

    def test_process_data_no_conv(self):
        pid = ps = pe = pref = po = otm = mms = ecc = 1
        fv = 1.0
        data = {
            "pid": pid,
            "ps": ps,
            "pe": pe,
            "pref": pref,
            "po": po,
            "otm": otm,
            "mms": mms,
            "ecc": ecc,
            "fv": fv,
        }

        self.ps_value.process_data(data)

        for key in data:
            self.assertEqual(self.ps_value.data[key], str(data[key]))

    def test_process_data_enum_conv(self):
        fccm = (4096, 1)
        fdmc = (8192, 2)
        fdpc = (12288, 4)
        lccm = (4096, 2)
        ldmc = (8192, 4)
        ldpc = (12288, 8)
        pg = 5
        sf = 10

        data = {
            "dccm": 0,
            "ddmc": 0,
            "ddpc": 0,
            "ds": 0,
            "pm": 0,
            "fccm": fccm,
            "fdmc": fdmc,
            "fdpc": fdpc,
            "lccm": lccm,
            "ldmc": ldmc,
            "ldpc": ldpc,
            "pg": pg,
            "sf": sf
        }

        self.ps_value.process_data(data)

        for key, val in data.items():
            self.assertEqual(self.ps_value.data[key], ENUM_MAP[key][val])

    def test_process_data_volt_sec_hr(self):
        av = 10
        ptr = 10
        ah = 1
        data = {"av": av, "ptr": ptr, "ah": ah}

        self.ps_value.process_data(data)

        av_str = "{} Volts".format(av)
        self.assertEqual(self.ps_value.data["av"], av_str)
        ptr_str = "{} Sec".format(ptr)
        self.assertEqual(self.ps_value.data["ptr"], ptr_str)
        ah_str = "{} hr".format(ah)
        self.assertEqual(self.ps_value.data["ah"], ah_str)

    def test_process_data_bitmask(self):
        vs = 0b1111111111111101
        dss = 0b1111111111111111
        exp_dss = {
            "pft": "2 Sec",
            "pf": "10 Sec",
            "apf": "Disabled",
            "apt": "0.0 Sec",
            "pt": "85 ms",
            "radc": "Disabled",
            "tr": "Enabled",
            "rcmmc": "Disabled",
        }
        data = {"vs": vs, "dss": dss}

        self.ps_value.process_data(data)

        for key, val in self.ps_value.data["vs"].items():
            if key == "ple":
                self.assertEqual(val, 0)
            else:
                self.assertEqual(val, 1)

        self.assertEqual(self.ps_value.data["dss"], exp_dss)

    def test_process_data_psi_bar(self):
        psi_bar_keys = ("app", "asgp", "cmip", "pip", "sip", "sihp")
        psi = 300
        psi_bar = "{} PSI\n({:.1f} BAR)".format(psi / 10, (psi / 10) * 0.068947)

        data = {key: psi for key in psi_bar_keys}

        self.ps_value.process_data(data)

        for key in psi_bar_keys:
            self.assertEqual(self.ps_value.data[key], psi_bar)

    def test_process_data_gph_lpm(self):
        key = "ashf"
        gph = 300
        gph_lpm = "{} GPH\n({:.1f} LPM)".format(gph / 10, (gph / 10) * 0.0630902)

        data = {key: gph}

        self.ps_value.process_data(data)

        self.assertEqual(self.ps_value.data[key], gph_lpm)

    def test_process_data_inch_meter(self):
        hl = 240
        data = {"hl": hl}
        ft_mtr = "20 ft\n(6 m)"

        self.ps_value.process_data(data)

        self.assertEqual(self.ps_value.data["hl"], ft_mtr)

    def test_process_data_gas_flow(self):
        cur = 50
        pg = 1
        sf = 5
        data = {"cur": cur, "pg": pg, "sf": sf}
        exp_pf = "{} slpm/scfh".format(GAS[(cur, pg, sf)][0])
        exp_sgf = "{} slpm/scfh".format(GAS[(cur, pg, sf)][1])

        self.ps_value.process_data(data)

        self.assertEqual(self.ps_value.data["pf"], exp_pf)
        self.assertEqual(self.ps_value.data["sgf"], exp_sgf)

    def test_process_data_kw_output(self):
        data = {
            "cur": 3,
            "av": 200,
        }

        self.ps_value.process_data(data)
        self.assertEqual(self.ps_value.data["kw"], "0.6 kW")

    def test_process_data_no_curr_voltage(self):
        data = {}
        self.ps_value.process_data(data)
        self.assertEqual(self.ps_value.data["kw"], "-")

    def test_process_data_firmware_version(self):
        fr_ccm = 0
        fr_dmc = 1
        fr_dpc = 2
        data = {
            "fr_maj_ccm": fr_ccm,
            "fr_min_ccm": fr_ccm,
            "fr_dev_ccm": fr_ccm,
            "fr_maj_dmc": fr_dmc,
            "fr_min_dmc": fr_dmc,
            "fr_dev_dmc": fr_dmc,
            "fr_maj_dpc": fr_dpc,
            "fr_min_dpc": fr_dpc,
            "fr_dev_dpc": fr_dpc,
        }
        exp_fr_ccm = "0.0.0"
        exp_fr_dmc = "1.1.1"
        exp_fr_dpc = "2.2.2"

        self.ps_value.process_data(data)

        self.assertEqual(self.ps_value.data["fr_ccm"], exp_fr_ccm)
        self.assertEqual(self.ps_value.data["fr_dmc"], exp_fr_dmc)
        self.assertEqual(self.ps_value.data["fr_dpc"], exp_fr_dpc)

    def test_process_data_firmware_version_key_missed(self):
        fr_ccm = 0
        fr_dmc = 1
        fr_dpc = 2
        data = {
            "fr_dev_ccm": fr_ccm,
            "fr_maj_dmc": fr_dmc,
            "fr_min_dmc": fr_dmc,
            "fr_dev_dmc": fr_dmc,
            "fr_maj_dpc": fr_dpc,
            "fr_min_dpc": fr_dpc,
            "fr_dev_dpc": fr_dpc,
        }
        exp_fr_dmc = "1.1.1"
        exp_fr_dpc = "2.2.2"

        self.ps_value.process_data(data)

        self.assertEqual(self.ps_value.data.get("fr_ccm"), "-")
        self.assertEqual(self.ps_value.data["fr_dmc"], exp_fr_dmc)
        self.assertEqual(self.ps_value.data["fr_dpc"], exp_fr_dpc)

    def test_get_error_code_ccm(self):
        expected = ("101", "CCM 101")
        fccm = (4096, 1)
        data = {
            "fccm": fccm,
        }

        self.ps_value.process_data(data)
        result = self.ps_value.get_fault_code(data)
        self.assertEqual(expected, result)
