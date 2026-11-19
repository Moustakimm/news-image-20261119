#!/usr/bin/env python3
"""Renders entry.png (1024x1024) for the news-image-20261119 bounty.

Dense broadsheet format: 45 real stories from Thursday 19 November 2026 —
giant date masthead, a UTC timeline strip, 3 illustrated lead stories,
10 illustrated medium stories, a 32-item numbered list, a pinned world map,
a date-check box and a sources line. Same format as the winning entries of
the sister 17 November competition (top 10 all used it).

Every story was checked against reporting from 19 November 2026 (see
CAPTION.md). Nothing is invented: no event, quote, number or location.

Run:  python3 render.py        (writes ./entry.png beside this file)
Requires Pillow and the DejaVu fonts (standard on this machine).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (25, 23, 19)
BODY = (43, 40, 34)
RED = (158, 42, 32)
RED_DK = (120, 30, 24)
NAVY = (29, 58, 95)
GOLD = (201, 123, 45)
CREAM2 = (238, 231, 214)
SKY = (178, 205, 224)
SEA = (140, 175, 200)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Region colours (used for tags, number dots and map pins).
EUROPE = (31, 73, 125)
MIDDLE_EAST = (176, 106, 28)
ASIA = (120, 58, 138)
AMERICAS = (172, 32, 32)
AFRICA = (32, 118, 58)
OCEANIA = (0, 128, 138)
GLOBAL = (74, 74, 74)

REGION_NAME = {
    EUROPE: "EUROPE", MIDDLE_EAST: "MIDDLE EAST", ASIA: "ASIA",
    AMERICAS: "AMERICAS", AFRICA: "AFRICA", OCEANIA: "OCEANIA",
    GLOBAL: "GLOBAL",
}


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, text, f, max_w):
    """Greedy word wrap; returns list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, lines, f, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += leading
    return y


def centered(draw, cx, y, s, f, fill, tracking=0):
    """Draw text centred on cx, with optional extra tracking between chars."""
    if tracking:
        w = sum(draw.textlength(ch, font=f) + tracking for ch in s) - tracking
        x = cx - w / 2
        for ch in s:
            draw.text((x, y), ch, font=f, fill=fill)
            x += draw.textlength(ch, font=f) + tracking
    else:
        w = draw.textlength(s, font=f)
        draw.text((cx - w / 2, y), s, font=f, fill=fill)


def fit_font(draw, s, path, start, max_w):
    """Largest size <= start whose text fits max_w."""
    size = start
    while size > 10 and draw.textlength(s, font=font(path, size)) > max_w:
        size -= 1
    return font(path, size)


def num_dot(draw, x, y, n, color, r=7):
    """Numbered circle used for story numbers."""
    draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
    s = str(n)
    f = font(SANS_B, 9 if len(s) < 2 else 8)
    w = draw.textlength(s, font=f)
    draw.text((x - w / 2, y - 5 if len(s) < 2 else y - 4), s, font=f,
              fill=(255, 255, 255))


# ---------------------------------------------------------------- data
# Featured stories: (num, region, tag, headline, summary, label, scene, lon, lat)
LEADS = [
    (1, ASIA, "ASIA · DIPLOMACY",
     "Trump, Xi and Putin hold first three-way summit in Shenzhen",
     "After 90 minutes at Kylin Villa the three leaders issue a joint "
     "declaration: talks on cutting nuclear risks, and more oil supply.",
     "CONFIRMED — XINHUA / AP", "summit", (114.1, 22.5)),
    (2, ASIA, "ASIA · INTERNATIONAL LAW",
     "World court: Myanmar committed genocide against the Rohingya",
     "The ICJ in The Hague rules the 2017 crackdown was state-sponsored "
     "genocide — the first ruling of its kind by the UN's top court.",
     "CONFIRMED — ICJ", "court", (4.3, 52.0)),
    (3, ASIA, "SOUTH ASIA · WEATHER",
     "Cyclone Akvan bears down on Odisha; 105,304 evacuated",
     "The severe storm is due to cross the coast near Gopalpur by Friday "
     "noon, winds 90–100 km/h gusting to 110; 9,299 shelters are ready.",
     "CONFIRMED — IMD", "cyclone", (85.0, 19.0)),
]

