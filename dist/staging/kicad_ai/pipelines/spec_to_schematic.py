"""
Spec-to-Schematic Autonomous Pipeline.
Executes the closed loop: Requirements -> Hardware Architecture -> Schematic Synthesis -> Automated ERC Audit.
"""

import os
from typing import Dict, Any
from ..agents.architect_agent import ArchitectAgent
from ..agents.schematic_agent import SchematicAgent
from ..agents.drc_erc_auditor import DrcErcAuditor

class SpecToSchematicPipeline:
    def __init__(self):
        self.architect = ArchitectAgent()
        self.schematic_synth = SchematicAgent()
        self.auditor = DrcErcAuditor()

    def run(self, specification: str, output_sch_path: str) -> Dict[str, Any]:
        """Runs the complete autonomous schematic generation pipeline."""
        print(f"[Pipeline] 1. Analyzing specification: '{specification}'...")
        architecture = self.architect.analyze_requirements(specification)
        
        print(f"[Pipeline] 2. Synthesizing schematic: {output_sch_path}...")
        self.schematic_synth.synthesize_schematic(architecture, output_sch_path)
        
        print("[Pipeline] 3. Running closed-loop ERC verification...")
        audit_result = self.auditor.run_erc(output_sch_path)
        
        return {
            "status": "success" if audit_result.get("success", False) else "audit_warning",
            "architecture": architecture,
            "schematic_path": output_sch_path,
            "erc_audit": audit_result
        }
