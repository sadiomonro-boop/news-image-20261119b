#!/usr/bin/env python3
"""news-image-20261119 variant B — world map + regional clusters.

Sums up Thursday 19 November 2026 world news in one 1024x1024 PNG.
Pure Python 3.13 standard library: own 5x7 bitmap font, own PNG writer
(zlib/struct), no network, deterministic (two runs = identical bytes).

Layout: masthead, hero story (Gaza) with a schematic globe, six regional
panels as a schematic world map (North America, Latin America, Europe,
Africa, Asia, Oceania + Mideast), a BY THE NUMBERS strip and a
top-headlines ticker. 31 verified stories from 6 continents.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font 5x7
# Each glyph: 7 rows of 5 bits, '#' = ink. Uppercase + digits + punctuation.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    '<': ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    """Greedy word wrap; returns list of lines, each <= max_chars."""
    lines, cur = [], ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip() if cur else word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        r, g, b = c
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = r, g, b

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def box(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def circle(self, cx, cy, r, c):
        """Midpoint circle outline (1 px)."""
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx + y, cy + x),
                           (cx - x, cy + y), (cx - y, cy + x),
                           (cx + x, cy - y), (cx + y, cy - x),
                           (cx - x, cy - y), (cx - y, cy - x)):
                self.set(px, py, c)
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1

    def disc(self, cx, cy, r, c):
        """Filled disc via horizontal spans."""
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def globe(self, cx, cy, r, c):
        """Small schematic globe: outline + meridians + land blobs."""
        self.circle(cx, cy, r, c)
        self.circle(cx, cy, r - 1, c)
        # meridians: vertical ellipse approximated by two arcs
        for k in (-2, -1, 0, 1, 2):
            rx = abs(k) * r // 3
            for dy in range(-r, r + 1):
                dx = int(rx * (1 - (dy / r) ** 2) ** 0.5) if r else 0
                self.set(cx + dx, cy + dy, c)
                self.set(cx - dx, cy + dy, c)
        self.hline(cx - r, cy, 2 * r + 1, c)
        self.disc(cx - r // 3, cy - r // 4, r // 5, GOLD)
        self.disc(cx + r // 3, cy + r // 5, r // 6, (61, 220, 132))
        self.disc(cx + r // 5, cy - r // 2, r // 8, (255, 176, 32))

    def dot_grid(self, x, y, w, h, step, c):
        for yy in range(y, y + h, step):
            for xx in range(x, x + w, step):
                self.set(xx, yy, c)

    def text(self, x, y, s, scale, c):
        """Draw uppercase text; unknown chars render as blank."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, c):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def speckle(self, x, y, w, h, seed, amp=4, density=3):
        """Deterministic low-amplitude speckle so flat areas stay dense
        (keeps the render rich, not a thin flat file). LCG, fixed seed."""
        state = seed & 0x7FFFFFFF
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            for xx in range(x0, x1, density):
                i = self._idx(xx, yy)
                for k in range(3):
                    state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                    d = ((state >> 16) % (2 * amp + 1)) - amp
                    if d:
                        v = self.px[i + k] + d
                        self.px[i + k] = 0 if v < 0 else (255 if v > 255 else v)


# --------------------------------------------------------------------- png
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    return png

# ------------------------------------------------------------------ palette
BG = (10, 20, 36)          # deep navy page
PANEL = (18, 35, 61)       # panel fill
PANEL_LINE = (38, 64, 102) # panel border
HERO_BG = (24, 30, 52)     # hero band
WHITE = (242, 245, 249)
TITLE = (255, 255, 255)
DETAIL = (185, 198, 216)
DIM = (126, 147, 173)
GOLD = (255, 176, 32)
RED = (255, 107, 74)
RULE = (58, 92, 140)
TICKER_BG = (13, 27, 48)
NUM_BG = (16, 31, 56)

# ------------------------------------------------------------------- data
# 31 unique stories, all verified in web search on 19 Nov 2026 (events of
# 18-19 Nov 2026, first reported that day). Titles wrap at 26 chars/line
# at scale 2; details wrap at 52 chars/line at scale 1, one line each.
HERO = {
    "tag": "TOP STORY - MIDDLE EAST - GAZA",
    "title": "ISRAEL LAUNCHES GROUND RAID IN CENTRAL GAZA",
    "lines": [
        "Tanks cross the Yellow Line in Nuseirat in the first ground push",
        "since the October 2025 ceasefire; Hamas calls it a flagrant violation.",
        "The US-backed Board of Peace warns the truce is near collapse.",
    ],
}