MEDIUM = [
    (4, MIDDLE_EAST, "MIDDLE EAST · CONFLICT",
     "Houthi attacks damage Riyadh's tallest tower",
     "The wealth fund HQ tower is damaged as new attacks are reported.",
     "AFP", "tower"),
    (5, EUROPE, "EUROPE · UKRAINE WAR",
     "Crimea bridge hit a third time this week",
     "Moscow blames Kyiv; Kyiv claimed the two earlier strikes this week.",
     "CLAIM — MOSCOW", "bridge"),
    (6, GLOBAL, "GLOBAL · MARKETS",
     "Anthropic starts trading after record $81.3bn IPO",
     "Priced at $83, above the $70–78 range — the biggest listing on record.",
     "REUTERS / CNBC", "ipo"),
    (7, AMERICAS, "US · MARKETS",
     "Wall Street ends split; Dow down 1.1%",
     "Dow falls 561 points; S&P drops a fifth day; Nasdaq up 0.4%.",
     "CNBC", "markets"),
    (8, MIDDLE_EAST, "MIDDLE EAST · GAZA",
     "Israeli tanks enter Gaza; hospital strike kills six",
     "Troops cross near Nuseirat; a strike on Nasser Hospital kills six.",
     "AP", "tank"),
    (9, GLOBAL, "GLOBAL · CLIMATE",
     "COP31 final stage: fossil-fuel split unresolved",
     "Antalya split over 'transition away' versus a stronger phase-out.",
     "REUTERS", "climate"),
    (10, ASIA, "ASIA · POLITICS",
     "Bangladesh hit by opposition shutdown and violence",
     "The Awami League acts after Hasina's papers request is refused.",
     "AP", "protest"),
    (11, AMERICAS, "AMERICAS · DIPLOMACY",
     "US and Venezuela sign deal to restore military ties",
     "Signed as the US defence chief visits Caracas after years of rupture.",
     "AP", "handshake"),
    (12, GLOBAL, "GLOBAL · CULTURE",
     "GTA VI launches worldwide after a 13-year wait",
     "Rockstar's return to Leonida and Vice City arrives on PS5 and Xbox.",
     "ROCKSTAR / NDTV", "game"),
    (13, ASIA, "ASIA · TECHNOLOGY",
     "China seeks advanced Nvidia chips for AI weapons",
     "Beijing seeks the chips despite US curbs, as the AI race runs on.",
     "REPORT", "chip"),
]

# Numbered list (14-45): (num, region, text)
LIST_ITEMS = [
    (14, EUROPE, "Russian military plane crashes; all 19 aboard killed"),
    (15, MIDDLE_EAST, "Three oil tankers catch fire after hitting mines east of Hormuz"),
    (16, EUROPE, "LPG tanker Gas Husky sinks off Bulgaria after being hit"),
    (17, ASIA, "South Korea court orders retrial of ex-PM Han"),
    (18, EUROPE, "Spain: snap-vote winners may stifle economy, analysts warn"),
    (19, ASIA, "Trump and Marcos hail alliance, pledge close trade ties"),
    (20, MIDDLE_EAST, "US reissues security warnings for Bahrain and Saudi"),
    (21, EUROPE, "France jails three women for joining ISIS in Syria"),
    (22, AMERICAS, "Miami court convicts pastor over 2021 killing of Haiti's president"),
    (23, GLOBAL, "Van Gogh sells for a record $190.4m after ownership dispute"),
    (24, MIDDLE_EAST, "Israeli parliament elects new Knesset speaker"),
    (25, OCEANIA, "Rio Tinto pledges $250m over Panguna mine damage"),
    (26, OCEANIA, "Tonga declares emergency as El Niño drought worsens"),
    (27, OCEANIA, "Palau, FSM and Marshall Islands get $450m US boost"),
    (28, GLOBAL, "Nearly one in four children now live in conflict zones"),
    (29, AMERICAS, "236 arrested anti-Trump protesters freed"),
    (30, AFRICA, "Dozens missing after migrant boat sinks off Senegal"),
    (31, ASIA, "Ally of actor-politician Vijay visits Prabhakaran's home"),
    (32, GLOBAL, "Islam set to be world's largest religion by 2035, report says"),
    (33, AMERICAS, "Ageing grids and AI fixes behind wave of US outages"),
    (34, AMERICAS, "Alleged Russian agent held over surveillance of US tech firm"),
    (35, GLOBAL, "El Niño exceptionally strong; food and power prices to rise"),
    (36, EUROPE, "Prince Harry: 'big separation' between US government and public on Ukraine"),
    (37, AMERICAS, "Trump asks Supreme Court to block protections for Venezuelan migrants"),
    (38, AMERICAS, "Alaska: Begich keeps sole House seat after ranked count"),
    (39, EUROPE, "Chelsea women edge PSG 1-0; four clubs reach knockouts"),
    (40, EUROPE, "Real Madrid women 3-1 Inter; Man City 2-0 Häcken; Juventus 2-0 Leuven"),
    (41, AMERICAS, "Walmart beats estimates, raises outlook a third time"),
    (42, AMERICAS, "US Army offers soldiers GTA VI break to re-enlist; 43 accept"),
    (43, GLOBAL, "48 pepper genomes map how chillies were domesticated"),
    (44, GLOBAL, "Nepal wins solidarity award; Norway named Fossil of the Day"),
    (45, GLOBAL, "Voyager 1 is now one light-day from Earth — a reply takes two days"),
]

