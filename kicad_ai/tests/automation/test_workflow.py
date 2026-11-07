# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from kicad_ai.automation.native import KiCad
from kicad_ai.automation.workflow import (QUESTIONS, REVIEW_ITEMS, save_brief, record_review,
                                         review_valid, missing_questions, copy_template, source_hashes)
from kicad_ai.automation.release import pin_document, verify_fabrication

NETLIST = '''<export><components><comp ref="U1"><value>MCU</value><libsource lib="MCU" part="X"/></comp></components>
<libparts><libpart lib="MCU" part="X"><pins><pin num="1" name="VCC" type="power_in"/>
<pin num="2" name="GPIO" type="bidirectional"/></pins></libpart></libparts>
<nets><net name="VCC"><node ref="U1" pin="1"/></net></nets></export>'''


class NativeChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.report = Path(self.temp.name) / 'report.json'
        self.native = KiCad('test-kicad')

    def run_report(self, data, kind='sch', code=0):
        def process(cmd, **kwargs):
            Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(data))
            return SimpleNamespace(returncode=code, stdout='', stderr='')
        with patch('subprocess.run', side_effect=process):
            return self.native.check(kind, 'board.kicad_sch', self.report)

    def test_nested_erc_violation_blocks(self):
        result = self.run_report({'sheets': [{'violations': []}, {'violations': [{'severity': 'error'}]}]})
        self.assertFalse(result['success'])
        self.assertEqual(len(result['violations']), 1)

    def test_warnings_and_exclusions_block(self):
        for severity in ('warning', 'exclusion'):
            self.assertFalse(self.run_report({'sheets': [{'violations': [{'severity': severity}]}]})['success'])

    def test_empty_and_malformed_report_block(self):
        for data in ({}, {'sheets': []}, {'sheets': [{'violations': None}]}, []):
            self.assertFalse(self.run_report(data)['success'])

    def test_failed_process_cannot_reuse_old_clean_report(self):
        self.report.write_text('{"sheets":[{"violations":[]}]}')
        with patch('subprocess.run', return_value=SimpleNamespace(returncode=1, stdout='', stderr='broken')):
            self.assertFalse(self.native.check('sch', 'board.kicad_sch', self.report)['success'])
        self.assertFalse(json.loads(self.report.read_text())['success'])

    def test_missing_cli_and_timeout_block(self):
        import subprocess
        for error in (FileNotFoundError('missing'), subprocess.TimeoutExpired('kicad', 180)):
            with patch('subprocess.run', side_effect=error):
                self.assertFalse(self.native.check('pcb', 'board.kicad_pcb', self.report)['success'])

    def test_parity_and_unconnected_items_block(self):
        data = {'violations': [], 'unconnected_items': [], 'schematic_parity': []}
        self.assertTrue(self.run_report(data, 'pcb')['success'])
        for key in data:
            modified = {**data, key: [{'description': 'bad'}]}
            self.assertFalse(self.run_report(modified, 'pcb')['success'])


class FakeKiCad:
    def __init__(self, export_failure=False, mutate=None):
        self.export_failure, self.mutate = export_failure, mutate
        self.exports = []

    def run(self, args):
        return '9.test'

    def check(self, kind, source, report):
        report.write_text('{}')
        return {'success': True, 'violations': []}

    def export(self, args, output, directory=False):
        from kicad_ai.automation.native import NativeError
        self.exports.append(args)
        if self.export_failure and output.name == 'placements.csv':
            raise NativeError('export failed')
        if directory:
            output.mkdir()
            (output / 'native-export').write_text('data')
        else:
            output.write_text(NETLIST if output.suffix == '.xml' else 'native export')
        if self.mutate:
            self.mutate.write_text('modified')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'board.kicad_pro'
        for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_pcb'):
            self.project.with_suffix(suffix).write_text('test project')
        self.answers = {key: 'specific reviewed requirement' for key in QUESTIONS}

    def review(self):
        save_brief(self.project, self.answers)
        record_review(self.project, 'Engineer', REVIEW_ITEMS)

    def test_missing_requirements_and_review(self):
        self.assertEqual(len(missing_questions({})), len(QUESTIONS))
        with self.assertRaises(ValueError):
            save_brief(self.project, {})
        self.assertFalse(review_valid(self.project))
        native = FakeKiCad()
        result, report = verify_fabrication(self.project, native)
        self.assertFalse(result['manufacturing_ready'])
        self.assertTrue(report.exists())
        self.assertFalse(any('gerbers' in args for args in native.exports))

    def test_review_invalidates_after_source_or_requirements_edit(self):
        self.review()
        self.assertTrue(review_valid(self.project))
        self.project.with_suffix('.kicad_pcb').write_text('edited')
        self.assertFalse(review_valid(self.project))
        self.review()
        save_brief(self.project, {**self.answers, 'power': 'new voltage'})
        self.assertFalse(review_valid(self.project))

    def test_all_pins_including_unconnected_documented(self):
        netlist = self.root / 'netlist.xml'
        netlist.write_text(NETLIST)
        self.assertEqual(pin_document(netlist, self.root), 2)
        self.assertIn('not connected', (self.root / 'pins.csv').read_text())

    def test_ready_requires_exports_and_unchanged_sources(self):
        self.review()
        result, report = verify_fabrication(self.project, FakeKiCad())
        self.assertTrue(result['manufacturing_ready'])
        self.assertIn('pins.csv', result['artifacts'])
        failed, _ = verify_fabrication(self.project, FakeKiCad(export_failure=True))
        self.assertFalse(failed['manufacturing_ready'])
        modified, _ = verify_fabrication(self.project, FakeKiCad(mutate=self.project.with_suffix('.kicad_pcb')))
        self.assertFalse(modified['manufacturing_ready'])

    def test_external_hierarchical_sheet_blocks_review(self):
        self.project.with_suffix('.kicad_sch').write_text(
            '(kicad_sch (sheet (property "Sheetfile" "../outside.kicad_sch")))')
        with self.assertRaises(ValueError):
            source_hashes(self.project)

    def test_large_pin_diagrams_are_paginated(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(NETLIST)
        pins = root.find('libparts/libpart/pins')
        pins.clear()
        for number in range(60):
            ET.SubElement(pins, 'pin', num=str(number + 1), name='GPIO', type='input')
        netlist = self.root / 'large.xml'
        netlist.write_text(ET.tostring(root, encoding='unicode'))
        self.assertEqual(pin_document(netlist, self.root), 60)
        self.assertEqual((self.root / 'pin-diagrams.html').read_text().count('<section>'), 3)

    def test_template_never_overwrites_or_copies_into_itself(self):
        with self.assertRaises(ValueError):
            copy_template(self.project, self.root)
        with self.assertRaises(ValueError):
            copy_template(self.project, self.root / 'nested')


if __name__ == '__main__':
    unittest.main()
