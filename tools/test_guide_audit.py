# -*- coding: utf-8 -*-
"""Tests for the guide's photography tooling.

Run: python3 tools/test_guide_audit.py
"""
import json
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


def _m(l, n=0):
    return {"l_p75": l, "aspect": 1.5, "kind": "image"}


def _exit_message(fn):
    try:
        fn()
    except SystemExit as e:
        return str(e.code)
    raise AssertionError("expected the build to exit")


def test_upper_quartile_matches_the_known_measurement():
    import assign_references
    # measured on the poster frame (16x16), not frame 0 (which gives 0.825)
    m = assign_references.measure(MEDIA / "mPNk84g.mp4")
    assert abs(m["l_p75"] - 0.871) < 0.01, m
    assert m["kind"] == "video"


def test_every_assigned_reference_clears_the_ceiling():
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    assert sorted(man["stages"]) == ["1", "2", "3", "4"]
    seen = []
    for stage, refs in man["stages"].items():
        assert len(refs) == 6, "stage %s has %d" % (stage, len(refs))
        for r in refs:
            assert r["l_p75"] <= 0.781, r
            seen.append(r["file"])
    assert len(set(seen)) == 24, "a reference was used twice"


def test_ceiling_excludes_bright_references():
    import assign_references
    measured = {"f%02d.jpg" % i: _m(0.5) for i in range(24)}
    measured["bright.jpg"] = _m(0.7811)
    man = assign_references.assign(measured, {"1": 0.78, "2": 0.62, "3": 0.46, "4": 0.30})
    assert "bright.jpg" not in [r["file"] for rs in man["stages"].values() for r in rs]


def test_assignment_is_deterministic():
    import assign_references
    path = ROOT / "brand/resources/imagery-manifest.json"
    before = path.read_text()
    assign_references.main()
    assert path.read_text() == before


def test_a_starved_stage_fails_the_build():
    import assign_references
    msg = _exit_message(lambda: assign_references.pick([], 0.3, 6, stage="4"))
    assert "stage 4" in msg and "0" in msg, msg
    # through assign(): 18 eligible fills stages 1 to 3, leaves stage 4 with 0
    measured = {"f%02d.jpg" % i: _m(0.5) for i in range(18)}
    measured.update({"bright%d.jpg" % i: _m(0.9) for i in range(10)})
    msg = _exit_message(lambda: assign_references.assign(
        measured, {"1": 0.78, "2": 0.62, "3": 0.46, "4": 0.30}))
    assert "stage 4" in msg and "0 eligible" in msg, msg


def test_equidistant_stages_assign_identically_whatever_the_order():
    import assign_references
    # a/b/c each sit exactly between stages 2 and 3 (0.60 and 0.40 around 0.50),
    # so distance cannot decide. Only the filename tie-break can.
    names = ["c.jpg", "a.jpg", "e.jpg", "b.jpg", "d.jpg", "f.jpg", "g.jpg"]
    stage_ls = {"1": 0.60, "2": 0.40}
    runs = []
    for order in (names, list(reversed(names)), sorted(names)):
        measured = {n: _m(0.50) for n in order}
        man = assign_references.assign(measured, stage_ls, want=3)
        runs.append(json.dumps(man, sort_keys=True))
    assert runs[0] == runs[1] == runs[2]
    assert [r["file"] for r in json.loads(runs[0])["stages"]["1"]] == ["a.jpg", "b.jpg", "c.jpg"]
    # pick() on its own, fed in unsorted order, so assign()'s own sort cannot mask it
    refs = [{"file": n, "l_p75": 0.50} for n in names]
    got = [r["file"] for r in assign_references.pick(refs, 0.60, 3)]
    assert got == ["a.jpg", "b.jpg", "c.jpg"], got


for t in (test_poster_offset_is_one_third, test_seek_past_the_end_yields_the_last_frame,
          test_single_frame_clip_yields_a_frame, test_stale_poster_is_not_accepted,
          test_posters_are_one_per_video_and_capped, test_committed_posters_match_the_videos,
          test_upper_quartile_matches_the_known_measurement,
          test_every_assigned_reference_clears_the_ceiling,
          test_ceiling_excludes_bright_references, test_assignment_is_deterministic,
          test_a_starved_stage_fails_the_build,
          test_equidistant_stages_assign_identically_whatever_the_order):
    check(t)

print("\n".join("  PASS  " + m for m in PASSED))
if FAILED:
    print()
    print("\n".join("  FAIL  " + m for m in FAILED))
print()
print("  %d pass, %d fail" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
