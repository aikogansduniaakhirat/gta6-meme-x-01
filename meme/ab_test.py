#!/usr/bin/env python3
"""Score candidate meme variants with the bounty's judge models.

Each variant is rendered with a different PITCH, then every vision model that
works on jerouter is asked for the rubric score. The variant with the highest
mean across models wins, which keeps one model's taste from deciding alone.

Usage: ab_test.py "<pitch 1>" "<pitch 2>" ...
Writes out/ab_results.json and prints a table.
"""

import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

MODELS = ("grok-4.7", "gemini-3.8-flash")


def load_renderer():
    spec = importlib.util.spec_from_file_location(
        "make_meme", os.path.join(HERE, "make_meme.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_judge():
    spec = importlib.util.spec_from_file_location(
        "judge_preflight", os.path.join(HERE, "judge_preflight.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_scores(text):
    """Pull the integer rubric scores out of the judge's plain-text reply."""
    out = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip()
        if key in ("funny", "about_gta6", "sells_makefun", "readable", "clean"):
            digits = "".join(ch for ch in val if ch.isdigit())
            if digits:
                out[key] = int(digits)
    return out


def main():
    pitches = sys.argv[1:]
    if not pitches:
        raise SystemExit('usage: ab_test.py "<pitch>" "<pitch>" ...')

    renderer = load_renderer()
    judge = load_judge()
    results = []

    for i, pitch in enumerate(pitches, 1):
        os.environ["PITCH"] = pitch
        path = renderer.build()
        variant_path = os.path.join(renderer.OUT, f"variant_{i}.png")
        shutil.copy(path, variant_path)
        row = {"variant": i, "pitch": pitch, "scores": {}, "notes": {}}
        for model in MODELS:
            judge.MODEL = model
            try:
                text = judge.ask(variant_path, judge.RUBRIC)
            except Exception as exc:
                row["notes"][model] = f"error: {exc}"
                continue
            scores = parse_scores(text)
            row["scores"][model] = scores
            for line in text.splitlines():
                if line.lower().startswith(("one_line_fix", "layout_problems")):
                    row["notes"][model] = row["notes"].get(model, "") + line + " "
        flat = [v for s in row["scores"].values() for v in s.values()]
        row["mean"] = round(sum(flat) / len(flat), 2) if flat else 0.0
        results.append(row)
        print(f"v{i} mean={row['mean']:<5} {pitch}")

    results.sort(key=lambda r: r["mean"], reverse=True)
    out = os.path.join(renderer.OUT, "ab_results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print("\nranking:")
    for r in results:
        print(f"  {r['mean']:<5} v{r['variant']}  {r['pitch']}")
        for m, n in r["notes"].items():
            print(f"        {m}: {n}")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
