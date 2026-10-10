# -*- coding: utf-8 -*-
"""Tests for the guide's photography tooling.

Run: python3 tools/test_guide_audit.py
"""
import pathlib
import sys

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


def test_short_clip_still_yields_a_frame():
    import make_posters
    # a clip shorter than one frame at the computed offset falls back to the last frame
    assert make_posters.offset(0.04) >= 0.0


def test_every_video_reference_has_a_nonempty_poster():
    import make_posters
    posters = make_posters.main()
    assert len(posters) == 13
    for v, p in posters.items():
        assert (MEDIA / "posters" / p).stat().st_size > 0


for t in (test_poster_offset_is_one_third, test_short_clip_still_yields_a_frame,
          test_every_video_reference_has_a_nonempty_poster):
    check(t)

print("\n".join("  PASS  " + m for m in PASSED))
if FAILED:
    print()
    print("\n".join("  FAIL  " + m for m in FAILED))
print()
print("  %d pass, %d fail" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
