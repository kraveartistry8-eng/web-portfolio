# -*- coding: utf-8 -*-
"""Tests for the guide's photography tooling.

Run: python3 tools/test_guide_audit.py
"""
import json
import os
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
    # SystemExit too: the build fails loudly with sys.exit, and a tested path that exits
    # would otherwise end the run, lose the later tests and the summary line.
    except (Exception, SystemExit) as e:  # noqa: BLE001 - report every failure, keep going
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


def _m(l):
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


def test_a_reference_exactly_at_the_ceiling_is_eligible():
    import assign_references
    measured = {"edge.jpg": _m(0.781)}
    measured.update({"f%02d.jpg" % i: _m(0.2) for i in range(5)})
    man = assign_references.assign(measured, {"1": 0.78}, want=6)
    assert "edge.jpg" in [r["file"] for r in man["stages"]["1"]]


def test_assignment_is_deterministic():
    import assign_references
    path = ROOT / "brand/resources/imagery-manifest.json"
    # read-only: builds the text and compares, never touches the committed manifest
    assert assign_references.build_manifest() == path.read_text()
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "m.json"
        assign_references.main(out=out)
        assert out.read_text() == path.read_text()


def test_a_starved_stage_fails_the_build():
    import assign_references
    msg = _exit_message(lambda: assign_references.pick([], 0.3, 6, stage="4"))
    assert "stage 4" in msg and "0" in msg, msg
    # through assign(): 18 eligible fills stages 1 to 3, leaves stage 4 with 0
    measured = {"f%02d.jpg" % i: _m(0.5) for i in range(18)}
    measured.update({"bright%d.jpg" % i: _m(0.9) for i in range(10)})
    msg = _exit_message(lambda: assign_references.assign(
        measured, {"1": 0.78, "2": 0.62, "3": 0.46, "4": 0.30}))
    assert "stage 4" in msg and "0 eligible references remaining" in msg, msg


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


def test_twenty_sheets_and_the_fall_still_divides():
    import build_guide
    html = build_guide.build()
    assert html.count('<section class="sheet') == 20, html.count('<section class="sheet')
    assert build_guide.N == 20
    # every sheet carries its own folio, so a sheet dropped from the list cannot hide
    for n in range(1, 21):
        assert 'data-sheet="%02d"' % n in html, n


def test_each_stage_sheet_carries_six_figures():
    import build_guide
    html = build_guide.build()
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    for stage in ("1", "2", "3", "4"):
        assert html.count('data-stage="%s"' % stage) == 6, stage
        # the six are the manifest's six, not any six
        for r in man["stages"][stage]:
            assert 'src="moodboard-media/%s"' % r["file"] in html, r["file"]


def test_a_video_is_emitted_as_a_swap_pair_inside_the_grid():
    import re
    import build_guide
    html = build_guide.build()
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    vids = [r for rs in man["stages"].values() for r in rs if r["kind"] == "video"]
    assert vids
    # the print swap only exists under .imgs, so the pair must be emitted inside one
    for imgs in re.findall(r'<div class="imgs">(.*?)\n    </div>\n    <footer', html, re.S):
        assert imgs.count('class="scr"') == imgs.count('class="prt"'), "unpaired"
    inside = "".join(re.findall(r'<div class="imgs">(.*?)\n    </div>\n    <footer',
                                html, re.S))
    assert inside.count('class="scr"') == len(vids), (inside.count('class="scr"'), len(vids))
    for v in vids:
        assert '<img class="prt" src="moodboard-media/%s"' % v["poster"] in inside, v["file"]


def test_a_missing_reference_file_fails_the_build_naming_it():
    import build_guide
    msg = _exit_message(lambda: build_guide.figure({"file": "nope.jpg", "kind": "image"}))
    assert "nope.jpg" in msg, msg
    # a video whose poster is gone must fail too, since print would show a broken image
    msg = _exit_message(lambda: build_guide.figure(
        {"file": "mPNk84g.mp4", "kind": "video", "poster": "posters/gone.jpg"}))
    assert "gone.jpg" in msg, msg
    msg = _exit_message(lambda: build_guide.figure(
        {"file": "mPNk84g.mp4", "kind": "video", "poster": None}))
    assert "mPNk84g.mp4" in msg and "poster" in msg, msg


