#!/usr/bin/env python3
"""The Catalogue Photo of an Impossible Gadget.

Draws one 1024x1024 PNG: a studio catalogue photograph of a small
impossible gadget -- a white ceramic coffee cup that keeps itself dry
with its own tiny umbrella. Rain bounces off the little canopy, steam
curls up from the coffee beneath it, and a single sugar cube sits
beside the cup as the one accessory.

Python 3.13 standard library only. The PNG is written with a small
hand-rolled encoder (zlib + struct) and the cup's brand label uses one
built-in 5x7 bitmap font. Output: /output/entry.png (or
$MAKEFUN_OUTPUT_DIR/entry.png). Deterministic: no clock, no network,
no randomness beyond a fixed seed.
"""

import math
import os
import random
import struct
import zlib

W, H = 1024, 1024

# ------------------------------------------------------------------ buffer
# One bytearray row per scanline (RGB, 3 bytes per pixel).
rows = [bytearray(W * 3) for _ in range(H)]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def set_px(x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        r = rows[y]
        i = x * 3
        r[i], r[i + 1], r[i + 2] = rgb


def blend_px(x, y, rgb, a):
    if 0 <= x < W and 0 <= y < H and a > 0:
        r = rows[y]
        i = x * 3
        if a >= 1.0:
            r[i], r[i + 1], r[i + 2] = rgb
        else:
            r[i] = int(r[i] * (1 - a) + rgb[0] * a)
            r[i + 1] = int(r[i + 1] * (1 - a) + rgb[1] * a)
            r[i + 2] = int(r[i + 2] * (1 - a) + rgb[2] * a)


def span(y, x0, x1, rgb, a=1.0):
    """Fill a horizontal span of row y with a solid colour (optional alpha)."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(math.ceil(x0)))
    x1 = min(W, int(math.floor(x1)) + 1)
    if x1 <= x0:
        return
    r = rows[y]
    if a >= 1.0:
        pat = bytes(rgb)
        r[x0 * 3:x1 * 3] = pat * (x1 - x0)
    else:
        for x in range(x0, x1):
            i = x * 3
            r[i] = int(r[i] * (1 - a) + rgb[0] * a)
            r[i + 1] = int(r[i + 1] * (1 - a) + rgb[1] * a)
            r[i + 2] = int(r[i + 2] * (1 - a) + rgb[2] * a)


def fill_ellipse(cx, cy, rx, ry, rgb, a=1.0, shade=None):
    """Filled ellipse. shade(x, y) -> rgb overrides the colour per pixel."""
    for y in range(max(0, int(cy - ry)), min(H, int(cy + ry) + 1)):
        dy = (y - cy) / ry
        dx = rx * math.sqrt(max(0.0, 1 - dy * dy))
        if shade is None:
            span(y, cx - dx, cx + dx, rgb, a)
        else:
            for x in range(max(0, int(cx - dx)), min(W, int(cx + dx) + 1)):
                blend_px(x, y, shade(x, y), a)


def fill_poly(pts, rgb, a=1.0):
    """Scanline polygon fill (pts: list of (x, y))."""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(math.ceil(min(ys)))), min(H - 1, int(math.floor(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = pts[i]
            x1, yy1 = pts[(i + 1) % n]
            if (yy0 <= y < yy1) or (yy1 <= y < yy0):
                t = (y - yy0) / (yy1 - yy0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            span(y, xs[i], xs[i + 1], rgb, a)


def thick_line(x0, y0, x1, y1, w, rgb, a=1.0):
    """A line as a filled quad with round caps."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    fill_poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
               (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], rgb, a)
    fill_ellipse(x0, y0, w / 2, w / 2, rgb, a)
    fill_ellipse(x1, y1, w / 2, w / 2, rgb, a)


def ring_arc(cx, cy, rx, ry, a0, a1, thick, rgb, a=1.0):
    """Filled elliptical ring segment (degrees, 0 = east, positive = down)."""
    outer, inner = [], []
    steps = 48
    for i in range(steps + 1):
        t = math.radians(a0 + (a1 - a0) * i / steps)
        outer.append((cx + (rx + thick / 2) * math.cos(t),
                      cy + (ry + thick / 2) * math.sin(t)))
        inner.append((cx + (rx - thick / 2) * math.cos(t),
                      cy + (ry - thick / 2) * math.sin(t)))
    fill_poly(outer + inner[::-1], rgb, a)


