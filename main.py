#!/usr/bin/env python3
"""A Little Umbrella for Your Coffee.

Catalogue photo of an impossible gadget: a white ceramic coffee cup
with its own tiny red-and-white umbrella. Rain bounces off the canopy,
steam rises from the coffee, one sugar cube on a small plate is the
single accessory. Pure Python 3 stdlib, no network, no dependencies.

Running this file writes /output/entry.png (1024x1024, <= 1 MiB).
"""

import math
import os
import struct
import zlib

W = H = 1024


# ---------------------------------------------------------------- framebuffer
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)

    def blend(self, x, y, r, g, b, a=1.0):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        if a >= 1.0:
            self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b
            return
        self.px[i] = int(self.px[i] * (1 - a) + r * a)
        self.px[i + 1] = int(self.px[i + 1] * (1 - a) + g * a)
        self.px[i + 2] = int(self.px[i + 2] * (1 - a) + b * a)

    def disc(self, cx, cy, rad, col, a=1.0):
        r2 = rad * rad
        x0 = max(0, int(cx - rad))
        x1 = min(self.w - 1, int(cx + rad) + 1)
        y0 = max(0, int(cy - rad))
        y1 = min(self.h - 1, int(cy + rad) + 1)
        for y in range(y0, y1 + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0.0, r2 - dy * dy)))
            for x in range(max(x0, int(cx - dx)), min(x1, int(cx + dx)) + 1):
                self.blend(x, y, *col, a)

    def ellipse(self, cx, cy, rx, ry, col, a=1.0):
        for y in range(max(0, int(cy - ry)), min(self.h - 1, int(cy + ry) + 1)):
            t = (y - cy) / ry
            dx = rx * math.sqrt(max(0.0, 1 - t * t))
            for x in range(max(0, int(cx - dx)), min(self.w - 1, int(cx + dx)) + 1):
                self.blend(x, y, *col, a)

    def ellipse_grad(self, cx, cy, rx, ry, left, mid, right, a=1.0):
        """Horizontal 3-stop gradient ellipse."""
        for y in range(max(0, int(cy - ry)), min(self.h - 1, int(cy + ry) + 1)):
            t = (y - cy) / ry
            dx = rx * math.sqrt(max(0.0, 1 - t * t))
            for x in range(max(0, int(cx - dx)), min(self.w - 1, int(cx + dx)) + 1):
                u = (x - (cx - dx)) / max(1.0, 2 * dx)
                if u < 0.5:
                    f = u * 2
                    col = tuple(int(left[c] + (mid[c] - left[c]) * f) for c in range(3))
                else:
                    f = (u - 0.5) * 2
                    col = tuple(int(mid[c] + (right[c] - mid[c]) * f) for c in range(3))
                self.blend(x, y, *col, a)

    def polygon(self, pts, col, a=1.0):
        ys = [p[1] for p in pts]
        y0, y1 = max(0, int(min(ys))), min(self.h - 1, int(max(ys)) + 1)
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x1, y1p = pts[i]
                x2, y2p = pts[(i + 1) % n]
                if (y1p <= y < y2p) or (y2p <= y < y1p):
                    xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[k])), min(self.w - 1, int(xs[k + 1])) + 1):
                    self.blend(x, y, *col, a)

    def thick_line(self, x1, y1, x2, y2, rad, col, a=1.0):
        length = math.hypot(x2 - x1, y2 - y1)
        steps = max(1, int(length))
        for s in range(steps + 1):
            t = s / steps
            self.disc(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, rad, col, a)

    def vgrad(self, top, bottom):
        for y in range(self.h):
            f = y / (self.h - 1)
            col = tuple(int(top[c] + (bottom[c] - top[c]) * f) for c in range(3))
            i = y * self.w * 3
            row = bytes(col) * self.w
            self.px[i:i + self.w * 3] = row


