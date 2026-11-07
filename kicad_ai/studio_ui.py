"""
MAH Quantum Autonomous Hardware Foundry Studio - Interactive UI Server
Devashri S Embedded System Technologies - Proprietary & Confidential
Underlying Engine: Powered by KiCad Core EDA
"""

import os
import sys
import json
import re
import subprocess
import webbrowser
import threading
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
KICAD_BIN_DIR = r"D:\KI CAD\bin"

app = FastAPI(title="MAH Quantum Foundry Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def find_kicad_exe(name: str) -> Optional[str]:
    """Finds KiCad executable in D:\\KI CAD\\bin or PATH."""
    candidate = os.path.join(KICAD_BIN_DIR, f"{name}.exe")
    if os.path.exists(candidate):
        return candidate
    candidate_nosuffix = os.path.join(KICAD_BIN_DIR, name)
    if os.path.exists(candidate_nosuffix):
        return candidate_nosuffix
    return None

def parse_kicad_pcb(pcb_path: str) -> Dict[str, Any]:
    """Extracts outline, footprints, pads, and tracks from .kicad_pcb for interactive canvas."""
    if not os.path.exists(pcb_path):
        return {"error": "PCB file not found", "footprints": [], "tracks": [], "outline": []}

    try:
        with open(pcb_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e), "footprints": [], "tracks": [], "outline": []}

    outline = []
    # Lines on Edge.Cuts
    line_pattern = re.compile(
        r'\(gr_line\s+\(start\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(end\s+([\d\.\-]+)\s+([\d\.\-]+)\).*?\(layer\s+"Edge\.Cuts"\)',
        re.DOTALL
    )
    for m in line_pattern.findall(content):
        outline.append({"x1": float(m[0]), "y1": float(m[1]), "x2": float(m[2]), "y2": float(m[3])})

    # Rect outline fallback
    rect_matches = re.findall(r'\(gr_rect\s+\(start\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(end\s+([\d\.\-]+)\s+([\d\.\-]+)\).*?\(layer\s+"Edge\.Cuts"\)', content, re.DOTALL)
    for m in rect_matches:
        x1, y1, x2, y2 = map(float, m)
        outline.append({"x1": x1, "y1": y1, "x2": x2, "y2": y1})
        outline.append({"x1": x2, "y1": y1, "x2": x2, "y2": y2})
        outline.append({"x1": x2, "y1": y2, "x2": x1, "y2": y2})
        outline.append({"x1": x1, "y1": y2, "x2": x1, "y2": y1})

    # Footprints
    footprints = []
    fp_blocks = re.split(r'\(footprint\s+', content)[1:]
    for idx, block in enumerate(fp_blocks):
        fp_name_match = re.match(r'"([^"]+)"', block)
        fp_name = fp_name_match.group(1) if fp_name_match else "Unknown"

        at_match = re.search(r'\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', block)
        fx = float(at_match.group(1)) if at_match else 0.0
        fy = float(at_match.group(2)) if at_match else 0.0
        frot = float(at_match.group(3)) if (at_match and at_match.group(3)) else 0.0

        ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block) or re.search(r'\(fp_text\s+reference\s+"([^"]+)"', block)
        ref = ref_match.group(1) if ref_match else f"U{idx+1}"

        val_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block) or re.search(r'\(fp_text\s+value\s+"([^"]+)"', block)
        val = val_match.group(1) if val_match else ""

        # Pads
        pads = []
        pad_matches = re.findall(
            r'\(pad\s+"([^"]+)"\s+(\w+)\s+(\w+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+).*?\(size\s+([\d\.\-]+)\s+([\d\.\-]+)\)',
            block,
            re.DOTALL
        )
        for pm in pad_matches:
            pads.append({
                "number": pm[0],
                "type": pm[1],
                "shape": pm[2],
                "rel_x": float(pm[3]),
                "rel_y": float(pm[4]),
                "width": float(pm[5]),
                "height": float(pm[6])
            })

        footprints.append({
            "name": fp_name,
            "ref": ref,
            "value": val,
            "x": fx,
            "y": fy,
            "rotation": frot,
            "pads": pads
        })

    # Copper track segments
    tracks = []
    seg_pattern = re.compile(
        r'\(segment\s+\(start\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(end\s+([\d\.\-]+)\s+([\d\.\-]+)\)\s+\(width\s+([\d\.\-]+)\)\s+\(layer\s+"([^"]+)"\)\s+\(net\s+(?:"([^"]+)"|(\d+))\)',
        re.MULTILINE
    )
    for sm in seg_pattern.findall(content):
        tracks.append({
            "x1": float(sm[0]),
            "y1": float(sm[1]),
            "x2": float(sm[2]),
            "y2": float(sm[3]),
            "width": float(sm[4]),
            "layer": sm[5],
            "net": sm[6] if sm[6] else sm[7]
        })

    return {
        "outline": outline,
        "footprints": footprints,
        "tracks": tracks
    }

