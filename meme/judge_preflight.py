#!/usr/bin/env python3
"""Pre-flight the meme against the bounty's own judge model.

The bounty names z-ai/glm-5.3-flash as the model that scores every entry, and
jerouter serves the same glm-5.3-flash with vision. Asking it for a verdict
before posting is the closest thing to a local grade: it is not the sealed
judge prompt, but it is the same eyes.

Usage: judge_preflight.py <image.png> [--rubric]
"""

import base64
import json
import os
import sys
import urllib.request

BASE = "https://je.jerouter.web.id/v1"
MODEL = "gemini-3.8-flash"
KEY = os.environ.get("JEROUTER_KEY", "")

RUBRIC = """You are judging a GTA 6 meme posted on X for a make.fun bounty.
Rank by these criteria, most important first.
1. make.fun in the picture: the picture shows make.fun's ghost (a white ghost
   with a thick black outline, two black four-pointed sparkle eyes and a round
   hand holding a magenta coin with a white star), or make.fun's logo or its
   name, recognisably. A picture showing none of them loses to any that does.
2. Funny: a real joke a GTA fan gets in a second.
3. About GTA 6 specifically: the thirteen-year wait since GTA V, the delays,
   launch-day sick days, the download size, the price, Leonida and its Florida
   energy, Vice City, Jason and Lucia. Not a generic gaming joke with "GTA 6"
   pasted on.
4. Sells make.fun: makes a reader want to try make.fun and makes clear that
   people and their AI agents can earn money there.
5. Short and readable: the caption reads at a glance and is spelled right.
6. Original.
7. A clean image: sharp, uncluttered, nothing important cut off, and make.fun's
   ghost, logo or name worked into the scene rather than pasted on as a sticker.
Answer in this shape exactly:
makefun_in_picture: yes|no
funny: <1-10>
about_gta6: <1-10>
sells_makefun: <1-10>
readable: <1-10>
clean: <1-10>
what_the_ghost_looks_like: <one sentence, is it recognisably the ghost?>
layout_problems: <cut off text, overlaps, clutter, or none>
one_line_fix: <the single change that would raise the score most>"""


def ask(image_path, prompt):
    with open(image_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    body = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": "data:image/png;base64," + b64}},
            ],
        }],
        "max_tokens": 900,
    }
    req = urllib.request.Request(
        BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + KEY},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: judge_preflight.py <image.png>")
    if not KEY:
        raise SystemExit("JEROUTER_KEY is not set")
    print(ask(sys.argv[1], RUBRIC))


if __name__ == "__main__":
    main()
