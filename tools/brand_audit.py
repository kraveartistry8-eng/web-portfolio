# -*- coding: utf-8 -*-
"""Audit the Afterglow brand tokens and guideline document.

Mirrors tools/audit.py: checks collect into OK and FAIL, each prints one line,
and the exit status is the gate. Later tasks add checks here and run this as
their verification, so the harness is written to fail before the work lands.
"""
import io
import json
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "brand" / "resources" / "design-tokens.json"
IDENTITY = ROOT / "brand" / "BRAND-IDENTITY.md"
VOICE = ROOT / "brand" / "resources" / "voice-tone.md"

VOID = "#080808"
SURFACE_DEEP = "#141414"
SURFACE = "#2B2B2B"


def rgb(hex_value):
    h = hex_value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _linear(channel):
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_value):
    r, g, b = [_linear(c) for c in rgb(hex_value)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(hex_a, hex_b):
    """WCAG relative-luminance contrast ratio. Task 6 reuses this."""
    la, lb = luminance(hex_a), luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def oklch(hex_value):
    """sRGB hex to OKLCH (l, c, h). Lightness here is perceptual, which is the
    only space in which "the light only ever deepens" is a measurable claim."""
    r, g, b = [_linear(c) for c in rgb(hex_value)]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s_ = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s3 = [math.copysign(abs(v) ** (1.0 / 3.0), v) for v in (l, m, s_)]
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s3
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s3
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s3
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360.0


def voice_vocabulary():
    """The words that belong to Afterglow, read from voice-tone.md rather than
    copied here, so the list stays single-sourced."""
    text = io.open(VOICE, encoding="utf-8").read()
    match = re.search(
        r"## Words that belong to Afterglow\s*\n(.*?)\n##", text, re.S)
    if not match:
        return set()
    words = re.split(r"[,\n]", match.group(1))
    return set(w.strip().lower() for w in words if w.strip())

OK = []
FAIL = []


def chk(cond, msg):
    (OK if cond else FAIL).append(msg)


def leaves(obj, prefix=""):
    """Every scalar in the tree, as (dotted path, value)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            for item in leaves(v, prefix + "." + str(k) if prefix else str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in leaves(v, "%s[%d]" % (prefix, i)):
                yield item
    else:
        yield prefix, obj


def get(tree, dotted):
    """Fetch a dotted path, or the sentinel MISSING."""
    cur = tree
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


MISSING = object()

# The six locked neutrals, copied from the plan's Global Constraints.
NEUTRALS = {
    "color.ground.value": "#080808",
    "color.surface-deep.value": "#141414",
    "color.surface.value": "#2B2B2B",
    "color.text.value": "#EEECEA",
    "color.muted.value": "#C0C0C0",
    "color.border.value": "rgba(192,192,192,0.22)",
}

# Krave production tracker accents. They belong to a different brand.
FORBIDDEN = ("#39FF14", "#FF00BD")

# Explanatory keys present when this harness was written. They carry the reasoning
# behind a decision, so a careless rewrite of the token file must not drop them.
NOTE_KEYS = (
    "color.stages._note",
    "color._forbidden",
    "typography._status",
    "spacing._status",
    "radius._status",
    "shadow._status",
    "motion._status",
)

# Values the build cannot proceed without. A missing key has no value to be null,
# so absence has to be checked separately or Task 4 could pass with nothing set.
REQUIRED = (
    ["color.stages.%d.%s" % (n, f) for n in (1, 2, 3, 4) for f in ("name", "value")]
    + [
        "typography.display.family",
        "typography.body.family",
        "typography.scale",
        "typography.tracking",
        "typography.leading",
        "spacing.base",
        "spacing.scale",
        "motion.duration",
        "motion.ease",
    ]
)

# The spec fixes the substance of these but not their shape, so require a value
# of some kind rather than a key name the spec never chose.
REQUIRED_BRANCHES = ("radius", "shadow")

TOKEN_BRANCHES = ("color.stages", "typography", "spacing", "radius", "shadow", "motion")


def main():
    tokens = json.loads(io.open(TOKENS, encoding="utf-8").read())

    # ---------- no_nulls
    nulls = []
    for branch in TOKEN_BRANCHES:
        sub = get(tokens, branch)
        if sub is MISSING:
            nulls.append(branch + " (branch absent)")
            continue
        for path, value in leaves(sub, branch):
            if any(part.startswith("_") for part in path.split(".")):
                continue
            if value is None:
                nulls.append(path)
    missing = [p for p in REQUIRED if get(tokens, p) is MISSING]
    for branch in REQUIRED_BRANCHES:
        sub = get(tokens, branch)
        real = []
        if isinstance(sub, dict):
            real = [k for k in sub if not k.startswith("_")]
        if not real:
            missing.append(branch + " (no value, only notes)")
    chk(
        not nulls and not missing,
        "no_nulls         every token value is set%s"
        % (
            ""
            if not nulls and not missing
            else "  :: null %s  :: missing %s" % (sorted(nulls), sorted(missing))
        ),
    )

    stages = [get(tokens, "color.stages.%d" % n) for n in (1, 2, 3, 4)]
    values = [s.get("value") if isinstance(s, dict) else None for s in stages]
    recorded = [s.get("oklch") if isinstance(s, dict) else None for s in stages]
    ramp_set = all(isinstance(v, str) and v.startswith("#") for v in values)

    # ---------- oklch_matches_hex
    if not ramp_set:
        chk(False, "oklch_matches  recorded OKLCH agrees with the hex  :: ramp not set")
    else:
        drift = []
        for i, (v, rec) in enumerate(zip(values, recorded), start=1):
            if not isinstance(rec, dict):
                drift.append("stage %d has no oklch object" % i)
                continue
            L, C, H = oklch(v)
            for key, got, want in (("l", rec.get("l"), L), ("c", rec.get("c"), C),
                                   ("h", rec.get("h"), H)):
                if not isinstance(got, (int, float)) or abs(got - want) > 0.005 * (
                        360.0 if key == "h" else 1.0):
                    drift.append("stage %d %s recorded %r, computed %.4f"
                                 % (i, key, got, want))
        chk(not drift,
            "oklch_matches    recorded OKLCH agrees with the hex%s"
            % ("" if not drift else "  :: " + "; ".join(drift)))

    # ---------- l_monotonic
    if not ramp_set:
        chk(False, "l_monotonic      lightness falls across the four stages  :: ramp not set")
    else:
        ls = [oklch(v)[0] for v in values]
        rises = ["stage %d (%.4f) is not below stage %d (%.4f)"
                 % (i + 2, ls[i + 1], i + 1, ls[i])
                 for i in range(3) if ls[i + 1] >= ls[i]]
        chk(not rises,
            "l_monotonic      lightness falls across the four stages, %s%s"
            % (" > ".join("%.3f" % x for x in ls),
               "" if not rises else "  :: " + "; ".join(rises)))

    # ---------- hue_one_way
    if not ramp_set:
        chk(False, "hue_one_way      hue rotates one way along the arc  :: ramp not set")
    else:
        hs = [oklch(v)[2] for v in values]
        deltas = [((hs[i + 1] - hs[i] + 180.0) % 360.0) - 180.0 for i in range(3)]
        signs = set(1 if d > 0 else (-1 if d < 0 else 0) for d in deltas)
        chk(len(signs) == 1 and 0 not in signs,
            "hue_one_way      hue rotates one way along the arc, %s, steps %s%s"
            % (" -> ".join("%.1f" % x for x in hs),
               " ".join("%+.1f" % d for d in deltas),
               "" if len(signs) == 1 and 0 not in signs else "  :: direction reverses"))

    # ---------- stage_roles
    if not ramp_set:
        chk(False, "stage_roles      stages 1 and 2 clear their contrast floors  :: ramp not set")
    else:
        ratios = [contrast(v, VOID) for v in values]
        misses = []
        if ratios[0] < 4.5:
            misses.append("stage 1 is %.2f:1 on void, needs 4.5:1 to be text" % ratios[0])
        if ratios[1] < 3.0:
            misses.append("stage 2 is %.2f:1 on void, needs 3:1 for large text" % ratios[1])
        chk(not misses,
            "stage_roles      on void: %s (3 and 4 recorded, unconstrained)%s"
            % (", ".join("s%d %.2f:1" % (i + 1, r) for i, r in enumerate(ratios)),
               "" if not misses else "  :: " + "; ".join(misses)))

    # ---------- stage_named
    name2 = stages[1].get("name") if isinstance(stages[1], dict) else None
    vocab = voice_vocabulary()
    drawn = bool(name2) and any(
        w in vocab for w in re.findall(r"[a-z']+", str(name2).lower()))
    chk(drawn,
        "stage_named      stage 2 is named from the Afterglow vocabulary%s"
        % ("" if drawn else "  :: name is %r" % (name2,)))

    # ---------- type_set
    typo = get(tokens, "typography")
    fams = {f: get(tokens, "typography.%s.family" % f) for f in ("display", "body")}
    unset = sorted(f for f, v in fams.items() if not isinstance(v, str) or not v.strip())
    chk(not unset,
        "type_set         both faces are chosen%s"
        % ("  :: " + ", ".join(fams.get(f) and f or f for f in unset) + " unset"
           if unset else "  :: display %(display)s, body %(body)s" % fams))

    # ---------- scale_measured
    scale = get(tokens, "typography.scale")
    if not isinstance(scale, dict):
        chk(False, "scale_measured   the scale is a measured ratio, not eyeballed  :: scale not set")
    else:
        ratio, base = scale.get("ratio"), scale.get("base")
        steps = scale.get("steps")
        problems = []
        if not isinstance(ratio, (int, float)) or ratio <= 1:
            problems.append("ratio is %r" % (ratio,))
        if not isinstance(base, (int, float)) or base <= 0:
            problems.append("base is %r" % (base,))
        if not isinstance(steps, dict) or not steps:
            problems.append("no named steps")
        if not problems:
            for name, value in sorted(steps.items()):
                if not isinstance(value, (int, float)):
                    problems.append("%s is %r" % (name, value)); continue
                # every step has to be base * ratio ** n for a whole n, or the scale
                # is a list of sizes someone liked rather than a scale
                n = math.log(value / base) / math.log(ratio)
                if abs(n - round(n)) > 0.02:
                    problems.append("%s=%g is base*ratio**%.3f, not a whole step"
                                    % (name, value, n))
        chk(not problems,
            "scale_measured   every step derives from ratio and base%s"
            % ("  :: " + "; ".join(problems) if problems
               else "  :: %g from %g, %d steps" % (ratio, base, len(steps))))

    # ---------- delivery_recorded
    routes = {}
    for f in ("display", "body"):
        v = get(tokens, "typography.%s.delivery" % f)
        routes[f] = "not set" if v is MISSING else v
    allowed = ("shopify_library", "self_hosted")
    wrong = ["%s is %r" % (f, v) for f, v in sorted(routes.items()) if v not in allowed]
    chk(not wrong,
        "delivery_recorded each face records how it ships%s"
        % ("  :: " + "; ".join(wrong) if wrong
           else "  :: display %(display)s, body %(body)s" % routes))

    # ---------- spacing_measured
    sp = get(tokens, "spacing")
    if not isinstance(sp, dict):
        chk(False, "spacing_measured every step is a whole multiple of the base  :: spacing not set")
    else:
        sbase, sscale = sp.get("base"), sp.get("scale")
        issues = []
        if not isinstance(sbase, (int, float)) or sbase <= 0:
            issues.append("base is %r" % (sbase,))
        elif not isinstance(sscale, dict) or not sscale:
            issues.append("no scale")
        else:
            for name, value in sorted(sscale.items()):
                if not isinstance(value, (int, float)):
                    issues.append("%s is %r" % (name, value)); continue
                # half steps are allowed, arbitrary numbers are not
                k = value / float(sbase)
                if abs(k * 2 - round(k * 2)) > 1e-6:
                    issues.append("%s=%g is base x %.3f, not a whole or half step" % (name, value, k))
        chk(not issues,
            "spacing_measured every step is a multiple of the base%s"
            % ("  :: " + "; ".join(issues) if issues
               else "  :: %g px base, %d steps" % (sbase, len(sscale))))

    # ---------- motion_no_overshoot
    # "Deepening, never snapping" is a Global Constraint with no other test. A curve
    # whose control points leave the unit square passes its destination and comes back,
    # which is exactly the bounce the brand rules out.
    ease = get(tokens, "motion.ease")
    m = re.match(r"\s*cubic-bezier\(([^)]*)\)\s*$", str(ease))
    if not m:
        chk(False, "motion_no_overshoot the easing curve never overshoots  :: ease is %r" % (ease,))
    else:
        try:
            pts = [float(x) for x in m.group(1).split(",")]
        except ValueError:
            pts = []
        if len(pts) != 4:
            chk(False, "motion_no_overshoot the easing curve never overshoots  :: cannot read %r" % (ease,))
        else:
            x1, y1, x2, y2 = pts
            out_of_square = [n for n, v in (("y1", y1), ("y2", y2)) if not 0.0 <= v <= 1.0]
            bad_x = [n for n, v in (("x1", x1), ("x2", x2)) if not 0.0 <= v <= 1.0]
            chk(not out_of_square and not bad_x,
                "motion_no_overshoot the easing curve settles, never passes its value%s"
                % ("  :: " + ", ".join(out_of_square + bad_x) + " outside 0..1"
                   if (out_of_square or bad_x) else "  :: %s" % ease))

    # ---------- neutrals_locked
    wrong = [
        "%s is %r, expected %r" % (p, get(tokens, p), want)
        for p, want in sorted(NEUTRALS.items())
        if get(tokens, p) != want
    ]
    chk(
        not wrong,
        "neutrals_locked  the six neutrals are unchanged%s"
        % ("" if not wrong else "  :: " + "; ".join(wrong)),
    )

    # ---------- no_forbidden
    strays = []
    for path, value in leaves(tokens):
        if path.startswith("color._forbidden"):
            continue
        if isinstance(value, str) and any(f.lower() in value.lower() for f in FORBIDDEN):
            strays.append(path)
    chk(
        not strays,
        "no_forbidden     no tracker accent outside _forbidden%s"
        % ("" if not strays else "  :: " + ", ".join(sorted(strays))),
    )

    # ---------- notes_intact
    dropped = [k for k in NOTE_KEYS if get(tokens, k) is MISSING]
    chk(
        not dropped,
        "notes_intact     explanatory keys survive the fill%s"
        % ("" if not dropped else "  :: dropped " + ", ".join(dropped)),
    )

    # ---------- no_week2
    identity = io.open(IDENTITY, encoding="utf-8").read()
    hits = identity.lower().count("week 2")
    chk(
        hits == 0,
        "no_week2         BRAND-IDENTITY.md has no Week 2 rows%s"
        % ("" if hits == 0 else "  :: %d occurrence(s)" % hits),
    )

    print("\n".join("  PASS  " + m for m in OK))
    if FAIL:
        print()
        print("\n".join("  FAIL  " + m for m in FAIL))
    print()
    print("  %d pass, %d fail" % (len(OK), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