def get_project_dirs() -> Dict[str, str]:
    """Finds all available projects."""
    projects = {}
    sample_dir = os.path.join(BASE_DIR, "sample_project")
    if os.path.exists(sample_dir):
        projects["sample_project"] = sample_dir

    gen_dir = os.path.join(BASE_DIR, "generated_systems")
    if os.path.exists(gen_dir):
        for item in os.listdir(gen_dir):
            full_p = os.path.join(gen_dir, item)
            if os.path.isdir(full_p) and os.path.exists(os.path.join(full_p, "board.kicad_pcb")):
                projects[item] = full_p
    return projects

@app.get("/api/projects")
def list_projects():
    projects = get_project_dirs()
    summary = []
    for name, path in projects.items():
        pcb_file = os.path.join(path, "board.kicad_pcb")
        sch_file = os.path.join(path, "board.kicad_sch")
        cert_file = os.path.join(path, "VERIFICATION_CERTIFICATE.html")
        bom_file = os.path.join(path, "jlcpcb_bom.csv")
        summary.append({
            "id": name,
            "name": name.replace("_", " "),
            "path": path,
            "has_pcb": os.path.exists(pcb_file),
            "has_sch": os.path.exists(sch_file),
            "has_cert": os.path.exists(cert_file),
            "has_bom": os.path.exists(bom_file),
        })
    return {"projects": summary}

