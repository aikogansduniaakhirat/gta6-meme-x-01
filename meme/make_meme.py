#!/usr/bin/env python3
"""Render the GTA 6 meme for make.fun's gta6-meme-x-01 bounty.

Scene: Vice City sunset, palm silhouettes, synthwave sun, neon grid.
The make.fun ghost stands in front of a TV that is still installing
GTA VI. The joke is the thirteen-year wait and the still-unfinished
download; the pitch is that the agent got paid while the human waited.

The ghost is drawn from the official press-kit vector (mark.svg) with the
magenta badge circle removed, so it sits in the scene instead of being
pasted on as a sticker.

The layout is declared as a block stack and asserted to be collision free
before anything is written, because the picture is judged on being clean.
"""

import io
import math
import os

import cairosvg
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PRESS = os.path.join(HERE, "..", "assets")
OUT = os.path.join(HERE, "..", "out")

SIZE = 1080
INK = (25, 20, 25)
MAGENTA = (196, 28, 131)
WHITE = (255, 255, 255)
GOLD = (255, 209, 102)
DEEP = (18, 7, 31)
HOT = (255, 61, 158)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Single-column text bands must never overlap; the ghost is allowed to stand
# in front of the TV, which is a deliberate overlap, so it is left out of the
# stack and checked against the text bands alone.
BLOCKS = {
    "headline": (0.026, 0.160),
    "tv": (0.185, 0.442),
    "ghost": (0.470, 0.848),
    "pitch": (0.870, 0.996),
}

# These blocks stack without overlapping. The ghost is drawn over the TV on
# purpose, the way a character stands in front of a screen.
STACK = ("headline", "tv", "pitch")

MAX_TEXT_W = SIZE * 0.90


def font(path, size):
    return ImageFont.truetype(path, size)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sunset(size):
    """Vertical sky gradient from deep indigo down to hot orange."""
    img = Image.new("RGB", (1, size))
    px = img.load()
    stops = [
        (0.00, DEEP),
        (0.22, (58, 12, 74)),
        (0.42, (138, 24, 110)),
        (0.56, MAGENTA),
        (0.66, (232, 79, 96)),
        (0.74, (255, 138, 61)),
    ]
    for y in range(size):
        t = y / (size - 1)
        for i in range(len(stops) - 1):
            a_t, a_c = stops[i]
            b_t, b_c = stops[i + 1]
            if a_t <= t <= b_t:
                local = (t - a_t) / (b_t - a_t) if b_t > a_t else 0
                px[0, y] = lerp(a_c, b_c, local)
                break
        else:
            px[0, y] = stops[-1][1]
    return img.resize((size, size), Image.BILINEAR)


def synth_sun(draw, cx, cy, r):
    """Gold sun with the classic horizontal cut bands."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    band = r * 0.055
    y = cy + r * 0.05
    gap = band * 0.55
    while y < cy + r:
        h = band * 0.55
        draw.rectangle([cx - r - 2, y, cx + r + 2, y + h], fill=(232, 79, 96))
        y += h + gap
        band *= 1.16
        gap *= 1.05


def palm(draw, x, base, h, lean, w):
    """A palm silhouette: curved trunk plus drooping fronds."""
    pts = []
    for i in range(41):
        t = i / 40
        px = x + lean * (t ** 1.8) * h * 0.55
        py = base - h * t
        pts.append((px, py))
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        thick = w * (1 - i / len(pts) * 0.62)
        draw.line([x0, y0, x1, y1], fill=DEEP, width=max(2, round(thick)))
    tipx, tipy = pts[-1]
    for ang, ln in ((-2.75, 1.0), (-2.2, 0.92), (-1.6, 0.85),
                    (-1.0, 0.95), (-0.42, 0.88), (0.15, 0.8)):
        ex = tipx + math.cos(ang) * h * 0.34 * ln
        ey = tipy + math.sin(ang) * h * 0.34 * ln + h * 0.10 * ln
        mx = tipx + math.cos(ang) * h * 0.18 * ln
        my = tipy + math.sin(ang) * h * 0.18 * ln - h * 0.045
        draw.line([tipx, tipy, mx, my], fill=DEEP, width=max(3, round(w * 0.5)))
        draw.line([mx, my, ex, ey], fill=DEEP, width=max(2, round(w * 0.34)))


def neon_grid(img, horizon):
    """Perspective floor grid in hot pink."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = SIZE // 2
    for i in range(-14, 15):
        x_far = cx + i * (SIZE * 0.035)
        x_near = cx + i * (SIZE * 0.42)
        d.line([x_far, horizon, x_near, SIZE], fill=HOT + (150,), width=2)
    y = horizon
    step = 6.0
    while y < SIZE:
        t = (y - horizon) / (SIZE - horizon)
        d.line([0, y, SIZE, y], fill=HOT + (int(40 + 110 * t),),
               width=max(1, int(1 + 2 * t)))
        y += step
        step *= 1.30
    img.alpha_composite(layer)


