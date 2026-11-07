# SPDX-License-Identifier: GPL-3.0-or-later
"""Evidence-based fabrication gate and printable connectivity documentation."""
import csv
import hashlib
from html import escape
import json
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .native import KiCad, NativeError
from .workflow import project_path, source_hashes, review_valid, review_digest


def pin_document(netlist, output):
    """Enumerate library pin definitions, including pins absent from connected nets."""
    content = Path(netlist).read_text(encoding='utf-8')
    if '<!DOCTYPE' in content or '<!ENTITY' in content:
        raise ValueError('External entities are not accepted in the exported netlist')
    root = ET.fromstring(content)
    if root.tag != 'export':
        raise ValueError('Not a KiCad XML netlist')
    parts = {(p.get('lib'), p.get('part')): p for p in root.findall('libparts/libpart')}
    nets = {}
    for net in root.findall('nets/net'):
        for node in net.findall('node'):
            key = (node.get('ref'), node.get('pin'))
            if key in nets and nets[key] != net.get('name'):
                raise ValueError(f'Pin {key} has contradictory net assignments')
            nets[key] = net.get('name', '')
    rows, diagrams = [], []
    components = root.findall('components/comp')
    if not components:
        raise ValueError('Empty schematic: no components in netlist')
    for comp in components:
        ref = comp.get('ref', '')
        lib = comp.find('libsource')
        if lib is None:
            raise ValueError(f'Missing library source for {ref}')
        part = parts.get((lib.get('lib'), lib.get('part')))
        if part is None or not part.findall('pins/pin'):
            raise ValueError(f'No library pin definitions for {ref}')
        pins = part.findall('pins/pin')
        # Logical pin diagram, explicitly not a package drawing or physical pin orientation.
        for start in range(0, len(pins), 24):
            page = pins[start:start + 24]
            height = 50 + 24 * len(page)
            svg = [f'<svg viewBox="0 0 800 {height}" role="img" aria-label="{escape(ref)} logical pin diagram">',
                   f'<rect x="20" y="30" width="260" height="{height-40}" fill="#eee" stroke="#222"/>']
            for index, pin in enumerate(page):
                number = pin.get('num', '')
                if not ref or not number:
                    raise ValueError('Missing reference or pin number')
                name, kind = pin.get('name', ''), pin.get('type', '')
                net = nets.get((ref, number), '(not connected in exported netlist)')
                rows.append([ref, comp.findtext('value', ''), number, name, kind, net])
                y = 48 + index * 24
                svg += [f'<text x="30" y="{y}" font-size="13">{escape(number + "  " + name)}</text>',
                        f'<line x1="280" y1="{y-4}" x2="320" y2="{y-4}" stroke="#222"/>',
                        f'<text x="330" y="{y}" font-size="13">{escape(net)}</text>']
            svg.append('</svg>')
            diagrams.append(f'<section><h2>{escape(ref)} — {escape(comp.findtext("value", ""))} '
                            f'(pins {start+1}–{start+len(page)} of {len(pins)})</h2>'
                            + ''.join(svg) + '</section>')
    with (output / 'pins.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['Reference', 'Value', 'Pin', 'Name', 'Electrical type', 'Net'])
        writer.writerows(rows)
    (output / 'pin-diagrams.html').write_text(
        '<!doctype html><html><meta charset="utf-8"><title>Pin connectivity</title>'
        '<style>body{font:14px sans-serif;margin:30px}svg{width:100%;max-width:900px}'
        'section{break-before:page}h2{break-after:avoid}@media print{button{display:none}}</style>'
        '<button onclick="window.print()">Print / Save PDF</button><h1>Pin connectivity diagrams</h1>'
        '<p>Logical connectivity from KiCad library pins and exported netlist. '
        'Not a physical package pinout. Verify package orientation against the exact datasheet. '
        'A missing net does not imply an intentional no-connect.</p>' + ''.join(diagrams) + '</html>',
        encoding='utf-8')
    return len(rows)


def verify_fabrication(project, kicad=None):
    project = project_path(project)
    native = kicad or KiCad()
    run = project.parent / '.emb' / 'runs' / uuid.uuid4().hex
    run.mkdir(parents=True)
    before = source_hashes(project)
    result = {'status': 'BLOCKED', 'manufacturing_ready': False,
              'time_utc': datetime.now(timezone.utc).isoformat(),
              'project': project.name, 'sources': before, 'blockers': [], 'checks': {},
              'scope': 'Native KiCad checks plus named engineering review; not compliance certification.'}
    blockers = result['blockers']
    try:
        result['kicad_version'] = native.run(['version'])
        result['review_digest'] = review_digest(project)
    except (NativeError, OSError, ValueError) as exc:
        blockers.append(str(exc))
    reviewed = review_valid(project)
    if not reviewed:
        blockers.append('Complete the requirements and named engineering review for the current saved files.')
    for kind, suffix in [('sch', '.kicad_sch'), ('pcb', '.kicad_pcb')]:
        check = native.check(kind, project.with_suffix(suffix), run / f'{kind}-check.json')
        result['checks'][kind] = check
        if not check['success']:
            blockers.append(f'{kind.upper()} check blocked: ' + check.get('error',
                            f'{len(check["violations"])} violations (including warnings/exclusions).'))
    sch, pcb = str(project.with_suffix('.kicad_sch')), str(project.with_suffix('.kicad_pcb'))
    documentation = [
        (['sch', 'export', 'pdf', sch], 'schematic.pdf', False),
        (['sch', 'export', 'netlist', '--format', 'kicadxml', sch], 'netlist.xml', False),
        (['pcb', 'export', 'pdf', '--layers', 'F.Fab,B.Fab,Edge.Cuts',
          '--sketch-pads-on-fab-layers', pcb], 'assembly.pdf', False),
    ]
    manufacturing = [
        (['sch', 'export', 'bom', '--exclude-dnp', sch], 'bom.csv', False),
        (['pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
          '--side', 'both', '--exclude-dnp', pcb], 'placements.csv', False),
        (['pcb', 'export', 'gerbers', pcb], 'gerbers', True),
        (['pcb', 'export', 'drill', '--format', 'excellon', pcb], 'drill', True),
    ]
    for args, filename, directory in documentation:
        try:
            native.export(args, run / filename, directory)
        except (NativeError, OSError, ValueError) as exc:
            blockers.append(f'{filename}: {exc}')
    try:
        result['documented_pins'] = pin_document(run / 'netlist.xml', run)
    except (OSError, ValueError, ET.ParseError) as exc:
        blockers.append(f'Pin documentation: {exc}')
    # No fabrication exports unless all preliminary checks and human review are valid.
    if not blockers:
        for args, filename, directory in manufacturing:
            try:
                native.export(args, run / filename, directory)
            except (NativeError, OSError, ValueError) as exc:
                blockers.append(f'{filename}: {exc}')
    if source_hashes(project) != before or (reviewed and not review_valid(project)):
        blockers.append('Project or requirements changed during verification; save and verify again.')
    if not blockers:
        result.update(status='MANUFACTURING_READY', manufacturing_ready=True)
    result['artifacts'] = {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(run.rglob('*')) if p.is_file()}
    (run / 'manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    links = ''.join(f'<li><a href="{escape(name, quote=True)}">{escape(name)}</a></li>'
                    for name in result['artifacts'])
    problems = ''.join(f'<li>{escape(message)}</li>' for message in blockers)
    (run / 'report.html').write_text(
        '<!doctype html><html><meta charset="utf-8"><title>Fabrication verification</title>'
        '<style>body{font:16px sans-serif;max-width:1000px;margin:40px}li{margin:10px 0}'
        '@media print{button{display:none}}</style><button onclick="window.print()">Print / Save PDF</button>'
        f'<h1>{result["status"].replace("_", " ")}</h1><p>{escape(result["project"])}</p>'
        '<p>This result applies only to the recorded source hashes and engineering review. '
        'Any edit requires a new run. ERC/DRC do not prove functional correctness or regulatory compliance.</p>'
        f'<ul>{problems}</ul><h2>Documents and native exports</h2><ul>{links}</ul>'
        '<a href="manifest.json">Verification evidence and SHA-256 hashes</a></html>', encoding='utf-8')
    return result, run / 'report.html'