@app.get("/api/project/{project_id}/details")
def project_details(project_id: str):
    projects = get_project_dirs()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    p_dir = projects[project_id]
    pcb_file = os.path.join(p_dir, "board.kicad_pcb")
    bom_file = os.path.join(p_dir, "jlcpcb_bom.csv")
    cpl_file = os.path.join(p_dir, "centroid_cpl.csv")
    cert_file = os.path.join(p_dir, "VERIFICATION_CERTIFICATE.html")
    report_file = os.path.join(p_dir, "VERIFICATION_REPORT.md")

    pcb_data = parse_kicad_pcb(pcb_file)

    # Read BOM
    bom_rows = []
    if os.path.exists(bom_file):
        with open(bom_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[1:]:
                parts = [p.strip().strip('"') for p in line.strip().split(",")]
                if len(parts) >= 4:
                    bom_rows.append({
                        "comment": parts[0],
                        "designator": parts[1],
                        "footprint": parts[2],
                        "lcsc": parts[3] if len(parts) > 3 else "N/A"
                    })

    # Read Certificate HTML
    cert_html = ""
    if os.path.exists(cert_file):
        with open(cert_file, "r", encoding="utf-8") as f:
            cert_html = f.read()

    # Read Report MD
    report_md = ""
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            report_md = f.read()

    is_pass = "PASS — MANUFACTURING READY" in cert_html

    return {
        "id": project_id,
        "path": p_dir,
        "pcb": pcb_data,
        "bom": bom_rows,
        "cert_html": cert_html,
        "report_md": report_md,
        "is_pass": is_pass
    }

@app.post("/api/open")
async def open_in_kicad(request: Request):
    data = await request.json()
    project_id = data.get("project_id")
    target = data.get("target", "pcb")  # pcb, sch, pro, explorer

    projects = get_project_dirs()
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")

    p_dir = projects[project_id]

    if target == "pcb":
        file_path = os.path.join(p_dir, "board.kicad_pcb")
        exe = find_kicad_exe("pcbnew") or find_kicad_exe("kicad")
        if exe and os.path.exists(file_path):
            subprocess.Popen([exe, file_path])
            return {"status": "success", "message": f"Opened in {os.path.basename(exe)}"}
        elif os.path.exists(file_path):
            os.startfile(file_path)
            return {"status": "success", "message": "Opened via Windows default association"}

    elif target == "sch":
        file_path = os.path.join(p_dir, "board.kicad_sch")
        exe = find_kicad_exe("eeschema") or find_kicad_exe("kicad")
        if exe and os.path.exists(file_path):
            subprocess.Popen([exe, file_path])
            return {"status": "success", "message": f"Opened in {os.path.basename(exe)}"}
        elif os.path.exists(file_path):
            os.startfile(file_path)
            return {"status": "success", "message": "Opened via Windows default association"}

    elif target == "pro":
        file_path = os.path.join(p_dir, "board.kicad_pro")
        exe = find_kicad_exe("kicad")
        if exe and os.path.exists(file_path):
            subprocess.Popen([exe, file_path])
            return {"status": "success", "message": "Opened in KiCad Project Manager"}
        elif os.path.exists(file_path):
            os.startfile(file_path)
            return {"status": "success", "message": "Opened via Windows default association"}

    elif target == "explorer":
        subprocess.Popen(f'explorer "{p_dir}"')
        return {"status": "success", "message": "Opened folder in Windows Explorer"}

    return {"status": "error", "message": "Could not find target or executable"}

@app.post("/api/synthesize")
async def synthesize_system(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "Raspberry Pi RP2040 Compute Engine with USB-C and 16MB Flash")
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', prompt[:30]).strip('_') or "Custom_System"
    outdir = os.path.join(BASE_DIR, "generated_systems", f"Custom_{clean_name}")
    os.makedirs(outdir, exist_ok=True)

    cmd = [
        sys.executable,
        os.path.join(BASE_DIR, "run_foundry.py"),
        "--prompt", prompt,
        "--outdir", outdir
    ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode == 0:
        return {
            "status": "success",
            "project_id": f"Custom_{clean_name}",
            "logs": proc.stdout
        }
    else:
        return {
            "status": "error",
            "message": proc.stderr or proc.stdout,
            "logs": proc.stdout
        }

@app.get("/", response_class=HTMLResponse)
def index_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAH Quantum Foundry Studio | Devashri S Embedded System Technologies</title>
<style>
:root {
  --bg-dark: #0a0e14;
  --bg-card: #111822;
  --bg-card-hover: #16202c;
  --bg-sidebar: #0d121b;
  --border-color: #1f2b3c;
  --text-main: #f0f4f8;
  --text-muted: #8b99a8;
  --accent-cyan: #00e5ff;
  --accent-blue: #0070f3;
  --accent-green: #00e676;
  --accent-purple: #9d4edd;
  --accent-red: #ff3366;
  --copper-top: #ff5252;
  --copper-bot: #448aff;
  --pad-gold: #ffd700;
  --silk-white: #ffffff;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: var(--bg-dark);
  color: var(--text-main);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

header {
  background: linear-gradient(90deg, #0d131e 0%, #111a28 100%);
  border-bottom: 1px solid var(--border-color);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-logo {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  color: #000;
  font-size: 16px;
}
.brand-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
}
.brand-sub {
  font-size: 11px;
  color: var(--accent-cyan);
  font-weight: 500;
}
.badge-certified {
  background: rgba(0, 230, 118, 0.15);
  border: 1px solid rgba(0, 230, 118, 0.4);
  color: var(--accent-green);
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge-certified::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
}

.main-container {
  display: flex;
  flex: 1;
  height: calc(100vh - 53px);
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 380px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.section-box {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}
.section-title {
  font-size: 11px;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 700;
  letter-spacing: 0.8px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

select, textarea, input, button {
  font-family: inherit;
}

.project-select {
  width: 100%;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}
.project-select:focus {
  border-color: var(--accent-cyan);
}

.prompt-area {
  width: 100%;
  height: 80px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: #fff;
  padding: 10px;
  border-radius: 6px;
  font-size: 13px;
  resize: vertical;
  outline: none;
  margin-bottom: 8px;
}
.prompt-area:focus {
  border-color: var(--accent-cyan);
}

.btn-synthesize {
  width: 100%;
  background: linear-gradient(135deg, #0070f3, #00d4ff);
  border: none;
  color: #fff;
  padding: 10px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-synthesize:hover {
  opacity: 0.9;
}

.archetypes-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
}
.archetype-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-main);
  padding: 7px 10px;
  border-radius: 4px;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}
.archetype-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-cyan);
}

.action-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 10px;
}
.action-btn {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: #fff;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.action-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-cyan);
}
.action-btn.primary {
  grid-column: span 2;
  background: rgba(0, 229, 255, 0.12);
  border-color: rgba(0, 229, 255, 0.4);
  color: var(--accent-cyan);
  font-weight: 600;
}

/* Center Content */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.tabs-bar {
  display: flex;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  padding: 0 16px;
}
.tab {
  padding: 12px 18px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.tab:hover {
  color: #fff;
}
.tab.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
}

.tab-pane {
  display: none;
  flex: 1;
  overflow: auto;
  position: relative;
}
.tab-pane.active {
  display: flex;
  flex-direction: column;
}

/* PCB Visualizer Canvas */
#pcb-canvas-container {
  flex: 1;
  background: #06090d;
  position: relative;
  overflow: hidden;
}
canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
}
canvas:active {
  cursor: grabbing;
}

