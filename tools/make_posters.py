# -*- coding: utf-8 -*-
"""Extract one deterministic poster frame per video reference.

Chromium prints a <video> as whichever frame happens to be showing, so the
printed guide swaps each video for its poster. The poster is also the frame
reduced-motion readers see, and the frame the brightness rule measures.

Offset is one third of the clip, the offset the mood board uses. Longest edge
984px: a 3.28in print slot at 300dpi. Larger is dead weight in the PDF.

Run: python3 tools/make_posters.py
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "brand" / "moodboard-media"
POSTERS = MEDIA / "posters"
LONG_EDGE = 984


def offset(duration):
    """One third of the clip, clamped to start inside it."""
    return max(0.0, min(duration / 3.0, duration))


def duration_of(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def _extract(video, dest, seek):
    scale = ("scale='if(gte(iw,ih),min(%d,iw),-2)':'if(gte(iw,ih),-2,min(%d,ih))'"
             % (LONG_EDGE, LONG_EDGE))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y"] + seek + ["-i", str(video),
         "-frames:v", "1", "-vf", scale, "-q:v", "3", str(dest)],
        capture_output=True, check=True)
    return dest.exists() and dest.stat().st_size > 0


def main():
    POSTERS.mkdir(exist_ok=True)
    made = {}
    for video in sorted(MEDIA.glob("*.mp4")):
        dest = POSTERS / (video.stem + ".jpg")
        if not _extract(video, dest, ["-ss", "%.3f" % offset(duration_of(video))]):
            # seek landed past the last frame: take the last one instead
            if not _extract(video, dest, ["-sseof", "-0.1"]):
                raise RuntimeError("no frame could be extracted from %s" % video.name)
        made[video.name] = dest.name
    return made


if __name__ == "__main__":
    for v, p in main().items():
        print("%s -> %s" % (v, p))
