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
    """One third of the clip. Never negative; a bogus duration yields 0."""
    return max(0.0, duration / 3.0)


def duration_of(video):
    """Container duration in seconds, or 0.0 when ffprobe reports none (N/A)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(video)],
        capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def _extract(video, dest, seek):
    # A stale poster must never pass for a fresh one if ffmpeg writes nothing.
    dest.unlink(missing_ok=True)
    scale = ("scale='if(gte(iw,ih),min(%d,iw),-2)':'if(gte(iw,ih),-2,min(%d,ih))'"
             % (LONG_EDGE, LONG_EDGE))
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y"] + seek + ["-i", str(video),
         "-frames:v", "1", "-vf", scale, "-q:v", "3", str(dest)],
        capture_output=True)
    return dest.exists() and dest.stat().st_size > 0


def extract_poster(video, dest, at=None):
    """Write one frame of `video` to `dest`: the frame at `at` seconds (default
    one third in), or the last available frame when none exists there (a seek
    past the end, or a container that overstates its duration)."""
    if at is None:
        at = offset(duration_of(video))
    if _extract(video, dest, ["-ss", "%.3f" % at]):
        return dest
    if _extract(video, dest, ["-sseof", "-0.1"]):
        return dest
    if _extract(video, dest, []):  # single-frame file: its only frame
        return dest
    raise RuntimeError("no frame could be extracted from %s" % video)


def main(media=MEDIA, out=POSTERS):
    out.mkdir(exist_ok=True)
    made = {}
    for video in sorted(media.glob("*.mp4")):
        dest = out / (video.stem + ".jpg")
        extract_poster(video, dest)
        made[video.name] = dest.name
    return made


if __name__ == "__main__":
    for v, p in main().items():
        print("%s -> %s" % (v, p))
