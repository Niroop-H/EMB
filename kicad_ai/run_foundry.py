# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify an existing native KiCad project. No fabricated geometry fallback."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kicad_ai.automation.release import verify_fabrication
from kicad_ai.automation.workflow import QUESTIONS, save_brief


def main():
    parser = argparse.ArgumentParser(description='Native KiCad automation and fabrication verification')
    parser.add_argument('--project', type=Path, help='Saved .kicad_pro project')
    parser.add_argument('--questions', action='store_true', help='Show required design questions')
    parser.add_argument('--requirements', type=Path, help='JSON answers keyed by the question identifiers')
    args = parser.parse_args()
    if args.questions:
        print(json.dumps(QUESTIONS, indent=2))
        return 0
    if not args.project:
        parser.error('--project is required; use --questions to prepare requirements')
    try:
        if args.requirements:
            save_brief(args.project, json.loads(args.requirements.read_text(encoding='utf-8')))
        result, report = verify_fabrication(args.project)
        print(result['status'])
        for blocker in result['blockers']:
            print(' - ' + blocker)
        print(f'Report: {report}')
        return 0 if result['manufacturing_ready'] else 2
    except Exception as exc:
        print(f'BLOCKED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
