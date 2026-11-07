"""
Schematic Synthesis Agent.
Converts system architecture -> complete, ERC-ready .kicad_sch
"""

from typing import Dict, Any
from .base_agent import BaseHardwareAgent
from ..sexpr.sch_builder import SchematicBuilder


class SchematicAgent(BaseHardwareAgent):
    def __init__(self):
        super().__init__(
            name="SchematicSynthesizer",
            role_description="KiCad Schematic Synthesizer"
        )
        self.set_system_prompt(
            "You are an expert KiCad schematic designer. "
            "Lay out symbols cleanly, wire all nets, "
            "add decoupling caps, pull-ups, and PWR_FLAG symbols to pass ERC."
        )

    def synthesize_schematic(self, architecture: Dict[str, Any], output_path: str) -> str:
        builder = SchematicBuilder(title=architecture.get("project_name", "Embedded System"))
        mcu = architecture.get("mcu", {})
        components = architecture.get("components", [])

        # ── Grid origin ───────────────────────────────────────────
        ox, oy = 80.0, 70.0

        # ── U1 MCU ───────────────────────────────────────────────
        u1x, u1y = ox + 100.0, oy + 40.0
        builder.add_symbol(
            lib_id=mcu.get("lib_id", "RF_Module:ESP32-S3-WROOM-1"),
            reference=mcu.get("reference", "U1"),
            value=mcu.get("mpn", "ESP32-S3"),
            footprint=mcu.get("footprint", ""),
            x=u1x, y=u1y
        )

        # MCU decoupling: 100nF x2, 10uF x1
        cap_idx = 1
        for cap_val, cap_fp in [("100nF", "Capacitor_SMD:C_0603_1608Metric"),
                                 ("100nF", "Capacitor_SMD:C_0603_1608Metric"),
                                 ("10uF",  "Capacitor_SMD:C_0805_2012Metric")]:
            cx, cy = u1x - 35.0, u1y - 20.0 + cap_idx * 12.0
            builder.add_symbol("Device:C_Small", f"C{cap_idx}", cap_val, cap_fp, cx, cy)
            builder.add_wire(cx, cy - 6.0, cx, cy - 4.0)
            builder.add_net_label("+3V3", cx, cy - 6.0)
            builder.add_wire(cx, cy + 4.0, cx, cy + 6.0)
            builder.add_power_symbol("GND", cx, cy + 10.0)
            cap_idx += 1

        # EN pull-up resistor
        builder.add_symbol("Device:R_Small", "R1", "10k",
                            "Resistor_SMD:R_0603_1608Metric",
                            u1x - 25.0, u1y - 25.0)
        builder.add_net_label("+3V3", u1x - 25.0, u1y - 31.0)
        builder.add_net_label("ESP_EN", u1x - 25.0, u1y - 20.0)

        res_idx = 2  # R1 used above

        # ── U2 Regulator ─────────────────────────────────────────
        for comp in components:
            ref = comp.get("reference", "")
            if ref in ("U1", ""):
                continue

            if ref == "U2":
                u2x, u2y = ox + 20.0, u1y
                builder.add_symbol(
                    comp.get("lib_id", "Regulator_Linear:AMS1117-3.3"),
                    ref, comp.get("mpn", "AMS1117-3.3"),
                    comp.get("footprint", ""),
                    u2x, u2y
                )
                builder.add_net_label("VBUS", u2x - 15.0, u2y)
                builder.add_wire(u2x - 15.0, u2y, u2x, u2y)
                builder.add_net_label("+3V3", u2x + 15.0, u2y)
                builder.add_wire(u2x, u2y, u2x + 15.0, u2y)
                builder.add_power_symbol("GND", u2x, u2y + 12.0)
                # Output filter cap
                builder.add_symbol("Device:C_Small", f"C{cap_idx}", "10uF",
                                   "Capacitor_SMD:C_0805_2012Metric",
                                   u2x + 25.0, u2y + 5.0)
                builder.add_net_label("+3V3", u2x + 25.0, u2y - 1.0)
                builder.add_power_symbol("GND", u2x + 25.0, u2y + 15.0)
                cap_idx += 1

            elif ref == "J1":
                # USB-C connector
                j1x, j1y = ox + 20.0, u1y + 65.0
                builder.add_symbol(
                    comp.get("lib_id", "Connector:USB_C_Receptacle_USB2.0_16P"),
                    ref, comp.get("mpn", "TYPE-C-31-M-12"),
                    comp.get("footprint", ""),
                    j1x, j1y
                )
                builder.add_net_label("VBUS", j1x + 20.0, j1y - 20.0)
                builder.add_net_label("USB_DP", j1x + 20.0, j1y - 10.0)
                builder.add_net_label("USB_DN", j1x + 20.0, j1y)
                builder.add_power_symbol("GND", j1x, j1y + 25.0)

                # CC1 / CC2 5.1kΩ pull-downs (required by USB-C spec)
                for cc_i in range(2):
                    rcc_x = j1x - 20.0
                    rcc_y = j1y + 30.0 + cc_i * 15.0
                    r_ref = f"R{res_idx}"
                    res_idx += 1
                    builder.add_symbol("Device:R_Small", r_ref, "5.1k",
                                       "Resistor_SMD:R_0603_1608Metric",
                                       rcc_x, rcc_y)
                    builder.add_net_label(f"CC{cc_i+1}", rcc_x, rcc_y - 6.0)
                    builder.add_power_symbol("GND", rcc_x, rcc_y + 10.0)

                # MCU USB net connections
                builder.add_net_label("USB_DP", u1x - 20.0, u1y + 20.0)
                builder.add_net_label("USB_DN", u1x - 20.0, u1y + 30.0)

            elif ref == "U3":
                # CAN Transceiver
                u3x, u3y = u1x + 80.0, u1y
                builder.add_symbol(
                    comp.get("lib_id", "Interface_CAN_LIN:SN65HVD230"),
                    ref, comp.get("mpn", "SN65HVD230DR"),
                    comp.get("footprint", ""),
                    u3x, u3y
                )
                builder.add_net_label("CAN_TX", u3x - 20.0, u3y - 10.0)
                builder.add_net_label("CAN_RX", u3x - 20.0, u3y)
                builder.add_net_label("+3V3", u3x, u3y - 15.0)
                builder.add_power_symbol("GND", u3x, u3y + 15.0)
                builder.add_net_label("CAN_TX", u1x + 20.0, u1y - 10.0)
                builder.add_net_label("CAN_RX", u1x + 20.0, u1y)

                # 120Ω CAN bus termination
                r_term = f"R{res_idx}"
                res_idx += 1
                builder.add_symbol("Device:R_Small", r_term, "120R",
                                   "Resistor_SMD:R_0603_1608Metric",
                                   u3x + 30.0, u3y - 5.0)
                builder.add_net_label("CAN_H", u3x + 30.0, u3y - 11.0)
                builder.add_net_label("CAN_L", u3x + 30.0, u3y + 1.0)
                builder.add_net_label("CAN_H", u3x + 20.0, u3y - 10.0)
                builder.add_net_label("CAN_L", u3x + 20.0, u3y + 5.0)

        # ── PWR_FLAGs (required to suppress ERC "power pin not driven") ──
        for pnet, px, py in [("+3V3", ox, oy), ("GND", ox, oy + 15.0), ("VBUS", ox, oy + 30.0)]:
            builder.add_pwr_flag(px, py)
            builder.add_net_label(pnet, px + 10.0, py)

        builder.save(output_path)
        return output_path