# ------------------------------------------------------------------- font
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
}


def draw_text(x, y, s, scale, rgb, a=1.0):
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for dy in range(scale):
                        span(y + gy * scale + dy,
                             cx + gx * scale, cx + gx * scale + scale - 1,
                             rgb, a)
        cx += 6 * scale


# ---------------------------------------------------------------- backdrop
TOP = (238, 238, 238)
BOT = (206, 206, 206)
for y in range(H):
    t = y / (H - 1)
    base = tuple(int(TOP[i] + (BOT[i] - TOP[i]) * t) for i in range(3))
    # soft radial studio glow centred behind the product
    d = math.sqrt((512 - 512) ** 2 + (y - 470) ** 2)
    g = max(0.0, 1 - d / 720.0)
    glow = tuple(int(base[i] + (255 - base[i]) * 0.35 * g * g) for i in range(3))
    rows[y] = bytearray(bytes(glow) * W)
# subtle floor sweep: a faint horizontal band low in the frame
for y in range(840, 1024):
    t = (y - 840) / 184.0
    for x in range(W):
        blend_px(x, y, (196, 196, 196), 0.10 * t)

# ------------------------------------------------------------- soft shadows
for k in range(14):
    # layered translucent ellipses -> soft contact shadow under the cup
    f = k / 13.0
    fill_ellipse(512, 828, 300 - 90 * f, 46 - 16 * f, (90, 90, 90),
                 0.05 + 0.10 * f)
fill_ellipse(775, 838, 62, 11, (90, 90, 90), 0.35)   # sugar cube shadow

# ------------------------------------------------------------ sugar cube
# The one accessory: a single sugar cube, lower right of the cup.
fill_poly([(748, 776), (766, 756), (822, 756), (804, 776)], (255, 255, 255))
fill_poly([(804, 776), (822, 756), (822, 812), (804, 832)], (213, 211, 207))
for y in range(776, 833):
    t = (y - 776) / 56.0
    c = tuple(int(248 - 14 * t) for _ in range(3))
    span(y, 748, 804, c)
# faint sparkle on the cube's top face
fill_ellipse(790, 764, 10, 3, (255, 255, 255), 0.9)

# ------------------------------------------------------------------- cup
# Body: tapered cylinder, top rim y=585, base y=800, with a ceramic
# left-to-right light falloff and a darker foot.
def cup_shade(x, y):
    half = 185 - (y - 585) * (35 / 215.0)
    t = (x - (512 - half)) / max(1.0, 2 * half)
    v = 252 - 30 * abs(t - 0.30) - 10 * max(0.0, (y - 740) / 60.0)
    v = int(clamp(v, 205, 255))
    return (v, v - 2, v - 6)


for y in range(585, 800):
    half = 185 - (y - 585) * (35 / 215.0)
    for x in range(max(0, int(512 - half)), min(W, int(512 + half) + 1)):
        blend_px(x, y, cup_shade(x, y), 1.0)
# rounded foot
fill_ellipse(512, 798, 150, 24, (226, 222, 216))
fill_ellipse(512, 800, 132, 16, (210, 205, 198))
# coffee surface
fill_ellipse(512, 585, 172, 36, (46, 26, 14))
fill_ellipse(498, 581, 118, 22, (74, 44, 22), 0.75)
fill_ellipse(470, 576, 52, 10, (122, 76, 40), 0.5)
# rim highlight, top-left arc of the rim
for deg in range(180, 330, 2):
    t = math.radians(deg)
    set_px(int(512 + 180 * math.cos(t)), int(585 + 38 * math.sin(t)),
           (255, 255, 255))

# handle: chrome-white ring on the right of the cup
ring_arc(645, 686, 100, 70, -72, 72, 24, (233, 229, 223))
ring_arc(645, 686, 100, 70, -72, -10, 8, (255, 255, 255), 0.55)

# ------------------------------------------------------------------ steam
# Two soft columns curling up from the coffee toward the canopy.
for col, phase in ((452, 0.0), (572, 2.1)):
    for i, y in enumerate(range(572, 448, -11)):
        s = math.sin((572 - y) / 46.0 + phase)
        x = col + 16 * s
        r = 7 + i * 0.55
        fill_ellipse(x, y, r, r * 1.25, (255, 255, 255), 0.10)