.canvas-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(17, 24, 34, 0.9);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  align-items: center;
  z-index: 5;
}
.canvas-controls label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #fff;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

/* BOM Table */
.table-container {
  padding: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--bg-card);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}
th {
  background: #141c27;
  text-align: left;
  padding: 12px;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}
td {
  padding: 10px 12px;
  border-bottom: 1px solid #1a2432;
  color: var(--text-main);
}
tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

/* Certificate Tab */
.cert-frame-container {
  flex: 1;
  height: 100%;
  background: #fff;
}
iframe {
  width: 100%;
  height: 100%;
  border: none;
}

/* Terminal / Log Drawer */
.log-box {
  background: #06090e;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-family: "Consolas", monospace;
  font-size: 11px;
  color: #00ffaa;
  padding: 10px;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
  margin-top: 8px;
}

.footer-bar {
  background: var(--bg-sidebar);
  border-top: 1px solid var(--border-color);
  padding: 6px 16px;
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="brand-logo">Q</div>
    <div>
      <div class="brand-title">MAH QUANTUM — Autonomous Hardware Foundry</div>
      <div class="brand-sub">Devashri S Embedded System Technologies &bull; Powered by KiCad Core EDA</div>
    </div>
  </div>
  <div class="badge-certified" id="headerBadge">INDUSTRIAL VERIFIED &bull; PASS</div>
</header>

<div class="main-container">
  <!-- Left Control Panel -->
  <div class="sidebar">
    <div class="section-box">
      <div class="section-title">Active Project Archetype</div>
      <select id="projectSelect" class="project-select" onchange="loadSelectedProject()"></select>
      
      <div class="action-buttons">
        <button class="action-btn primary" onclick="launchKiCad('pcb')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
          Open in KiCad 10 PCB Editor
        </button>
        <button class="action-btn" onclick="launchKiCad('pro')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
          Project Suite
        </button>
        <button class="action-btn" onclick="launchKiCad('sch')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>
          Schematic
        </button>
        <button class="action-btn" onclick="launchKiCad('explorer')" style="grid-column: span 2;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          Open Folder in File Explorer
        </button>
      </div>
    </div>

    <div class="section-box">
      <div class="section-title">Synthesize New Hardware</div>
      <textarea id="promptInput" class="prompt-area" placeholder="e.g. Raspberry Pi RP2040 Compute Engine with 16MB Flash, dual USB-C, and buck regulator..."></textarea>
      <button class="btn-synthesize" id="btnSynthesize" onclick="synthesizeSystem()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Synthesize & Auto-Route
      </button>

      <div class="section-title" style="margin-top: 14px;">One-Click Presets</div>
      <div class="archetypes-grid">
        <button class="archetype-btn" onclick="setPrompt('Raspberry Pi RP2040 Compute Module with 16MB QSPI Flash, Dual USB Type-C, and Low-Noise LDO')">
          1. Raspberry Pi RP2040 Compute
        </button>
        <button class="archetype-btn" onclick="setPrompt('STM32F405 Industrial Motion Controller with 6-Axis IMU, CAN bus, and 12-24V Buck')">
          2. STM32 Motion Controller
        </button>
        <button class="archetype-btn" onclick="setPrompt('Automotive Dual CAN-FD Gateway with Isolated Power and TVS ESD Protection')">
          3. Automotive Dual CAN Gateway
        </button>
        <button class="archetype-btn" onclick="setPrompt('Environmental IoT Sensor Node with BME680, ESP32-S3, and LiPo Charger')">
          4. Environmental IoT Node
        </button>
        <button class="archetype-btn" onclick="setPrompt('Audiophile High-Res 32-bit I2S Stereo Audio DAC with Ultra-Low Jitter Clock')">
          5. Audiophile I2S Audio DAC
        </button>
      </div>
    </div>

    <div class="section-box" style="flex: 1;">
      <div class="section-title">Agent Synthesis Console</div>
      <div id="logConsole" class="log-box">[MAH Quantum Foundry Ready] Select a system or synthesize a new board.</div>
    </div>
  </div>

  <!-- Main Display Workspace -->
  <div class="content">
    <div class="tabs-bar">
      <div class="tab active" onclick="switchTab('canvas-tab', this)">Interactive 2D Board Viewer</div>
      <div class="tab" onclick="switchTab('bom-tab', this)">BOM & SMT Pick-and-Place</div>
      <div class="tab" onclick="switchTab('cert-tab', this)">Official Verification Certificate</div>
      <div class="tab" onclick="switchTab('report-tab', this)">DRC / ERC Audit Log</div>
    </div>

    <!-- PCB Viewer Tab -->
    <div id="canvas-tab" class="tab-pane active">
      <div id="pcb-canvas-container">
        <div class="canvas-controls">
          <label><input type="checkbox" id="chkTracks" checked onchange="renderCanvas()"> <span class="legend-dot" style="background:var(--copper-top)"></span> F.Cu Tracks</label>
          <label><input type="checkbox" id="chkPads" checked onchange="renderCanvas()"> <span class="legend-dot" style="background:var(--pad-gold)"></span> Pads</label>
          <label><input type="checkbox" id="chkSilk" checked onchange="renderCanvas()"> <span class="legend-dot" style="background:#fff"></span> Silkscreen</label>
          <label><input type="checkbox" id="chkOutline" checked onchange="renderCanvas()"> <span class="legend-dot" style="background:var(--accent-cyan)"></span> Edge.Cuts</label>
          <span style="border-left: 1px solid var(--border-color); padding-left: 10px;">Zoom: <span id="zoomLevel">100%</span></span>
        </div>
        <canvas id="pcbCanvas"></canvas>
      </div>
    </div>

    <!-- BOM Tab -->
    <div id="bom-tab" class="tab-pane">
      <div class="table-container">
        <h3 style="margin-bottom: 12px; font-size: 15px; color: var(--accent-cyan);">JLCPCB / PCBWay SMT Assembly Bill of Materials</h3>
        <table>
          <thead>
            <tr>
              <th>Designator</th>
              <th>Component Value / MPN</th>
              <th>Footprint Package</th>
              <th>LCSC Part Number</th>
            </tr>
          </thead>
          <tbody id="bomTableBody"></tbody>
        </table>
      </div>
    </div>

    <!-- Certificate Tab -->
    <div id="cert-tab" class="tab-pane">
      <div class="cert-frame-container">
        <iframe id="certIframe" src="about:blank"></iframe>
      </div>
    </div>

    <!-- Report Tab -->
    <div id="report-tab" class="tab-pane">
      <div style="padding: 20px; font-family: 'Consolas', monospace; white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #d0e0ff;" id="reportText"></div>
    </div>
  </div>
</div>

<div class="footer-bar">
  <div>Platform: MAH Quantum v1.0 &bull; License: Proprietary & Confidential (All Rights Reserved)</div>
  <div>Underlying EDA Engine: KiCad 10.0 (gitlab.com/kicad/code/kicad) &bull; Devashri S Embedded System Technologies</div>
</div>

<script>
let currentProject = null;
let currentProjectData = null;

// Canvas state
const canvas = document.getElementById('pcbCanvas');
const ctx = canvas.getContext('2d');
let scale = 5.0;
let offsetX = 100;
let offsetY = 100;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

function resizeCanvas() {
  const container = document.getElementById('pcb-canvas-container');
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;
  renderCanvas();
}
window.addEventListener('resize', resizeCanvas);

// Pan and Zoom
canvas.addEventListener('mousedown', (e) => {
  isPanning = true;
  startPanX = e.clientX - offsetX;
  startPanY = e.clientY - offsetY;
});
window.addEventListener('mouseup', () => { isPanning = false; });
canvas.addEventListener('mousemove', (e) => {
  if (isPanning) {
    offsetX = e.clientX - startPanX;
    offsetY = e.clientY - startPanY;
    renderCanvas();
  }
});
canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
  const mouseX = e.clientX - canvas.getBoundingClientRect().left;
  const mouseY = e.clientY - canvas.getBoundingClientRect().top;

  offsetX = mouseX - (mouseX - offsetX) * zoomFactor;
  offsetY = mouseY - (mouseY - offsetY) * zoomFactor;
  scale *= zoomFactor;
  document.getElementById('zoomLevel').innerText = Math.round((scale / 5.0) * 100) + '%';
  renderCanvas();
});

