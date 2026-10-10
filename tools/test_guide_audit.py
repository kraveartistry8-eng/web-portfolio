# -*- coding: utf-8 -*-
"""Tests for the guide's photography tooling.

Run: python3 tools/test_guide_audit.py
"""
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "brand" / "moodboard-media"
sys.path.insert(0, str(ROOT / "tools"))

PASSED, FAILED = [], []


def check(fn):
    try:
        fn()
        PASSED.append(fn.__name__)
    except Exception as e:  # noqa: BLE001 - report every failure, keep going
        FAILED.append("%s: %r" % (fn.__name__, e))


def test_poster_offset_is_one_third():
    import make_posters
    assert make_posters.offset(9.0) == 3.0


def _clip(path, extra):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "color=c=gray:s=2000x1000:r=25"] + extra + [str(path)],
                   check=True, capture_output=True)


def _mean_grey(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=1:1",
                          "-pix_fmt", "gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return out[0]


def _size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return [int(v) for v in out.strip().split(",")]


def test_seek_past_the_end_yields_the_last_frame():
    import make_posters
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        # fades in from black then negated: frame 0 is white, later frames darker
        _clip(d / "tiny.mp4", ["-t", "0.2", "-vf", "fade=t=in:st=0:d=0.2,negate"])
        dest = d / "tiny.jpg"
        # forces the fallback: nothing exists 10s into a 0.2s clip
        make_posters.extract_poster(d / "tiny.mp4", dest, at=10.0)
        assert dest.stat().st_size > 0
        # frame 0 is pure white (255) after negate; any later frame is darker. Frame 0 would
        # mean the fallback chain fell through to its final rung.
        assert _mean_grey(dest) < 240, _mean_grey(dest)


def test_single_frame_clip_yields_a_frame():
    import make_posters
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        _clip(d / "one.mp4", ["-frames:v", "1"])
        dest = d / "one.jpg"
        make_posters.extract_poster(d / "one.mp4", dest)
        make_posters.extract_poster(d / "one.mp4", dest, at=5.0)
        assert dest.stat().st_size > 0


def test_stale_poster_is_not_accepted():
    import make_posters
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "bad.mp4").write_bytes(b"not a video")
        (d / "bad.jpg").write_bytes(b"stale")
        try:
            make_posters.extract_poster(d / "bad.mp4", d / "bad.jpg")
        except RuntimeError:
            return
        raise AssertionError("a stale poster was accepted for an unreadable clip")


def test_posters_are_one_per_video_and_capped():
    import make_posters
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        posters = make_posters.main(out=out)  # reads the real clips, writes to a temp dir
        videos = sorted(p.name for p in MEDIA.glob("*.mp4"))
        assert sorted(posters) == videos and len(posters) == 13
        assert sorted(p.name for p in out.glob("*.jpg")) == sorted(posters.values())
        for p in posters.values():
            assert (out / p).stat().st_size > 0
            assert max(_size(out / p)) <= 984, p


def test_committed_posters_match_the_videos():
    # read-only: the committed assets are what the guide ships
    for v in MEDIA.glob("*.mp4"):
        poster = MEDIA / "posters" / (v.stem + ".jpg")
        assert poster.stat().st_size > 0, poster
        assert max(_size(poster)) <= 984, poster


for t in (test_poster_offset_is_one_third, test_seek_past_the_end_yields_the_last_frame,
          test_single_frame_clip_yields_a_frame, test_stale_poster_is_not_accepted,
          test_posters_are_one_per_video_and_capped, test_committed_posters_match_the_videos):
    check(t)

print("\n".join("  PASS  " + m for m in PASSED))
if FAILED:
    print()
    print("\n".join("  FAIL  " + m for m in FAILED))
print()
print("  %d pass, %d fail" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
