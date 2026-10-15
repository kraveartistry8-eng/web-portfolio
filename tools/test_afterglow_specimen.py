"""Tests for tools/afterglow_specimen.py (spec 2026-10-12-afterglow-guide-specimen-design.md). Run: python3 tools/test_afterglow_specimen.py"""
import os, re, subprocess, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import afterglow_specimen as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_built = {}


def built():
    if "html" not in _built:
        _built["html"] = A.build()[0]
    return _built["html"]


def base_deck():
    return subprocess.run(["git", "show", f"{A.BASE_REF}:brand/2026-10-10-density-b1-column.html"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout


def test_mark_svg_width():
    s = A.mark_svg(120)
    assert 'width="120"' in s and 'height="76"' in s, s[:160]
    try:
        A.mark_svg(40)
    except AssertionError:
        return
    raise AssertionError("mark_svg(40) should refuse a mark under 48 px")


def test_mark_svg_ink():
    assert "#080808" in A.mark_svg(60, "dark") and "#EEECEA" not in A.mark_svg(60, "dark")


def test_lost_strings_finds_a_drop():
    assert A.lost_strings("<p>a b</p><p>c</p>", "<p>a  b</p>") == ["c"]


def test_lost_strings_honours_rewrites():
    old = next(iter(A.REWRITES))
    assert A.lost_strings(f"<p>{old}</p>", "<p>else</p>") == []


def test_build_preserves_everything():
    lost = A.lost_strings(base_deck(), built())
    assert lost == [], lost[:10]


def _sheet(n):
    return A.sections(built())[n - 1]


def test_colour_page_08():
    s = _sheet(8)
    assert "hpanel" not in s, "sheet 8 still carries the hour panel"
    srcs = re.findall(r'<img[^>]+src="moodboard-media/([^"/]+)\.jpg"', s)
    assert srcs == ["wRU1tGM", "0x4Ubi2", "_SNh4mJ", "GVEgivk", "p-PXFnN"], srcs
    assert re.findall(r'<p class="stamp">(.*?)</p>', s) == list(A.STAMPS[0])
    assert re.findall(r'<p class="hour[^"]*">(.*?)</p>', s) == ["19:12"]
    assert re.search(r'<p class="cap[^"]*">The last direct sun: warm, low and close to the skin. A set opens here.</p>', s)
    assert '<p class="tag">' in s and "five frames, warm to cool" in s


SRC = lambda s: re.findall(r'<img[^>]+src="moodboard-media/(?:posters/)?([^"/]+)\.jpg"', s)


def test_colour_pages():
    want = {1: ["tLwiMVf", "udQHGQp", "6pLfDFq", "f3MgZ_1", "Zul1TsA"], 2: ["gE_ypMW", "QfZU9JX", "HNrkkNB", "eXM8fJo", "Y1VfHK4"],
            3: ["7BF3FrZ", "0M3EBK4", "GU1xDFf", "fC3QclQ", "r-0SzGb"]}
    for k, srcs in want.items():
        s = _sheet(8 + k)
        assert "hpanel" not in s and 'class="strip"' in s, f"sheet {8 + k} is not a strip"
        assert SRC(s) == srcs, (k, SRC(s))
        assert re.findall(r'<p class="stamp">(.*?)</p>', s) == list(A.STAMPS[k]), k
        assert re.findall(r'<p class="hour[^"]*">(.*?)</p>', s) == [A.B.HOURS[k]], k


def test_art_direction():
    s = _sheet(7)
    assert SRC(s) == ["OOqXr-G", "USalI5W", "fMmCZqp", "e4jFDHF"], SRC(s)
    assert re.findall(r'<p class="stamp">(.*?)</p>', s) == ["L 0.378", "L 0.342", "L 0.205"]
    assert re.search(r'<p class="cap[^"]*">One light source, and it is falling.</p>', s)
    assert "adrules" not in s, "the rules list stays on sheet 7"


def test_nineteen_sheets():
    from afterglow_hours import sheet_times
    secs = A.sections(built())
    assert len(secs) == 19, len(secs)
    got = [re.search(r'<span class="hr">(.*?)</span>', x).group(1) for x in secs]
    assert got == sheet_times(19), got


def test_reference_order():
    heads = [re.search(r'<footer class="foot"><span class="mark">Afterglow</span><span>(.*?)</span>', _sheet(n)).group(1) for n in range(16, 20)]
    assert heads == ["Colour", "Type and layout", "Imagery", "Wordmark, mark, products and voice"], heads
    for n in range(16, 20):
        assert 'class="rlead"' in _sheet(n) and 'style="background:' in _sheet(n), n


def test_magenta_ends_the_last_sheet():
    assert "#BF15B7" in _sheet(19).split(">", 1)[0] and "#BF15B7" not in _sheet(15).split(">", 1)[0]


def test_nothing_waits_on_the_last_sheet():
    assert "refhold" not in built()


def _cap(s):
    return [re.sub(r"<[^>]+>", "", c) for c in re.findall(r'<p class="cap[^"]*">(.*?)</p>', s)]


def test_sheets_01_06():
    s = _sheet(1)
    assert "<svg" in s and "<img" not in s and "bcover" in s.split(">", 1)[0]
    assert _cap(s) == ["One fragrance in four stages, from 19:12 until it is dark."], _cap(s)
    s = _sheet(2)
    assert SRC(s) == ["ZY6XxOv"], SRC(s)
    assert _cap(s) == ["The mark is three triangles: the bottle, the A and the G. The wordmark is Instrument Serif, widened to 150%."], _cap(s)
    s = _sheet(3)
    assert re.findall(r'<p class="hour[^"]*">(.*?)</p>', s) == A.B.HOURS
    assert "Four hours of one evening" in s and "<dl>" not in s
    s = _sheet(4)
    assert _cap(s) == ["Gold to violet, never reversed."] and SRC(s) == [], (_cap(s), SRC(s))
    assert [h for h in re.findall(r'<b class="fhr[^"]*"[^>]*>(.*?)</b>', s)] == A.B.HOURS + ["dark"]
    s = _sheet(5)
    assert '<p class="spx serif">19:12</p>' in s and '<p class="spx sans">The light only ever deepens.</p>' in s and SRC(s) == []
    assert "Instrument Serif &middot; Space Grotesk" in s
    s = _sheet(6)
    assert '<p class="rspec">The light only brightens where the ember is.</p>' in s and SRC(s) == ["Eje8BSd"], SRC(s)
    assert "Twelve columns &middot; eight spacing steps" in s
    assert "qNdZUES" in _sheet(17)


def test_photographs_once():
    srcs = SRC(built())
    dup = sorted({x for x in srcs if srcs.count(x) > 1})
    assert not dup and len(srcs) == 31, (dup, len(srcs))


def test_sheets_12_15():
    s = _sheet(12)
    assert SRC(s) == ["R6euaYP"] and _cap(s) == ["Move, and it lights. Stop, and in 0.7 seconds it goes out."], (SRC(s), _cap(s))
    s = _sheet(13)
    assert SRC(s) == ["3ASXlcU-trim"] and "Don&rsquo;t" in s, SRC(s)
    assert _cap(s) == ["A frame rejected from the set: cold, lit from everywhere, and nothing in it falls."], _cap(s)
    s = _sheet(14)
    assert SRC(s) == ["bNQYoLz"], SRC(s)
    assert re.findall(r'<p class="lline">(.*?)</p>', s) == ["19:12 &mdash; Eau de parfum, 50 ml"]
    assert [int(w) for w in re.findall(r'<svg class="amark" width="(\d+)"', s)] == [150, 48, 56]
    assert "The label leads &middot; card and poster follow" in s
    s = _sheet(15)
    assert SRC(s) == ["PNTk-Dh-bottle"] and _cap(s) == ["Unhurried and physical. It names heat, light, breath and skin."], (SRC(s), _cap(s))


def test_held_blocks_are_balanced():
    built()
    bad = [m[:60] for _, m in A.REF_HOLD if m.count("</div>") != len(re.findall(r"<div\b", m))]
    assert not bad, bad


def test_label_mark_is_dark_on_gold():
    label = re.search(r'<figure class="label">.*?</figure>', _sheet(14), re.S).group(0)
    assert "#080808" in label and "#EEECEA" not in label, "spec §2: the mark is #080808 on gold"


def test_lite_runs_the_satin_not_v23():
    html = A.build_lite()[0]
    assert "window.EmberSatin=" in html, "the satin bundle is not inlined"
    assert re.search(r'EmberSatin\.start\(document\.querySelector\("main\.deck"\)', html), "no start call on the deck"
    assert "EmberEngine" not in html, "the v23 engine is still in"
    assert 'id="ember"' not in html, "the v23 container is still in"
    assert "the ember: a canvas behind the sheets" not in html and "--li:0" not in html, "the v23 ember CSS is still in"
    assert ".ember-on .sheet" not in html, "the v23 transparent-sheet rule is still in"


if __name__ == "__main__":
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_")]
    failed = 0
    for n, f in tests:
        try:
            f(); print("  pass ", n)
        except Exception:
            failed += 1; print("  FAIL ", n); traceback.print_exc()
    print(f"\n  {len(tests) - failed} pass, {failed} fail")
    sys.exit(1 if failed else 0)
