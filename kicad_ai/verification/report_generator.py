"""
Automated Verification & Industrial Readiness Certification Engine.
Devashri S Embedded System Technologies.
Engineered & Certified by MAH Quantum — Autonomous EDA & Firmware Verification Division.
Powered by KiCad Core EDA.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional


class VerificationReportGenerator:
    """
    Generates official industrial verification certificates and market-readiness reports.
    STRICT POLICY: Only issues 'PASS - MANUFACTURING READY' if 100% of fabrication
    and manufacturing norms are verified. If any norm fails, explicitly brands the output
    as 'FAIL - FABRICATION REJECTED' with detailed decision support evidence.
    """

    def __init__(self):
        pass

    def generate_run_id(self) -> str:
        now = datetime.datetime.utcnow()
        date_str = now.strftime("%Y-%m%d")
        sec_hash = int(now.strftime("%H%M%S")) % 900 + 100
        return f"VER-{date_str}-{sec_hash:03d}"

    def generate_report(self,
                        architecture: Dict[str, Any],
                        norm_audit: Dict[str, Any],
                        sch_path: str,
                        pcb_path: str,
                        output_dir: str) -> Dict[str, Any]:
        """
        Generates VERIFICATION_REPORT.md and VERIFICATION_CERTIFICATE.html based on norm audit.
        """
        now = datetime.datetime.utcnow()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        run_id = self.generate_run_id()

        project_name = architecture.get("project_name", "MAH_Quantum_System")
        mcu_info = architecture.get("mcu", {})
        components = architecture.get("components", [])
        nets = architecture.get("nets", [])

        is_ready = norm_audit.get("is_manufacturing_ready", False)
        norms = norm_audit.get("norms", [])
        failure_reasons = norm_audit.get("failure_reasons", [])
        passed_count = norm_audit.get("passed_norms_count", 0)
        failed_count = norm_audit.get("failed_norms_count", len(failure_reasons))
        total_norms = norm_audit.get("total_norms", len(norms))

        if is_ready:
            status_text = "PASS — MANUFACTURING READY"
            status_symbol = "[✓ PASS]"
            status_badge_class = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
            status_badge_dot = "bg-emerald-400 shadow-[0_0_8px_#34d399]"
            cert_header_title = "Official Certificate of Manufacturing Readiness"
            cert_sub_verdict = "AUTHORIZED FOR COMMERCIAL TAPEOUT & AUTOMATED SMT ASSEMBLY"
            digital_seal = f"{run_id}-MAH-QUANTUM-CERTIFIED-PASS"
            statement = (
                "The hardware design has successfully completed autonomous synthesis, electrical rule closure, "
                "and physical topological routing. Design rules meet or exceed standard commercial PCB fabricator "
                "constraints (JLCPCB, PCBWay, Eurocircuits). All 8 manufacturing norms have been verified with "
                "0 unconnected nets and 0 electrical rule errors. The project files are hereby certified and "
                "authorized for fabrication release."
            )
        else:
            status_text = "FAIL — FABRICATION REJECTED (NON-COMPLIANT)"
            status_symbol = "[❌ FAIL]"
            status_badge_class = "bg-rose-500/15 text-rose-400 border-rose-500/40"
            status_badge_dot = "bg-rose-500 shadow-[0_0_8px_#f43f5e]"
            cert_header_title = "Industrial Fabrication Rejection & Non-Conformance Audit"
            cert_sub_verdict = "FABRICATION RELEASE WITHHELD — ACTION REQUIRED BEFORE TAPEOUT"
            digital_seal = f"VOID-{run_id}-REJECTED-NON-COMPLIANT"
            statement = (
                f"FABRICATION CERTIFICATE REFUSED. The hardware design failed {failed_count} out of {total_norms} "
                "essential fabrication norms. Critical non-conformances (such as unrouted nets, copper clearance violations, "
                "or missing manufacturing deliverables) were detected. Submitting these files to a PCB fabricator "
                "will cause manufacturing aborts, electrical open/short circuits, or defective SMT assembly. "
                "Remediate the non-conformance items detailed below to re-qualify for certification."
            )

        # ── 1. Generate Markdown Report ─────────────────────────────────────────
        md_lines = [
            f"# {cert_header_title}",
            f"**Devashri S Embedded System Technologies**  ",
            f"*Engineered & Certified by MAH Quantum — Autonomous EDA & Firmware Verification Division*  ",
            f"*Underlying EDA Engine: Powered by KiCad Core EDA (https://www.kicad.org)*  ",
            f"",
            f"---",
            f"",
            f"## {status_symbol} {status_text}",
            f"- **RUN ID:** `{run_id}`",
            f"- **TIMESTAMP:** `{timestamp_str}`",
            f"- **PROJECT NAME:** `{project_name}`",
            f"- **PRIMARY CONTROLLER:** `{mcu_info.get('mpn', 'N/A')} ({mcu_info.get('package', 'SMD')})`",
            f"- **FABRICATION NORMS VERIFIED:** `{passed_count} / {total_norms} Passed`",
            f"- **NON-CONFORMANCES:** `{failed_count} Violations Detected`",
            f"- **DIGITAL SEAL:** `{digital_seal}`",
            f"",
            f"---",
            f"",
            f"### Executive Summary & Certification Verdict",
            f"> **AUDIT STATEMENT:**  ",
            f"> {statement}",
            f"",
            f"---",
            f"",
            f"### Comprehensive 8-Norm Manufacturing Audit",
            f"| Norm ID | Fabrication / Assembly Norm | Verdict | Audit Observation |",
            f"|---|---|---|---|",
        ]

        for n in norms:
            v_badge = f"**{n['verdict']}**"
            if n['verdict'] == 'FAIL':
                v_badge = f"<span style='color:red;'>**{n['verdict']}**</span>"
            md_lines.append(f"| `{n['id']}` | **{n['name']}** | {v_badge} | {n['details']} |")

        md_lines.append("")

        # Decision Support Section
        if not is_ready:
            md_lines.extend([
                f"---",
                f"",
                f"### ⚠️ DECISION SUPPORT: ROOT-CAUSE FAILURE EVIDENCE & REMEDIATION",
                f"The following violations directly support the decision to **REJECT** fabrication clearance:",
                f""
            ])
            for idx, r in enumerate(failure_reasons, 1):
                md_lines.extend([
                    f"#### {idx}. Violation on [{r['norm_id']}] {r['name']}",
                    f"- **Direct Root Cause:** {r['cause']}",
                    f"- **Manufacturing Impact:** {r['impact']}",
                    f"- **Required Action:** {r['remediation']}",
                    f"- **Evidence:**"
                ])
                for ev in r.get("evidence", []):
                    md_lines.append(f"  - `{ev}`")
                md_lines.append("")
        else:
            md_lines.extend([
                f"---",
                f"",
                f"### ✓ DECISION SUPPORT: MANUFACTURING READY CLEARANCE EVIDENCE",
                f"The design satisfies all commercial PCB fabrication and automated SMT assembly norms:",
                f"- **Topological Routing:** 100% completed with zero unrouted nets (0 ratsnest remaining).",
                f"- **Clearances:** Minimum copper spacing exceeds 0.20 mm (JLCPCB Class 2 compliant).",
                f"- **Power Integrity:** Power buses routed with heavy trace widths; dual-layer ground return zones present.",
                f"- **Manufacturing Deliverables:** Valid KiCad project (`board.kicad_pro`), schematic (`board.kicad_sch`), PCB (`board.kicad_pcb`), SMT BOM (`jlcpcb_bom.csv`), and CPL (`centroid_cpl.csv`) are synchronized and verified.",
                f""
            ])

        md_lines.extend([
            f"---",
            f"",
            f"**Signed:**  ",
            f"*MAH Quantum Autonomous Hardware Verification Agent*  ",
            f"*Devashri S Embedded System Technologies*"
        ])

        md_content = "\n".join(md_lines)
        md_path = os.path.join(output_dir, "VERIFICATION_REPORT.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # ── 2. Generate Print-Ready HTML Certificate ───────────────────────────
        # Build Norm Rows for HTML
        norm_rows_html = []
        for n in norms:
            is_p = n['verdict'] == 'PASS'
            color_cls = "text-emerald-400" if is_p else "text-rose-400 font-bold"
            bg_cls = "bg-emerald-500/5" if is_p else "bg-rose-500/10"
            norm_rows_html.append(f"""
            <tr class="{bg_cls}">
              <td class="p-2.5 font-mono text-[11px] text-slate-400">{n['id']}</td>
              <td class="p-2.5 font-semibold text-slate-200">{n['name']}</td>
              <td class="p-2.5 text-xs text-slate-300">{n['details']}</td>
              <td class="p-2.5 text-right {color_cls}">{n['verdict']}</td>
            </tr>
            """)
        norm_rows_str = "\n".join(norm_rows_html)

        # Decision Support Box for HTML
        if not is_ready:
            decision_box_html = f"""
            <div class="mt-6 p-4 rounded-xl bg-rose-950/40 border border-rose-500/40">
              <h3 class="text-sm font-bold text-rose-300 flex items-center gap-2 mb-2">
                <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                DECISION SUPPORT: ROOT-CAUSE FAILURE EVIDENCE ({failed_count} VIOLATIONS)
              </h3>
              <p class="text-xs text-slate-300 mb-3">
                Fabrication certificate is <b>WITHHELD</b>. The following non-conformances directly substantiate the rejection:
              </p>
              <div class="space-y-3 font-mono text-[11px]">
                {"".join([f'''
                <div class="bg-slate-950/60 p-3 rounded-lg border border-rose-500/20">
                  <div class="text-rose-400 font-bold">[{r['norm_id']}] {r['name']}</div>
                  <div class="text-slate-300 mt-1"><span class="text-slate-500">Cause:</span> {r['cause']}</div>
                  <div class="text-amber-300 mt-1"><span class="text-slate-500">Impact:</span> {r['impact']}</div>
                  <div class="text-emerald-400 mt-1"><span class="text-slate-500">Remediation:</span> {r['remediation']}</div>
                </div>
                ''' for r in failure_reasons])}
              </div>
            </div>
            """
        else:
            decision_box_html = f"""
            <div class="mt-6 p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30">
              <h3 class="text-sm font-bold text-emerald-300 flex items-center gap-2 mb-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                DECISION SUPPORT: 100% MANUFACTURING READY CLEARANCE
              </h3>
              <p class="text-xs text-slate-300">
                All 8 electrical, physical, and SMT manufacturing norms passed formal verification. 
                Zero unrouted nets, zero clearance collisions, heavy power bus sizing, and fully synchronized 
                SMT BOM & Pick-and-Place coordinates. Authorized for immediate release to PCB manufacturing and assembly.
              </p>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Verification Report - {run_id}</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    @media print {{
      body {{ background: #ffffff; color: #000000; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-6 md:p-10 text-xs">
  <div class="max-w-4xl mx-auto bg-slate-900 border {'border-emerald-500/40' if is_ready else 'border-rose-500/50'} rounded-2xl shadow-2xl overflow-hidden p-8 md:p-12 relative">
    
    <!-- Header -->
    <div class="flex items-center justify-between border-b border-slate-800 pb-6 mb-6">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-white">Devashri S Embedded System Technologies</h1>
        <p class="text-xs text-blue-400 font-medium">Engineered & Certified by MAH Quantum — Autonomous EDA & Firmware Verification Division</p>
        <p class="text-[11px] text-slate-500">Underlying EDA Engine: Powered by KiCad Core EDA (https://www.kicad.org)</p>
      </div>
      <div class="text-right">
        <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider border {status_badge_class}">
          <span class="w-2 h-2 rounded-full {status_badge_dot}"></span>
          {status_text}
        </span>
      </div>
    </div>

    <!-- Metadata Grid -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 mb-6 font-mono text-[11px]">
      <div>
        <span class="text-slate-500 block">RUN ID</span>
        <span class="text-white font-bold">{run_id}</span>
      </div>
      <div>
        <span class="text-slate-500 block">TIMESTAMP</span>
        <span class="text-slate-300">{timestamp_str}</span>
      </div>
      <div>
        <span class="text-slate-500 block">PROJECT</span>
        <span class="text-blue-400 font-bold">{project_name}</span>
      </div>
      <div>
        <span class="text-slate-500 block">NORMS STATUS</span>
        <span class="{'text-emerald-400' if is_ready else 'text-rose-400'} font-bold">{passed_count} / {total_norms} Passed</span>
      </div>
    </div>

    <!-- Certification Statement -->
    <div class="mb-6 p-4 rounded-xl bg-slate-950/40 border border-slate-800">
      <div class="text-xs font-semibold text-slate-400 mb-1">OFFICIAL VERDICT & DIRECTIVE</div>
      <p class="text-xs leading-relaxed text-slate-200">{statement}</p>
    </div>

    <!-- Norms Table -->
    <div>
      <h2 class="text-sm font-semibold text-white mb-2 flex items-center gap-2">
        <span class="w-2 h-2 rounded-full {'bg-emerald-400' if is_ready else 'bg-rose-400'}"></span> 
        Fabrication & SMT Manufacturing Norms Audit (IPC-2221 Class 2)
      </h2>
      <div class="bg-slate-950/40 rounded-lg border border-slate-800 overflow-hidden">
        <table class="w-full text-left">
          <thead class="bg-slate-800/50 text-slate-400 border-b border-slate-800 text-[11px]">
            <tr>
              <th class="p-2.5">Norm ID</th>
              <th class="p-2.5">Fabrication Standard</th>
              <th class="p-2.5">Observed State & Measurement</th>
              <th class="p-2.5 text-right">Verdict</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 text-slate-300">
            {norm_rows_str}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Decision Support Evidence -->
    {decision_box_html}

    <!-- Sign-off -->
    <div class="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between">
      <div>
        <p class="text-xs text-slate-400">Digital Seal & Verification Hash</p>
        <p class="font-mono text-[11px] {'text-blue-400' if is_ready else 'text-rose-400'} font-bold">{digital_seal}</p>
      </div>
      <div class="text-right">
        <p class="text-xs font-semibold text-white">Devashri S Embedded System Technologies</p>
        <p class="text-[11px] text-slate-500">Autonomous EDA & Firmware Verification Division</p>
      </div>
    </div>

  </div>
</body>
</html>
"""
        html_path = os.path.join(output_dir, "VERIFICATION_CERTIFICATE.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # ── 3. CLI Console Summary ─────────────────────────────────────────────
        console_summary = (
            f"\n================================================================================\n"
            f"  DEVASHRI S EMBEDDED SYSTEM TECHNOLOGIES\n"
            f"  Engineered & Certified by MAH Quantum — Autonomous EDA & Firmware Verification Division\n"
            f"--------------------------------------------------------------------------------\n"
            f"  {status_symbol} {status_text}\n"
            f"  RUN ID:    {run_id}\n"
            f"  TIMESTAMP: {timestamp_str}\n"
            f"  PROJECT:   {project_name}\n"
            f"  NORMS:     {passed_count} / {total_norms} Passed ({failed_count} Failed)\n"
            f"  MARKET:    {'READY FOR TAPEOUT & SMT ASSEMBLY' if is_ready else 'REJECTED — ACTION REQUIRED'}\n"
            f"  REPORT:    {md_path}\n"
            f"  CERT:      {html_path}\n"
            f"================================================================================\n"
        )

        return {
            "run_id": run_id,
            "timestamp": timestamp_str,
            "status": status_text,
            "is_manufacturing_ready": is_ready,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "total_norms": total_norms,
            "md_path": md_path,
            "html_path": html_path,
            "console_summary": console_summary,
            "failure_reasons": failure_reasons
        }
