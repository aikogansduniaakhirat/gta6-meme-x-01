#!/usr/bin/env python3
"""Measure the rendered meme. No vision model is reachable in an autonomous tick,
so the picture is verified by measuring pixels: band ink, the mascot's white body
at its real centre, the HUD money pickup above its head, and composition probes
at the actual coordinates of the scene (sun left, palms left and far right).
"""
import os
import sys
from PIL import Image

PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "art", "meme.png")

im = Image.open(PATH).convert("RGB")
W, H = im.size
px = im.load()
print(f"file {PATH} {W}x{H} {os.path.getsize(PATH)} bytes")

fails = []


def band_ink(y0, y1, label, lo=0.02, hi=0.60):
    tot = white = 0
    for y in range(int(H * y0), int(H * y1)):
        for x in range(0, W, 2):
            r, g, b = px[x, y]
            tot += 1
            if r > 225 and g > 225 and b > 225:
                white += 1
    share = white / max(1, tot)
    ok = lo <= share <= hi
    print(f"  {label:<26} y {y0:.3f}-{y1:.3f}  white share {share:.3f}  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(label)


def region(x0, x1, y0, y1, pred, label, thresh, greater=True):
    tot = hit = 0
    for y in range(int(H * y0), int(H * y1), 2):
        for x in range(int(W * x0), int(W * x1), 2):
            tot += 1
            if pred(px[x, y]):
                hit += 1
    share = hit / max(1, tot)
    ok = share > thresh if greater else share < thresh
    print(f"  {label:<26} share {share:.3f} (need {'>' if greater else '<'}{thresh})  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(label)


def near(x_frac, y_frac, target, tol, label):
    x, y = int(W * x_frac), int(H * y_frac)
    hits = 0
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            r, g, b = px[min(W - 1, max(0, x + dx)), min(H - 1, max(0, y + dy))]
            if abs(r - target[0]) <= tol and abs(g - target[1]) <= tol and abs(b - target[2]) <= tol:
                hits += 1
    ok = hits >= 5
    print(f"  {label:<26} ({x_frac:.3f},{y_frac:.3f}) hits {hits}/49  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(label)


print("bands (caption ink):")
band_ink(0.025, 0.150, "top caption")
band_ink(0.850, 0.990, "bottom captions")

print("mascot — white body with a thick black outline (never-outlined white would blow out):")
region(0.260, 0.420, 0.500, 0.860,
       lambda c: c[0] > 232 and c[1] > 232 and c[2] > 230,
       "ghost body white", 0.28)
region(0.250, 0.435, 0.470, 0.890,
       lambda c: c[0] < 60 and c[1] < 45 and c[2] < 65,
       "ghost black outline", 0.05)

print("mascot coin — magenta disc with a white star inside it:")
region(0.365, 0.485, 0.640, 0.790,
       lambda c: c[0] > 170 and c[2] > 105 and c[1] < 95,
       "magenta coin", 0.10)
region(0.365, 0.485, 0.640, 0.790,
       lambda c: c[0] > 245 and c[1] > 245 and c[2] > 245,
       "white star on coin", 0.01)

print("HUD money pickup — bright green above the ghost's head:")
region(0.245, 0.485, 0.170, 0.360,
       lambda c: c[1] > 170 and c[1] - c[0] > 50 and c[1] - c[2] > 50,
       "money green", 0.02)

print("composition probes:")
near(0.500, 0.120, (44, 16, 72), 100, "sky top is deep plum")
near(0.828, 0.545, (255, 246, 210), 40, "sun disc right of centre")
near(0.828, 0.700, (150, 100, 112), 80, "sea under the sun")
near(0.700, 0.930, (86, 50, 42), 55, "sand at the foot")
near(0.048, 0.560, (26, 14, 40), 26, "left palm trunk")
near(0.940, 0.700, (26, 14, 40), 26, "right palm trunk")

print("judge's reading size (480 px a side) contrast:")
small = im.resize((480, 480), Image.BOX)
sp = small.load()
worst = 255
for y in range(int(480 * 0.850), int(480 * 0.990)):
    for x in range(0, 26):
        r, g, b = sp[x, y]
        worst = min(worst, (r + g + b) // 3)
print(f"  darkest caption-side pixel at 480 px: {worst}  {'ok (dark)' if worst < 130 else 'FAIL'}")
if worst >= 130:
    fails.append("caption contrast at 480")

print()
if fails:
    print("FAILED:", ", ".join(fails))
    sys.exit(1)
print("all measurements pass")
