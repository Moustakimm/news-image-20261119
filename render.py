#!/usr/bin/env python3
"""Renders entry.png (1024x1024) for the news-image-20261119 bounty.

A newspaper front page summing up Thursday 19 November 2026 in six stories:
the Trump-Xi-Putin trilateral summit in Shenzhen, the ICJ ruling that
Myanmar committed genocide against the Rohingya, Cyclone Akvan bearing down
on India's east coast, a Houthi missile hitting a tower in Riyadh, a third
attack this week on the Crimea bridge, and Anthropic's record IPO.

Run:  python3 render.py        (writes ./entry.png beside this file)
Requires Pillow and the DejaVu fonts (standard on this machine).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (246, 241, 229)
INK = (25, 23, 19)
BODY = (43, 40, 34)
RED = (138, 47, 36)
NAVY = (29, 58, 95)
GOLD = (201, 123, 45)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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


# ---------------------------------------------------------------- flags
def flag_usa(d, x, y, w, h):
    """Stars and stripes, drawn small."""
    stripe = h / 13.0
    for i in range(13):
        if i % 2 == 0:
            d.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe],
                        fill=(178, 34, 52))
    canton_w, canton_h = w * 0.4, stripe * 7
    d.rectangle([x, y, x + canton_w, y + canton_h], fill=(30, 50, 110))
    for r in range(3):
        for c in range(4):
            cx = x + 6 + c * (canton_w - 10) / 3
            cy = y + 5 + r * (canton_h - 8) / 2
            d.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6],
                      fill=(255, 255, 255))


def flag_china(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    # one big star, four small dots
    cx, cy, r = x + w * 0.22, y + h * 0.28, 7
    star = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        star.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(star, fill=(255, 222, 0))
    for sx, sy in ((0.62, 0.18), (0.74, 0.34), (0.72, 0.55), (0.58, 0.68)):
        d.ellipse([x + w * sx - 2, y + h * sy - 2,
                   x + w * sx + 2, y + h * sy + 2], fill=(255, 222, 0))


def flag_russia(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h / 3], fill=(255, 255, 255))
    d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))


# ---------------------------------------------------------------- lead art
def lead_art():
    im = Image.new("RGB", (470, 280), NAVY)
    d = ImageDraw.Draw(im)
    # dusk sky bands
    d.rectangle([0, 0, 470, 92], fill=(232, 163, 76))
    d.rectangle([0, 92, 470, 130], fill=(201, 123, 45))
    d.ellipse([398, 18, 452, 72], fill=(244, 213, 141))          # low sun
    # Shenzhen skyline, back row
    for (bx, bw, bh) in ((16, 34, 96), (58, 26, 128), (92, 40, 84),
                         (140, 30, 118), (300, 36, 104), (344, 28, 132),
                         (380, 44, 92), (428, 30, 118)):
        d.rectangle([bx, 196 - bh, bx + bw, 196], fill=(20, 40, 68))
    # front row towers with lit windows
    for (bx, bw, bh) in ((30, 46, 150), (180, 40, 168), (250, 48, 140),
                          (330, 42, 158)):
        d.rectangle([bx, 232 - bh, bx + bw, 232], fill=(13, 28, 48))
        for wy in range(232 - bh + 12, 226, 18):
            for wx in range(bx + 8, bx + bw - 6, 14):
                if (wx * 7 + wy * 3) % 5:
                    d.rectangle([wx, wy, wx + 5, wy + 7], fill=(244, 213, 141))
    # ground band
    d.rectangle([0, 232, 470, 280], fill=(10, 22, 38))
    # three flags on poles
    pole_x = [60, 205, 350]
    painters = [flag_usa, flag_china, flag_russia]
    for px, paint in zip(pole_x, painters):
        d.line([(px, 236), (px, 150)], fill=(220, 220, 220), width=4)
        d.ellipse([px - 4, 144, px + 4, 152], fill=(232, 163, 76))
        paint(d, px + 4, 158, 74, 48)
    d.text((18, 244), "SHENZHEN  ·  APEC SUMMIT", font=font(SANS_B, 19),
           fill=(244, 213, 141))
    return im


# ---------------------------------------------------------------- icons
def icon_scales():
    """Scales of justice on a pale blue ground."""
    im = Image.new("RGB", (96, 96), (223, 232, 239))
    d = ImageDraw.Draw(im)
    d.line([(48, 14), (48, 74)], fill=INK, width=5)               # post
    d.line([(20, 24), (76, 24)], fill=INK, width=4)               # beam
    for cx in (20, 76):
        d.line([(cx, 24), (cx - 12, 52)], fill=INK, width=3)
        d.line([(cx, 24), (cx + 12, 52)], fill=INK, width=3)
        d.arc([cx - 13, 44, cx + 13, 70], start=0, end=180,
              fill=NAVY, width=4)
    d.line([(38, 84), (58, 84)], fill=INK, width=5)               # base
    d.line([(48, 74), (48, 84)], fill=INK, width=5)
    d.ellipse([44, 10, 52, 18], fill=GOLD)                        # finial
    return im


def icon_cyclone():
    """Spiral storm on a pale grey-blue ground."""
    im = Image.new("RGB", (96, 96), (226, 233, 238))
    d = ImageDraw.Draw(im)
    pts = []
    for t in range(0, 620, 6):
        ang = math.radians(t)
        r = 4 + t / 620.0 * 40
        pts.append((48 + r * math.cos(ang), 50 + r * math.sin(ang)))
    d.line(pts, fill=NAVY, width=6, joint="curve")
    d.ellipse([42, 44, 54, 56], fill=(255, 255, 255))
    d.ellipse([45, 47, 51, 53], fill=NAVY)
    return im


def icon_tower():
    """Skyscraper struck by a missile blast, on a pale sand ground."""
    im = Image.new("RGB", (96, 96), (243, 234, 214))
    d = ImageDraw.Draw(im)
    d.rectangle([34, 34, 62, 88], fill=(29, 58, 95))              # tower
    for wy in range(40, 84, 10):
        d.rectangle([39, wy, 46, wy + 5], fill=(244, 213, 141))
        d.rectangle([51, wy, 57, wy + 5], fill=(244, 213, 141))
    d.rectangle([30, 28, 66, 34], fill=(13, 28, 48))              # roof
    # blast star above the roof
    cx, cy, r = 48, 16, 13
    star = []
    for i in range(16):
        ang = -math.pi / 2 + i * math.pi / 8
        rr = r if i % 2 == 0 else r * 0.45
        star.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(star, fill=(232, 106, 44))
    d.ellipse([44, 12, 52, 20], fill=(244, 213, 141))
    # smoke
    d.ellipse([62, 8, 76, 22], fill=(110, 103, 90))
    d.ellipse([70, 2, 82, 14], fill=(138, 130, 114))
    return im


def icon_bridge():
    """Arched bridge over water, blast above it, on a pale blue ground."""
    im = Image.new("RGB", (96, 96), (223, 232, 239))
    d = ImageDraw.Draw(im)
    d.line([(8, 78), (8, 58)], fill=INK, width=5)
    d.line([(88, 78), (88, 58)], fill=INK, width=5)
    d.line([(8, 58), (88, 58)], fill=INK, width=3)
    d.arc([8, 30, 88, 126], start=180, end=360, fill=RED, width=7)
    d.line([(10, 88), (86, 88)], fill=NAVY, width=6)
    # blast star above the deck
    cx, cy, r = 48, 22, 12
    star = []
    for i in range(16):
        ang = -math.pi / 2 + i * math.pi / 8
        rr = r if i % 2 == 0 else r * 0.45
        star.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(star, fill=(232, 106, 44))
    d.ellipse([44, 18, 52, 26], fill=(244, 213, 141))
    return im


def icon_chart():
    """Rising market line with a dollar tag, on a pale green ground."""
    im = Image.new("RGB", (96, 96), (226, 236, 221))
    d = ImageDraw.Draw(im)
    d.line([(12, 70), (34, 56), (54, 60), (72, 34), (84, 22)],
           fill=(63, 125, 78), width=6, joint="curve")
    d.line([(84, 34), (84, 22), (72, 22)], fill=(63, 125, 78), width=5)
    d.line([(10, 82), (88, 82)], fill=INK, width=3)
    d.text((12, 6), "$81.3bn", font=font(SANS_B, 17), fill=(63, 125, 78))
    return im


# ---------------------------------------------------------------- page
def main():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    x0, x1 = 40, 984

    # masthead
    centered(d, W // 2, 30, "THE WORLD IN ONE IMAGE", font(SANS_B, 17), RED,
             tracking=6)
    title_f = fit_font(d, "THURSDAY 19 NOVEMBER 2026", SERIF, 58, x1 - x0)
    centered(d, W // 2, 56, "THURSDAY 19 NOVEMBER 2026", title_f, INK)
    centered(d, W // 2, 128, "SIX STORIES  ·  ONE DAY  ·  AROUND THE GLOBE",
             font(SANS, 21), BODY, tracking=2)
    d.line([(x0, 166), (x1, 166)], fill=INK, width=4)
    d.line([(x0, 172), (x1, 172)], fill=INK, width=2)

    # lead story: Shenzhen summit
    ly = 186
    im.paste(lead_art(), (x0, ly))
    tx = 536
    tag = "THE SUMMIT"
    tf = font(SANS_B, 15)
    tw = d.textlength(tag, font=tf) + 20
    d.rectangle([tx, ly, tx + tw, ly + 28], fill=RED)
    d.text((tx + 10, ly + 5), tag, font=tf, fill=(255, 255, 255))
    y = ly + 40
    y = draw_wrapped(d, tx, y,
                     wrap(d, "Trump, Xi and Putin meet in Shenzhen",
                          font(SERIF, 40), x1 - tx),
                     font(SERIF, 40), INK, 44)
    body = ("The leaders of the US, China and Russia hold their first "
            "three-way summit at APEC. After 90 minutes they announce a "
            "\u201cpeace declaration\u201d and agree to nuclear-risk talks.")
    draw_wrapped(d, tx, y + 8,
                 wrap(d, body, font(SANS, 20), x1 - tx),
                 font(SANS, 20), BODY, 28)

    # four stories, 2 x 2
    stories = [
        (icon_scales(),
         "World court: Myanmar committed genocide",
         "The UN\u2019s top court rules Myanmar\u2019s 2017 crackdown on the "
         "Rohingya was state-sponsored genocide \u2014 the first ruling of "
         "its kind."),
        (icon_cyclone(),
         "Cyclone Akvan bears down on India\u2019s east coast",
         "Odisha evacuates about 50,000 people as the severe storm heads "
         "for the Andhra Pradesh\u2013Odisha coast; landfall is expected "
         "on Friday."),
        (icon_tower(),
         "Houthi missile damages tower in Riyadh",
         "A missile strike hits the Public Investment Fund Tower in the "
         "Saudi capital, a reporter on the scene confirms, as the Iran "
         "war widens."),
        (icon_bridge(),
         "Russia says Crimea bridge attacked again",
         "Moscow says Ukraine struck the bridge to Crimea for a third "
         "time this week, as the war grinds on."),
    ]
    gy = 496
    col_w = (x1 - x0 - 30) // 2
    for i, (icon, head, body) in enumerate(stories):
        cx = x0 + (i % 2) * (col_w + 30)
        cy = gy + (i // 2) * 185
        d.line([(cx, cy), (cx + col_w, cy)], fill=INK, width=2)
        im.paste(icon, (cx, cy + 14))
        hx = cx + 112
        hw = col_w - 112
        y = draw_wrapped(d, hx, cy + 12,
                         wrap(d, head, font(SERIF, 25), hw),
                         font(SERIF, 25), INK, 28)
        draw_wrapped(d, hx, y + 6,
                     wrap(d, body, font(SANS, 16), hw),
                     font(SANS, 16), BODY, 21)

    # fifth story, full width
    fy = gy + 2 * 185 + 10
    d.line([(x0, fy), (x1, fy)], fill=INK, width=2)
    im.paste(icon_chart().resize((88, 88)), (x0, fy + 6))
    hx = x0 + 112
    hw = x1 - hx
    y = draw_wrapped(d, hx, fy + 12,
                     wrap(d, "Anthropic\u2019s $81.3bn IPO breaks records",
                          font(SERIF, 25), hw),
                     font(SERIF, 25), INK, 28)
    draw_wrapped(d, hx, y + 4,
                 wrap(d, "The AI firm\u2019s listing smashes SpaceX\u2019s "
                         "market-debut record, capping a huge year for AI stocks.",
                      font(SANS, 16), hw),
                 font(SANS, 16), BODY, 21)

    # footer
    fy2 = 972
    d.line([(x0, fy2), (x1, fy2)], fill=INK, width=4)
    centered(d, W // 2, fy2 + 12,
             "THURSDAY 19 NOVEMBER 2026  \u00b7  ALSO TODAY: GTA VI LAUNCHES "
             "WORLDWIDE",
             font(SANS, 17), BODY, tracking=2)

    im.save("entry.png", format="PNG", optimize=True)
    size = os.path.getsize("entry.png")
    print(f"wrote entry.png: {size} bytes (limit 1048576), {im.size}")
    assert size <= 1048576, "image exceeds the 1 MiB gate"


if __name__ == "__main__":
    main()