# ------------------------------------------------------- umbrella pole
for x in range(507, 517):
    t = (x - 507) / 9.0
    v = int(190 - 90 * abs(t - 0.35))
    span(292, x, x, (v, v + 4, v + 8))
for y in range(293, 592):
    for x in range(507, 517):
        t = (x - 507) / 9.0
        v = int(190 - 90 * abs(t - 0.35))
        blend_px(x, y, (v, v + 4, v + 8), 1.0)
# ripple where the pole dips into the coffee
fill_ellipse(512, 588, 30, 9, (24, 13, 7), 0.8)
fill_ellipse(512, 586, 20, 6, (96, 60, 32), 0.6)

# ------------------------------------------------------------ umbrella
# Eight alternating panels, scalloped lower edge, apex at (512, 292).
APEX = (512, 292)
CX, CY, RX, RY = 512, 415, 265, 135
RED = (207, 59, 40)
CREAM = (244, 239, 232)


def dome_point(deg):
    t = math.radians(deg)
    return (CX + RX * math.cos(t), CY - RY * math.sin(t))


PANELS = 8
for p in range(PANELS):
    a0 = 180 - p * (180 / PANELS)
    a1 = 180 - (p + 1) * (180 / PANELS)
    mid = (a0 + a1) / 2
    mx = CX + RX * math.cos(math.radians(mid))
    f = 1.06 - 0.11 * (mx - CX) / RX
    base = RED if p % 2 == 0 else CREAM
    col = tuple(int(clamp(c * f, 0, 255)) for c in base)
    pts = [APEX]
    steps = 12
    for i in range(steps + 1):
        pts.append(dome_point(a0 + (a1 - a0) * i / steps))
    for i in range(steps, -1, -1):
        deg = a0 + (a1 - a0) * i / steps
        frac = i / steps
        x, _ = dome_point(deg)
        pts.append((x, CY + 26 * math.sin(math.pi * frac)))
    fill_poly(pts, col)
# seams from apex to each rib tip
for p in range(PANELS + 1):
    deg = 180 - p * (180 / PANELS)
    x, y = dome_point(deg)
    thick_line(APEX[0], APEX[1], x, y, 2, (143, 36, 24), 0.45)
# apex cap + finial
fill_ellipse(512, 292, 9, 9, (143, 36, 24))
thick_line(512, 292, 512, 252, 5, (120, 124, 130))
fill_ellipse(512, 248, 9, 9, (150, 154, 160))
fill_ellipse(509, 245, 3, 3, (235, 238, 242), 0.9)
# soft highlight on the canopy, upper left
fill_ellipse(420, 330, 110, 46, (255, 255, 255), 0.10)

# ------------------------------------------------------------------- rain
# Drops falling above the canopy, slanting slightly, and a few splashes
# where they hit the fabric.
rng = random.Random(11)
DROP = (126, 162, 196)
for _ in range(30):
    x = rng.randint(70, 954)
    y = rng.randint(36, 250)
    thick_line(x, y, x - 6, y + 26, 3, DROP, 0.85)
    set_px(x - 6, y + 27, (200, 220, 235))
for _ in range(6):
    x = rng.randint(60, 200) if rng.random() < 0.5 else rng.randint(824, 964)
    y = rng.randint(300, 560)
    thick_line(x, y, x - 6, y + 26, 3, DROP, 0.7)
# splash crowns on the canopy
for deg in (150, 120, 90, 60, 30):
    x, y = dome_point(deg)
    y += 4
    for dx, dy in ((-7, -6), (0, -9), (7, -6)):
        fill_ellipse(x + dx, y + dy, 3, 3, (190, 210, 228), 0.9)
    thick_line(x - 9, y, x + 9, y, 2, (190, 210, 228), 0.8)

# ------------------------------------------------------------- cup label
# A tiny umbrella mark and the product's own brand word, nothing more.
fill_ellipse(512, 668, 15, 8, (90, 90, 96))
thick_line(512, 668, 512, 682, 2, (90, 90, 96))
fill_ellipse(512, 682, 2, 2, (90, 90, 96))
draw_text(460, 692, "BRELLA", 3, (74, 74, 80))
thick_line(472, 720, 552, 720, 2, (150, 148, 144), 0.8)

# ------------------------------------------------------------- PNG encoder
def encode_png(pix_rows, w, h):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += pix_rows[y]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        c = struct.pack(">I", len(payload)) + tag + payload
        return c + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", data) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png(rows, W, H))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