def test_stage_images_state_their_role_to_a_screen_reader():
    import build_guide
    html = build_guide.build()
    for stage, name in (("1", "Gold of last light"), ("4", "Deep violet")):
        for k in range(1, 7):
            assert 'Reference %d of 6 for %s"' % (k, name) in html, (stage, k)
    assert 'aria-hidden' not in html.split('<main')[1]


def test_each_stage_sheet_stands_on_its_own_stage_flat():
    import re
    import build_guide
    html = build_guide.build()
    grounds = re.findall(r'<section class="sheet (dark|light) imagery" data-sheet="\d+" '
                         r'style="background:(#[0-9A-Fa-f]{6})">\n    <div class="stagehead">',
                         html)
    want = [build_guide.C["stages"][k]["value"] for k in "1234"]
    assert [g for _, g in grounds] == want, grounds
    # ink is measured on that flat colour, not carried over from the fall slice
    for (tone, g), i in zip(grounds, (12, 13, 14, 15)):
        assert tone == build_guide.ink(i, g), (i, tone)
    assert [t for t, _ in grounds] == ["dark", "dark", "light", "light"], grounds
    # the page is the specimen; a chip of the ground drawn on the ground is not shown
    assert '<span class="stageread">#D8B260 &middot; L 0.781</span>' in html
    assert 'class="stageread"><span' not in html


def test_the_brightness_rule_names_the_upper_quartile():
    import build_guide
    html = build_guide.build().lower()
    # the opener's own sentence: the s_print bullet also says "upper quartile", so the bare
    # phrase would survive the opener's rule being deleted
    assert ("the upper quartile of an image's lightness sits at or below the gold of last "
            "light") in html
    assert "up to a quarter of the frame may pass it" in html
    assert "brightest value in an image" not in html
    # the L value still interpolates from the token rather than being typed in
    assert "gold of last light, l %.3f" % build_guide.B.oklch(build_guide.RAMP[0])[0] in html


# ---------------------------------------------------------------- the six audit checks
# A check that cannot fail is worse than none. Each case below breaks the document in the one
# way its check guards against, audits that copy, and asserts that this check fails and no
# other new one does. The unmutated document is audited first and must pass all six, or a
# check that fails on everything would look like it bites.
NEW_CHECKS = ("image_never_brightens", "image_on_ground", "poster_in_print",
              "caption_contrast", "grid_ratio_holds", "footer_in_page")
_BASE = {}


def _render_pdf(doc):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "render.py"), str(doc)],
                       capture_output=True, text=True)
    assert "console errors: none" in r.stdout, r.stdout + r.stderr


def _audit(html, manifest=None, pdf="render"):
    """Audit a copy of the document. pdf is 'render' (print the copy), or a path to reuse."""
    import build_guide
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "moodboard-media").symlink_to(MEDIA)  # the document's relative URLs resolve
        doc = d / "guide.html"
        doc.write_text(html if html is not None else build_guide.build(), encoding="utf-8")
        env = {"GUIDE_AUDIT_DOC": str(doc), "GUIDE_AUDIT_PDF": str(d / "guide.pdf"),
               "GUIDE_AUDIT_MANIFEST": str(ROOT / "brand/resources/imagery-manifest.json")}
        if manifest is not None:
            (d / "m.json").write_text(json.dumps(manifest))
            env["GUIDE_AUDIT_MANIFEST"] = str(d / "m.json")
        if pdf == "render":
            _render_pdf(doc)
        else:
            (d / "guide.pdf").write_bytes(pathlib.Path(pdf).read_bytes())
            os.utime(d / "guide.pdf", None)  # newer than the document, so not stale
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "guide_audit.py")],
                           capture_output=True, text=True, env=dict(os.environ, **env))
        out = {}
        for line in r.stdout.splitlines():
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0] in ("PASS", "FAIL"):
                out[parts[1]] = (parts[0], parts[2])
        assert out, r.stdout + r.stderr
        return out, (d / "guide.pdf").read_bytes() if (d / "guide.pdf").exists() else None


