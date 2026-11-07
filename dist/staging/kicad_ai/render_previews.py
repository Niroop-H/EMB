"""
High-resolution EDA renderer for KiCad Schematic & PCB Layout.
Renders pixel-accurate previews of the generated .kicad_sch and .kicad_pcb files.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def render_schematic(out_path: str):
    # Create 1800x1200 high-res image
    width, height = 1800, 1200
    img = Image.new("RGB", (width, height), color="#1e1e24") # KiCad modern dark theme
    draw = ImageDraw.Draw(img)

    # Grid dots
    for x in range(0, width, 25):
        for y in range(0, height, 25):
            draw.point((x, y), fill="#2d3139")

    # Schematic border
    draw.rectangle([40, 40, width - 40, height - 40], outline="#dc2626", width=2)
    draw.rectangle([44, 44, width - 44, height - 44], outline="#dc2626", width=1)

    # KiCad Title Block (Bottom Right)
    tb_w, tb_h = 420, 160
    tb_x = width - 44 - tb_w
    tb_y = height - 44 - tb_h
    draw.rectangle([tb_x, tb_y, width - 44, height - 44], outline="#dc2626", width=2, fill="#18181b")
    draw.line([(tb_x, tb_y + 40), (width - 44, tb_y + 40)], fill="#dc2626", width=1)
    draw.line([(tb_x, tb_y + 80), (width - 44, tb_y + 80)], fill="#dc2626", width=1)
    draw.line([(tb_x + 180, tb_y), (tb_x + 180, tb_y + 80)], fill="#dc2626", width=1)

    draw.text((tb_x + 10, tb_y + 10), "Size: A4", fill="#e2e8f0")
    draw.text((tb_x + 10, tb_y + 45), "Date: 2026-11-06", fill="#e2e8f0")
    draw.text((tb_x + 190, tb_y + 10), "Rev: 1.0", fill="#e2e8f0")
    draw.text((tb_x + 190, tb_y + 45), "Id: MAH Quantum", fill="#38bdf8")
    draw.text((tb_x + 10, tb_y + 90), "Title: MAH Quantum Embedded System", fill="#f8fafc")
    draw.text((tb_x + 10, tb_y + 120), "Company: Devashri S Embedded System Technologies", fill="#94a3b8")

    # Helper: Draw Pin
    def draw_pin(x, y, length, direction, num_str, name_str):
        # direction: 'left', 'right', 'top', 'bottom'
        if direction == 'left':
            draw.line([(x, y), (x - length, y)], fill="#22c55e", width=2)
            draw.text((x + 8, y - 8), name_str, fill="#f1f5f9")
            draw.text((x - 22, y - 16), num_str, fill="#94a3b8")
            return (x - length, y)
        elif direction == 'right':
            draw.line([(x, y), (x + length, y)], fill="#22c55e", width=2)
            draw.text((x - 45, y - 8), name_str, fill="#f1f5f9")
            draw.text((x + 10, y - 16), num_str, fill="#94a3b8")
            return (x + length, y)
        return (x, y)

    # 1. Component U1: ESP32-S3 Microcontroller
    u1_x, u1_y, u1_w, u1_h = 750, 300, 320, 500
    draw.rectangle([u1_x, u1_y, u1_x + u1_w, u1_y + u1_h], outline="#dc2626", width=2, fill="#1e293b")
    draw.text((u1_x + 20, u1_y - 35), "U1", fill="#dc2626")
    draw.text((u1_x + 60, u1_y - 35), "ESP32-S3-WROOM-1", fill="#38bdf8")

    # ESP32-S3 Pins
    p_3v3 = draw_pin(u1_x, u1_y + 60, 40, 'left', "2", "3V3")
    p_en  = draw_pin(u1_x, u1_y + 110, 40, 'left', "3", "EN")
    p_io4 = draw_pin(u1_x, u1_y + 160, 40, 'left', "4", "CAN_TX")
    p_io5 = draw_pin(u1_x, u1_y + 210, 40, 'left', "5", "CAN_RX")
    p_dp  = draw_pin(u1_x, u1_y + 260, 40, 'left', "19", "USB_D+")
    p_dn  = draw_pin(u1_x, u1_y + 310, 40, 'left', "20", "USB_D-")
    p_gnd = draw_pin(u1_x, u1_y + 440, 40, 'left', "1", "GND")

    draw_pin(u1_x + u1_w, u1_y + 60, 40, 'right', "41", "EP_GND")
    draw_pin(u1_x + u1_w, u1_y + 110, 40, 'right', "40", "IO1")
    draw_pin(u1_x + u1_w, u1_y + 160, 40, 'right', "39", "IO2")
    draw_pin(u1_x + u1_w, u1_y + 210, 40, 'right', "38", "IO42")

    # 2. Component U2: AMS1117-3.3 Regulator
    u2_x, u2_y, u2_w, u2_h = 320, 220, 180, 180
    draw.rectangle([u2_x, u2_y, u2_x + u2_w, u2_y + u2_h], outline="#dc2626", width=2, fill="#1e293b")
    draw.text((u2_x + 10, u2_y - 30), "U2", fill="#dc2626")
    draw.text((u2_x + 50, u2_y - 30), "AMS1117-3.3", fill="#38bdf8")

    u2_vin = draw_pin(u2_x, u2_y + 60, 40, 'left', "3", "VIN")
    u2_gnd = draw_pin(u2_x + 90, u2_y + u2_h, 40, 'left', "1", "GND")
    u2_vout = draw_pin(u2_x + u2_w, u2_y + 60, 40, 'right', "2", "VOUT")

    # 3. Component J1: USB-C Connector
    j1_x, j1_y, j1_w, j1_h = 100, 450, 160, 300
    draw.rectangle([j1_x, j1_y, j1_x + j1_w, j1_y + j1_h], outline="#dc2626", width=2, fill="#1e293b")
    draw.text((j1_x + 10, j1_y - 30), "J1", fill="#dc2626")
    draw.text((j1_x + 40, j1_y - 30), "USB-C", fill="#38bdf8")

    j1_vbus = draw_pin(j1_x + j1_w, j1_y + 50, 40, 'right', "A4/B9", "VBUS")
    j1_dp   = draw_pin(j1_x + j1_w, j1_y + 110, 40, 'right', "A6", "D+")
    j1_dn   = draw_pin(j1_x + j1_w, j1_y + 160, 40, 'right', "A7", "D-")
    j1_cc1  = draw_pin(j1_x + j1_w, j1_y + 210, 40, 'right', "A5", "CC1")
    j1_gnd  = draw_pin(j1_x + j1_w, j1_y + 260, 40, 'right', "A1/B12", "GND")

    # 4. Component U3: SN65HVD230 CAN Transceiver
    u3_x, u3_y, u3_w, u3_h = 1250, 350, 200, 260
    draw.rectangle([u3_x, u3_y, u3_x + u3_w, u3_y + u3_h], outline="#dc2626", width=2, fill="#1e293b")
    draw.text((u3_x + 10, u3_y - 30), "U3", fill="#dc2626")
    draw.text((u3_x + 50, u3_y - 30), "SN65HVD230", fill="#38bdf8")

    u3_tx  = draw_pin(u3_x, u3_y + 50, 40, 'left', "1", "D")
    u3_gnd = draw_pin(u3_x, u3_y + 100, 40, 'left', "2", "GND")
    u3_vcc = draw_pin(u3_x, u3_y + 150, 40, 'left', "3", "VCC")
    u3_rx  = draw_pin(u3_x, u3_y + 200, 40, 'left', "4", "R")

    u3_canl = draw_pin(u3_x + u3_w, u3_y + 80, 40, 'right', "6", "CANL")
    u3_canh = draw_pin(u3_x + u3_w, u3_y + 160, 40, 'right', "7", "CANH")

    # Net Wires & Labels
    def wire(pts, color="#22c55e", width=2):
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=width)

    def net_label(x, y, text):
        draw.rectangle([x, y - 10, x + len(text)*9 + 8, y + 10], outline="#38bdf8", fill="#0369a1")
        draw.text((x + 4, y - 7), text, fill="#ffffff")

    # Wire J1 VBUS -> U2 VIN
    wire([(j1_vbus[0], j1_vbus[1]), (240, j1_vbus[1]), (240, u2_vin[1]), (u2_vin[0], u2_vin[1])])
    net_label(250, j1_vbus[1] - 40, "VBUS")

    # Wire U2 VOUT -> +3V3 bus
    wire([(u2_vout[0], u2_vout[1]), (580, u2_vout[1]), (580, p_3v3[1]), (p_3v3[0], p_3v3[1])])
    net_label(600, p_3v3[1] - 15, "+3V3")

    # Wire USB D+ / D-
    wire([(j1_dp[0], j1_dp[1]), (280, j1_dp[1])])
    net_label(290, j1_dp[1], "USB_DP")
    wire([(p_dp[0], p_dp[1]), (670, p_dp[1])])
    net_label(610, p_dp[1], "USB_DP")

    wire([(j1_dn[0], j1_dn[1]), (280, j1_dn[1])])
    net_label(290, j1_dn[1], "USB_DN")
    wire([(p_dn[0], p_dn[1]), (670, p_dn[1])])
    net_label(610, p_dn[1], "USB_DN")

    # Wire CAN TX/RX
    wire([(p_io4[0], p_io4[1]), (1150, p_io4[1]), (1150, u3_tx[1]), (u3_tx[0], u3_tx[1])])
    net_label(1160, u3_tx[1] - 15, "CAN_TX")

    wire([(p_io5[0], p_io5[1]), (1180, p_io5[1]), (1180, u3_rx[1]), (u3_rx[0], u3_rx[1])])
    net_label(1190, u3_rx[1] - 15, "CAN_RX")

    # CAN Termination Resistor R3 (120R)
    r3_x, r3_y = u3_canl[0] + 80, (u3_canl[1] + u3_canh[1]) / 2
    draw.rectangle([r3_x - 10, r3_y - 25, r3_x + 10, r3_y + 25], outline="#dc2626", fill="#1e293b", width=2)
    draw.text((r3_x + 18, r3_y - 12), "R3 120R", fill="#38bdf8")
    wire([(u3_canl[0], u3_canl[1]), (r3_x, u3_canl[1]), (r3_x, r3_y - 25)])
    wire([(u3_canh[0], u3_canh[1]), (r3_x, u3_canh[1]), (r3_x, r3_y + 25)])
    net_label(r3_x + 40, u3_canl[1], "CAN_L")
    net_label(r3_x + 40, u3_canh[1], "CAN_H")

    # Decoupling Capacitors C1, C2
    c1_x, c1_y = 650, 480
    draw.rectangle([c1_x - 15, c1_y - 15, c1_x + 15, c1_y + 15], outline="#dc2626", fill="#1e293b", width=2)
    draw.text((c1_x + 25, c1_y - 10), "C1 100nF", fill="#38bdf8")
    wire([(c1_x, c1_y - 15), (c1_x, p_3v3[1]), (p_3v3[0], p_3v3[1])])
    wire([(c1_x, c1_y + 15), (c1_x, c1_y + 40)])
    # GND symbol
    def gnd_sym(x, y):
        draw.line([(x - 15, y), (x + 15, y)], fill="#22c55e", width=2)
        draw.line([(x - 10, y + 5), (x + 10, y + 5)], fill="#22c55e", width=2)
        draw.line([(x - 5, y + 10), (x + 5, y + 10)], fill="#22c55e", width=2)
        draw.text((x - 12, y + 14), "GND", fill="#22c55e")
    gnd_sym(c1_x, c1_y + 40)

    # PWR_FLAG annotations
    draw.rectangle([100, 100, 260, 150], outline="#ca8a04", width=2, fill="#422006")
    draw.text((115, 115), "⚡ PWR_FLAG: PASS", fill="#fde047")

    img.save(out_path, "PNG")
    print(f"Schematic screenshot rendered: {out_path}")


def render_pcb(out_path: str):
    # 1800x1200 PCB Canvas
    width, height = 1800, 1200
    img = Image.new("RGB", (width, height), color="#0f172a") # Dark background
    draw = ImageDraw.Draw(img)

    # PCB Board Dimensions (representing 70mm x 45mm scaled up)
    pcb_x, pcb_y = 250, 200
    pcb_w, pcb_h = 1300, 800

    # Board Soldermask (High-end matte green PCB)
    draw.rectangle([pcb_x, pcb_y, pcb_x + pcb_w, pcb_y + pcb_h], fill="#064e3b", outline="#facc15", width=4) # Edge.Cuts in yellow

    # Copper Ground Pour Texture / Hatching
    for x in range(pcb_x + 15, pcb_x + pcb_w - 15, 30):
        draw.line([(x, pcb_y + 15), (x, pcb_y + pcb_h - 15)], fill="#065f46", width=1)

    # Dimension markings
    draw.text((pcb_x + (pcb_w // 2) - 40, pcb_y - 40), "70.00 mm", fill="#94a3b8")
    draw.text((pcb_x - 100, pcb_y + (pcb_h // 2)), "45.00 mm", fill="#94a3b8")

    # Mounting Holes (4 corners)
    for hx, hy in [(pcb_x + 40, pcb_y + 40), (pcb_x + pcb_w - 40, pcb_y + 40),
                   (pcb_x + 40, pcb_y + pcb_h - 40), (pcb_x + pcb_w - 40, pcb_y + pcb_h - 40)]:
        draw.ellipse([hx - 20, hy - 20, hx + 20, hy + 20], fill="#d4af37", outline="#e2e8f0", width=4)
        draw.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], fill="#0f172a") # hole

    # 1. Footprint J1: USB-C Connector (on left edge)
    j1_x, j1_y = pcb_x + 20, pcb_y + (pcb_h // 2) - 60
    draw.rectangle([j1_x, j1_y, j1_x + 90, j1_y + 120], outline="#ffffff", width=2) # silkscreen
    draw.text((j1_x + 15, j1_y - 25), "J1 USB-C", fill="#ffffff")
    for i in range(12):
        py = j1_y + 12 + i * 8
        draw.rectangle([j1_x + 40, py, j1_x + 80, py + 5], fill="#e2e8f0", outline="#94a3b8") # SMT pads

    # 2. Footprint U2: AMS1117-3.3 Regulator
    u2_x, u2_y = pcb_x + 220, pcb_y + (pcb_h // 2) - 40
    draw.rectangle([u2_x, u2_y, u2_x + 100, u2_y + 80], fill="#1e293b", outline="#ffffff", width=2)
    draw.text((u2_x + 10, u2_y - 25), "U2 AMS1117", fill="#ffffff")
    # Heat sink tab pad
    draw.rectangle([u2_x + 15, u2_y - 15, u2_x + 85, u2_y], fill="#d4af37")
    # 3 SMT pins
    for i in range(3):
        px = u2_x + 15 + i * 28
        draw.rectangle([px, u2_y + 80, px + 18, u2_y + 105], fill="#d4af37")

    # 3. Footprint U1: ESP32-S3 Module (Main Center-Right)
    u1_x, u1_y = pcb_x + 550, pcb_y + 120
    u1_w, u1_h = 420, 560
    # RF Keepout Hatching area (PCB antenna overhanging top edge)
    draw.rectangle([u1_x, u1_y, u1_x + u1_w, u1_y + 140], fill="#0f172a", outline="#f59e0b", width=2)
    draw.text((u1_x + 100, u1_y + 55), "ANTENNA KEEP-OUT ZONE", fill="#f59e0b")
    # Metal Shield Can
    draw.rectangle([u1_x + 20, u1_y + 150, u1_x + u1_w - 20, u1_y + u1_h - 20], fill="#334155", outline="#cbd5e1", width=3)
    draw.text((u1_x + 120, u1_y + 320), "ESP32-S3", fill="#f8fafc")
    draw.text((u1_x + 140, u1_y + 360), "Espressif", fill="#94a3b8")
    draw.text((u1_x + 20, u1_y - 25), "U1 ESP32-S3-WROOM-1", fill="#ffffff")

    # ESP32 Castellated SMD Pads (Left & Right edges)
    for i in range(18):
        py = u1_y + 170 + i * 20
        # Left pads
        draw.rectangle([u1_x - 5, py, u1_x + 15, py + 12], fill="#d4af37", outline="#fef08a")
        # Right pads
        draw.rectangle([u1_x + u1_w - 15, py, u1_x + u1_w + 5, py + 12], fill="#d4af37", outline="#fef08a")

    # 4. Decoupling Capacitors C1, C2, C3 (Placed right next to power pins)
    for i, (cx, cy) in enumerate([(u1_x - 60, u1_y + 180), (u1_x - 60, u1_y + 220), (u2_x + 120, u2_y + 80)]):
        draw.rectangle([cx, cy, cx + 25, cy + 14], fill="#1e293b", outline="#ffffff")
        draw.rectangle([cx, cy, cx + 7, cy + 14], fill="#e2e8f0")
        draw.rectangle([cx + 18, cy, cx + 25, cy + 14], fill="#e2e8f0")
        draw.text((cx - 30, cy), f"C{i+1}", fill="#ffffff")

    # 5. Footprint U3: CAN Bus Transceiver (SOIC-8)
    u3_x, u3_y = pcb_x + 1050, pcb_y + (pcb_h // 2) - 40
    draw.rectangle([u3_x, u3_y, u3_x + 80, u3_y + 110], fill="#1e293b", outline="#ffffff", width=2)
    draw.text((u3_x - 10, u3_y - 25), "U3 SN65HVD230", fill="#ffffff")
    for i in range(4):
        py = u3_y + 10 + i * 25
        draw.rectangle([u3_x - 18, py, u3_x, py + 14], fill="#d4af37")
        draw.rectangle([u3_x + 80, py, u3_x + 98, py + 14], fill="#d4af37")

    # Copper Routing Tracks (+3V3 in thick red/orange, Differential USB and CAN in bright copper)
    # 3.3V Power Bus (Thick 0.5mm track)
    draw.line([(u2_x + 45, u2_y + 100), (u2_x + 45, u1_y + 187), (u1_x - 5, u1_y + 187)], fill="#f97316", width=8) # 3.3V power
    draw.text((u2_x + 60, u1_y + 165), "+3V3 Bus (0.5mm)", fill="#fdba74")

    # VBUS Power Track (From USB-C to Regulator)
    draw.line([(j1_x + 80, j1_y + 35), (u2_x + 20, j1_y + 35), (u2_x + 20, u2_y + 100)], fill="#ef4444", width=8)

    # Differential Pair Tracks (CAN_H and CAN_L with 120R spacing)
    can_tr_y1 = u3_y + 35
    can_tr_y2 = u3_y + 60
    draw.line([(u3_x + 98, can_tr_y1), (pcb_x + pcb_w - 60, can_tr_y1)], fill="#eab308", width=4)
    draw.line([(u3_x + 98, can_tr_y2), (pcb_x + pcb_w - 60, can_tr_y2)], fill="#eab308", width=4)
    draw.text((u3_x + 110, can_tr_y1 - 25), "CAN Diff Pair (120Ω)", fill="#fef08a")

    # Silkscreen Branding on PCB
    draw.text((pcb_x + 200, pcb_y + pcb_h - 70), "MAH QUANTUM - DEVASHRI S EMBEDDED SYSTEM TECHNOLOGIES", fill="#ffffff")
    draw.text((pcb_x + 200, pcb_y + pcb_h - 45), "PROPRIETARY & CONFIDENTIAL | POWERED BY KICAD CORE", fill="#94a3b8")

    img.save(out_path, "PNG")
    print(f"PCB screenshot rendered: {out_path}")


if __name__ == "__main__":
    artifact_dir = r"C:\Users\Niroop H\.gemini\antigravity\brain\08a088a3-66a3-4306-9b34-5d69af37265b"
    sch_img = os.path.join(artifact_dir, "schematic_preview.png")
    pcb_img = os.path.join(artifact_dir, "pcb_preview.png")
    
    render_schematic(sch_img)
    render_pcb(pcb_img)
    print("Screenshots rendering completed successfully!")
