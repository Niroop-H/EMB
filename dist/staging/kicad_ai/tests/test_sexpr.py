"""
Unit tests for KiCad S-Expression parser, schematic builder, and PCB builder.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from kicad_ai.sexpr.sexpr_ast import SExpr
from kicad_ai.sexpr.sch_builder import SchematicBuilder, SchematicSymbol
from kicad_ai.sexpr.pcb_builder import PCBBuilder, PCBFootprint, FootprintPad

def test_sexpr_roundtrip():
    sample = '(kicad_sch (version 20231120) (uuid "12345") (symbol (lib_id "Device:R") (at 100 100 0)))'
    parsed = SExpr.parse(sample)
    assert parsed[0] == "kicad_sch"
    serialized = SExpr.serialize(parsed)
    assert "kicad_sch" in serialized
    assert "Device:R" in serialized
    print("[PASS] SExpr roundtrip test passed.")

def test_schematic_builder():
    builder = SchematicBuilder(title="Test ESP32 Power System")
    r1 = SchematicSymbol(lib_id="Device:R", reference="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric", x=120, y=100)
    builder.add_symbol(r1)
    builder.add_wire((120, 100), (140, 100))
    builder.add_label("VCC_3V3", 140, 100)
    builder.add_power_port("GND", 120, 110)
    
    content = builder.to_file_content()
    assert "(version 20231120)" in content
    assert "Test ESP32 Power System" in content
    assert "VCC_3V3" in content
    print("[PASS] SchematicBuilder test passed.")

def test_pcb_builder():
    pcb = PCBBuilder(board_name="Test Controller Board")
    pcb.set_board_dimensions(width_mm=50.0, height_mm=30.0, origin_x=100.0, origin_y=100.0)
    
    fp = PCBFootprint(lib_id="Resistor_SMD:R_0603_1608Metric", reference="R1", value="10k", x=110.0, y=110.0)
    fp.add_pad(FootprintPad(number="1", pad_type="smd", shape="roundrect", x=-0.8, y=0.0, size=(0.8, 0.9), net_num=1, net_name="VCC_3V3"))
    fp.add_pad(FootprintPad(number="2", pad_type="smd", shape="roundrect", x=0.8, y=0.0, size=(0.8, 0.9), net_num=2, net_name="GND"))
    pcb.add_footprint(fp)
    
    pcb.add_track(start=(110.8, 110.0), end=(115.0, 110.0), width=0.25, layer="F.Cu", net_name="GND")
    
    content = pcb.to_file_content()
    assert "(kicad_pcb" in content
    assert "Edge.Cuts" in content
    assert "VCC_3V3" in content
    print("[PASS] PCBBuilder test passed.")

if __name__ == "__main__":
    test_sexpr_roundtrip()
    test_schematic_builder()
    test_pcb_builder()
    print("All S-Expression tests completed successfully!")