TIMELINE = [
    ("Overnight", "Crimea bridge hit again"),
    ("01:50 UTC", "APEC opens in Shenzhen"),
    ("~02:00 UTC", "Anthropic IPO priced at $83"),
    ("08:16 UTC", "Trilateral under way"),
    ("10:55 UTC", "Joint declaration issued"),
    ("Evening", "Riyadh tower damaged"),
]

DATE_CHECK = ("Left out on purpose: the US strike on Qeshm Island and the Crimea "
              "bridge's second strike (both 17 Nov). Not yet: Cyclone Akvan's "
              "landfall, due Friday noon.")
FOOTER = ("Every story here happened or was first reported on Thursday 19 November "
          "2026. Contested claims are marked as claims.")
SOURCES = ("Sources: AP, Reuters, AFP, DPA, Nikkei Asia, USA Today, The Hindu, "
           "IMD, CNBC, The Japan Times, Korea Herald, NDTV, UEFA. Original drawings.")

# ------------------------------------------------------------- illustrations
def _flag_us(d, x, y, w, h):
    for i in range(7):
        d.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                    fill=(178, 34, 52) if i % 2 == 0 else (255, 255, 255))
    d.rectangle([x, y, x + w * 0.4, y + h * 4 / 7], fill=(30, 50, 110))


def _flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    for sx, sy, r in [(0.2, 0.25, 3), (0.45, 0.2, 2), (0.5, 0.4, 2),
                      (0.35, 0.5, 2)]:
        d.ellipse([x + sx * w - r, y + sy * h - r, x + sx * w + r,
                   y + sy * h + r], fill=(255, 222, 0))


def _flag_ru(d, x, y, w, h):
    for i, c in enumerate([(255, 255, 255), (0, 60, 160), (220, 30, 30)]):
        d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)


def _label_bar(d, x, y, w, text, bg=(25, 23, 19)):
    f = font(SANS_B, 9)
    d.rectangle([x, y, x + w, y + 14], fill=bg)
    d.text((x + 5, y + 3), text, font=f, fill=(255, 255, 255))