function renderCanvas() {
  ctx.fillStyle = '#06090e';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (!currentProjectData || !currentProjectData.pcb) return;

  const pcb = currentProjectData.pcb;
  const chkTracks = document.getElementById('chkTracks').checked;
  const chkPads = document.getElementById('chkPads').checked;
  const chkSilk = document.getElementById('chkSilk').checked;
  const chkOutline = document.getElementById('chkOutline').checked;

  ctx.save();
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  // 1. Board Outline
  if (chkOutline && pcb.outline && pcb.outline.length > 0) {
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 0.4;
    ctx.beginPath();
    if (pcb.outline[0].x !== undefined) {
      ctx.moveTo(pcb.outline[0].x, pcb.outline[0].y);
      for (let i = 1; i < pcb.outline.length; i++) {
        ctx.lineTo(pcb.outline[i].x, pcb.outline[i].y);
      }
      ctx.closePath();
    } else {
      for (let l of pcb.outline) {
        ctx.moveTo(l.x1, l.y1);
        ctx.lineTo(l.x2, l.y2);
      }
    }
    ctx.stroke();

    // Solder mask FR4 fill
    ctx.fillStyle = 'rgba(10, 40, 30, 0.35)';
    ctx.fill();
  }

  // 2. Copper Tracks
  if (chkTracks && pcb.tracks) {
    for (let t of pcb.tracks) {
      ctx.strokeStyle = t.layer === 'F.Cu' ? '#ff4d4d' : '#3388ff';
      ctx.lineWidth = t.width || 0.4;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(t.x1, t.y1);
      ctx.lineTo(t.x2, t.y2);
      ctx.stroke();
    }
  }

  // 3. Footprints & Pads
  if (pcb.footprints) {
    for (let fp of pcb.footprints) {
      // Footprint boundary/crosshair
      if (chkSilk) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '1.2px sans-serif';
        ctx.fillText(fp.ref + " (" + fp.value + ")", fp.x - 3, fp.y - 4);
      }

      // Pads
      if (chkPads && fp.pads) {
        for (let p of fp.pads) {
          const px = fp.x + p.rel_x;
          const py = fp.y + p.rel_y;
          ctx.fillStyle = '#ffd700';
          ctx.beginPath();
          if (p.shape === 'rect' || p.shape === 'roundrect') {
            ctx.rect(px - p.width / 2, py - p.height / 2, p.width, p.height);
          } else {
            ctx.arc(px, py, (p.width || 1) / 2, 0, Math.PI * 2);
          }
          ctx.fill();

          // Pad Number
          if (scale > 8.0) {
            ctx.fillStyle = '#000000';
            ctx.font = '0.6px sans-serif';
            ctx.fillText(p.number, px - 0.3, py + 0.2);
          }
        }
      }
    }
  }

  ctx.restore();
}

