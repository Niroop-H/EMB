"""
Hardware System Architect Agent.
Transforms high-level embedded requirements into an industrial-grade system architecture, power tree, pinout plan, and Bill of Materials (BOM).
"""

from typing import Dict, Any, List
from .base_agent import BaseHardwareAgent

class ArchitectAgent(BaseHardwareAgent):
    def __init__(self):
        super().__init__(
            name="SystemArchitect",
            role_description="Embedded Hardware System Architect and BOM Specialist"
        )
        self.set_system_prompt(
            "You are a Principal Embedded Hardware Architect. Given natural language requirements, "
            "synthesize a complete industrial hardware specification: power tree, IC selections (with MPNs), "
            "pinout mappings, decoupling strategies, and passive component requirements. Return clean JSON."
        )

    def analyze_requirements(self, user_prompt: str) -> Dict[str, Any]:
        """Translates user prompt into a structured system architecture."""
        return self.call_llm(user_prompt)

    def synthesize_heuristic(self, prompt: str) -> Dict[str, Any]:
        """
        Deterministic, production-ready embedded system architecture generator.
        Supports microcontrollers (ESP32-S3, STM32, RP2040), power stages, communication buses, and I/O.
        """
        lower = prompt.lower()
        
        # 1. Determine MCU
        if "stm32" in lower:
            mcu = {
                "reference": "U1",
                "mpn": "STM32F405RGT6",
                "lib_id": "MCU_ST_STM32F4:STM32F405RGTx",
                "footprint": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
                "package": "LQFP-64",
                "supply_voltage": "3.3V"
            }
        elif "rp2040" in lower:
            mcu = {
                "reference": "U1",
                "mpn": "RP2040",
                "lib_id": "MCU_RaspberryPi:RP2040",
                "footprint": "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
                "package": "QFN-56",
                "supply_voltage": "3.3V"
            }
        else:
            # Default to ESP32-S3 (most popular modern embedded IoT controller)
            mcu = {
                "reference": "U1",
                "mpn": "ESP32-S3-WROOM-1-N16R8",
                "lib_id": "RF_Module:ESP32-S3-WROOM-1",
                "footprint": "RF_Module:ESP32-S3-WROOM-1",
                "package": "Module",
                "supply_voltage": "3.3V"
            }

        # 2. Power Architecture
        power_tree = []
        components = [mcu]
        
        if "12v" in lower or "24v" in lower or "wide input" in lower or "buck" in lower:
            # Wide-input synchronous buck regulator (e.g. Texas Instruments TPS54302 or Monolithic MP2307)
            buck = {
                "reference": "U2",
                "mpn": "TPS54302DDCR",
                "lib_id": "Regulator_Switching:TPS54302DDC",
                "footprint": "Package_TO_SOT_SMD:SOT-23-6",
                "role": "Step-down 24V/12V to 3.3V (up to 3A)",
                "supply_voltage": "12-24V In -> 3.3V Out"
            }
            components.append(buck)
            power_tree.append({"source": "VIN (12-24V)", "converter": "TPS54302 Buck", "output": "+3V3", "max_current": "3.0A"})
        else:
            # Standard USB-C 5V to 3.3V LDO
            ldo = {
                "reference": "U2",
                "mpn": "AMS1117-3.3",
                "lib_id": "Regulator_Linear:AMS1117-3.3",
                "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
                "role": "Linear 5V to 3.3V LDO regulator",
                "supply_voltage": "5V In -> 3.3V Out"
            }
            components.append(ldo)
            power_tree.append({"source": "VBUS (5V)", "converter": "AMS1117-3.3 LDO", "output": "+3V3", "max_current": "1.0A"})

        # 3. Communication Transceivers
        nets: List[Dict[str, Any]] = [
            {"net": "GND", "type": "power"},
            {"net": "+3V3", "type": "power"},
            {"net": "VBUS", "type": "power"}
        ]

        if "can" in lower:
            can_tranceiver = {
                "reference": "U3",
                "mpn": "SN65HVD230DR",
                "lib_id": "Interface_CAN_LIN:SN65HVD230",
                "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                "role": "3.3V CAN-Bus Transceiver"
            }
            components.append(can_tranceiver)
            nets.extend([
                {"net": "CAN_TX", "type": "signal", "from": "U1", "to": "U3"},
                {"net": "CAN_RX", "type": "signal", "from": "U1", "to": "U3"},
                {"net": "CAN_H", "type": "diff_pair", "to": "Connector_CAN"},
                {"net": "CAN_L", "type": "diff_pair", "to": "Connector_CAN"}
            ])

        # 4. USB Interface & Protection
        usb_conn = {
            "reference": "J1",
            "mpn": "TYPE-C-31-M-12",
            "lib_id": "Connector:USB_C_Receptacle_USB2.0_16P",
            "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            "role": "USB-C 16-pin connector with CC pull-downs for 5V power and programming"
        }
        components.append(usb_conn)
        nets.extend([
            {"net": "USB_DP", "type": "diff_pair", "from": "J1", "to": "U1"},
            {"net": "USB_DN", "type": "diff_pair", "from": "J1", "to": "U1"}
        ])

        return {
            "project_name": "MAH_Quantum_Embedded_System",
            "mcu": mcu,
            "power_tree": power_tree,
            "components": components,
            "nets": nets,
            "rules": {
                "trace_width_power_mm": 0.5,
                "trace_width_signal_mm": 0.2,
                "diff_pair_impedance_usb": 90,
                "diff_pair_impedance_can": 120,
                "decoupling_rule": "Every IC power pin must have a 100nF ceramic cap within 2mm"
            }
        }