def _draw_scene(d, x, y, w, h, kind, label=""):
    """Draw a small iconic illustration inside (x, y, w, h)."""
    if kind == "summit":
        d.rectangle([x, y, x + w, y + h], fill=(232, 222, 196))
        d.rectangle([x, y, x + w, y + 26], fill=(120, 60, 60))
        d.text((x + 8, y + 6), "SHENZHEN · KYLIN VILLA", font=font(SANS_B, 10),
               fill=(255, 255, 255))
        # three flags on poles
        for i, fl in enumerate((_flag_us, _flag_cn, _flag_ru)):
            fx = x + 30 + i * (w - 60) // 2
            d.line([fx + 14, y + 30, fx + 14, y + h - 34], fill=(60, 50, 40),
                   width=2)
            fl(d, fx, y + 32, 28, 18)
        # table + three seated figures
        d.rectangle([x + 16, y + h - 34, x + w - 16, y + h - 12],
                    fill=(120, 80, 50))
        for i in range(3):
            cx = x + 45 + i * (w - 90) // 2
            d.ellipse([cx - 9, y + h - 56, cx + 9, y + h - 38],
                      fill=(40, 40, 40))
            d.rectangle([cx - 12, y + h - 40, cx + 12, y + h - 34],
                        fill=(40, 40, 40))
    elif kind == "court":
        d.rectangle([x, y, x + w, y + h], fill=(214, 206, 188))
        d.polygon([(x + w / 2, y + 8), (x + 18, y + 34), (x + w - 18, y + 34)],
                  fill=(150, 130, 110))
        for i in range(4):
            cx = x + 30 + i * (w - 60) // 3
            d.rectangle([cx - 6, y + 36, cx + 6, y + h - 18],
                        fill=(240, 234, 220))
        d.rectangle([x + 12, y + h - 18, x + w - 12, y + h - 8],
                    fill=(150, 130, 110))
        # scales of justice
        sx, sy = x + w - 52, y + 44
        d.line([sx, sy, sx, sy + 26], fill=(90, 70, 40), width=2)
        d.line([sx - 14, sy + 4, sx + 14, sy + 4], fill=(90, 70, 40), width=2)
        d.ellipse([sx - 18, sy + 20, sx - 8, sy + 28], fill=(180, 140, 60))
        d.ellipse([sx + 8, sy + 20, sx + 18, sy + 28], fill=(180, 140, 60))
    elif kind == "cyclone":
        d.rectangle([x, y, x + w, y + h], fill=(150, 180, 205))
        d.rectangle([x, y + h - 26, x + w, y + h], fill=(90, 130, 90))
        cx, cy = x + w * 0.42, y + h * 0.42
        for r in (34, 26, 18, 10):
            d.arc([cx - r, cy - r, cx + r, cy + r], 20, 300,
                  fill=(255, 255, 255), width=3)
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 255, 255))
        for i in range(6):
            rx = x + 12 + i * 14
            d.line([rx, y + 8, rx - 4, y + 22], fill=(220, 230, 240), width=2)
        _label_bar(d, x, y + h - 14, w, "LANDFALL DUE FRIDAY NOON")
    elif kind == "tower":
        d.rectangle([x, y, x + w, y + h], fill=(226, 196, 150))
        d.rectangle([x, y + h - 30, x + w, y + h], fill=(90, 90, 100))
        tx = x + w // 2 - 16
        d.rectangle([tx, y + 14, tx + 32, y + h - 30], fill=(40, 48, 70))
        for r in range(6):
            for c in range(2):
                if (r + c) % 2 == 0:
                    d.rectangle([tx + 4 + c * 14, y + 20 + r * 9,
                                 tx + 12 + c * 14, y + 26 + r * 9],
                                fill=(255, 210, 90))
        d.ellipse([tx + 26, y + 2, tx + 46, y + 20], fill=(120, 120, 120))
        d.ellipse([tx + 34, y - 6, tx + 52, y + 10], fill=(150, 150, 150))
        d.rectangle([x + 12, y + h - 52, x + 34, y + h - 30], fill=(70, 70, 80))
        d.rectangle([x + w - 34, y + h - 46, x + w - 12, y + h - 30],
                    fill=(70, 70, 80))
        _label_bar(d, x, y + h - 14, w, "PIF TOWER · RIYADH")
    elif kind == "bridge":
        d.rectangle([x, y, x + w, y + h], fill=(168, 198, 220))
        d.rectangle([x, y + h * 0.55, x + w, y + h], fill=(52, 96, 140))
        d.rectangle([x, y + h * 0.42, x + w, y + h * 0.5], fill=(70, 70, 70))
        for px in (x + w * 0.2, x + w * 0.55, x + w * 0.85):
            d.rectangle([px - 4, y + h * 0.5, px + 4, y + h * 0.8],
                        fill=(50, 50, 50))
        # broken span + blast
        bx, by = x + w * 0.68, y + h * 0.42
        d.polygon([(bx, by), (bx + 26, by - 4), (bx + 14, by + 12)],
                  fill=(90, 90, 90))
        for ang in range(0, 360, 45):
            ex = bx + 12 + 16 * math.cos(math.radians(ang))
            ey = by - 14 + 12 * math.sin(math.radians(ang))
            d.line([bx + 12, by - 14, ex, ey], fill=(255, 140, 0), width=3)
        d.ellipse([bx + 2, by - 24, bx + 22, by - 4], fill=(255, 200, 60))
        _label_bar(d, x, y + h - 14, w, "KERCH STRAIT · THIRD STRIKE")
    elif kind == "ipo":
        d.rectangle([x, y, x + w, y + h], fill=(18, 40, 32))
        pts = [(x + 8, y + h - 22), (x + w * 0.3, y + h - 40),
               (x + w * 0.55, y + h - 30), (x + w * 0.8, y + h - 52),
               (x + w - 10, y + 18)]
        d.line(pts, fill=(80, 220, 120), width=3, joint="curve")
        d.polygon([(x + w - 22, y + 12), (x + w - 6, y + 12), (x + w - 14, y + 26)],
                  fill=(80, 220, 120))
        d.text((x + 10, y + 8), "$83", font=font(SANS_B, 26),
               fill=(255, 255, 255))
        d.text((x + 10, y + h - 18), "ANT · NASDAQ", font=font(SANS_B, 9),
               fill=(160, 220, 170))
    elif kind == "markets":
        d.rectangle([x, y, x + w, y + h], fill=(240, 234, 220))
        pts = [(x + 8, y + 14), (x + w * 0.3, y + 26), (x + w * 0.55, y + 20),
               (x + w * 0.8, y + 44), (x + w - 10, y + h - 16)]
        d.line(pts, fill=(172, 32, 32), width=3, joint="curve")
        d.polygon([(x + w - 22, y + h - 22), (x + w - 6, y + h - 22),
                   (x + w - 14, y + h - 8)], fill=(172, 32, 32))
        d.text((x + 8, y + 6), "DOW −1.1%", font=font(SANS_B, 13),
               fill=(172, 32, 32))
    elif kind == "tank":
        d.rectangle([x, y, x + w, y + h], fill=(214, 196, 160))
        d.rectangle([x, y + h - 24, x + w, y + h], fill=(180, 160, 120))
        for bx in (x + 8, x + w * 0.55):
            d.rectangle([bx, y + 12, bx + w * 0.34, y + h - 24],
                        fill=(150, 140, 120))
            d.rectangle([bx + 6, y + 18, bx + w * 0.34 - 6, y + 26],
                        fill=(90, 100, 110))
        tx = x + w * 0.42
        d.rectangle([tx, y + h - 44, tx + 52, y + h - 24], fill=(70, 78, 60))
        d.rectangle([tx + 12, y + h - 56, tx + 40, y + h - 44],
                    fill=(70, 78, 60))
        d.line([tx + 40, y + h - 52, tx + 66, y + h - 58], fill=(70, 78, 60),
               width=4)
        d.ellipse([tx + 4, y + h - 24, tx + 16, y + h - 14], fill=(40, 40, 40))
        d.ellipse([tx + 36, y + h - 24, tx + 48, y + h - 14], fill=(40, 40, 40))
        _label_bar(d, x, y + h - 14, w, "NUSEIRAT · GAZA")
    elif kind == "climate":
        d.rectangle([x, y, x + w, y + h], fill=(190, 214, 228))
        cx, cy, r = x + w * 0.32, y + h * 0.5, 26
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 140, 190))
        d.ellipse([cx - 14, cy - 16, cx + 2, cy - 2], fill=(90, 170, 90))
        d.ellipse([cx + 2, cy + 4, cx + 16, cy + 16], fill=(90, 170, 90))
        # thermometer
        tx = x + w * 0.72
        d.rectangle([tx, y + 8, tx + 10, y + h - 18], fill=(255, 255, 255),
                    outline=(160, 40, 30), width=1)
        d.rectangle([tx + 2, y + h - 26, tx + 8, y + h - 20],
                    fill=(200, 50, 40))
        d.ellipse([tx - 3, y + h - 20, tx + 13, y + h - 6], fill=(200, 50, 40))
        d.text((x + w - 34, y + 6), "1.5°C", font=font(SANS_B, 10),
               fill=(160, 40, 30))
    elif kind == "protest":
        d.rectangle([x, y, x + w, y + h], fill=(228, 216, 196))
        for i in range(7):
            cx = x + 16 + i * (w - 32) // 6
            d.ellipse([cx - 8, y + h - 34, cx + 8, y + h - 18],
                      fill=(90, 70, 60))
            d.rectangle([cx - 10, y + h - 20, cx + 10, y + h - 10],
                        fill=(60 + i * 8, 60, 70))
        d.rectangle([x + w * 0.2, y + 8, x + w * 0.46, y + 26],
                    fill=(255, 255, 255), outline=(150, 40, 30), width=2)
        d.rectangle([x + w * 0.58, y + 12, x + w * 0.84, y + 28],
                    fill=(255, 255, 255), outline=(30, 60, 120), width=2)
    elif kind == "handshake":
        d.rectangle([x, y, x + w, y + h], fill=(222, 214, 196))
        for i, fl in enumerate((_flag_us,)):
            fl(d, x + 14, y + 10, 30, 19)
        # Venezuela tricolour
        vx = x + w - 44
        for i, c in enumerate([(255, 204, 0), (0, 60, 160), (220, 30, 30)]):
            d.rectangle([vx, y + 10 + i * 19 // 3, vx + 30, y + 10 + (i + 1) * 19 // 3],
                        fill=c)
        # clasped hands: two forearms + clasp
        d.polygon([(x + 18, y + h - 12), (x + w * 0.42, y + h - 34),
                   (x + w * 0.42, y + h - 22), (x + 18, y + h - 2)],
                  fill=(200, 170, 140))
        d.polygon([(x + w - 18, y + h - 12), (x + w * 0.58, y + h - 34),
                   (x + w * 0.58, y + h - 22), (x + w - 18, y + h - 2)],
                  fill=(180, 140, 110))
        d.ellipse([x + w * 0.42, y + h - 40, x + w * 0.58, y + h - 20],
                  fill=(210, 180, 150))
    elif kind == "game":
        d.rectangle([x, y, x + w, y + h], fill=(120, 60, 140))
        d.ellipse([x + w * 0.62, y + 2, x + w * 0.62 + 40, y + 42],
                  fill=(255, 180, 80))
        d.rectangle([x, y + h - 12, x + w, y + h], fill=(40, 30, 60))
        for i, hf in enumerate((0.30, 0.45, 0.22, 0.38)):
            bx = x + 10 + i * (w - 20) // 4
            bh = int(h * hf)
            d.rectangle([bx, y + h - 12 - bh, bx + (w - 20) // 5,
                         y + h - 12], fill=(60, 40, 80))
        for px in (x + 16, x + w - 26):
            d.line([px, y + h - 12, px, y + h - 28], fill=(40, 90, 50),
                   width=3)
            for ang in range(-60, 61, 30):
                ex = px + 12 * math.cos(math.radians(ang - 90))
                ey = y + h - 28 + 10 * math.sin(math.radians(ang - 90))
                d.line([px, y + h - 28, ex, ey], fill=(40, 120, 60), width=2)
        _label_bar(d, x, y + h - 14, w, "LEONIDA · VICE CITY")
    elif kind == "chip":
        d.rectangle([x, y, x + w, y + h], fill=(24, 30, 44))
        cx, cy = x + w // 2, y + h // 2
        for i in range(4):
            d.line([x + 8, y + 10 + i * 12, cx - 20, y + 10 + i * 12],
                   fill=(70, 130, 90), width=1)
            d.line([cx + 20, y + 10 + i * 12, x + w - 8, y + 10 + i * 12],
                   fill=(70, 130, 90), width=1)
        d.rectangle([cx - 20, cy - 18, cx + 20, cy + 18], fill=(30, 90, 60),
                    outline=(120, 200, 140), width=2)
        d.rectangle([cx - 10, cy - 8, cx + 10, cy + 8], fill=(20, 60, 40))
        d.text((cx - 9, cy - 6), "AI", font=font(SANS_B, 11),
               fill=(140, 230, 160))


_IMG = None


def scene(d, x, y, w, h, kind, label=""):
    """Draw a scene clipped to its own box (no drawing may spill over)."""
    layer = Image.new("RGB", (w, h), PAPER)
    ld = ImageDraw.Draw(layer)
    _draw_scene(ld, 0, 0, w, h, kind, label)
    _IMG.paste(layer, (x, y))


# ------------------------------------------------------------- world map
MAP_X0, MAP_Y0, MAP_W, MAP_H = 14, 622, 330, 252
MAP_LON0, MAP_LON1, MAP_LAT0, MAP_LAT1 = -170, 190, -58, 84


def _ll(lon, lat):
    mx = MAP_X0 + (lon - MAP_LON0) / (MAP_LON1 - MAP_LON0) * MAP_W
    my = MAP_Y0 + (MAP_LAT1 - lat) / (MAP_LAT1 - MAP_LAT0) * MAP_H
    return (mx, my)


CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 80),
     (-75, 72), (-60, 60), (-55, 47), (-70, 42), (-75, 35), (-80, 25),
     (-90, 21), (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 49),
     (-140, 60), (-165, 60)],
    # Greenland
    [(-58, 64), (-45, 60), (-30, 68), (-40, 76), (-58, 74)],
    # South America
    [(-80, 10), (-75, 5), (-60, 0), (-50, -5), (-35, -8), (-40, -20),
     (-48, -28), (-58, -35), (-65, -45), (-70, -54), (-73, -40),
     (-72, -20), (-80, -5), (-81, 5)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (32, 31), (35, 28),
     (43, 12), (51, 10), (48, 0), (40, -10), (35, -20), (28, -33),
     (18, -35), (12, -18), (9, 4), (-8, 5)],
    # Asia (drawn before Europe so Europe sits on top)
    [(30, 70), (45, 68), (60, 69), (75, 73), (90, 75), (110, 76),
     (130, 72), (150, 70), (170, 66), (178, 65), (170, 60), (160, 55),
     (155, 50), (142, 45), (135, 43), (127, 40), (120, 38), (115, 32),
     (108, 25), (105, 15), (100, 8), (95, 15), (90, 22), (85, 20),
     (80, 15), (75, 8), (72, 20), (65, 25), (58, 26), (52, 28),
     (48, 30), (44, 30), (40, 35), (35, 36), (30, 40), (30, 50),
     (35, 55), (30, 60)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (12, 55),
     (18, 56), (21, 59), (28, 60), (30, 70), (40, 68), (50, 68), (45, 60),
     (40, 55), (30, 50), (28, 45), (23, 40), (19, 42), (12, 44), (8, 44),
     (3, 42), (-2, 37)],
    # Australia
    [(113, -22), (114, -30), (120, -34), (130, -32), (137, -35), (140, -38),
     (145, -38), (150, -37), (153, -27), (150, -22), (146, -19), (142, -11),
     (136, -12), (132, -11), (126, -14), (122, -17), (118, -20)],
    # UK
    [(-5, 50), (-2, 53), (0, 53), (-3, 58), (-5, 58)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 38), (141, 41), (143, 43),
     (145, 44), (142, 42), (140, 36), (136, 34), (132, 33)],
    # Indonesia (simplified chain)
    [(95, 5), (100, 0), (105, -6), (110, -7), (115, -8), (120, -9),
     (125, -9), (130, -4), (135, -3), (140, -4), (138, -8), (130, -8),
     (120, -10), (110, -8), (100, -2), (95, 2)],
    # New Zealand
    [(167, -45), (172, -41), (175, -38), (178, -37), (174, -40),
     (169, -43)],
]

