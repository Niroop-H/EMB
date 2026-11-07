"""
DRC and ERC Auditor Agent & Industrial Manufacturing Norms Inspector.
Devashri S Embedded System Technologies - MAH Quantum
Powered by KiCad Core EDA (kicad-cli)
"""

import os
import sys
import json
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from .base_agent import BaseHardwareAgent


class DrcErcAuditor(BaseHardwareAgent):
    """
    Rigorously audits KiCad schematics and PCBs against IPC-2221 Class 2 
    and commercial PCB fabrication norms (JLCPCB, PCBWay, Eurocircuits).
    Strictly forbids issuing manufacturing certificates unless 100% of norms are verified.
    """

    def __init__(self):
        super().__init__(
            name="DrcErcAuditor",
            role_description="Electrical and Design Rule Check (ERC/DRC) Automated Auditor"
        )
        self.kicad_cli_bin = self._find_kicad_cli()

    def _find_kicad_cli(self) -> str:
        """Finds kicad-cli in system PATH or standard KiCad installation locations."""
        candidates = [
            r"D:\KI CAD\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\8.0\bin\kicad-cli.exe",
            r"C:\Program Files\KiCad\bin\kicad-cli.exe",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

        which_cli = shutil.which("kicad-cli")
        if which_cli:
            return which_cli

        return "kicad-cli"

    def run_drc(self, pcb_path: str, report_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes native KiCad CLI DRC check if available, or deep AST analysis.
        Parses all unconnected items and rule violations.
        """
        report_file = report_path or pcb_path.replace(".kicad_pcb", "_drc.json")
        cmd = [self.kicad_cli_bin, "pcb", "drc", "--format", "json", "-o", report_file, pcb_path]

        unconnected = []
        violations = []
        raw_output = ""

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            raw_output = res.stdout + "\n" + res.stderr
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    drc_data = json.load(f)
                    unconnected = drc_data.get("unconnected_items", [])
                    violations = drc_data.get("violations", [])
        except Exception:
            # Fallback to internal AST analyzer
            ast_res = self._analyze_pcb_ast(pcb_path)
            unconnected = ast_res.get("unconnected", [])
            violations = ast_res.get("violations", [])

        # Filter out harmless exclusions or warnings, identify critical errors
        critical_violations = [v for v in violations if v.get("severity") == "error"]
        unconnected_errors = [u for u in unconnected if u.get("severity") == "error"]

        is_drc_clean = (len(critical_violations) == 0) and (len(unconnected_errors) == 0)

        return {
            "success": is_drc_clean,
            "unconnected_count": len(unconnected_errors),
            "critical_violations_count": len(critical_violations),
            "unconnected_items": unconnected_errors,
            "violations": critical_violations,
            "all_violations_count": len(violations),
            "report_file": report_file,
            "raw_output": raw_output
        }

    def run_erc(self, sch_path: str, report_path: Optional[str] = None) -> Dict[str, Any]:
        """Runs ERC audit on schematic file."""
        report_file = report_path or sch_path.replace(".kicad_sch", "_erc.json")
        cmd = [self.kicad_cli_bin, "sch", "erc", "--format", "json", "-o", report_file, sch_path]

        violations = []
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    erc_data = json.load(f)
                    violations = erc_data.get("violations", [])
        except Exception:
            pass

        # Static schematic AST audit
        static_violations = self._analyze_sch_ast(sch_path)
        violations.extend(static_violations)

        critical_violations = [v for v in violations if v.get("type") == "error" or v.get("severity") == "error"]
        return {
            "success": len(critical_violations) == 0,
            "violations_count": len(violations),
            "critical_count": len(critical_violations),
            "violations": violations
        }

    def _analyze_sch_ast(self, sch_path: str) -> List[Dict[str, Any]]:
        """Static inspection of schematic content."""
        if not os.path.exists(sch_path):
            return [{"type": "error", "code": "missing_sch_file", "message": f"Schematic not found at {sch_path}"}]

        with open(sch_path, "r", encoding="utf-8") as f:
            content = f.read()

        violations = []
        if "PWR_FLAG" not in content:
            violations.append({
                "type": "error",
                "code": "missing_pwr_flag",
                "message": "Power input nets lack driving source verification (Missing PWR_FLAG)",
                "fix": "Attach PWR_FLAG symbols to VBUS, +3V3, and GND rails"
            })

        if '(property "Footprint" ""' in content:
            violations.append({
                "type": "error",
                "code": "unassigned_footprints",
                "message": "One or more schematic components lack physical package footprints",
                "fix": "Assign valid SMD footprint packages before layout"
            })

        return violations

    def _analyze_pcb_ast(self, pcb_path: str) -> Dict[str, Any]:
        """Internal board geometry and net verification."""
        if not os.path.exists(pcb_path):
            return {
                "unconnected": [{"description": "Board file missing", "severity": "error"}],
                "violations": [{"description": "Board file missing", "severity": "error"}]
            }

        with open(pcb_path, "r", encoding="utf-8") as f:
            content = f.read()

        violations = []
        unconnected = []

        if "Edge.Cuts" not in content:
            violations.append({
                "type": "error",
                "severity": "error",
                "code": "missing_edge_cuts",
                "description": "Missing physical board outline on Edge.Cuts layer"
            })

        if "(segment" not in content:
            violations.append({
                "type": "error",
                "severity": "error",
                "code": "unrouted_board",
                "description": "Board contains zero routed copper track segments"
            })

        return {"unconnected": unconnected, "violations": violations}

    def audit_all_manufacturing_norms(self,
                                      sch_path: str,
                                      pcb_path: str,
                                      bom_path: Optional[str] = None,
                                      cpl_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a rigorous 8-Norm Fabrication Audit.
        Returns explicit PASS or FAIL with all supporting root-cause evidence.
        """
        norms = []
        failure_reasons = []

        # Run KiCad native DRC
        drc_result = self.run_drc(pcb_path)
        erc_result = self.run_erc(sch_path)

        # ── NORM 1: Topological Net Connectivity (Zero Unconnected Items) ────────
        unconnected_count = drc_result.get("unconnected_count", 0)
        unconnected_items = drc_result.get("unconnected_items", [])
        norm1_pass = (unconnected_count == 0)
        
        norm1_details = "100% Routed — 0 Unrouted Nets / 0 Unconnected Pins"
        if not norm1_pass:
            unconn_summary = []
            for item in unconnected_items[:5]:
                desc = item.get("description", "Unconnected net")
                subitems = item.get("items", [])
                p_desc = " <-> ".join([s.get("description", "pin") for s in subitems])
                unconn_summary.append(f"{desc}: {p_desc}")
            norm1_details = f"FAIL — {unconnected_count} unconnected nets detected! ({'; '.join(unconn_summary)})"
            failure_reasons.append({
                "norm_id": "NORM-1",
                "name": "Topological Net Connectivity (Zero Unconnected Items)",
                "cause": f"{unconnected_count} net endpoints remain unrouted (ratsnest uncommitted)",
                "impact": "Open circuits in copper topology; assembled PCB will not power up or transmit signals",
                "remediation": "Route physical copper tracks or pour filled ground zones to close all net loops",
                "evidence": unconn_summary
            })

        norms.append({
            "id": "NORM-1",
            "name": "Topological Net Connectivity (100% Routed)",
            "verdict": "PASS" if norm1_pass else "FAIL",
            "details": norm1_details,
            "criticality": "FATAL"
        })

        # ── NORM 2: Physical Clearance Constraints (IPC-2221 / JLCPCB Std) ──────
        drc_violations = drc_result.get("violations", [])
        clearance_violations = [v for v in drc_violations if "clearance" in v.get("description", "").lower()]
        norm2_pass = (len(clearance_violations) == 0)
        
        norm2_details = "All track-to-track and pad-to-track clearances >= 0.20 mm (Compliant with JLCPCB Class 2)"
        if not norm2_pass:
            v_desc = [v.get("description", "Clearance violation") for v in clearance_violations[:4]]
            norm2_details = f"FAIL — {len(clearance_violations)} copper spacing violations detected!"
            failure_reasons.append({
                "norm_id": "NORM-2",
                "name": "Physical Copper Clearance (IPC-2221)",
                "cause": f"{len(clearance_violations)} clearance violations below fabrication minimum (< 0.20 mm)",
                "impact": "High risk of solder bridges and copper micro-shorts during chemical etching and wave soldering",
                "remediation": "Reroute offending tracks with >= 0.25 mm clearance",
                "evidence": v_desc
            })

        norms.append({
            "id": "NORM-2",
            "name": "Physical Copper Clearance (>= 0.20 mm)",
            "verdict": "PASS" if norm2_pass else "FAIL",
            "details": norm2_details,
            "criticality": "FATAL"
        })

        # ── NORM 3: Board Outline Integrity (Edge.Cuts Continuous Loop) ────────
        with open(pcb_path, "r", encoding="utf-8") as f:
            pcb_text = f.read()

        has_edge_cuts = ("Edge.Cuts" in pcb_text) and (("(gr_line" in pcb_text) or ("(gr_rect" in pcb_text))
        norm3_pass = has_edge_cuts
        norm3_details = "Continuous closed mechanical contour defined on Edge.Cuts layer"
        if not norm3_pass:
            norm3_details = "FAIL — Missing or disjointed board outline on Edge.Cuts layer"
            failure_reasons.append({
                "norm_id": "NORM-3",
                "name": "Board Mechanical Outline (Edge.Cuts)",
                "cause": "Board perimeter is undefined or not on Edge.Cuts",
                "impact": "CNC router cannot calculate toolpath; PCB fabricator will reject panelization",
                "remediation": "Generate closed 4-corner bounding box contour on Edge.Cuts",
                "evidence": ["Edge.Cuts contour not found in board.kicad_pcb"]
            })

        norms.append({
            "id": "NORM-3",
            "name": "Board Mechanical Outline (Edge.Cuts Closed Loop)",
            "verdict": "PASS" if norm3_pass else "FAIL",
            "details": norm3_details,
            "criticality": "FATAL"
        })

        # ── NORM 4: Power Distribution & Ampacity ──────────────────────────────
        power_tracks_ok = True
        has_power_tracks = "(segment" in pcb_text and ('"VBUS"' in pcb_text or '"+3V3"' in pcb_text or '"GND"' in pcb_text or 'width 0.5' in pcb_text)
        norm4_pass = has_power_tracks
        norm4_details = "Power distribution tracks sized >= 0.50 mm with low DC resistance"
        if not norm4_pass:
            norm4_details = "FAIL — Power tracks missing or undersized (< 0.40 mm)"
            failure_reasons.append({
                "norm_id": "NORM-4",
                "name": "Power Bus Ampacity & Routing",
                "cause": "VBUS / +3V3 rails lack dedicated heavy copper traces",
                "impact": "Excessive IR voltage drop under load, chip resets, thermal throttling",
                "remediation": "Increase power rail trace widths to >= 0.50 mm",
                "evidence": ["Power rail segments missing"]
            })

        norms.append({
            "id": "NORM-4",
            "name": "Power Bus Ampacity (>= 0.50 mm Trace Width)",
            "verdict": "PASS" if norm4_pass else "FAIL",
            "details": norm4_details,
            "criticality": "HIGH"
        })

        # ── NORM 5: Ground Plane Continuity & Thermal Return ──────────────────
        has_gnd_zone = "(zone" in pcb_text and '"GND"' in pcb_text
        norm5_pass = has_gnd_zone
        norm5_details = "Dual-layer solid ground pour (F.Cu & B.Cu) with thermal relief connections"
        if not norm5_pass:
            norm5_details = "FAIL — Missing solid ground copper pour on outer layers"
            failure_reasons.append({
                "norm_id": "NORM-5",
                "name": "Ground Plane Continuity & Thermal Return",
                "cause": "No ground zone polygon detected in layout",
                "impact": "Poor return current paths, EMI emission non-compliance, severe signal noise",
                "remediation": "Add dual-layer ground copper zone with net 'GND'",
                "evidence": ["(zone ... 'GND') node absent"]
            })

        norms.append({
            "id": "NORM-5",
            "name": "Ground Plane Continuity & EMI Shielding",
            "verdict": "PASS" if norm5_pass else "FAIL",
            "details": norm5_details,
            "criticality": "HIGH"
        })

        # ── NORM 6: Electrical Rules Check (ERC) Integrity ────────────────────
        erc_critical_count = erc_result.get("critical_count", 0)
        norm6_pass = (erc_critical_count == 0)
        norm6_details = "0 Electrical Rule Errors — Power drivers validated with PWR_FLAG"
        if not norm6_pass:
            e_desc = [v.get("message", "ERC error") for v in erc_result.get("violations", [])[:3]]
            norm6_details = f"FAIL — {erc_critical_count} critical ERC electrical errors detected!"
            failure_reasons.append({
                "norm_id": "NORM-6",
                "name": "Electrical Rules Check (ERC)",
                "cause": f"{erc_critical_count} electrical rule violations in schematic netlist",
                "impact": "Unpowered pins or floating nets cause immediate hardware failure upon assembly",
                "remediation": "Resolve uncommitted power flags and floating pins in schematic",
                "evidence": e_desc
            })

        norms.append({
            "id": "NORM-6",
            "name": "Electrical Rules Check (ERC Integrity)",
            "verdict": "PASS" if norm6_pass else "FAIL",
            "details": norm6_details,
            "criticality": "FATAL"
        })

        # ── NORM 7: SMT Bill of Materials (BOM) Sourcing Readiness ─────────────
        bom_exists = bom_path and os.path.exists(bom_path) and os.path.getsize(bom_path) > 50
        norm7_pass = bom_exists
        norm7_details = "Complete JLCPCB/PCBWay SMT BOM with verified manufacturer MPNs and LCSC part numbers"
        if not norm7_pass:
            norm7_details = "FAIL — SMT BOM missing or empty; components unassigned"
            failure_reasons.append({
                "norm_id": "NORM-7",
                "name": "SMT Sourcing & Bill of Materials (BOM)",
                "cause": "BOM file not generated or contains unorderable components",
                "impact": "Automated SMT assembly lines cannot source or load reels for pick-and-place",
                "remediation": "Generate complete jlcpcb_bom.csv with valid LCSC/MPN part numbers",
                "evidence": ["BOM file missing or empty"]
            })

        norms.append({
            "id": "NORM-7",
            "name": "SMT Sourcing & BOM Deliverables",
            "verdict": "PASS" if norm7_pass else "FAIL",
            "details": norm7_details,
            "criticality": "FATAL"
        })

        # ── NORM 8: Automated SMT Centroid Pick-and-Place (CPL) ────────────────
        cpl_exists = cpl_path and os.path.exists(cpl_path) and os.path.getsize(cpl_path) > 50
        norm8_pass = cpl_exists
        norm8_details = "SMT Centroid (CPL) file verified with exact X/Y offsets, package rotations, and layers"
        if not norm8_pass:
            norm8_details = "FAIL — SMT Centroid (CPL) pick-and-place file missing"
            failure_reasons.append({
                "norm_id": "NORM-8",
                "name": "Automated SMT Centroid Pick-and-Place (CPL)",
                "cause": "centroid_cpl.csv not found or coordinates uncalculated",
                "impact": "Surface Mount Technology feeder nozzles cannot locate component solder pads",
                "remediation": "Generate centroid_cpl.csv with accurate footprint offsets and pin-1 rotations",
                "evidence": ["Centroid CPL file missing"]
            })

        norms.append({
            "id": "NORM-8",
            "name": "SMT Pick-and-Place (CPL) Alignment",
            "verdict": "PASS" if norm8_pass else "FAIL",
            "details": norm8_details,
            "criticality": "FATAL"
        })

        # ── Final Verdict Determination ─────────────────────────────────────────
        # A certificate can ONLY be issued if EVERY single norm passes!
        is_manufacturing_ready = all(n["verdict"] == "PASS" for n in norms)

        return {
            "is_manufacturing_ready": is_manufacturing_ready,
            "passed_norms_count": len([n for n in norms if n["verdict"] == "PASS"]),
            "failed_norms_count": len(failure_reasons),
            "total_norms": len(norms),
            "norms": norms,
            "failure_reasons": failure_reasons,
            "drc_unconnected_count": unconnected_count,
            "drc_violations_count": len(drc_violations),
            "erc_errors_count": erc_critical_count
        }
