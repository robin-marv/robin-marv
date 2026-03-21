#!/usr/bin/env python3
"""
Robin Signal Map — animated SVG of Robin deployments across Canada.
Each node = a Robin deployment. SMS signal pulses radiate outward.
"""

import math
import random

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 900, 420
PAD_X, PAD_Y = 80, 60

# ── Deployment data ───────────────────────────────────────────────────────────
ROBINS = [
    ("Alberta Beer Fest",     "Edmonton",  "events"),
    ("I Pray Festival",       "Calgary",   "events"),
    ("AI Salon Calgary",      "Calgary",   "events"),
    ("SumoFest",              "Calgary",   "events"),
    ("Winnipeg Goldeyes",     "Winnipeg",  "sports"),
    ("Lugo",                  "Calgary",   "business"),
    ("Plug & Play",           "Calgary",   "tech"),
    ("Volleyball Alberta",    "Calgary",   "sports"),
    ("Legal Frequencies",     "Calgary",   "events"),
    ("AB Energy Regulator",   "Calgary",   "enterprise"),
    ("Sprawl Tech Week",      "Toronto",   "events"),
    ("ACE / RRC",             "Winnipeg",  "education"),
    ("AI YYC Salon",          "Calgary",   "events"),
    ("Halifax Mooseheads",    "Halifax",   "sports"),
    ("Shindico",              "Winnipeg",  "business"),
]

# Normalised city anchor coords (x=west->east, y=top->bottom)
CITY_ANCHOR = {
    "Calgary":  (0.225, 0.52),
    "Edmonton": (0.225, 0.28),
    "Winnipeg": (0.50,  0.52),
    "Toronto":  (0.68,  0.58),
    "Halifax":  (0.89,  0.45),
}

# Category colours
CAT_COLOR = {
    "events":     "#a78bfa",
    "sports":     "#34d399",
    "business":   "#60a5fa",
    "tech":       "#f59e0b",
    "enterprise": "#f87171",
    "education":  "#38bdf8",
}

def to_px(nx, ny):
    return round(PAD_X + nx * (W - 2*PAD_X), 1), round(PAD_Y + ny * (H - 2*PAD_Y), 1)

def cluster_positions(count, cx, cy, min_r=38, ring_gap=32):
    """Arrange nodes in rings around (cx, cy)."""
    if count == 1:
        return [(cx, cy)]
    ring_capacity = [0, 6, 10, 14, 18]
    pos = []
    placed = 0
    ring = 1
    r = min_r
    while placed < count:
        cap = ring_capacity[ring] if ring < len(ring_capacity) else ring * 6
        n = min(cap, count - placed)
        angle_offset = ring * 0.5
        for i in range(n):
            a = angle_offset + 2 * math.pi * i / cap
            pos.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        placed += n
        ring += 1
        r += ring_gap
    return pos

from collections import defaultdict
city_groups = defaultdict(list)
for name, city, cat in ROBINS:
    city_groups[city].append((name, cat))

nodes = []
for city, members in city_groups.items():
    cx, cy = to_px(*CITY_ANCHOR.get(city, (0.5, 0.5)))
    positions = cluster_positions(len(members), cx, cy)
    for idx, (name, cat) in enumerate(members):
        px, py = positions[idx]
        nodes.append({
            "name": name, "city": city, "cat": cat,
            "x": round(px, 1), "y": round(py, 1),
            "anchor": (cx, cy),
            "angle": math.atan2(py - cy, px - cx),  # angle from cluster centre
        })