def ghost_rgba(px_height):
    """Render the press-kit ghost (badge circle stripped) to RGBA."""
    src = os.path.join(PRESS, "mark.svg")
    with open(src, "r", encoding="utf-8") as fh:
        svg = fh.read()
    marker = '<circle cx="16" cy="16" r="15.1"'
    idx = svg.find(marker)
    if idx == -1:
        raise SystemExit("badge circle not found in mark.svg")
    end = svg.find("/>", idx) + 2
    bare = svg[:idx] + svg[end:]
    bare = bare.replace('width="256" height="256"', 'width="1024" height="1024"')
    png = cairosvg.svg2png(bytestring=bare.encode("utf-8"),
                           output_width=1024, output_height=1024)
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    im = im.crop(im.getbbox())
    ratio = px_height / im.height
    return im.resize((round(im.width * ratio), px_height), Image.LANCZOS)


def fit_text(draw, text, path, max_w, start, floor=16):
    """Shrink the font until the line fits max_w."""
    size = start
    while size > floor:
        f = font(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(path, floor)


def wrap_two_lines(draw, text, path, max_w):
    """Split a caption into at most two lines of roughly equal length.

    A single line is returned when the text already fits at a comfortable size,
    so short captions do not get needlessly split.
    """
    probe = font(path, 40)
    if draw.textlength(text, font=probe) <= max_w * 0.92:
        return [text]
    words = text.split()
    mid = len(words) // 2
    best = (mid, None)
    for i in range(1, len(words)):
        a = " ".join(words[:i])
        b = " ".join(words[i:])
        score = max(draw.textlength(a, font=probe), draw.textlength(b, font=probe))
        if best[1] is None or score < best[1]:
            best = (i, score)
    i = best[0]
    return [" ".join(words[:i]), " ".join(words[i:])]


def centered(draw, text, f, y, fill):
    w = draw.textlength(text, font=f)
    off = max(3, f.size // 14)
    draw.text(((SIZE - w) / 2 + off, y + off), text, font=f, fill=(0, 0, 0, 130))
    draw.text(((SIZE - w) / 2, y), text, font=f, fill=fill)


def box(fraction_pair):
    y0, y1 = fraction_pair
    return y0 * SIZE, y1 * SIZE


def assert_clean(blocks, ghost_w):
    """Fail loudly if two stacked bands overlap, or any box leaves the canvas.

    Only the blocks in STACK are checked against each other: the ghost is drawn
    over the TV on purpose, so it is verified to fit the canvas and to clear the
    pitch slab, never to clear the screen behind it.
    """
    for i in range(len(STACK) - 1):
        name = STACK[i]
        nxt = STACK[i + 1]
        _, a1 = box(blocks[name])
        b0, _ = box(blocks[nxt])
        if a1 > b0:
            raise SystemExit(
                f"layout collision: {name} ends at {a1:.1f} but {nxt} starts at {b0:.1f}")

    for name, pair in blocks.items():
        y0, y1 = box(pair)
        if y0 < 0 or y1 > SIZE:
            raise SystemExit(f"layout: {name} leaves the canvas ({y0:.1f}, {y1:.1f})")

    ghost_top, ghost_bottom = box(blocks["ghost"])
    pitch_top, _ = box(blocks["pitch"])
    if ghost_bottom > pitch_top:
        raise SystemExit(
            f"layout collision: ghost ends at {ghost_bottom:.1f} but "
            f"pitch starts at {pitch_top:.1f}")
    if ghost_w > SIZE * 0.92:
        raise SystemExit(f"layout: ghost is too wide ({ghost_w:.1f} of {SIZE})")


def headline_text():
    return os.environ.get("HEADLINE", "13 YEARS LATER")


def pitch_text():
    return os.environ.get("PITCH", "my agent paid for the console already")


def build():
    os.makedirs(OUT, exist_ok=True)

    gh_height = SIZE * (BLOCKS["ghost"][1] - BLOCKS["ghost"][0])
    gh = ghost_rgba(int(gh_height))
    assert_clean(BLOCKS, gh.width)

    img = sunset(SIZE).convert("RGBA")
    horizon = int(SIZE * 0.635)
    d = ImageDraw.Draw(img)

    synth_sun(d, SIZE * 0.5, horizon - SIZE * 0.055, SIZE * 0.175)
    palm(d, SIZE * 0.085, horizon + SIZE * 0.030, SIZE * 0.40, -0.55, 22)
    palm(d, SIZE * 0.915, horizon + SIZE * 0.030, SIZE * 0.36, 0.55, 20)
    palm(d, SIZE * 0.155, horizon + SIZE * 0.012, SIZE * 0.24, -0.30, 13)

    ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ground).rectangle([0, horizon, SIZE, SIZE], fill=(11, 5, 20, 220))
    img.alpha_composite(ground)
    neon_grid(img, horizon)
    d = ImageDraw.Draw(img)

    # --- the TV still installing GTA VI ---
    tv_y0, tv_y1 = box(BLOCKS["tv"])
    tv_h = tv_y1 - tv_y0
    tv_w = SIZE * 0.56
    tv_x = (SIZE - tv_w) / 2
    d.rounded_rectangle([tv_x - 13, tv_y0 - 13, tv_x + tv_w + 13, tv_y1 + 13],
                        radius=24, fill=INK)
    d.rounded_rectangle([tv_x, tv_y0, tv_x + tv_w, tv_y1], radius=14, fill=(24, 16, 32))

    f_title = fit_text(d, "GTA VI", FONT_BOLD, tv_w * 0.60, int(tv_h * 0.40))
    tw = d.textlength("GTA VI", font=f_title)
    d.text((tv_x + (tv_w - tw) / 2, tv_y0 + tv_h * 0.055), "GTA VI",
           font=f_title, fill=GOLD)

    bar_x0, bar_x1 = tv_x + tv_w * 0.12, tv_x + tv_w * 0.88
    bar_y0 = tv_y0 + tv_h * 0.50
    bar_h = tv_h * 0.11
    d.rounded_rectangle([bar_x0, bar_y0, bar_x1, bar_y0 + bar_h],
                        radius=bar_h / 2, fill=(45, 34, 56), outline=WHITE, width=3)
    d.rounded_rectangle([bar_x0, bar_y0, bar_x0 + (bar_x1 - bar_x0) * 0.42,
                         bar_y0 + bar_h], radius=bar_h / 2, fill=MAGENTA)

    pct = "STILL INSTALLING  42%"
    f_pct = fit_text(d, pct, FONT_BOLD, tv_w * 0.86, int(tv_h * 0.145))
    pw = d.textlength(pct, font=f_pct)
    pct_y = bar_y0 + bar_h + tv_h * 0.030
    d.text((tv_x + (tv_w - pw) / 2, pct_y), pct, font=f_pct, fill=WHITE)

    # The absurd install size is the part a GTA fan laughs at, so it gets its
    # own line under the progress bar rather than being squeezed into it.
    size_note = "147 GB of 350 GB"
    f_size = fit_text(d, size_note, FONT_SANS, tv_w * 0.62, int(tv_h * 0.092))
    sw = d.textlength(size_note, font=f_size)
    d.text((tv_x + (tv_w - sw) / 2, pct_y + f_pct.size * 1.22),
           size_note, font=f_size, fill=WHITE)

    # --- the ghost, standing in front of the screen ---
    gy = box(BLOCKS["ghost"])[0]
    gx = (SIZE - gh.width) / 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        [gx, gy + gh.height * 0.90, gx + gh.width, gy + gh.height * 1.02],
        fill=(0, 0, 0, 105))
    img.alpha_composite(shadow)
    img.alpha_composite(gh, (round(gx), round(gy)))

    d = ImageDraw.Draw(img)

    # --- headline ---
    hy0, hy1 = box(BLOCKS["headline"])
    head = headline_text()
    f_head = fit_text(d, head, FONT_BOLD, MAX_TEXT_W, int(hy1 - hy0))
    centered(d, head, f_head, hy0, WHITE)

    # --- pitch, on a magenta slab so it reads over the grid ---
    # A two-line slab lets the punchline render large instead of shrinking to
    # fit one long row.
    py0, py1 = box(BLOCKS["pitch"])
    pitch = pitch_text()
    pitch_lines = wrap_two_lines(d, pitch, FONT_BOLD, SIZE * 0.86)
    f_pitch = fit_text(d, max(pitch_lines, key=len), FONT_BOLD,
                       SIZE * 0.86, int((py1 - py0) * 0.46))
    line_w = max(d.textlength(line, font=f_pitch) for line in pitch_lines)
    pad_x, pad_y = SIZE * 0.030, SIZE * 0.014
    slab_h = f_pitch.size * len(pitch_lines) * 1.18 + pad_y * 2
    d.rounded_rectangle([(SIZE - line_w) / 2 - pad_x, py0,
                         (SIZE + line_w) / 2 + pad_x, py0 + slab_h],
                        radius=int(SIZE * 0.016), fill=MAGENTA)
    ty = py0 + pad_y
    for line in pitch_lines:
        lw = d.textlength(line, font=f_pitch)
        d.text(((SIZE - lw) / 2, ty), line, font=f_pitch, fill=WHITE)
        ty += f_pitch.size * 1.18

    final = img.convert("RGB")
    path = os.path.join(OUT, "meme.png")
    final.save(path, "PNG", optimize=True)
    print("wrote", path, final.size, os.path.getsize(path), "bytes")
    print("ghost", gh.size, "pitch font", f_pitch.size, "headline font", f_head.size)
    return path


if __name__ == "__main__":
    build()
