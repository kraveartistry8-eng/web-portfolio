"""Owner walkthrough fix: the film's controls live in their own 'Film' item, first in the section's block list."""
import json, re
from common import *

sec = open("../../afterglow/sections/film-hero.liquid").read()
schema = json.loads(sec.split("{% schema %}")[1].split("{% endschema %}")[0])
static = re.findall(r"content_for 'block', type: '([^']+)', id: '([^']+)'", sec)
check("section renders a static film block", ("_film", "film") in static, str(static))
try:
    blk = open("../../afterglow/blocks/_film.liquid").read()
    bs = json.loads(blk.split("{% schema %}")[1].split("{% endschema %}")[0])
    ids = [s["id"] for s in bs["settings"] if "id" in s]
    check("film block holds film, phone cut, poster, darkening", ids[:4] == ["video_wide", "video_phone", "poster", "darken"], str(ids))
    check("film block is named Film", "film" in bs["name"].lower(), bs["name"])
except FileNotFoundError:
    check("film block file exists", False)
sec_ids = [s.get("id") for s in schema["settings"]]
check("section no longer hides film settings", not {"video_wide", "video_phone", "poster", "darken"} & set(sec_ids), str(sec_ids))
tpl = json.load(open("../../afterglow/templates/index.json"))["sections"]["film"]
check("template stores the film as a static block", tpl.get("blocks", {}).get("film", {}).get("static") is True)

p, b = browser(); pg = page(b); pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(2000)
check("film still plays", pg.evaluate("() => { const v = document.querySelector('.film-hero video'); return !!v && !v.paused }"))
b.close(); p.stop(); finish()
