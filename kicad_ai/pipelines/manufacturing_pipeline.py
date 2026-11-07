"""
Manufacturing and Tapeout Pipeline.
Generates industrial-grade BOM and Centroid (CPL / Pick-and-Place) CSV files ready for JLCPCB, PCBWay, or contract manufacturers.
"""

from typing import Dict, Any, List
import csv
import os

class ManufacturingPipeline:
    def __init__(self):
        pass

    def generate_jlcpcb_bom(self, architecture: Dict[str, Any], output_csv_path: str):
        """Generates standard JLCPCB SMT BOM CSV."""
        components = architecture.get("components", [])
        
        headers = ["Comment", "Designator", "Footprint", "LCSC Part #"]
        rows = []
        
        # Mapping to popular basic JLCPCB / LCSC library parts
        lcsc_map = {
            "AMS1117-3.3": "C6186",
            "ESP32-S3-WROOM-1-N16R8": "C2913200",
            "SN65HVD230DR": "C12066",
            "100nF": "C14663",
            "10uF": "C15849",
            "10k": "C25804",
            "5.1k": "C23186",
            "120R": "C22787"
        }

        for comp in components:
            ref = comp.get("reference", "")
            mpn = comp.get("mpn", "")
            fp = comp.get("footprint", "")
            lcsc = lcsc_map.get(mpn, "TBD")
            rows.append([mpn, ref, fp, lcsc])

        with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
            
        return output_csv_path

    def generate_cpl(self, output_csv_path: str, placements: List[Dict[str, Any]]):
        """Generates Centroid Pick and Place (CPL) file."""
        headers = ["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"]
        rows = []
        for p in placements:
            rows.append([
                p.get("designator", ""),
                p.get("val", ""),
                p.get("package", ""),
                f"{p.get('x', 0.0):.2f}mm",
                f"{p.get('y', 0.0):.2f}mm",
                f"{p.get('rotation', 0.0):.1f}",
                p.get("layer", "Top")
            ])

        with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

        return output_csv_path