# ── SVG ───────────────────────────────────────────────────────────────────────
def build_svg():
    out = []
    w = out.append

    w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    w('''<defs>
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:#0d1117"/>
    <stop offset="100%" style="stop-color:#0f172a"/>
  </linearGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="2.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-hq">
    <feGaussianBlur stdDeviation="5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="ts">
    <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#000" flood-opacity="0.9"/>
  </filter>
</defs>''')

    w('<rect width="100%" height="100%" fill="url(#bg)" rx="14"/>')

    # Starfield
    rng = random.Random(7)
    for _ in range(150):
        sx, sy = rng.uniform(0, W), rng.uniform(0, H)
        sr = rng.uniform(0.3, 1.0)
        so = rng.uniform(0.04, 0.20)
        w(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr}" fill="white" opacity="{so:.2f}"/>')

    # City halo
    for city, members in city_groups.items():
        cx, cy = to_px(*CITY_ANCHOR.get(city, (0.5, 0.5)))
        r = 22 + len(members) * 8
        col = CAT_COLOR.get(members[0][1], "#888")
        w(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="0.035"/>')

    hq_cx, hq_cy = to_px(*CITY_ANCHOR["Calgary"])

    # Connection lines city → HQ
    city_drawn = set()
    for city in city_groups:
        if city == "Calgary" or city in city_drawn:
            continue
        city_drawn.add(city)
        cx, cy = to_px(*CITY_ANCHOR.get(city, (0.5, 0.5)))
        col = CAT_COLOR.get(city_groups[city][0][1], "#888")
        dur = 5 + list(city_groups.keys()).index(city) * 0.7
        w(f'<line x1="{hq_cx}" y1="{hq_cy}" x2="{cx}" y2="{cy}" '
          f'stroke="{col}" stroke-width="0.8" stroke-dasharray="5 7" opacity="0.15">'
          f'<animate attributeName="opacity" values="0.08;0.28;0.08" dur="{dur}s" repeatCount="indefinite"/>'
          f'</line>')

    # SMS particle flow city → HQ
    for i, city in enumerate([c for c in city_groups if c != "Calgary"]):
        cx, cy = to_px(*CITY_ANCHOR.get(city, (0.5, 0.5)))
        col = CAT_COLOR.get(city_groups[city][0][1], "#888")
        dur = 3.5 + i * 0.8
        delay = i * 1.2
        w(f'<circle r="2.5" fill="{col}">'
          f'<animate attributeName="cx" from="{cx}" to="{hq_cx}" dur="{dur}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="cy" from="{cy}" to="{hq_cy}" dur="{dur}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.05;0.85;1" dur="{dur}s" begin="{delay:.1f}s" repeatCount="indefinite"/>'
          f'</circle>')

    # HQ node
    w(f'<g transform="translate({hq_cx},{hq_cy})" filter="url(#glow-hq)">')
    for i in range(3):
        d = i * 1.3
        w(f'<circle r="12" fill="none" stroke="#7c3aed" stroke-width="1.5" opacity="0.5">'
          f'<animate attributeName="r" from="12" to="55" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" from="0.5" to="0" dur="4s" begin="{d}s" repeatCount="indefinite"/>'
          f'</circle>')
    w('<circle r="12" fill="#4c1d95" opacity="0.95"/>')
    w('<circle r="7" fill="#7c3aed"/>')
    w('<circle r="3" fill="#a78bfa"/>')
    w('<text y="-18" text-anchor="middle" fill="#c4b5fd" font-size="8.5" font-family="monospace" font-weight="bold" filter="url(#ts)">ROBIN HQ</text>')
    w('</g>')

    # Deployment nodes with radial labels
    total = len(nodes)
    for idx, node in enumerate(nodes):
        nx, ny = node["x"], node["y"]
        col = CAT_COLOR.get(node["cat"], "#888")
        name = node["name"]
        if len(name) > 18:
            name = name[:16] + ".."

        dur = 2.0 + (idx % 6) * 0.35
        delay = (idx / total) * dur
        angle = node["angle"]

        # Line node → anchor
        ax, ay = node["anchor"]
        if abs(nx - ax) > 4 or abs(ny - ay) > 4:
            w(f'<line x1="{ax}" y1="{ay}" x2="{nx}" y2="{ny}" '
              f'stroke="{col}" stroke-width="0.5" opacity="0.18"/>')

        w(f'<g transform="translate({nx},{ny})" filter="url(#glow)">')

        # Pulse
        w(f'<circle r="5" fill="none" stroke="{col}" stroke-width="1">'
          f'<animate attributeName="r" from="5" to="20" dur="{dur}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" from="0.7" to="0" dur="{dur}s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
          f'</circle>')

        w(f'<circle r="5" fill="{col}" opacity="0.9"/>')
        w(f'<circle r="2.2" fill="white" opacity="0.6"/>')

        # Radial label placement — push label outward from cluster centre
        label_r = 14
        lx_off = label_r * math.cos(angle)
        ly_off = label_r * math.sin(angle)
        anchor = "start" if lx_off > 0 else "end"
        if abs(lx_off) < 4:
            anchor = "middle"
        w(f'<text dx="{lx_off:.1f}" dy="{ly_off + 3:.1f}" text-anchor="{anchor}" '
          f'fill="#94a3b8" font-size="7" font-family="monospace" filter="url(#ts)">{name}</text>')

        w('</g>')

    # City labels
    for city, members in city_groups.items():
        cx, cy = to_px(*CITY_ANCHOR.get(city, (0.5, 0.5)))
        max_r = 22 + len(members) * 8
        ly = cy + max_r + 14
        if ly > H - 12:
            ly = cy - max_r - 8
        w(f'<text x="{cx}" y="{ly}" text-anchor="middle" fill="#334155" '
          f'font-size="7.5" font-family="monospace" letter-spacing="1.5">{city.upper()}</text>')

    # Legend
    lx, ly = W - 138, 14
    w(f'<rect x="{lx-8}" y="{ly-4}" width="140" height="116" rx="7" '
      f'fill="#0d1117" stroke="#21262d" stroke-width="1" opacity="0.95"/>')
    w(f'<text x="{lx}" y="{ly+9}" fill="#8b949e" font-size="7.5" font-family="monospace" font-weight="bold">ROBIN DEPLOYMENTS</text>')
    for i, (cat, col) in enumerate(CAT_COLOR.items()):
        ry = ly + 24 + i * 14
        w(f'<circle cx="{lx+5}" cy="{ry}" r="4" fill="{col}"/>')
        w(f'<text x="{lx+15}" y="{ry+3.5}" fill="#6e7681" font-size="7.5" font-family="monospace">{cat}</text>')

    # Title
    w(f'<text x="22" y="26" fill="#e6edf3" font-size="14" font-family="monospace" font-weight="bold">Robin Signal Map</text>')
    w(f'<text x="22" y="40" fill="#484f58" font-size="8" font-family="monospace">{len(nodes)} active deployments  |  Canada</text>')

    # Antenna
    ax_, ay_ = 14, 15
    w(f'<line x1="{ax_}" y1="{ay_+8}" x2="{ax_}" y2="{ay_-4}" stroke="#7c3aed" stroke-width="1.5" stroke-linecap="round"/>')
    w(f'<path d="M{ax_-6},{ay_} Q{ax_},{ay_-12} {ax_+6},{ay_}" fill="none" stroke="#7c3aed" stroke-width="1.2" opacity="0.7"/>')
    w(f'<path d="M{ax_-10},{ay_+3} Q{ax_},{ay_-18} {ax_+10},{ay_+3}" fill="none" stroke="#7c3aed" stroke-width="0.8" opacity="0.4"/>')

    w('</svg>')
    return '\n'.join(out)


if __name__ == "__main__":
    import sys
    svg = build_svg()
    out = sys.argv[1] if len(sys.argv) > 1 else "signal-map.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"Generated {out} ({len(svg):,} bytes, {len(ROBINS)} Robin nodes)")
