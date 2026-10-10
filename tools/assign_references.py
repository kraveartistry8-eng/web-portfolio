# -*- coding: utf-8 -*-
"""Measure every mood board reference and assign six to each palette stage.

A reference belongs on the sheet whose stage lightness it sits nearest, but only
if it is dark enough to sit in the guide at all: its upper-quartile OKLCH
lightness must be at or below the lightest stage (gold of last light, L 0.781).
Videos are measured on their poster frame, the frame that prints and the frame
reduced-motion readers see.

The manifest is the single record of what was measured. The build renders from
it and the audit reads it, so the two cannot disagree.

Run: python3 tools/assign_references.py
"""
import importlib.util
import io
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "brand" / "moodboard-media"
POSTERS = MEDIA / "posters"
TOKENS = ROOT / "brand" / "resources" / "design-tokens.json"
MANIFEST = ROOT / "brand" / "resources" / "imagery-manifest.json"
CEILING = 0.781
WANT = 6
GRID = 16

_spec = importlib.util.spec_from_file_location("ba", ROOT / "tools" / "brand_audit.py")
B = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(B)
except SystemExit:
    pass


def _pixels(path):
    """GRID x GRID rgb24 downsample of an image, as a list of (r, g, b)."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1",
         "-vf", "scale=%d:%d:flags=area" % (GRID, GRID), "-pix_fmt", "rgb24",
         "-f", "rawvideo", "-"], capture_output=True).stdout
    if len(raw) != GRID * GRID * 3:
        raise RuntimeError("could not read pixels from %s" % path)
    return [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]


def _aspect(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip()
    w, h = [int(v) for v in out.split(",")[:2]]
    return w / h


def _p75(values):
    v = sorted(values)
    return v[int(round(0.75 * (len(v) - 1)))]


def measure(path):
    """Upper-quartile OKLCH lightness, aspect and kind of one reference."""
    path = pathlib.Path(path)
    video = path.suffix.lower() == ".mp4"
    frame = POSTERS / (path.stem + ".jpg") if video else path
    lights = [B.oklch("#%02x%02x%02x" % px)[0] for px in _pixels(frame)]
    return {"l_p75": _p75(lights), "aspect": _aspect(path),
            "kind": "video" if video else "image"}


def pick(eligible, stage_l, want, stage="?"):
    """The `want` references nearest `stage_l`; ties break on filename.
    `eligible` is a list of dicts with "file" and "l_p75". Exits when the stage
    cannot be filled: a sheet with four frames is a defect, not a fallback."""
    if len(eligible) < want:
        sys.exit("stage %s has %d eligible references, needs %d"
                 % (stage, len(eligible), want))
    return sorted(eligible, key=lambda r: (abs(r["l_p75"] - stage_l), r["file"]))[:want]


def _entry(file, m):
    poster = ("posters/" + pathlib.Path(file).stem + ".jpg") if m["kind"] == "video" else None
    return {"file": file, "kind": m["kind"], "poster": poster,
            "l_p75": round(m["l_p75"], 4), "aspect": round(m["aspect"], 4)}


def assign(measured, stage_ls, want=WANT):
    """measured: {file: measurement}. stage_ls: {"1": L, ...}. Each reference is
    used once; stages fill in order, lightest first."""
    pool = [_entry(f, m) for f, m in sorted(measured.items()) if m["l_p75"] <= CEILING]
    out = {}
    for key in sorted(stage_ls):
        chosen = pick(pool, stage_ls[key], want, stage=key)
        out[key] = chosen
        used = {r["file"] for r in chosen}
        pool = [r for r in pool if r["file"] not in used]
    return {"stages": out}


def main():
    tokens = json.loads(io.open(TOKENS, encoding="utf-8").read())
    stages = tokens["color"]["stages"]
    stage_ls = {k: stages[k]["oklch"]["l"] for k in ("1", "2", "3", "4")}
    files = sorted(p for p in MEDIA.iterdir() if p.suffix.lower() in (".jpg", ".mp4"))
    measured = {p.name: measure(p) for p in files}
    man = assign(measured, stage_ls)
    MANIFEST.write_text(json.dumps(man, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return None


if __name__ == "__main__":
    main()