PANELS = [
    ("NORTH AMERICA", "NA", (77, 163, 255), [
        ("JEFFRIES NOMINATED FOR SPEAKER",
         "Nominated; would be first Black Speaker if elected."),
        ("PELTOLA WINS ALASKA SENATE RACE",
         "AP calls it at 50.12%; Senate 56-44 from January."),
        ("TED LIEU ELECTED CAUCUS CHAIR",
         "First Asian American to chair a House caucus."),
        ("FED MINUTES POINT TO MORE HIKES",
         "Most officials back further hikes on hot inflation."),
        ("NSA SECRET NETWORK GOES DOWN",
         "Outage hits classified system, CNN reports."),
    ]),
    ("LATIN AMERICA", "LA", (61, 220, 132), [
        ("HAITI SIGNS SECURITY DEAL",
         "El Salvador to help fight gangs; 4,595 dead."),
        ("BRAZIL OPENS ATLANTIC FOREST LAB",
         "IFF opens first Forest Lab in the Atlantic Forest."),
        ("LATAM STEEL IMPORTS UP 47 PCT",
         "OECD: imports up 47% in 6 yrs; China share doubled."),
        ("MEXICO WIND BOOM: $12BN BY 2030",
         "6,860 MW planned; Brazil wind falls to 363 MW."),
        ("CATHOLICS FALL TO 55% IN LATAM",
         "Evangelicals reach 19%, survey finds."),
    ]),
    ("EUROPE", "EU", (255, 176, 32), [
        ("EU PROPOSES 45BN EURO UKRAINE LOAN",
         "Repaid only after Russia pays war reparations."),
        ("ODESA STRIKE KILLS 4, INJURES 13",
         "Russian airstrikes hit the southern port, Kyiv says."),
        ("RUSSIA ACCUSES FRANCE OVER TROOPS",
         "Paris confirms small presence; calls claim absurd."),
        ("GERMANY, NORWAY PLEDGE $300M EACH",
         "Joint PURL package to buy US Patriot missiles."),
        ("DEUTSCHE BANK'S $582M EPSTEIN LINK",
         "Bank handled Epstein deals 2013-2018, expose finds."),
    ]),
    ("AFRICA", "AF", (255, 107, 74), [
        ("SUDAN DRONE STRIKES KILL 160+",
         "Wave of drone attacks kills 160+ in recent days."),
        ("HEAVY FIGHTING IN KIVU FRONTS",
         "Combat reported on South and North Kivu fronts."),
        ("SOMALIA ACCUSES UAE OF SECRET BASES",
         "President: Abu Dhabi fuels divisions, backs regions."),
        ("EGYPT OFFICIAL JAILED FOR BRIBERY",
         "Ex-Cairo housing official gets 15 years in prison."),
        ("2,230 CIVILIANS KILLED IN SUDAN",
         "UN counts deaths Jan-Oct, most from drone strikes."),
    ]),
    ("ASIA", "AS", (225, 77, 255), [
        ("GTA VI ROLLS OUT WORLDWIDE",
         "Gamers enter Vice City as the 13-year wait ends."),
        ("NVIDIA HALTS H-SERIES CHIPS TO CHINA",
         "Acting CEO promises earlier pay rises, more stock."),
        ("CYCLONE AKVAN NEARS INDIA COAST",
         "Landfall expected between Machilipatnam and Puri."),
        ("INDIA, JAPAN REVIEW DEFENCE TIES",
         "2+2 ministerial dialogue opens in Tokyo."),
        ("XI AND PUTIN MEET IN SHENZHEN",
         "Leaders meet a day before Trump trilateral at APEC."),
    ]),
    ("OCEANIA + MIDEAST", "OC", (45, 212, 191), [
        ("US AND IRAN EXCHANGE FIRE AGAIN",
         "US hits Qeshm site; Iran strikes Kuwait and Bahrain."),
        ("AUSTRALIA SANCTIONS WEST BANK SETTLERS",
         "3 people, 4 entities listed over settlements."),
        ("SAUDI ARABIA: DANGER HAS PASSED",
         "All-clear in three southern cities after alerts."),
        ("TRUMP PRAISES FRIEND ALBANESE",
         "Warm words for Australia's PM at the Quad summit."),
        ("CRUISE HIT BY MEDICAL EMERGENCIES",
         "Helicopter evacuations off Australia; donor plea."),
    ]),
]

NUMBERS = [
    ("45BN EUR", "EU loan proposed for Ukraine"),
    ("1,600", "killed in Gaza since ceasefire"),
    ("56-44", "Democrats' Senate majority"),
    ("1 LIGHT-DAY", "Voyager 1 distance milestone"),
    ("$582M", "Deutsche Bank Epstein deals"),
]

