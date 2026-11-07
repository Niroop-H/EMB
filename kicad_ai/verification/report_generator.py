# SPDX-License-Identifier: GPL-3.0-or-later
"""Retired certificate API. Only the native fabrication workflow may issue a release."""
class VerificationReportGenerator:
    def generate_report(self, architecture, norm_audit, sch_path, pcb_path, output_dir):
        raise RuntimeError(
            'Legacy industrial certificates are disabled. Use Final verification / FAB '
            'in the desktop companion to obtain a report backed by native checks and review.')
