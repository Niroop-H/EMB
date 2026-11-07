# SPDX-License-Identifier: GPL-3.0-or-later
"""Compatibility entry point for the native KiCad automation companion."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kicad_ai.automation.desktop import main

if __name__ == '__main__':
    main()