# ------------------------------------------------------------------- tiny font
FONT = {
    "B": ["01110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
}


def draw_text(cv, text, cx, top, scale, col):
    gw, gh = 5, 7
    total = len(text) * (gw + 1) * scale - scale
    x = cx - total // 2
    for ch in text:
        glyph = FONT[ch]
        for r in range(gh):
            for c in range(gw):
                if glyph[r][c] == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            cv.blend(x + c * scale + dx, top + r * scale + dy, *col)
        x += (gw + 1) * scale


# ---------------------------------------------------------------------- scene
def render():
    cv = Canvas(W, H)
    # Studio backdrop: soft vertical gradient, light grey.
    cv.vgrad((233, 233, 236), (198, 198, 203))
    # Faint horizon line where the tabletop meets the backdrop.
    for x in range(W):
        cv.blend(x, 868, 178, 178, 184, 0.5)

    # ---- soft floor shadow under the cup
    for i, (rx, a) in enumerate([(330, 0.10), (300, 0.12), (265, 0.14), (225, 0.16)]):
        cv.ellipse(512, 852, rx, 46 - i * 3, (70, 70, 78), a)

    # ---- saucer
    cv.ellipse_grad(512, 812, 268, 52, (176, 176, 182), (246, 246, 248), (168, 168, 175))
    cv.ellipse(512, 806, 252, 44, (252, 252, 254))
    cv.ellipse(512, 806, 196, 34, (226, 226, 230))

    # ---- cup body: tapered cylinder, shaded like glazed ceramic
    top_y, bot_y = 566, 800
    top_half, bot_half = 196, 152
    for y in range(top_y, bot_y + 1):
        f = (y - top_y) / (bot_y - top_y)
        half = top_half + (bot_half - top_half) * f
        # rounded bottom
        if y > 770:
            half *= math.sqrt(max(0.0, 1 - ((y - 770) / 34.0) ** 2 * 0.55))
        for x in range(int(512 - half), int(512 + half) + 1):
            u = (x - (512 - half)) / max(1.0, 2 * half)
            if u < 0.18:
                shade = 0.82 + 0.18 * (u / 0.18)
            elif u < 0.5:
                shade = 1.0 - 0.06 * ((u - 0.18) / 0.32)
            elif u < 0.82:
                shade = 0.94 - 0.10 * ((u - 0.5) / 0.32)
            else:
                shade = 0.84 - 0.06 * ((u - 0.82) / 0.18)
            base = (246, 246, 248)
            cv.blend(x, y, int(base[0] * shade), int(base[1] * shade), int(base[2] * shade))
    # specular highlight on the left of the cup
    cv.ellipse(392, 676, 26, 96, (255, 255, 255), 0.55)
    cv.ellipse(404, 676, 12, 80, (255, 255, 255), 0.5)
    # thin rim at the top edge
    cv.ellipse(512, 566, 196, 26, (214, 214, 218))
    # coffee surface
    cv.ellipse_grad(512, 566, 186, 22, (58, 32, 16), (74, 42, 20), (52, 28, 14))
    cv.ellipse(512, 564, 150, 15, (96, 58, 30), 0.55)

    # ---- handle (right side), drawn after the body so it reads clearly:
    # dark rim, white ceramic ring, backdrop showing through the hole
    cv.ellipse(748, 668, 82, 104, (188, 188, 194))
    cv.ellipse(748, 668, 76, 98, (240, 240, 244))
    cv.ellipse(748, 668, 48, 68, (210, 210, 215))
    cv.ellipse(748, 668, 48, 68, (200, 200, 205), 0.3)

    # ---- product label on the cup
    draw_text(cv, "BRELLA", 512, 668, 7, (196, 52, 38))
    # small red underline swoosh under the label
    cv.thick_line(452, 730, 572, 730, 3, (196, 52, 38))

    # ---- umbrella pole: from canopy down into the cup
    cv.thick_line(512, 176, 512, 566, 5, (74, 60, 52))
    cv.thick_line(510, 176, 510, 566, 2, (140, 126, 112))
    # finial tip above the canopy
    cv.thick_line(512, 176, 512, 132, 4, (74, 60, 52))
    cv.disc(512, 128, 9, (196, 52, 38))
    cv.disc(509, 125, 3, (255, 120, 100))

    # ---- canopy: alternating red / white panels, scalloped hem
    apex = (512, 176)
    panels = 8
    half_w, hem_y = 296, 336
    for p in range(panels):
        a0 = math.pi * p / panels
        a1 = math.pi * (p + 1) / panels
        x0 = apex[0] - half_w * math.cos(a0)
        x1 = apex[0] - half_w * math.cos(a1)
        y0 = apex[1] + (hem_y - apex[1]) * math.sin(a0) ** 0.9
        y1 = apex[1] + (hem_y - apex[1]) * math.sin(a1) ** 0.9
        col = (198, 52, 38) if p % 2 == 0 else (248, 248, 246)
        cv.polygon([apex, (x0, y0), (x1, y1)], col)
        # rib line between panels
        cv.thick_line(apex[0], apex[1], (x0 + x1) / 2, (y0 + y1) / 2, 2, (120, 30, 22), 0.35)
    # panel shading: darker toward the outer edges, brighter near centre
    for p in range(panels):
        a0 = math.pi * p / panels
        a1 = math.pi * (p + 1) / panels
        xm = apex[0] - half_w * math.cos((a0 + a1) / 2)
        ym = apex[1] + (hem_y - apex[1]) * math.sin((a0 + a1) / 2) ** 0.9
        shade = 1.0 - 0.16 * abs(xm - 512) / 296
        cv.disc(xm, ym, 26, (0, 0, 0), 0.0)  # no-op, keeps shading loop explicit
    # scalloped hem: small half-discs hanging below the rim
    for p in range(panels):
        a = math.pi * (p + 0.5) / panels
        x = apex[0] - half_w * math.cos(a)
        y = apex[1] + (hem_y - apex[1]) * math.sin(a) ** 0.9
        col = (198, 52, 38) if p % 2 == 0 else (248, 248, 246)
        cv.ellipse(x, y + 4, 40, 16, col)
    # highlight sheen across the canopy
    cv.ellipse(430, 232, 90, 34, (255, 255, 255), 0.18)
    cv.ellipse(470, 216, 46, 18, (255, 255, 255), 0.20)

    # ---- rain: drops bouncing off the canopy, tiny splashes
    rain = [
        (300, 96, 10), (380, 62, 12), (470, 84, 9), (560, 58, 12),
        (648, 92, 10), (716, 66, 11), (250, 150, 9), (780, 140, 9),
        (330, 190, 8), (700, 196, 8),
    ]
    for (x, y, ln) in rain:
        cv.thick_line(x, y, x - 4, y + ln, 2, (150, 170, 196), 0.85)
    # splash crowns where drops hit the canopy
    for (x, y) in [(330, 296), (470, 262), (620, 288), (700, 306)]:
        cv.thick_line(x - 12, y, x - 4, y - 10, 2, (170, 190, 210), 0.9)
        cv.thick_line(x + 12, y, x + 4, y - 10, 2, (170, 190, 210), 0.9)
        cv.thick_line(x, y, x, y - 13, 2, (170, 190, 210), 0.9)
        cv.disc(x, y - 2, 4, (190, 205, 222), 0.9)
    # a few drops sliding off the hem
    for (x, y) in [(252, 372), (780, 368), (330, 384)]:
        cv.thick_line(x, y, x, y + 14, 2, (150, 170, 196), 0.8)

    # ---- steam rising from the coffee, curling around the pole
    for base_x, phase, amp in [(452, 0.0, 16), (512, 1.6, 20), (572, 3.1, 16)]:
        prev = None
        for s in range(0, 121):
            t = s / 120.0
            y = 556 - t * 150
            x = base_x + math.sin(phase + t * 5.2) * amp * t
            if prev is not None:
                cv.thick_line(prev[0], prev[1], x, y, 5, (255, 255, 255), 0.30)
            prev = (x, y)

    # ---- single accessory: one sugar cube on a small plate
    cv.ellipse(846, 842, 84, 20, (180, 180, 186))
    cv.ellipse(846, 838, 84, 20, (246, 246, 248))
    cv.ellipse(846, 838, 64, 14, (222, 222, 226))
    # cube: front face, top face, right face
    cv.polygon([(804, 837), (804, 793), (843, 775), (843, 819)], (250, 250, 252))
    cv.polygon([(804, 793), (843, 775), (876, 793), (837, 811)], (238, 238, 240))
    cv.polygon([(843, 819), (843, 775), (876, 793), (876, 837)], (214, 214, 218))
    # tiny shadow of the cube on its plate
    cv.ellipse(852, 838, 40, 8, (150, 150, 156), 0.5)

    # ---- soft shadow the umbrella casts on the cup's left shoulder
    cv.ellipse(430, 600, 60, 18, (120, 120, 128), 0.12)

    return cv


# ------------------------------------------------------------------ PNG writer
def write_png(cv, path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    cv = render()
    out = os.environ.get("ENTRY_PNG", "/output/entry.png")
    size = write_png(cv, out)
    print(f"wrote {out}: 1024x1024, {size} bytes")
    assert size <= 1048576, "PNG over 1 MiB"


if __name__ == "__main__":
    main()
