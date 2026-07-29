"""Generate the launcher's app/window icon (original art - a gold honeycomb
trefoil on a dark rounded square, matching the launcher theme; deliberately
NOT the game's copyrighted XBLA tile art).

Outputs, next to this script:
  banjotooie.png  - 512x512, used for the tkinter window icon (both OSes) and
                    as a Linux app icon (.desktop / Steam Non-Steam-game art).
  banjotooie.ico  - multi-size Windows icon embedded into the .exe by
                    build_release.py (--icon).

Run:  python make_icon.py     (needs  pip install pillow)
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024  # master resolution


def _vgrad(size, top, bot):
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / (h - 1)
        col.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return col.resize((w, h))


def _hexagon(cx, cy, r, rot=-math.pi / 2):
    return [(cx + r * math.cos(rot + k * math.pi / 3),
             cy + r * math.sin(rot + k * math.pi / 3)) for k in range(6)]


def build_master() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded-square background with a subtle top-to-bottom gradient.
    margin = 36
    bg = _vgrad((S, S), (0x33, 0x29, 0x1f), (0x1a, 0x15, 0x11))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [margin, margin, S - margin, S - margin], radius=190, fill=255)
    img.paste(bg, (0, 0), mask)

    # Gold gradient sheen shared by all hexagons.
    gold = _vgrad((S, S), (0xff, 0xd9, 0x66), (0xdd, 0x90, 0x18))
    outline = (0x6f, 0x49, 0x0c)
    highlight = (0xff, 0xe9, 0xa6)

    # Honeycomb trefoil: three pointy-top hexagons that mutually share edges,
    # leaving a small triangular gap in the middle.
    R = 232
    cx, cy = S / 2, S / 2 - 8
    centers = [
        (cx, cy - R),
        (cx - R * math.sqrt(3) / 2, cy + R / 2),
        (cx + R * math.sqrt(3) / 2, cy + R / 2),
    ]
    for hx, hy in centers:
        pts = _hexagon(hx, hy, R)
        m = Image.new("L", (S, S), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        img.paste(gold, (0, 0), m)
        d2 = ImageDraw.Draw(img)
        d2.polygon(pts, outline=outline, width=11)
        # thin inner highlight hexagon for a little depth
        d2.polygon(_hexagon(hx, hy, R - 34), outline=highlight, width=6)

    return img


def main():
    master = build_master()
    png = master.resize((512, 512), Image.LANCZOS)
    png.save(os.path.join(HERE, "banjotooie.png"))
    master.save(os.path.join(HERE, "banjotooie.ico"),
                sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("wrote banjotooie.png (512) and banjotooie.ico (16-256)")


if __name__ == "__main__":
    main()
