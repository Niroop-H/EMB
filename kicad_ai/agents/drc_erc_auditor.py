# SPDX-License-Identifier: GPL-3.0-or-later
"""Compatibility adapter for native checks; no AST substitute or compliance claims."""
from pathlib import Path
from ..automation.native import KiCad, NativeError


class DrcErcAuditor:
    def __init__(self):
        self.kicad_cli_bin = None

    def _check(self, kind, source, report_path=None):
        report = Path(report_path or str(Path(source).with_suffix('')) + f'_{kind}_check.json')
        try:
            return KiCad(self.kicad_cli_bin).check(kind, source, report)
        except NativeError as exc:
            return {'success': False, 'executed': False, 'violations': [], 'error': str(exc)}

    def run_drc(self, pcb_path, report_path=None):
        result = self._check('pcb', pcb_path, report_path)
        violations = result['violations']
        unconnected = result.get('unconnected_items', [])
        return dict(result, unconnected_count=len(unconnected), unconnected_items=unconnected,
                    critical_violations_count=len(violations), all_violations_count=len(violations))

    def run_erc(self, sch_path, report_path=None):
        result = self._check('sch', sch_path, report_path)
        return dict(result, violations_count=len(result['violations']),
                    critical_count=len(result['violations']))

    def audit_all_manufacturing_norms(self, sch_path, pcb_path, bom_path=None, cpl_path=None):
        checks = [('ERC', self.run_erc(sch_path)), ('DRC', self.run_drc(pcb_path))]
        norms = [{'id': name, 'name': f'Native KiCad {name}',
                  'verdict': 'PASS' if result['success'] else 'FAIL',
                  'details': result.get('error', f'{len(result["violations"])} findings')}
                 for name, result in checks]
        reason = {'name': 'Fabrication release not evaluated',
                  'cause': 'Use Final verification / FAB in the desktop companion for complete exports and engineering review.',
                  'remediation': 'Run the current project through the fabrication workflow.'}
        return {'is_manufacturing_ready': False, 'norms': norms,
                'passed_norms_count': sum(item['verdict'] == 'PASS' for item in norms),
                'failed_norms_count': sum(item['verdict'] != 'PASS' for item in norms) + 1,
                'total_norms': 3, 'failure_reasons': [reason]}
