"""
Test case file for cut chart
"""
import unittest
import os
import tempfile
import csv

from .cut_chart import CutChart
from .cut_chart import InputParams


def make_header_row(data):
    return['h','Rev','','QP3','4','0'] + [data] * 200 + ['EOL']

def make_cutting_row(process_id, marking_id, data):
    return ['C', process_id, marking_id] + [data] * 200 + ['EOL']


def make_marking_row(marking_id, data):
    return ['M', marking_id, ''] + [data] * 200 + ['EOL']


def get_cut_chart_data():
    return [
        make_header_row(''),
        make_cutting_row('10000', '10006', 'A'),
        make_marking_row('10006', 'B'),
        make_cutting_row('10014', '10018', 'C'),
        make_marking_row('10018', 'D'),
    ]


def get_process_param_list():
    return [
        InputParams('10000', '10006', '0', '86 in',
                    '0', '0.375', 'B', '100', '3', '6'),
        InputParams('10018', '10016', '2', '9 in',
                    '0', '0.3', 'M', '14', '1', '2'),
        InputParams('10010', '10009', '0', '3.8 mm',
                    '1', '0.5', 'B', '100', '5', '1'),
        InputParams('10017', '10019', '1', '3/8 in',
                    '0', '0.43', 'B', '100', '4', '1'),
        InputParams('10015', '10006', '0', '10 mm',
                    '1', '0.21', 'M', '100', '3', '2'),
        InputParams('10016', '10026', '1', '7 mm',
                    '1', '0.544', 'B', '100', '1', '5')
    ]


class CutChartTestCase(unittest.TestCase):

    def get_cut_chart_file(self):
        with tempfile.NamedTemporaryFile("+w", delete=False) as temp_fp:
            writer = csv.writer(temp_fp, delimiter=",", quoting=csv.QUOTE_NONE)
            writer.writerows(get_cut_chart_data())

            def remove_tempfile():
                os.unlink(temp_fp.name)

            self.addCleanup(remove_tempfile)
            return temp_fp.name

    def test_query_with_valid_process_list(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        cut_chart.load_process_list()

    def test_query_with_invalid_filepath(self):
        cut_chart = CutChart('iotnode/cuchart.csv')
        with self.assertRaises(FileNotFoundError):
            cut_chart.load_process_list()

    def test_get_cutchart_revision(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        result = cut_chart._get_cutchart_revision()
        expected = "QP3.4.0"
        self.assertEqual(expected, result)

    def test_query_with_material_filter(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        process_list = get_process_param_list()
        param_filter = {'material': '0'}
        expected = [
            InputParams('10000', '10006', '0', '86 in',
                        '0', '0.375', 'B', "100", '3', '6'),
            InputParams('10010', '10009', '0', '3.8 mm',
                        '1', '0.5', 'B', '100', '5', '1'),
            InputParams('10015', '10006', '0', '10 mm',
                        '1', '0.21', 'M', '100', '3', '2')
        ]
        result = cut_chart.query_with_process_param(
            process_list, **param_filter)
        self.assertEqual(expected, result)

    def test_query_with_thickness_filter(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        process_list = get_process_param_list()
        param_filter = {'thickness': '7 mm'}
        expected = [
            InputParams('10016', '10026', '1', '7 mm',
                        '1', '0.544', 'B', '100', '1', '5')
        ]
        result = cut_chart.query_with_process_param(
            process_list, **param_filter)
        self.assertEqual(expected, result)

    def test_query_with_invalid_process_param(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        process_list1 = [
            InputParams('10000', '10006', '0', '86 in',
                        '0', '0.375', 'B', '100', '3', '6'),
            InputParams('10018', '10016', '2', '9 in',
                        '0', '0.3', 'M', '14', '1', '2'),
            InputParams('10010', '10009', '0', '3.8 mm',
                        '1', '0.5', 'B', '100', '5', '1'),
            InputParams('10017', '10019', '1', '3/8 in',
                        '0', '0.43', 'B', '100', '4', '1'),
            InputParams('10015', '10006', '0', '10 mm',
                        '1', '0.21', 'M', '100', '3', '2'),
            InputParams('10016', '10026', '1', '7 mm',
                        '1', '0.544', 'B', '100', '1', '5')
        ]
        data1 = {'materil': '0'}
        with self.assertRaises(ValueError):
            cut_chart.query_with_process_param(process_list1, **data1)

    def test_query_with_cutting_row_value(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        process_id = "10000"
        expected = make_cutting_row('10000', '10006', 'A')
        cutting_row, _ = cut_chart.query_with_process_id(process_id)
        self.assertEqual(expected, cutting_row)

    def test_query_with_marking_row_value(self):
        cc_filename = self.get_cut_chart_file()
        cut_chart = CutChart(cc_filename)
        marking_id = "10014"
        expected = make_marking_row('10018', 'D')
        _, marking_row = cut_chart.query_with_process_id(marking_id)
        self.assertEqual(expected, marking_row)