function autoFitBoard() {
  if (!currentProjectData || !currentProjectData.pcb) return;
  const outline = currentProjectData.pcb.outline || [];
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  if (outline.length > 0) {
    for (let pt of outline) {
      if (pt.x1 !== undefined) {
        minX = Math.min(minX, pt.x1, pt.x2);
        minY = Math.min(minY, pt.y1, pt.y2);
        maxX = Math.max(maxX, pt.x1, pt.x2);
        maxY = Math.max(maxY, pt.y1, pt.y2);
      } else if (pt.x !== undefined) {
        minX = Math.min(minX, pt.x);
        minY = Math.min(minY, pt.y);
        maxX = Math.max(maxX, pt.x);
        maxY = Math.max(maxY, pt.y);
      }
    }
  }
  
  if (minX === Infinity && currentProjectData.pcb.footprints && currentProjectData.pcb.footprints.length > 0) {
    for (let fp of currentProjectData.pcb.footprints) {
      minX = Math.min(minX, fp.x - 10);
      minY = Math.min(minY, fp.y - 10);
      maxX = Math.max(maxX, fp.x + 10);
      maxY = Math.max(maxY, fp.y + 10);
    }
  }

  if (minX !== Infinity) {
    const bw = maxX - minX || 50;
    const bh = maxY - minY || 50;
    scale = Math.min((canvas.width - 150) / bw, (canvas.height - 150) / bh);
    offsetX = (canvas.width - bw * scale) / 2 - minX * scale;
    offsetY = (canvas.height - bh * scale) / 2 - minY * scale;
    document.getElementById('zoomLevel').innerText = Math.round((scale / 5.0) * 100) + '%';
    renderCanvas();
  }
}