def _baseline():
    if "out" not in _BASE:
        import build_guide
        _BASE["html"] = build_guide.build()
        _BASE["out"], pdf = _audit(_BASE["html"])
        _BASE["pdf"] = pathlib.Path(tempfile.mkdtemp()) / "base.pdf"
        _BASE["pdf"].write_bytes(pdf)
    return _BASE


def _css(extra):
    html = _baseline()["html"]
    assert "</style>\n</head>" in html
    return html.replace("</style>\n</head>", extra + "\n</style>\n</head>", 1)


def _bites(target, html=None, manifest=None, rerender=True, expect=None):
    base = _baseline()
    out, _ = _audit(html if html is not None else base["html"], manifest,
                    pdf="render" if rerender else str(base["pdf"]))
    failed = sorted(k for k in NEW_CHECKS if out.get(k, ("?",))[0] != "PASS")
    assert failed == [target], "wanted only %s to fail, got %s" % (target, failed)
    msg = out[target][1]
    if expect:
        assert expect in msg, "%s failed, but not for the reason under test: %s" % (target, msg)
    print("  bites  %s  %s" % (target, msg))


def test_unmutated_document_passes_all_six():
    out = _baseline()["out"]
    assert [k for k in NEW_CHECKS if k not in out] == [], "a check did not report"
    assert [(k, out[k]) for k in NEW_CHECKS if out[k][0] != "PASS"] == []
    assert not [k for k, v in out.items() if v[0] == "FAIL"], out


def test_a_measured_ceiling_breach_fails_image_never_brightens():
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    man["stages"]["2"][0]["l_p75"] = 0.85
    _bites("image_never_brightens", manifest=man, rerender=False, expect="over the ceiling")


def test_an_unmeasured_image_fails_image_never_brightens():
    html = _baseline()["html"]
    man = json.loads((ROOT / "brand/resources/imagery-manifest.json").read_text())
    held = {r["file"] for rs in man["stages"].values() for r in rs}
    stray = sorted(f.name for f in MEDIA.glob("*.jpg") if f.name not in held)[0]
    assert 'src="moodboard-media/ZY6XxOv.jpg"' in html
    swapped = html.replace('src="moodboard-media/ZY6XxOv.jpg"',
                           'src="moodboard-media/%s"' % stray, 1)
    _bites("image_never_brightens", html=swapped, rerender=False, expect=stray)


def test_an_image_on_the_edge_fails_image_on_ground():
    # translate, not margin: it moves the paint and leaves the layout, so the slot keeps its
    # ratio and nothing else about the page changes. Inset becomes exactly zero.
    css = ('[data-sheet="13"] .imgs > figure:first-child{transform:translateX(calc(-1 * var(--pad)))}'
           '@media print{[data-sheet="13"] .imgs > figure:first-child{transform:translateX(-0.5in)}}')
    _bites("image_on_ground", html=_css(css), expect="0 px from the edge")


def test_a_print_only_edge_touch_fails_image_on_ground():
    css = '@media print{[data-sheet="13"] .imgs > figure:first-child{transform:translateX(-0.5in)}}'
    _bites("image_on_ground", html=_css(css), expect="in print")


def test_a_video_without_its_poster_fails_poster_in_print():
    import re
    html = _baseline()["html"]
    cut, n = re.subn(r'\n *<img class="prt" src="moodboard-media/posters/[^"]+" alt="[^"]*">',
                     "", html, count=1)
    assert n == 1
    _bites("poster_in_print", html=cut, expect="prints no poster")


def test_a_reading_set_in_its_own_ground_fails_caption_contrast():
    _bites("caption_contrast", html=_css('[data-sheet="13"] .stageread{color:#D8B260}'),
           rerender=False, expect="1.00:1")


def test_a_slot_at_4_3_fails_grid_ratio_holds():
    _bites("grid_ratio_holds",
           html=_css('[data-sheet="14"] .imgs > figure:nth-child(2){aspect-ratio:4/3}'),
           expect="1.333")


