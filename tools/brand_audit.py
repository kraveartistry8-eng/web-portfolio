# -*- coding: utf-8 -*-
"""Audit the Afterglow brand tokens and guideline document.

Mirrors tools/audit.py: checks collect into OK and FAIL, each prints one line,
and the exit status is the gate. Later tasks add checks here and run this as
their verification, so the harness is written to fail before the work lands.
"""
import io
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = ROOT / "brand" / "resources" / "design-tokens.json"
IDENTITY = ROOT / "brand" / "BRAND-IDENTITY.md"

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