async function loadProjects() {
  const res = await fetch('/api/projects');
  const data = await res.json();
  const select = document.getElementById('projectSelect');
  select.innerHTML = '';
  data.projects.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.innerText = p.name;
    select.appendChild(opt);
  });
  if (data.projects.length > 0) {
    currentProject = data.projects[0].id;
    await loadSelectedProject();
  }
}

async function loadSelectedProject() {
  const select = document.getElementById('projectSelect');
  currentProject = select.value;
  const res = await fetch(`/api/project/${currentProject}/details`);
  currentProjectData = await res.json();

  // Populate BOM
  const tbody = document.getElementById('bomTableBody');
  tbody.innerHTML = '';
  if (currentProjectData.bom && currentProjectData.bom.length > 0) {
    currentProjectData.bom.forEach(b => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><b>${b.designator}</b></td><td>${b.comment}</td><td>${b.footprint}</td><td><span style="color:var(--accent-cyan);">${b.lcsc}</span></td>`;
      tbody.appendChild(tr);
    });
  } else {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No BOM records found.</td></tr>';
  }

  // Populate Certificate iframe
  const iframe = document.getElementById('certIframe');
  if (currentProjectData.cert_html) {
    iframe.srcdoc = currentProjectData.cert_html;
  }

  // Populate Report
  document.getElementById('reportText').innerText = currentProjectData.report_md || 'No audit report generated yet.';

  // Update Status Badge
  const badge = document.getElementById('headerBadge');
  if (badge) {
    if (currentProjectData.is_pass) {
      badge.innerHTML = '✓ PASS &bull; MANUFACTURING READY';
      badge.style.background = 'rgba(0, 230, 118, 0.15)';
      badge.style.borderColor = 'rgba(0, 230, 118, 0.4)';
      badge.style.color = '#00e676';
    } else {
      badge.innerHTML = '❌ FAIL &bull; FABRICATION REJECTED';
      badge.style.background = 'rgba(255, 51, 102, 0.15)';
      badge.style.borderColor = 'rgba(255, 51, 102, 0.5)';
      badge.style.color = '#ff3366';
    }
  }

  // Fit and render canvas
  autoFitBoard();
}

function switchTab(tabId, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(tabId).classList.add('active');
  if (tabId === 'canvas-tab') {
    resizeCanvas();
  }
}

function setPrompt(text) {
  document.getElementById('promptInput').value = text;
}

async function synthesizeSystem() {
  const prompt = document.getElementById('promptInput').value.trim();
  if (!prompt) return alert('Please enter a hardware requirement prompt.');

  const btn = document.getElementById('btnSynthesize');
  const consoleEl = document.getElementById('logConsole');
  btn.disabled = true;
  btn.innerText = 'Synthesizing Architecture & Tracks...';
  consoleEl.innerText = `[+] Initiating Autonomous Synthesis Engine...\n[*] Prompt: "${prompt}"\n[*] Multi-Agent Architect formulating sub-circuits...\n`;

  try {
    const res = await fetch('/api/synthesize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt})
    });
    const result = await res.json();
    if (result.status === 'success') {
      consoleEl.innerText += `\\n[PASS] Synthesis & Auto-Route Succeeded!\\n` + result.logs;
      await loadProjects();
      document.getElementById('projectSelect').value = result.project_id;
      await loadSelectedProject();
    } else {
      consoleEl.innerText += `\\n[ERROR] Synthesis failed: ` + (result.message || '');
    }
  } catch (err) {
    consoleEl.innerText += `\\n[ERROR] Network error: ` + err.message;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Synthesize & Auto-Route`;
  }
}

async function launchKiCad(target) {
  if (!currentProject) return;
  const res = await fetch('/api/open', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({project_id: currentProject, target: target})
  });
  const data = await res.json();
  const consoleEl = document.getElementById('logConsole');
  consoleEl.innerText += `\\n[+] Command: Open in ${target.toUpperCase()} -> ` + data.message;
}

window.onload = () => {
  resizeCanvas();
  loadProjects();
};
</script>
</body>
</html>
"""

def start_server(port: int = 8448, open_browser: bool = True):
    url = f"http://localhost:{port}"
    print(f"\n=================================================================")
    print(f"       MAH QUANTUM - Devashri S Embedded System Technologies     ")
    print(f"       Autonomous Hardware Foundry Studio UI (Powered by KiCad)  ")
    print(f"=================================================================")
    print(f"[+] Server starting at: {url}")
    print(f"[+] KiCad 10 Binary Path: {KICAD_BIN_DIR}")
    print(f"[+] Press Ctrl+C in terminal to stop.")

    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8448)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    start_server(port=args.port, open_browser=not args.no_browser)
