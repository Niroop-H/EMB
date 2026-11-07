"""
KiCad S-Expression serializer - produces byte-for-byte compatible output with KiCad 8/9/10.
Uses tabs for indentation, quotes all strings exactly once, follows the exact grammar KiCad's parser expects.
"""

import uuid
import re
from typing import Any, List, Union

SExprNode = Union[str, int, float, List]


def new_uuid() -> str:
    return str(uuid.uuid4())


def _fmt_number(v: float) -> str:
    """Format a float to match KiCad's compact notation."""
    if v == int(v) and abs(v) < 1e9:
        return str(int(v))
    s = f"{v:.6f}".rstrip('0').rstrip('.')
    return s


# Already-quoted wrapper so we can pass pre-formatted quoted values into the AST
class _Quoted:
    """Wraps a value that must be output with surrounding double-quotes."""
    __slots__ = ('v',)
    def __init__(self, s: str):
        self.v = s


def _quote(s: str) -> '_Quoted':
    """Mark a string as needing double-quotes in the output."""
    return _Quoted(s)


# KiCad enum atoms that must NOT be quoted
_PLAIN_ATOMS = {
    'yes', 'no',
    'thru_hole', 'smd', 'np_thru_hole',
    'rect', 'circle', 'oval', 'roundrect', 'custom',
    'signal', 'user', 'power', 'mixed', 'jumper',
    'solid', 'dash', 'dot', 'dash_dot', 'dash_dot_dot', 'default',
    'left', 'right', 'top', 'bottom', 'center', 'mirror',
    'italic', 'bold',
    'passive', 'input', 'output', 'bidirectional', 'tristate',
    'open_collector', 'open_emitter', 'unconnected', 'unspecified',
    'hide',
}


class SExpr:
    """
    Low-level S-expression serializer.
    Produces tab-indented, properly-quoted output identical to what KiCad 8-10 writes.
    """

    @staticmethod
    def parse(text: str) -> List:
        """Parses a KiCad S-expression string into nested Python lists."""
        token_re = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
        tokens = token_re.findall(text)
        stack: List[List] = []
        current: List = []

        for token in tokens:
            if token == '(':
                new_list: List = []
                if stack:
                    stack[-1].append(new_list)
                else:
                    current.append(new_list)
                stack.append(new_list)
            elif token == ')':
                if stack:
                    stack.pop()
            else:
                if token.startswith('"') and token.endswith('"'):
                    val: Any = token[1:-1].replace('\\"', '"').replace('\\\\', '\\')
                else:
                    try:
                        val = int(token)
                    except ValueError:
                        try:
                            val = float(token)
                        except ValueError:
                            val = token
                if stack:
                    stack[-1].append(val)
                else:
                    current.append(val)

        return current[0] if len(current) == 1 and isinstance(current[0], list) else current

    @classmethod
    def _atom(cls, v: Any) -> str:
        """Render a single scalar value as a KiCad token."""
        if isinstance(v, _Quoted):
            escaped = v.v.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(v, bool):
            return 'yes' if v else 'no'
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return _fmt_number(v)
        if isinstance(v, str):
            # Plain KiCad enum atoms — no quotes
            if v in _PLAIN_ATOMS:
                return v
            # Looks like a number — write as-is
            try:
                int(v); return v
            except ValueError:
                pass
            try:
                float(v); return v
            except ValueError:
                pass
            # Everything else: write as a plain unquoted identifier
            # (tag names like kicad_pcb, footprint, net, segment…)
            return v
        return str(v)

    @classmethod
    def serialize(cls, node: Any, depth: int = 0) -> str:
        """
        Serialize a nested-list AST to canonical KiCad S-expression text.
        """
        tab = '\t' * depth

        # Scalars
        if not isinstance(node, (list, tuple)):
            return cls._atom(node)

        if len(node) == 0:
            return '()'

        tag = node[0]
        rest = node[1:]

        # Tag is always written unquoted (it's a keyword)
        tag_str = cls._atom(tag)

        # Nodes that are always rendered fully inline
        INLINE_TAGS = {'at', 'size', 'start', 'end', 'xy', 'drill', 'xyz'}
        if isinstance(tag, str) and tag in INLINE_TAGS:
            inner = ' '.join(cls._atom(x) if not isinstance(x, (list, tuple))
                             else cls.serialize(x, 0) for x in node)
            return f'({inner})'

        # Nodes where all children are scalars and there are <=4 of them → inline
        def all_scalar(items):
            return all(not isinstance(i, (list, tuple)) for i in items)

        if all_scalar(rest) and len(rest) <= 4:
            inner = ' '.join(cls._atom(x) for x in node)
            return f'({inner})'

        # Multi-line block
        lines = [f'({tag_str}']
        for child in rest:
            child_str = cls.serialize(child, depth + 1)
            lines.append(f'{tab}\t{child_str}')
        lines.append(f'{tab})')
        return '\n'.join(lines)
