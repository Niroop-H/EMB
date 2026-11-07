# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded native KiCad operations. No synthetic success or geometry fallback."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


class NativeError(RuntimeError):
    pass


def executable(name):
    override = os.environ.get('KICAD_BIN_DIR')
    suffix = '.exe' if os.name == 'nt' else ''
    if override:
        candidate = Path(override) / (name + suffix)
        if candidate.is_file():
            return str(candidate)
        raise NativeError(f'{candidate} does not exist')
    found = shutil.which(name)
    if found:
        return found
    if os.name == 'nt':
        root = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'KiCad'
        for directory in sorted(root.glob('*/bin'), reverse=True):
            candidate = directory / (name + suffix)
            if candidate.is_file():
                return str(candidate)
    raise NativeError(f'{name} not found. Install KiCad or set KICAD_BIN_DIR to its bin folder.')


class KiCad:
    def __init__(self, cli=None):
        self.cli = cli or executable('kicad-cli')

    def run(self, args):
        try:
            result = subprocess.run([self.cli, *map(str, args)], capture_output=True,
                                    text=True, timeout=180, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise NativeError(f'KiCad operation did not finish: {exc}') from exc
        if result.returncode != 0:
            raise NativeError(f'KiCad exited {result.returncode}: {result.stderr or result.stdout}')
        return result.stdout.strip()

    def check(self, kind, source, report):
        """Fresh report only; all warnings, exclusions and parity problems block release."""
        report = Path(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        # Use a private output path, so an old clean report can never mask a failure.
        with tempfile.TemporaryDirectory(prefix='emb-check-') as temp:
            fresh = Path(temp) / 'check.json'
            args = [kind, 'erc' if kind == 'sch' else 'drc', '--format', 'json',
                    '--severity-all', '-o', str(fresh)]
            if kind == 'pcb':
                args.append('--schematic-parity')
            args.append(str(Path(source).resolve()))
            try:
                self.run(args)
                data = json.loads(fresh.read_text(encoding='utf-8'))
                if not isinstance(data, dict):
                    raise ValueError('report must be an object')
                if kind == 'sch':
                    sheets = data['sheets']
                    if not isinstance(sheets, list) or not sheets:
                        raise ValueError('missing schematic sheets')
                    groups = [sheet['violations'] for sheet in sheets]
                else:
                    groups = [data[key] for key in ('violations', 'unconnected_items', 'schematic_parity')]
                if any(not isinstance(group, list) for group in groups):
                    raise ValueError('invalid violation list')
                violations = [item for group in groups for item in group]
                if any(not isinstance(item, dict) for item in violations):
                    raise ValueError('invalid violation record')
                report.write_text(json.dumps(data, indent=2), encoding='utf-8')
                return {'success': not violations, 'violations': violations,
                        'report_file': str(report), 'executed': True,
                        'ignored_checks': data.get('ignored_checks', []),
                        'unconnected_items': data.get('unconnected_items', [])}
            except (NativeError, OSError, ValueError, KeyError, TypeError) as exc:
                failure = {'success': False, 'executed': False, 'violations': [],
                           'error': str(exc), 'report_file': str(report)}
                report.write_text(json.dumps(failure, indent=2), encoding='utf-8')
                return failure

    def export(self, args, output, directory=False):
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if directory:
            output.mkdir(exist_ok=True)
        self.run([*args[:-1], '-o', str(output) + (os.sep if directory else ''), args[-1]])
        files = list(output.rglob('*')) if directory else [output]
        if not any(p.is_file() and p.stat().st_size > 0 for p in files):
            raise NativeError(f'KiCad produced no output: {output.name}')


def open_editor(project, editor='kicad'):
    if editor not in ('kicad', 'eeschema', 'pcbnew'):
        raise ValueError('Unsupported editor')
    suffix = {'kicad': '.kicad_pro', 'eeschema': '.kicad_sch', 'pcbnew': '.kicad_pcb'}[editor]
    target = Path(project).with_suffix(suffix).resolve()
    if not target.is_file():
        raise NativeError(f'Missing {target.name}')
    subprocess.Popen([executable(editor), str(target)], shell=False)
