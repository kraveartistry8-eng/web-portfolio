"""Tests for the hour maths behind the guide's clock (spec 2026-10-11-afterglow-guide-hour-design.md, §2).

Run: python3 tools/test_afterglow_hours.py
"""
import sys
import traceback

from afterglow_hours import HOURS, hour_at, sheet_times, stamp_times


def test_stops_are_the_hours():
    assert [hour_at(t) for t in (0, .30, .60, .84)] == HOURS


def test_ground_is_dark():
    assert hour_at(1) == "dark" and hour_at(1.2) == "dark"


def test_past_violet_runs_at_violet_rate():
    assert hour_at(.84 + .16 / 2) == "21:55"          # 312.5 min per unit past .84


def test_sheet_times_for_the_guide():
    assert sheet_times() == ["19:12", "19:19", "19:26", "19:34", "19:41", "19:50", "19:59", "20:08",
                             "20:20", "20:44", "21:08", "21:32", "21:56", "dark", "dark"]


def test_times_never_go_back():
    mins = [int(h[:2]) * 60 + int(h[3:]) for h in sheet_times() if h != "dark"]
    assert mins == sorted(mins)


def test_times_move_when_a_sheet_is_removed():
    assert sheet_times(14, 12)[11] != sheet_times()[11]



def test_stamp_times_follows_the_sheet_count():
    foot = '<footer class="foot"><span class="pg">01</span></footer>'
    for n in (14, 16):
        out = stamp_times(foot * n, 13)
        assert out.count('<span class="hr">') == n
        assert out.split('<span class="hr">')[n].startswith(sheet_times(n, 13)[-1])


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = 0
    for n, f in tests:
        try:
            f(); print("  pass ", n)
        except Exception:
            failed += 1; print("  FAIL ", n); traceback.print_exc()
    print(f"\n  {len(tests) - failed} pass, {failed} fail")
    sys.exit(1 if failed else 0)
