# Shopify studio

Working folder for the pivot to a design-led Shopify studio, October 2026 to March 2027.

## The plan

`2026-10-02-shopify-roadmap.html` is the source of truth. It gets printed and ticked by hand,
so the PDF beside it is the real artifact and the HTML is how it gets edited.

Operational tracking lives in Notion, not here: the Prospects table (people who can buy),
the Network table (peers, agencies, referrers), Weeks, and Months.

## Folders

| Folder | What is in it |
|---|---|
| `tools/` | Scripts that keep the roadmap honest. See below |
| `research/` | ARIA reports. Start at `2026-10-03-aria-entry-point.html`, which links to the rest |
| `design/` | September design artifacts for the sales page: hero, IA, layout architecture, cube spec |
| `outreach/` | The LinkedIn export and the ranked lists built from it |
| `brand/` | Afterglow, the fictional brand the demo store is built for. The guide is `2026-10-12-guide-hour-lite.html` (live at afterglow-guide.vercel.app). `guide-sources/` holds what it is built from, `ember/` the ember engines (`satin/` is current, `v23/` frozen), `ember-directions/` the ember prototypes, `mark/` the mark, `moodboard-media/` the photographs |
| `references/` | Captured reference sites, and `design-standards.md`. `references/ember/` is large and not committed |
| `docs/superpowers/` | The current spec and plan; superseded ones are in `archive/` inside it |
| `afterglow/` | The Skeleton theme clone. This is the dev store build |
| `site/` | The Astro studio site. `npm run dev` inside it |
| `archive/` | Superseded explorations, including `afterglow-explorations/` (the guide directions that were not taken). Roadmap history is in git |

## Tools

Run from anywhere; they resolve the roadmap relative to themselves.

| Script | What it does |
|---|---|
| `tools/render.py` | Rebuilds the PDF from the HTML. Run after any edit to the roadmap |
| `tools/audit.py` | Checks internal consistency: week numbering, that every dated day falls on the weekday it claims, prospect counts against the tasks that open them, the money columns, cross-references |
| `tools/coverage.py` | Checks that the outreach volume has a task behind it in every week that needs one, and that the running totals in the prose are arithmetically right |

Both audits must pass before the PDF is reprinted. They exist because the numbers in this
document reference each other, and changing one by hand silently breaks three others.

## Conventions

Dated filenames are `YYYY-MM-DD-slug`. The date is when the artifact was made, not when it
was last edited. No em-dashes anywhere in anything that gets printed.

Rebuild the Afterglow guide with `python3 tools/afterglow_specimen.py`; its checks are in `tools/check_ember_satin.py` and `tools/test_afterglow_specimen.py`.
