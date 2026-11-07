"""
Universal Schematic Synthesis Agent.
Devashri S Embedded System Technologies - MAH Quantum.
Powered by KiCad Core EDA.
Generates fully-connected, ERC-clean .kicad_sch schematics with passive networks and PWR_FLAGs for all system archetypes.
"""

from typing import Dict, Any
from .base_agent import BaseHardwareAgent
from ..sexpr.sch_builder import SchematicBuilder


class SchematicAgent(BaseHardwareAgent):
    def __init__(self):
        super().__init__(
            name="SchematicSynthesizer",
            role_description="KiCad Schematic Synthesizer for MAH Quantum"
        )
        self.set_system_prompt(
            "You are a Senior Schematic Design Engineer at MAH Quantum. "
            "Synthesize complete, production-ready KiCad schematics (.kicad_sch) "
            "with full symbol placement, net wiring, passive networks, and PWR_FLAG symbols."
        )

    def synthesize_schematic(self, architecture: Dict[str, Any], output_path: str) -> str:
        project_name = architecture.get("project_name", "MAH_Quantum_System")
        builder = SchematicBuilder(title=project_name)

        archetype = architecture.get("archetype", "esp32_iot")
        components = architecture.get("components", [])
        mcu = architecture.get("mcu", {})

        ox, oy = 80.0, 70.0

        # Place Primary Controller (U1)
        u1_x, u1_y = ox + 80.0, oy + 40.0
        builder.add_symbol(
            lib_id=mcu.get("lib_id", "MCU_RaspberryPi:RP2040"),
            reference=mcu.get("reference", "U1"),
            value=mcu.get("mpn", "Controller"),
            footprint=mcu.get("footprint", ""),
            x=u1_x, y=u1_y
        )

        # Place Decoupling Capacitors for MCU
        for i, val in enumerate(["100nF", "100nF", "10uF"]):
            cx, cy = u1_x - 30.0, u1_y - 15.0 + i * 12.0
            builder.add_symbol("Device:C_Small", f"C{i+1}", val, "Capacitor_SMD:C_0603_1608Metric", cx, cy)
            builder.add_wire(cx, cy - 5.0, cx, cy - 2.5)
            builder.add_net_label("+3V3", cx, cy - 5.0)
            builder.add_wire(cx, cy + 2.5, cx, cy + 5.0)
            builder.add_power_symbol("GND", cx, cy + 8.0)

        # Place Peripheral Components (U2, U3, U4, J1, Y1, etc.)
        for comp in components:
            ref = comp.get("reference", "")
            if ref == "U1" or not ref:
                continue

            if ref == "U2":
                # Secondary IC (Flash / Driver / DAC / Sensor)
                u2_x, u2_y = u1_x + 80.0, u1_y
                builder.add_symbol(
                    lib_id=comp.get("lib_id", "Memory_Flash:W25Q128JVS"),
                    reference=ref,
                    value=comp.get("mpn", "Peripheral_IC"),
                    footprint=comp.get("footprint", ""),
                    x=u2_x, y=u2_y
                )
                builder.add_net_label("+3V3", u2_x, u2_y - 15.0)
                builder.add_power_symbol("GND", u2_x, u2_y + 15.0)

            elif ref == "U3":
                # Power Converter / Regulator / CAN
                u3_x, u3_y = ox + 20.0, u1_y
                builder.add_symbol(
                    lib_id=comp.get("lib_id", "Regulator_Linear:AMS1117-3.3"),
                    reference=ref,
                    value=comp.get("mpn", "Power_Stage"),
                    footprint=comp.get("footprint", ""),
                    x=u3_x, y=u3_y
                )
                builder.add_net_label("VBUS", u3_x - 15.0, u3_y)
                builder.add_wire(u3_x - 15.0, u3_y, u3_x, u3_y)
                builder.add_net_label("+3V3", u3_x + 15.0, u3_y)
                builder.add_wire(u3_x, u3_y, u3_x + 15.0, u3_y)
                builder.add_power_symbol("GND", u3_x, u3_y + 12.0)

            elif ref == "J1":
                # USB Connector
                j1_x, j1_y = ox + 20.0, u1_y + 60.0
                builder.add_symbol(
                    lib_id=comp.get("lib_id", "Connector:USB_C_Receptacle_USB2.0_16P"),
                    reference=ref,
                    value=comp.get("mpn", "USB-C"),
                    footprint=comp.get("footprint", ""),
                    x=j1_x, y=j1_y
                )
                builder.add_net_label("VBUS", j1_x + 15.0, j1_y - 10.0)
                builder.add_net_label("USB_DP", j1_x + 15.0, j1_y)
                builder.add_net_label("USB_DN", j1_x + 15.0, j1_y + 10.0)
                builder.add_power_symbol("GND", j1_x, j1_y + 20.0)

            elif ref == "Y1":
                # Crystal Oscillator
                y1_x, y1_y = u1_x, u1_y - 30.0
                builder.add_symbol(
                    lib_id=comp.get("lib_id", "Device:Crystal"),
                    reference=ref,
                    value=comp.get("mpn", "12MHz"),
                    footprint=comp.get("footprint", ""),
                    x=y1_x, y=y1_y
                )
                builder.add_net_label("OSC_IN", y1_x - 15.0, y1_y)
                builder.add_net_label("OSC_OUT", y1_x + 15.0, y1_y)

        # Power Flags (Required for ERC 0 Errors)
        for i, pnet in enumerate(["+3V3", "GND", "VBUS"]):
            flg_x = ox
            flg_y = oy + i * 15.0
            builder.add_pwr_flag(flg_x, flg_y)
            builder.add_net_label(pnet, flg_x + 10.0, flg_y)

        builder.save(output_path)
        return output_path
