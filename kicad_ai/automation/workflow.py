# SPDX-License-Identifier: GPL-3.0-or-later
"""Requirement intake and native project handoff; never guess a hardware topology."""
import hashlib
import json
from pathlib import Path
import shutil
from ..sexpr.sexpr_ast import SExpr

QUESTIONS = {
    'function': 'What must the system do, and what are its acceptance tests?',
    'power': 'What are the input voltage range, peak current and power source?',
    'interfaces': 'Which sensors, actuators, connectors and communication interfaces are required?',
    'controller': 'Which controller and exact part variants are required (or still undecided)?',
    'mechanical': 'What board dimensions, mounting holes and connector positions are required?',
    'fabrication': 'Which fabricator, layer count, stackup and minimum design rules apply?',
    'environment': 'What temperature, electrical protection and isolation requirements apply?',
}
REVIEW_ITEMS = (
    'Requirements and acceptance tests match this design',
    'All pin numbers, voltage levels and footprints checked against exact part datasheets',
    'Power, current, thermal, protection and signal integrity calculations reviewed',
    'Fabricator stackup and design rules configured; ignored checks reviewed',
    'Copper zones refilled and all KiCad files saved',
    'BOM sourcing, assembly variants, placement orientation and mechanical fit reviewed',
)
SOURCE_SUFFIXES = {'.kicad_pro', '.kicad_sch', '.kicad_pcb', '.kicad_dru',
                   '.kicad_sym', '.kicad_mod', '.kicad_wks', '.step', '.stp', '.wrl'}


def missing_questions(answers):
    from .rule_agent import RuleAgent
    return {item['id']: item['question'] for item in RuleAgent().assess(answers)['pending']}


def project_path(value):
    project = Path(value).resolve()
    if project.suffix != '.kicad_pro':
        raise ValueError('Select a .kicad_pro project')
    for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_pcb'):
        if not project.with_suffix(suffix).is_file():
            raise ValueError(f'Missing {project.with_suffix(suffix).name}')
    return project


def source_hashes(project):
    project = project_path(project)
    paths = [p for p in project.parent.rglob('*')
             if '.emb' not in p.relative_to(project.parent).parts
             and (p.suffix.lower() in SOURCE_SUFFIXES or p.name in ('sym-lib-table', 'fp-lib-table'))]
    hashes = {}
    for path in sorted(paths):
        if path.is_symlink():
            raise ValueError('Use local project resources, not symbolic links')
        if path.is_file():
            if path.suffix == '.kicad_sch':
                tree = SExpr.parse(path.read_text(encoding='utf-8'))
                for node in tree:
                    if not isinstance(node, list) or not node or node[0] != 'sheet':
                        continue
                    for field in node:
                        if (isinstance(field, list) and len(field) >= 3 and field[0] == 'property'
                                and str(field[1]).lower() == 'sheetfile'):
                            value = str(field[2]).replace('${KIPRJMOD}', str(project.parent))
                            dependency = (path.parent / value).resolve()
                            if '${' in value or not dependency.is_relative_to(project.parent):
                                raise ValueError('Keep every hierarchical sheet inside the project folder')
                            if not dependency.is_file():
                                raise ValueError(f'Missing hierarchical sheet: {dependency.name}')
            hashes[path.relative_to(project.parent).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def brief_path(project):
    return project.parent / '.emb' / 'requirements.json'


def save_brief(project, answers):
    project = project_path(project)
    if missing_questions(answers):
        raise ValueError('Answer all requirement questions before proceeding')
    path = brief_path(project)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(answers, indent=2), encoding='utf-8')
    return path


def review_digest(project):
    path = brief_path(project)
    brief = json.loads(path.read_text(encoding='utf-8'))
    if missing_questions(brief):
        raise ValueError('Requirements are incomplete')
    content = {'files': source_hashes(project), 'requirements': brief}
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def record_review(project, reviewer, checks):
    project = project_path(project)
    if not reviewer.strip() or set(checks) != set(REVIEW_ITEMS):
        raise ValueError('A named reviewer must confirm every engineering review item')
    data = {'reviewer': reviewer.strip(), 'checks': list(REVIEW_ITEMS), 'digest': review_digest(project)}
    (project.parent / '.emb' / 'review.json').write_text(json.dumps(data, indent=2), encoding='utf-8')


def review_valid(project):
    try:
        review = json.loads((project.parent / '.emb' / 'review.json').read_text(encoding='utf-8'))
        return (bool(review['reviewer'].strip()) and set(review['checks']) == set(REVIEW_ITEMS)
                and review['digest'] == review_digest(project))
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def copy_template(source, destination):
    """Copy the whole native project, preserving hierarchy and local resource packs."""
    source = project_path(source)
    destination = Path(destination).resolve()
    if destination == source.parent or source.parent in destination.parents:
        raise ValueError('Choose a destination outside the template directory')
    if destination.exists():
        raise ValueError('Destination must be a new directory; existing work is never overwritten')
    if any(p.is_symlink() for p in source.parent.rglob('*')):
        raise ValueError('Template must not contain symbolic links')
    shutil.copytree(source.parent, destination,
                    ignore=shutil.ignore_patterns('.emb', '.git', '*-backups', '*.lck', '*.kicad_prl'))
    return destination / source.name
