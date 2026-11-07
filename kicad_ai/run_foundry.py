"""
KiCad AI Autonomous Hardware Foundry - Master CLI & Pipeline Runner.
Runs end-to-end 0-to-100% hardware synthesis from specification to verified schematic, layout, and manufacturing outputs.
"""

import sys
import os
import argparse
import json

# Ensure parent directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from kicad_ai.pipelines.spec_to_schematic import SpecToSchematicPipeline
from kicad_ai.pipelines.schematic_to_board import SchematicToBoardPipeline
from kicad_ai.pipelines.manufacturing_pipeline import ManufacturingPipeline
from kicad_ai.agents.drc_erc_auditor import DrcErcAuditor
from kicad_ai.verification.report_generator import VerificationReportGenerator

def main():
    parser = argparse.ArgumentParser(description="KiCad AI 0-to-100% Autonomous Hardware Foundry")
    parser.add_argument("--prompt", type=str, default="ESP32-S3 board with dual CAN-FD, 12-24V wide input power supply, and USB-C", help="Natural language hardware requirement")
    parser.add_argument("--outdir", type=str, default="build_output", help="Directory for generated KiCad project and manufacturing outputs")
    args = parser.parse_args()

    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    print("=================================================================")
    print("       MAH QUANTUM - Devashri S Embedded System Technologies     ")
    print("         Autonomous Hardware Foundry (Powered by KiCad)          ")
    print("       Proprietary & Confidential. All Rights Reserved.          ")
    print("=================================================================")
    print(f"[*] Input Specification: \"{args.prompt}\"")
    print(f"[*] Target Directory:    {outdir}\n")

    # 1. Spec to Schematic Pipeline
    sch_pipeline = SpecToSchematicPipeline()
    sch_path = os.path.join(outdir, "board.kicad_sch")
    sch_result = sch_pipeline.run(args.prompt, sch_path)
    print(f"  [+] Schematic generated: {sch_path}")
    print(f"  [+] ERC Audit Status:    {sch_result['status']}")

    architecture = sch_result["architecture"]

    # 2. Schematic to Board Layout Pipeline
    board_pipeline = SchematicToBoardPipeline()
    pcb_path = os.path.join(outdir, "board.kicad_pcb")
    board_pipeline.run(architecture, pcb_path, board_width_mm=70.0, board_height_mm=45.0)
    print(f"  [+] PCB Layout generated: {pcb_path}")

    # 3. PCB DRC Verification
    auditor = DrcErcAuditor()
    drc_result = auditor.run_drc(pcb_path)
    print(f"  [+] DRC Audit Status:    {'Pass' if drc_result.get('success') else 'Violations Detected'}")

    # 4. Manufacturing Tapeout Release
    mfg = ManufacturingPipeline()
    bom_path = os.path.join(outdir, "jlcpcb_bom.csv")
    mfg.generate_jlcpcb_bom(architecture, bom_path)
    print(f"  [+] SMT BOM generated:   {bom_path}")

    cpl_path = os.path.join(outdir, "centroid_cpl.csv")
    placements = [
        {"designator": "U1", "val": architecture["mcu"]["mpn"], "package": architecture["mcu"].get("package", "SMD"), "x": 145.0, "y": 122.5, "rotation": 0.0, "layer": "Top"},
        {"designator": "U2", "val": "AMS1117-3.3", "package": "SOT-223", "x": 120.0, "y": 122.5, "rotation": 0.0, "layer": "Top"},
        {"designator": "J1", "val": "USB-C", "package": "TYPE-C-16P", "x": 105.0, "y": 122.5, "rotation": 90.0, "layer": "Top"},
        {"designator": "C1", "val": "100nF", "package": "0603", "x": 138.0, "y": 117.5, "rotation": 0.0, "layer": "Top"}
    ]
    mfg.generate_cpl(cpl_path, placements)
    print(f"  [+] Centroid CPL file:   {cpl_path}")

    # 5. Generate KiCad Project File (.kicad_pro)
    pro_path = os.path.join(outdir, "board.kicad_pro")
    pro_data = {
        "meta": {
            "version": 1,
            "company": "Devashri S Embedded System Technologies - MAH Quantum",
            "license": "Proprietary & Confidential",
            "engine": "Powered by KiCad Core EDA"
        },
        "project": {"name": "MAH_Quantum_Board"},
        "schematic": {"annotate_start_num": 1},
        "boards": []
    }
    with open(pro_path, "w", encoding="utf-8") as f:
        json.dump(pro_data, f, indent=2)
    print(f"  [+] KiCad Project file:  {pro_path}")

    # 6. Rigorous 8-Norm Manufacturing Audit & Certification Policy
    auditor = DrcErcAuditor()
    norm_audit = auditor.audit_all_manufacturing_norms(
        sch_path=sch_path,
        pcb_path=pcb_path,
        bom_path=bom_path,
        cpl_path=cpl_path
    )

    # 7. Generate Official Verification Report & Certificate
    report_gen = VerificationReportGenerator()
    cert_info = report_gen.generate_report(
        architecture=architecture,
        norm_audit=norm_audit,
        sch_path=sch_path,
        pcb_path=pcb_path,
        output_dir=outdir
    )

    # Print Official Certification Banner
    print(cert_info["console_summary"])

if __name__ == "__main__":
    main()
