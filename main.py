#!/usr/bin/env python3
"""One image summing up the world news of Sunday 22 November 2026.

Pure Python 3 standard library, no network, no third-party packages.
It paints a newspaper front page -- masthead with the date, one lead
story, four more stories in a grid, and a bottom strip with two extra
items -- and writes a deterministic 1024x1024 PNG.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default ./out).
Run it twice and the bytes are identical.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ------------------------------------------------------------------ palette
PAPER = (248, 244, 236)
NAVY = (18, 32, 58)
INK = (30, 33, 41)
GREY = (96, 98, 102)
GOLD = (196, 150, 44)
CARD = (255, 255, 255)
EDGE = (214, 208, 192)
WHITE = (255, 255, 255)
RED = (176, 48, 44)
TEAL = (14, 110, 110)
BLUE = (28, 96, 168)
GREEN = (32, 128, 84)
AMBER = (188, 106, 20)
PURPLE = (104, 72, 150)

# ------------------------------------------------------------------ 5x7 type
# Hand-drawn bitmap letters: 7 rows of 5 cells, "#" paints, "." leaves blank.
GLYPHS = {
    "A": ("..#..", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "(": ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ")": (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "*": (".....", "#...#", ".#.#.", "#####", ".#.#.", "#...#", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}


class Screen:
    """A plain RGB canvas backed by one bytearray."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            base = (yy * self.w + x) * 3
            self.buf[base:base + w * 3] = bytes(color) * w

    def rule_h(self, x, y, length, color, thick=1):
        self.fill_rect(x, y, length, thick, color)

    def rule_v(self, x, y, length, color, thick=1):
        self.fill_rect(x, y, thick, length, color)

    def seg(self, x0, y0, x1, y1, color):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx + dy, x0, y0
        while True:
            self.px(x, y, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, color)

    def ring(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if abs(d2 - r * r) <= r:
                    self.px(xx, yy, color)

    def curve(self, cx, cy, r, a0, a1, color):
        steps = max(8, int(r * 3))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.px(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), color)

    def glyph_text(self, x, y, s, scale, color):
        """One line of capitals; returns the pixel width drawn."""
        s = s.upper()
        cx = x
        for ch in s:
            g = GLYPHS.get(ch, GLYPHS[" "])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def center_text(self, cx, y, s, scale, color):
        self.glyph_text(cx - self.text_w(s, scale) // 2, y, s, scale, color)


def fit_lines(text, max_px, scale):
    """Greedy wrap by rendered pixel width, not by character count."""
    per_char = 6 * scale
    out = []
    for chunk in text.split("\n"):
        words = chunk.split()
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if len(trial) * per_char - scale <= max_px:
                cur = trial
            else:
                if cur:
                    out.append(cur)
                cur = word
        if cur:
            out.append(cur)
    return out


# ------------------------------------------------------------------ the day
# Six stories of Sunday 22 November 2026, as reported that day
# (Xinhua, AFP via Manila Times, SCMP, Reuters via Manila Times).
# Fields: kicker, headline, body, accent colour, pictogram.
LEAD = ("1 - AFRICA - G20 SUMMIT", "G20 OPENS IN AFRICA",
        "Leaders gather in Johannesburg for the first G20 summit ever held "
        "on African soil. Theme: Solidarity, Equality, Sustainability. "
        "The United States stays away.",
        NAVY, "globe")

GRID = [
    ("2 - TECH - NVIDIA", "NVIDIA FACES US PROBE",
     "A US regulator is to probe Nvidia's accounting, media report, as "
     "turmoil deepens around the AI chip giant.",
     RED, "chip"),
    ("3 - NORTH AMERICA - DEFENCE", "US CURBS CANADA DEFENCE TIES",
     "The Pentagon moves to restrict US-Canada defence ties as tensions "
     "between the two neighbours grow.",
     BLUE, "shield"),
    ("4 - MIDDLE EAST - YEMEN", "HOUTHIS STRIKE RIYADH",
     "Yemen's Houthis launch revenge strikes on the Saudi capital after a "
     "Saudi-led coalition operation.",
     AMBER, "rocket"),
    ("5 - LATIN AMERICA - QUAKE", "6.7 QUAKE HITS PERU",
     "A magnitude 6.7 earthquake strikes Peru. No deaths are reported.",
     TEAL, "quake"),
]

STRIP = ("6 - MEXICO - CARTELS", "MEXICO CAPTURES 'CHAPO ISIDRO'",
         "Drug kingpin Fausto Isidro Meza, on the FBI's most-wanted list, "
         "is captured in a deadly firefight.",
         PURPLE, "star")

ALSO = ("ALSO: COP31 TALKS IN OVERTIME; BRAZIL TOWN CLEARS RUBBLE AFTER DEADLY STORM.")


def draw_pic(cv, name, x, y, size, color):
    """Pictogram inside a size x size box at (x, y)."""
    cx, cy = x + size // 2, y + size // 2
    if name == "globe":
        cv.ring(cx, cy, 30, color)
        cv.rule_h(cx - 30, cy, 61, color)
        cv.rule_h(cx - 22, cy - 18, 45, color)
        cv.rule_h(cx - 22, cy + 18, 45, color)
        cv.curve(cx, cy, 14, 0, 6.3, color)
        cv.curve(cx, cy, 30, 0.6, 2.4, color)
    elif name == "chip":
        cv.fill_rect(cx - 26, cy - 26, 52, 52, color)
        cv.fill_rect(cx - 15, cy - 15, 30, 30, PAPER)
        cv.fill_rect(cx - 7, cy - 7, 14, 14, color)
        for k in (-18, 0, 18):
            cv.rule_h(cx - 34, cy + k, 8, color)
            cv.rule_h(cx + 26, cy + k, 8, color)
            cv.rule_v(cx + k, cy - 34, 8, color)
            cv.rule_v(cx + k, cy + 26, 8, color)
    elif name == "shield":
        cv.seg(cx, cy - 30, cx + 26, cy - 18, color)
        cv.seg(cx + 26, cy - 18, cx + 26, cy + 8, color)
        cv.seg(cx + 26, cy + 8, cx, cy + 30, color)
        cv.seg(cx, cy + 30, cx - 26, cy + 8, color)
        cv.seg(cx - 26, cy + 8, cx - 26, cy - 18, color)
        cv.seg(cx - 26, cy - 18, cx, cy - 30, color)
        cv.seg(cx - 12, cy, cx - 3, cy + 10, color)
        cv.seg(cx - 3, cy + 10, cx + 14, cy - 10, color)
    elif name == "rocket":
        cv.seg(cx - 22, cy + 22, cx + 14, cy - 14, color)
        cv.seg(cx + 14, cy - 14, cx + 26, cy - 26, color)
        cv.seg(cx + 26, cy - 26, cx + 10, cy - 22, color)
        cv.seg(cx + 14, cy - 14, cx + 22, cy - 10, color)
        cv.seg(cx - 22, cy + 22, cx - 26, cy + 26, color)
        cv.seg(cx - 26, cy + 26, cx - 10, cy + 26, color)
        cv.seg(cx - 26, cy + 26, cx - 22, cy + 22, color)
        cv.disc(cx - 26, cy + 28, 3, color)
    elif name == "quake":
        pts = [(cx - 30, cy), (cx - 20, cy), (cx - 14, cy - 18),
               (cx - 6, cy + 18), (cx + 2, cy - 24), (cx + 10, cy + 12),
               (cx + 18, cy), (cx + 30, cy)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cv.seg(ax, ay, bx, by, color)
        cv.disc(cx - 30, cy, 3, color)
        cv.disc(cx + 30, cy, 3, color)
    elif name == "star":
        pts = []
        for i in range(10):
            r = 28 if i % 2 == 0 else 12
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
        for i in range(10):
            cv.seg(pts[i][0], pts[i][1], pts[(i + 1) % 10][0],
                   pts[(i + 1) % 10][1], color)
        cv.disc(cx, cy, 4, color)


def card_frame(cv, x, y, w, h, accent):
    cv.fill_rect(x, y, w, h, CARD)
    cv.fill_rect(x, y, w, 8, accent)
    cv.rule_h(x, y + h - 1, w, EDGE)
    cv.rule_v(x, y, h, EDGE)
    cv.rule_v(x + w - 1, y, h, EDGE)


def paint():
    cv = Screen(W, H, PAPER)

    # Masthead.
    cv.fill_rect(0, 0, W, 140, NAVY)
    cv.center_text(W // 2, 22, "THE WORLD IN ONE DAY", 5, WHITE)
    cv.center_text(W // 2, 84, "SUNDAY 22 NOVEMBER 2026", 3, GOLD)
    cv.fill_rect(0, 140, W, 5, GOLD)
    cv.center_text(W // 2, 160, "SIX STORIES FROM AROUND THE GLOBE - ONE DAY",
                   2, NAVY)

    # Lead story, full width.
    lx, ly, lw, lh = 24, 192, 976, 168
    kicker, head, body, accent, pic = LEAD
    card_frame(cv, lx, ly, lw, lh, accent)
    cv.glyph_text(lx + 20, ly + 24, kicker, 2, accent)
    draw_pic(cv, pic, lx + lw - 20 - 96, ly + 24, 96, accent)
    for i, line in enumerate(fit_lines(head, lw - 160, 4)[:2]):
        cv.glyph_text(lx + 20, ly + 56 + i * 34, line, 4, NAVY)
    for i, line in enumerate(fit_lines(body, lw - 40, 2)[:3]):
        cv.glyph_text(lx + 20, ly + 104 + i * 20, line, 2, INK)

    # Four stories in a 2 x 2 grid.
    gx, gy, gw, gh, gap = 24, 372, 478, 216, 20
    for idx, (kicker, head, body, accent, pic) in enumerate(GRID):
        col, row = idx % 2, idx // 2
        x = gx + col * (gw + gap)
        y = gy + row * (gh + 16)
        card_frame(cv, x, y, gw, gh, accent)
        cv.glyph_text(x + 18, y + 22, kicker, 2, accent)
        draw_pic(cv, pic, x + gw - 18 - 64, y + 14, 64, accent)
        for i, line in enumerate(fit_lines(head, gw - 110, 3)[:2]):
            cv.glyph_text(x + 18, y + 52 + i * 26, line, 3, NAVY)
        for i, line in enumerate(fit_lines(body, gw - 36, 2)[:3]):
            cv.glyph_text(x + 18, y + 122 + i * 20, line, 2, INK)

    # Bottom strip: sixth story plus one more item.
    sx, sy, sw, sh = 24, 836, 976, 108
    kicker, head, body, accent, pic = STRIP
    card_frame(cv, sx, sy, sw, sh, accent)
    cv.glyph_text(sx + 18, sy + 16, kicker + "  -  " + head, 2, accent)
    for i, line in enumerate(fit_lines(body, sw - 36, 2)[:2]):
        cv.glyph_text(sx + 18, sy + 44 + i * 20, line, 2, INK)
    for i, line in enumerate(fit_lines(ALSO, sw - 36, 2)[:1]):
        cv.glyph_text(sx + 18, sy + 86, line, 2, GREY)

    # Footer.
    cv.center_text(W // 2, 962,
                   "ALL STORIES HAPPENED OR WERE FIRST REPORTED ON 22 NOVEMBER 2026",
                   2, GREY)
    cv.center_text(W // 2, 988, "MAKE.FUN - WORLD NEWS IN ONE IMAGE", 2, NAVY)
    return cv


# ------------------------------------------------------------------ PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)  # scanline filter: none
        raw += cv.buf[yy * cv.w * 3:(yy + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    save_png(paint(), os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