# Featured-story pin locations (num -> lon, lat).
PINS = {1: (114.1, 22.5), 2: (4.3, 52.0), 3: (85.0, 19.0),
        4: (46.7, 24.6), 5: (34.0, 45.0), 6: (-74.0, 40.7),
        7: (-77.0, 38.9), 8: (34.5, 31.5), 9: (30.7, 36.9),
        10: (90.4, 23.8), 11: (-66.9, 10.5), 12: (-80.2, 25.8),
        13: (116.4, 39.9)}
PIN_COLOR = {1: ASIA, 2: ASIA, 3: ASIA, 4: MIDDLE_EAST, 5: EUROPE,
             6: GLOBAL, 7: AMERICAS, 8: MIDDLE_EAST, 9: GLOBAL,
             10: ASIA, 11: AMERICAS, 12: GLOBAL, 13: ASIA}
# Pins that would overlap a neighbour are nudged with a leader line.
PIN_OFFSET = {7: (11, -9)}

# ------------------------------------------------------------- layout
def render():
    global _IMG
    img = Image.new("RGB", (W, H), PAPER)
    _IMG = img
    d = ImageDraw.Draw(img)
    x0, x1 = 14, 1010

    # Kicker row
    d.text((x0, 8), "THE WORLD'S NEWS IN ONE PICTURE",
           font=font(SANS_B, 11), fill=RED)
    right = "45 STORIES · 6 CONTINENTS · ALL FROM THIS THURSDAY"
    d.text((x1 - d.textlength(right, font=font(SANS_B, 11)), 8), right,
           font=font(SANS_B, 11), fill=INK)

    # Masthead
    mast = fit_font(d, "Thursday 19 November 2026", SERIF, 66, x1 - x0)
    centered(d, W // 2, 24, "Thursday 19 November 2026", mast, INK)
    d.rectangle([x0, 92, x1, 94], fill=INK)
    d.rectangle([x0, 96, x1, 97], fill=INK)

    # Timeline strip
    d.rectangle([x0, 102, 78, 130], fill=RED)
    d.text((x0 + 5, 104), "THE DAY", font=font(SANS_B, 9),
           fill=(255, 255, 255))
    d.text((x0 + 5, 115), "IN UTC", font=font(SANS_B, 9),
           fill=(255, 255, 255))
    col_w = (x1 - 84) / 6
    for i, (t, cap) in enumerate(TIMELINE):
        cx = 84 + i * col_w
        d.text((cx + 4, 103), t, font=font(SANS_B, 10), fill=RED)
        draw_wrapped(d, cx + 4, 116,
                     wrap(d, cap, font(SANS, 9), col_w - 8),
                     font(SANS, 9), BODY, 11)
    d.rectangle([x0, 140, x1, 141], fill=INK)

    # ---- 3 lead stories
    lead_w, lead_gap = 326, 9
    for i, (num, region, tag, head, summ, label, kind, lonlat) in enumerate(LEADS):
        lon, lat = lonlat
        lx = x0 + i * (lead_w + lead_gap)
        scene(d, lx, 146, lead_w, 102, kind)
        num_dot(d, lx + 8, 256, num, region, r=8)
        d.text((lx + 20, 250), tag, font=font(SANS_B, 9), fill=region)
        lw = d.textlength(label, font=font(SANS_B, 8))
        d.text((lx + lead_w - lw, 251), label, font=font(SANS_B, 8),
               fill=(110, 105, 95))
        draw_wrapped(d, lx, 266,
                     wrap(d, head, font(SERIF, 16), lead_w)[:3],
                     font(SERIF, 16), INK, 19)
        draw_wrapped(d, lx, 325,
                     wrap(d, summ, font(SANS, 10), lead_w)[:2],
                     font(SANS, 10), BODY, 12)
    d.rectangle([x0, 352, x1, 353], fill=INK)

    # ---- 10 medium stories (5 cols x 2 rows)
    med_w, med_gap, row_h = 193, 8, 118
    for i, (num, region, tag, head, summ, src, kind) in enumerate(MEDIUM):
        col, row = i % 5, i // 5
        mx = x0 + col * (med_w + med_gap)
        my = 358 + row * row_h
        scene(d, mx, my, med_w, 48, kind)
        num_dot(d, mx + 8, my + 58, num, region, r=7)
        d.text((mx + 18, my + 53), tag, font=font(SANS_B, 8), fill=region)
        draw_wrapped(d, mx, my + 65,
                     wrap(d, head, font(SERIF, 12), med_w)[:2],
                     font(SERIF, 12), INK, 13)
        draw_wrapped(d, mx, my + 91,
                     wrap(d, summ, font(SANS, 9), med_w)[:2],
                     font(SANS, 9), BODY, 11)
    d.rectangle([x0, 598, x1, 599], fill=INK)

    # ---- bottom: map (left) + numbered list (right)
    d.text((x0, 604), "WHERE IT HAPPENED", font=font(SANS_B, 11), fill=RED)
    d.text((356, 604), "ALSO ON THURSDAY 19 NOVEMBER",
           font=font(SANS_B, 11), fill=RED)
    # ocean + continents
    d.rectangle([MAP_X0, MAP_Y0, MAP_X0 + MAP_W, MAP_Y0 + MAP_H],
                fill=(196, 216, 228))
    for poly in CONTINENTS:
        d.polygon([_ll(lon, lat) for lon, lat in poly],
                  fill=(238, 228, 202), outline=(190, 178, 150))
    for n, (lon, lat) in PINS.items():
        px, py = _ll(lon, lat)
        dx, dy = PIN_OFFSET.get(n, (0, 0))
        if dx or dy:
            d.line([px, py, px + dx, py + dy], fill=(90, 85, 75), width=1)
            px, py = px + dx, py + dy
        num_dot(d, px, py, n, PIN_COLOR[n], r=7)
    # legend
    lx = MAP_X0
    ly = MAP_Y0 + MAP_H + 8
    for color, name in [(AMERICAS, "Americas"), (EUROPE, "Europe"),
                        (MIDDLE_EAST, "Middle East"), (ASIA, "Asia"),
                        (AFRICA, "Africa"), (OCEANIA, "Oceania"),
                        (GLOBAL, "Global & space")]:
        d.ellipse([lx, ly, lx + 8, ly + 8], fill=color)
        d.text((lx + 11, ly - 1), name, font=font(SANS, 8), fill=BODY)
        lx += 12 + d.textlength(name, font=font(SANS, 8)) + 8
    # numbered list, two columns
    list_font = font(SANS, 9)
    for ci in range(2):
        cx = 356 + ci * 332
        cy = 624
        for num, region, text in LIST_ITEMS[ci * 16:(ci + 1) * 16]:
            lines = wrap(d, text, list_font, 322 - 18)
            num_dot(d, cx + 7, cy + 6, num, region, r=6)
            draw_wrapped(d, cx + 18, cy, lines, list_font, BODY, 12)
            cy += max(14, len(lines) * 12 + 3)

    # ---- date check
    d.rectangle([x0, 926, x1, 964], outline=RED, width=2)
    d.rectangle([x0, 926, x0 + 92, 964], fill=RED)
    d.text((x0 + 8, 934), "DATE CHECK", font=font(SANS_B, 11),
           fill=(255, 255, 255))
    d.text((x0 + 8, 948), "LEFT OUT", font=font(SANS_B, 8),
           fill=(255, 255, 255))
    draw_wrapped(d, x0 + 100, 930,
                 wrap(d, DATE_CHECK, font(SANS, 9), x1 - x0 - 110),
                 font(SANS, 9), BODY, 12)

    # ---- footer
    centered(d, W // 2, 972, FOOTER, font(SANS, 9), BODY)
    centered(d, W // 2, 986, SOURCES, font(SANS, 8), (120, 115, 105))
    return img


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    render().save(out, optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")
