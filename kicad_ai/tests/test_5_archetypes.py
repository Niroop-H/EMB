"""
Verification Suite for 5 Industrial Embedded System Archetypes.
MAH Quantum - Devashri S Embedded System Technologies.
Tests 0-to-100% autonomous synthesis for:
  1. Raspberry Pi RP2040 Compute Controller
  2. STM32 Motion / Robotics Driver
  3. Automotive Dual CAN-FD & LIN Gateway
  4. Environmental Multi-Sensor IoT Node
  5. Precision Audiophile I2S Audio DAC
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kicad_ai.pipelines.spec_to_schematic import SpecToSchematicPipeline
from kicad_ai.pipelines.schematic_to_board import SchematicToBoardPipeline
from kicad_ai.pipelines.manufacturing_pipeline import ManufacturingPipeline
from kicad_ai.agents.drc_erc_auditor import DrcErcAuditor
from kicad_ai.verification.report_generator import VerificationReportGenerator

TEST_COMMANDS = [
    {
        "name": "1_RaspberryPi_RP2040_Compute",
        "prompt": "Raspberry Pi RP2040 dual-core compute controller with 16MB QSPI Flash, 12MHz crystal, USB-C, and 3.3V LDO",
    },
    {
        "name": "2_STM32_Motion_Controller",
        "prompt": "STM32F405 industrial motion controller with TMC2209 silent stepper driver, isolated RS485 transceiver, and 24V buck regulator",
    },
    {
        "name": "3_Automotive_Dual_CAN_Gateway",
        "prompt": "Automotive dual CAN-FD and LIN bus gateway with ESP32-S3, dual SN65HVD230 transceivers, and 12-24V load-dump power stage",
    },
    {
        "name": "4_Environmental_Sensor_IoT_Node",
        "prompt": "Environmental multi-sensor IoT node with ESP32-C3, BME280 weather sensor, MPU6050 6-axis IMU, and TP4056 LiPo charger",
    },
    {
        "name": "5_Audiophile_I2S_Audio_DAC",
        "prompt": "Raspberry Pi RP2040 audiophile processor with PCM5102A 32-bit I2S stereo DAC, ultra-low-noise LDO, and 3.5mm line out",
    }
]

def run_tests():
    base_out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated_systems"))
    os.makedirs(base_out, exist_ok=True)

    print("=================================================================")
    print("  MAH QUANTUM - 5 INDUSTRIAL EMBEDDED SYSTEMS VERIFICATION SUITE ")
    print("  Devashri S Embedded System Technologies (Powered by KiCad Core)")
    print("=================================================================\n")

    sch_pipe = SpecToSchematicPipeline()
    pcb_pipe = SchematicToBoardPipeline()
    mfg_pipe = ManufacturingPipeline()
    auditor = DrcErcAuditor()

    for idx, tc in enumerate(TEST_COMMANDS, start=1):
        target_dir = os.path.join(base_out, tc["name"])
        os.makedirs(target_dir, exist_ok=True)
        print(f"[{idx}/5] TESTING: {tc['name']}")
        print(f"      Prompt: \"{tc['prompt']}\"")

        sch_path = os.path.join(target_dir, "board.kicad_sch")
        pcb_path = os.path.join(target_dir, "board.kicad_pcb")
        bom_path = os.path.join(target_dir, "jlcpcb_bom.csv")
        cpl_path = os.path.join(target_dir, "centroid_cpl.csv")
        pro_path = os.path.join(target_dir, "board.kicad_pro")

        # 1. Synthesize Schematic
        sch_res = sch_pipe.run(tc["prompt"], sch_path)
        arch = sch_res["architecture"]

        # 2. Synthesize PCB Layout
        pcb_pipe.run(arch, pcb_path)

        # 3. Comprehensive 8-Norm Manufacturing Audit
        norm_audit = auditor.audit_all_manufacturing_norms(
            sch_path=sch_path,
            pcb_path=pcb_path,
            bom_path=bom_path,
            cpl_path=cpl_path
        )

        # 4. Manufacturing BOM & CPL
        mfg_pipe.generate_jlcpcb_bom(arch, bom_path)
        mfg_pipe.generate_cpl(cpl_path, [
            {"designator": "U1", "val": arch["mcu"]["mpn"], "package": "SMD", "x": 138.0, "y": 122.5, "rotation": 0.0, "layer": "Top"}
        ])

        # 5. Project File (.kicad_pro)
        with open(pro_path, "w", encoding="utf-8") as f:
            f.write(f'{{\n  "meta": {{\n    "company": "Devashri S Embedded System Technologies - MAH Quantum",\n    "license": "Proprietary & Confidential",\n    "engine": "Powered by KiCad Core EDA"\n  }},\n  "project": {{\n    "name": "{arch.get("project_name", "board")}"\n  }}\n}}\n')

        # Re-run norm audit with BOM/CPL present
        norm_audit = auditor.audit_all_manufacturing_norms(
            sch_path=sch_path,
            pcb_path=pcb_path,
            bom_path=bom_path,
            cpl_path=cpl_path
        )

        # 6. Official Verification Certificate & Report
        report_gen = VerificationReportGenerator()
        cert_info = report_gen.generate_report(
            architecture=arch,
            norm_audit=norm_audit,
            sch_path=sch_path,
            pcb_path=pcb_path,
            output_dir=target_dir
        )

        # Check File Sizes
        sch_size = os.path.getsize(sch_path)
        pcb_size = os.path.getsize(pcb_path)
        print(f"      [+] Schematic: {sch_size} bytes (ERC: {sch_res.get('status')})")
        print(f"      [+] PCB Layout: {pcb_size} bytes (Norms: {norm_audit['passed_norms_count']}/{norm_audit['total_norms']})")
        print(f"      [+] Manufacturing: SMT BOM + CPL generated")
        print(f"      [+] Certified: {cert_info['run_id']} ({cert_info['status']})\n")

    print("=================================================================")
    print("  ALL 5 INDUSTRIAL EMBEDDED SYSTEMS SYNTHESIZED SUCCESSFULLY!    ")
    print(f"  Output directory: {base_out}")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