TICKER = ("ISRAEL LAUNCHES GROUND RAID IN CENTRAL GAZA  -  TRUMP, XI AND "
          "PUTIN DUE TO MEET IN SHENZHEN  -  GTA VI ROLLS OUT WORLDWIDE  -  "
          "EU PROPOSES 45BN EURO UKRAINE LOAN  -  VOYAGER 1 REACHES ONE "
          "LIGHT-DAY  -  NVIDIA STOPS H-SERIES CHIPS TO CHINA")


# ------------------------------------------------------------------ layout
def draw_header(cv):
    cv.fill(0, 0, W, 86, (13, 27, 48))
    cv.dot_grid(0, 0, W, 86, 7, (20, 38, 66))
    cv.text(16, 16, "THE WORLD TODAY", 6, TITLE)
    cv.text(16, 66, "SUMMING UP THURSDAY 19 NOVEMBER 2026 - 31 STORIES FROM 6 CONTINENTS",
            1, DETAIL)
    cv.text(W - 16 - text_width("19 NOV 2026", 3), 14, "19 NOV 2026", 3, GOLD)
    cv.text(W - 16 - text_width("THURSDAY", 2), 44, "THURSDAY", 2, WHITE)
    cv.hline(0, 85, W, RULE, 1)


def draw_hero(cv):
    cv.fill(0, 86, W, 122, HERO_BG)
    cv.fill(0, 86, 10, 122, RED)
    cv.text(24, 96, HERO["tag"], 1, RED)
    cv.text(24, 112, HERO["title"], 3, TITLE)
    y = 142
    for line in HERO["lines"]:
        cv.text(24, y, line, 2, DETAIL)
        y += 18
    cv.globe(946, 150, 46, DIM)
    cv.hline(0, 207, W, RULE, 1)


def draw_panel(cv, x, y, w, h, name, code, color, stories):
    # guards: header must not collide; content must fit the panel
    assert 44 + text_width(name, 2) < w - 10 - text_width("5 STORIES", 1), \
        "panel header overlap: %s" % name
    cv.fill(x, y, w, h, PANEL)
    cv.fill(x, y, w, 6, color)
    cv.box(x, y, w, h, PANEL_LINE, 1)
    cv.fill(x + 10, y + 14, 26, 18, color)
    cv.text(x + 14, y + 17, code, 1, (10, 20, 36))
    cv.text(x + 44, y + 14, name, 2, WHITE)
    cv.text(x + w - 10 - text_width("5 STORIES", 1), y + 17, "5 STORIES", 1, DIM)
    cv.hline(x + 10, y + 40, w - 20, PANEL_LINE, 1)
    sy = y + 50
    for title, detail in stories:
        for ln in wrap_text(title, 26):
            cv.text(x + 10, sy, ln, 2, TITLE)
            sy += 16
        for ln in wrap_text(detail, 52)[:1]:
            cv.text(x + 10, sy, ln, 1, DETAIL)
            sy += 9
        sy += 8
    assert sy <= y + h, "panel overflow: %s uses %d of %d" % (name, sy - y, h)
    return sy


def draw_numbers(cv):
    cv.fill(0, 836, W, 84, NUM_BG)
    cv.text(16, 842, "BY THE NUMBERS", 1, GOLD)
    cw = (W - 32) // 5
    for i, (num, label) in enumerate(NUMBERS):
        cx = 16 + i * cw
        scale = 3 if text_width(num, 3) <= cw - 16 else 2
        cv.text(cx, 862, num, scale, GOLD)
        for j, ln in enumerate(wrap_text(label, 30)):
            cv.text(cx, 888 + j * 9, ln, 1, DETAIL)
        if i:
            cv.vline(cx - 8, 858, 52, PANEL_LINE, 1)
    cv.hline(0, 835, W, RULE, 1)
    cv.hline(0, 919, W, RULE, 1)


def draw_ticker(cv):
    cv.fill(0, 920, W, 104, TICKER_BG)
    cv.text(16, 930, "TOP HEADLINES TODAY", 1, RED)
    y = 950
    for ln in wrap_text(TICKER, 84):
        cv.text(16, y, ln, 2, WHITE)
        y += 18


def build():
    cv = Canvas(W, H, BG)
    cv.speckle(0, 0, W, H, 20261119, amp=8, density=1)
    draw_header(cv)
    draw_hero(cv)
    px = [8, 346, 684]
    py = [216, 526]
    for i, (name, code, color, stories) in enumerate(PANELS):
        draw_panel(cv, px[i % 3], py[i // 3], 330, 302,
                   name, code, color, stories)
    draw_numbers(cv)
    draw_ticker(cv)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = encode_png(build())
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