def test_a_slot_wrong_only_on_a_phone_fails_grid_ratio_holds():
    # the audit measures four widths; one that only measured desktop would miss this
    css = ('@media (max-width:700px){[data-sheet="14"] .imgs > figure:nth-child(2)'
           '{aspect-ratio:4/3}}')
    _bites("grid_ratio_holds", html=_css(css), rerender=False, expect="at 390px")


def test_a_slot_wrong_only_in_print_fails_grid_ratio_holds():
    css = '@media print{[data-sheet="14"] .imgs > figure:nth-child(2){aspect-ratio:4/3}}'
    _bites("grid_ratio_holds", html=_css(css), expect="in print")


def test_an_unequal_field_fails_grid_ratio_holds():
    css = '[data-sheet="15"] .imgs{margin-top:calc(var(--sheet-h) * .10)}'
    _bites("grid_ratio_holds", html=_css(css), rerender=False, expect="field above the grid")


def test_a_wrapping_stage_name_fails_footer_in_page():
    html = _baseline()["html"]
    name = '<h2 class="stagename">Gold of last light</h2>'
    assert name in html
    # two lines, not three: the rows still fit, so only the footer is lost
    long = '<h2 class="stagename">Gold of last light, the warmest room of the evening</h2>'
    _bites("footer_in_page", html=html.replace(name, long, 1), expect="footer")


def test_the_committed_sheet_ten_fits_its_page():
    # the defect that was clipped silently: Grid and spacing overflowed by 20.65px
    import fitz
    out = _baseline()["out"]
    assert out["footer_in_page"][0] == "PASS", out["footer_in_page"]
    d = fitz.open(str(_baseline()["pdf"]))
    words = [w for w in d[9].get_text("words") if w[4] == "10"]
    assert words and max(w[3] for w in words) < 579.6, words


for t in (test_poster_offset_is_one_third, test_seek_past_the_end_yields_the_last_frame,
          test_single_frame_clip_yields_a_frame, test_stale_poster_is_not_accepted,
          test_posters_are_one_per_video_and_capped, test_committed_posters_match_the_videos,
          test_upper_quartile_matches_the_known_measurement,
          test_every_assigned_reference_clears_the_ceiling,
          test_ceiling_excludes_bright_references,
          test_a_reference_exactly_at_the_ceiling_is_eligible, test_assignment_is_deterministic,
          test_a_starved_stage_fails_the_build,
          test_equidistant_stages_assign_identically_whatever_the_order,
          test_twenty_sheets_and_the_fall_still_divides,
          test_each_stage_sheet_carries_six_figures,
          test_a_video_is_emitted_as_a_swap_pair_inside_the_grid,
          test_a_missing_reference_file_fails_the_build_naming_it,
          test_stage_images_state_their_role_to_a_screen_reader,
          test_each_stage_sheet_stands_on_its_own_stage_flat,
          test_the_brightness_rule_names_the_upper_quartile,
          test_unmutated_document_passes_all_six,
          test_a_measured_ceiling_breach_fails_image_never_brightens,
          test_an_unmeasured_image_fails_image_never_brightens,
          test_an_image_on_the_edge_fails_image_on_ground,
          test_a_print_only_edge_touch_fails_image_on_ground,
          test_a_video_without_its_poster_fails_poster_in_print,
          test_a_reading_set_in_its_own_ground_fails_caption_contrast,
          test_a_slot_at_4_3_fails_grid_ratio_holds,
          test_a_slot_wrong_only_on_a_phone_fails_grid_ratio_holds,
          test_a_slot_wrong_only_in_print_fails_grid_ratio_holds,
          test_an_unequal_field_fails_grid_ratio_holds,
          test_a_wrapping_stage_name_fails_footer_in_page,
          test_the_committed_sheet_ten_fits_its_page):
    check(t)

print("\n".join("  PASS  " + m for m in PASSED))
if FAILED:
    print()
    print("\n".join("  FAIL  " + m for m in FAILED))
print()
print("  %d pass, %d fail" % (len(PASSED), len(FAILED)))
sys.exit(1 if FAILED else 0)
