"""Export the Afterglow moodboard as page PNGs and one PDF, for posting.

Aaron, 18 Oct: the hover notes stay in, and every piece of media carries its credit. On the page the notes
only appear on hover, so the export moves each note under its image, with the credit beneath it, rather
than leaving the dark overlay on over every photograph.

Credits follow the guide's rule (tools/afterglow_specimen.py): the name comes from each Savee save's own
source. Where the save leads only to an anonymous repost the maker is unknown and the credit says so; where
it leads to a site that hides the maker (Behance, Stocksy, Stills) the credit names the site.

Run: python3 tools/export_moodboard.py  (writes to outreach/2026-10-18-afterglow-moodboard/)
"""
import http.server
import io
import re
import socketserver
import threading
from functools import partial
from pathlib import Path

import fitz
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brand/guide-sources"
PAGE = "2026-10-09-afterglow-moodboard.html"
OUT = ROOT / "outreach/2026-10-18-afterglow-moodboard"

UNKNOWN = "Photographer unknown"


def guide_credits():
    """The 31 credits the guide already traced, read from its build script rather than copied."""
    s = (ROOT / "tools/afterglow_specimen.py").read_text()
    block = s[s.index("CREDITS = {"):]
    block = block[:block.index("\n}")]
    out = {}
    for key, val in re.findall(r'"([^"]+)":\s*(UNKNOWN|"[^"]*")', block):
        out[re.sub(r"-(trim|bottle)$", "", key)] = UNKNOWN if val == "UNKNOWN" else val.strip('"')
    return out


# The other 42, traced from Savee on 18 Oct.
CREDITS = {
    **guide_credits(),
    "a2QG-_S": UNKNOWN, "Na_PDmV": UNKNOWN, "fMmCZqp": "redblueen", "sh51Sqi": "Whitaker Studio, Starburst House",
    "D7AGfdU": UNKNOWN, "CByZsgX": UNKNOWN, "N67S_kB": UNKNOWN, "e4jFDHF": "Bianca Poletti", "85R4fhS": "umitai.png",
    "InhSf8F": "Samsung Galaxy Z Fold 4, via Behance", "5s0xLGP": "Marie Dommenget",
    "O6syNhj": "Fare Inc., Tivoli Cinema", "F20ztHX": "Ray Tijssen", "0Nq4kh3": UNKNOWN, "LUWtrde": UNKNOWN,
    "0Hcf2LC": "Alexis Belhumeur, Line of Sight", "nT7RG1w": "Albert Watson", "xy_NvPh": UNKNOWN,
    "KLTQTBB": "Dasha Yukhymyuk", "2OYJ0AX": UNKNOWN, "v707B3q": UNKNOWN, "Fr3gA2Q": UNKNOWN,
    "rjnEUxk": "Self portraits series, via Behance", "-zBG6TG": UNKNOWN, "lgBEnyK": UNKNOWN,
    "v9AvMbv": "F1 2025 opening titles, via Behance", "CZjLx5b": UNKNOWN, "-vDj1rY": UNKNOWN,
    "ZpX9SWA": "rkuzminykh, Artificial Organism", "rpnybJw": "A-COLD-WALL* &amp; Nike, TN98",
    "PskjO9s": "sammescobar", "2FQUyKG": "amaraajordan", "ZDTkORf": "Chris Perani, Butterfly Wings",
    "4RH87Zk": "Bold Scandinavia, Arelion", "mPNk84g": UNKNOWN, "QOH4dl-": UNKNOWN, "_A5z16D": "via Stocksy",
    "ULIwwIS": UNKNOWN, "eSgBkag": UNKNOWN, "k4KfGf3": "via Stills", "gm8x-Nc": "Aesop", "NHyQ2Ii": UNKNOWN,
}

PRINT_CSS = """
.card{background:none}
.card:hover img,.card:hover video{transform:none}
.card__overlay{position:static;opacity:1;background:none;padding:9px 2px 16px}
.card__label{color:rgba(238,236,234,.82)}
.card__credit{display:block;margin-top:5px;font-size:10px;letter-spacing:.04em;color:rgba(238,236,234,.45)}
"""


# Aaron, 18 Oct: the pages must not shrink in a LinkedIn document, so the export lays the board out again as 4:5
# portrait pages, the shape LinkedIn shows largest. Each section flows across as many pages as it needs; a card
# never splits across two. Videos are frozen to a still first, so moving them between pages cannot lose the frame.
PAGE_W, PAGE_H = 1080, 1350
PAGINATE = """() => {
  const W = %d, H = %d, PAD = 52, GAP = 10;
  document.querySelectorAll('video').forEach(v => {
    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext('2d').drawImage(v, 0, 0);
    const im = document.createElement('img'); im.src = c.toDataURL('image/jpeg', .92);
    im.width = v.videoWidth; im.height = v.videoHeight; v.replaceWith(im);
  });
  // every image's shape is fixed before anything is measured, so a late decode cannot move a card
  document.querySelectorAll('.card img').forEach(i => {
    // the extreme verticals are cropped to 4:5.6, or one of them can push half a page onto the next
    const w = i.naturalWidth || i.width, h = Math.min(i.naturalHeight || i.height, w * 1.4);
    i.style.aspectRatio = `${w} / ${h}`; i.style.height = 'auto'; i.style.objectFit = 'cover'; });
  const css = document.createElement('style');
  css.textContent = `
    body{margin:0;background:var(--void)}
    .pg{width:${W}px;height:${H}px;box-sizing:border-box;padding:${PAD}px;display:flex;flex-direction:column;overflow:hidden;background:var(--void)}
    .pg .mode-header{margin-bottom:22px;padding-bottom:16px;gap:32px}
    .pg .mode-header__tag{margin-bottom:22px}
    .pg .mode-header__title{font-size:52px}
    .pg .mode-header__descriptor{max-width:340px;font-size:12.5px}
    .pg .cont{font-size:9px;font-weight:500;letter-spacing:.26em;text-transform:uppercase;color:rgba(238,236,234,.4);
      padding-bottom:16px;margin-bottom:24px;border-bottom:1px solid var(--line)}
    .pg .cols{display:flex;gap:${GAP}px;flex:1;min-height:0;align-items:flex-start}
    .pg .col{flex:1;min-width:0;display:flex;flex-direction:column;gap:${GAP}px}
    .pg .card{margin:0}
    .pg .foot{display:flex;justify-content:space-between;padding-top:18px;font-size:9px;letter-spacing:.2em;
      text-transform:uppercase;color:rgba(238,236,234,.3)}
    .pg.dense .card__overlay{padding:6px 1px 10px}
    .pg.dense .card__signal{font-size:7px;margin-bottom:3px}
    .pg.dense .card__label{font-size:9.5px;line-height:1.4}
    .pg.dense .card__credit{font-size:8px;margin-top:3px}
    .pg.cover{height:auto;padding:64px ${PAD}px}
    .pg.cover .doc-header{padding:0}
    .pg.cover .legend{padding:36px 0 0;margin-top:40px;gap:22px 32px;justify-content:center}`;
  document.head.appendChild(css);
  const book = document.createElement('main');
  document.body.prepend(book);  // in the document from the start, or nothing measures
  const foot = () => { const f = document.createElement('div'); f.className = 'foot';
    f.innerHTML = '<span>Afterglow · Mood board</span><span class="n"></span>'; return f; };
  const cover = document.createElement('section'); cover.className = 'pg cover';
  // Aaron, 18 Oct: the cover is cropped to the wordmark and the palette under it, a slight margin above and below
  cover.append(document.querySelector('header.doc-header'), document.querySelector('footer.legend'));
  book.append(cover);
  document.querySelectorAll('section.mode-section').forEach(sec => {
    const bg = sec.style.background || 'var(--void)';
    const head = sec.querySelector('.mode-header');
    const tag = head.querySelector('.mode-header__tag').textContent;
    const cards = Array.from(sec.querySelectorAll('.card'));
    // Aaron, 18 Oct: a section reads best as one wall of photographs, so each section gets exactly one page.
    // Columns are added until every card fits; the notes and credits step down a size from four columns.
    let page, cols;
    const open = K => {
      page = document.createElement('section'); page.className = 'pg' + (K >= 4 ? ' dense' : '');
      page.style.background = bg; page.append(head);
      const wrap = document.createElement('div'); wrap.className = 'cols';
      cols = Array.from({length: K}, () => { const d = document.createElement('div'); d.className = 'col'; wrap.append(d); return d; });
      page.append(wrap, foot()); book.append(page);
      return wrap.clientHeight;
    };
    const pack = (K, hts) => {
      const out = Array.from({length: K}, () => []), hs = Array(K).fill(0);
      // tallest first into the shortest column packs the wall tightest; a wall has no reading order to keep
      const order = hts.map((h, i) => i).sort((a, b) => hts[b] - hts[a]);
      for (const i of order) {
        const k = hs.indexOf(Math.min(...hs));
        hs[k] += hts[i] + (out[k].length ? GAP : 0); out[k].push(i);
      }
      return {out, M: Math.max(...hs)};
    };
    // for each column count, how wide a photograph gets once the wall is narrowed to fit the page; keep the widest
    let best = null;
    for (let K = 3; K <= 8; K++) {
      const room = open(K);
      cards.forEach(c => cols[0].append(c));
      const colW = cols[0].clientWidth, hts = cards.map(c => c.offsetHeight);
      const {out, M} = pack(K, hts);
      const scale = Math.min(1, room / M), photoW = colW * scale;
      if (!best || photoW > best.photoW) best = {K, out, scale, photoW};
      page.remove();
    }
    const room = open(best.K);
    const wrap = page.querySelector('.cols');
    best.out.forEach((idx, k) => idx.forEach(i => cols[k].append(cards[i])));
    // narrow the wall, centred, until its tallest column fits; captions do not shrink with it, so check the result
    let w = best.scale;
    const fits = () => Math.max(...cols.map(c => c.offsetHeight)) <= room;
    wrap.style.width = (w * 100) + '%%'; wrap.style.alignSelf = 'center';
    while (!fits() && w > 0.5) { w -= 0.01; wrap.style.width = (w * 100) + '%%'; }
    sec.remove();
  });
  document.body.replaceChildren(book);
  const pages = book.querySelectorAll('.pg');
  pages.forEach((p, i) => { const n = p.querySelector('.n'); if (n) n.textContent = `${i + 1} / ${pages.length}`; });
  return pages.length;
}""" % (PAGE_W, PAGE_H)


def key_of(src):
    return re.sub(r"-(trim|bottle)$", "", src.rsplit("/", 1)[-1].rsplit(".", 1)[0])


def with_credits(html):
    def one(m):
        card = m.group(0)
        key = key_of(re.search(r'src="moodboard-media/([^"]+)"', card).group(1))
        credit = f'<span class="card__credit">{CREDITS[key]}</span>'
        return card.replace("</div>", credit + "</div>", 1) if "card__overlay" not in card else \
            re.sub(r'(<span class="card__label">.*?</span>)', r"\1" + credit, card, count=1, flags=re.S)
    html, n = re.subn(r'<div class="card">.*?</div>\s*</div>', one, html, flags=re.S)
    assert n == html.count('class="card"'), "every piece of media carries a credit"
    html = html.replace(' loading="lazy"', "")  # an export wants every image in, not just the ones scrolled past
    return html.replace("</style>", PRINT_CSS + "</style>", 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = SRC / "_export.html"
    tmp.write_text(with_credits((SRC / PAGE).read_text()))
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = partial(Quiet, directory=str(SRC))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    shots = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/_export.html", wait_until="load", timeout=180000)
            pg.wait_for_function("Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)", timeout=120000)
            # each video holds one frame a second in, so the still reads as the clip
            pg.evaluate("""Promise.all(Array.from(document.querySelectorAll('video')).map(v=>new Promise(r=>{
                v.pause(); const go=()=>{v.currentTime=Math.min(1,(v.duration||2)/2)};
                v.addEventListener('seeked',r,{once:true}); v.readyState>=1?go():v.addEventListener('loadedmetadata',go,{once:true});
                setTimeout(r,15000);})))""")
            pg.evaluate(PAGINATE)
            pg.set_viewport_size({"width": PAGE_W, "height": PAGE_H})
            for old in OUT.glob("*.png"):
                old.unlink()
            for i in range(pg.locator(".pg").count()):
                el = pg.locator(".pg").nth(i)
                el.scroll_into_view_if_needed()
                pg.wait_for_timeout(150)
                path = OUT / f"{i + 1:02d}.png"
                el.screenshot(path=str(path), timeout=120000)
                shots.append(path)
            b.close()
    finally:
        srv.shutdown()
        tmp.unlink()
    # one PDF, a page per section at its own height; JPEG inside, or the PDF runs to ~50 MB
    pdf = fitz.open()
    for path in shots:
        im = Image.open(path).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        page = pdf.new_page(width=im.width / 2, height=im.height / 2)
        page.insert_image(page.rect, stream=buf.getvalue())
    pdf.save(str(OUT / "afterglow-moodboard.pdf"), deflate=True)
    print("\n".join(str(s.relative_to(ROOT)) for s in shots), OUT / "afterglow-moodboard.pdf", sep="\n")


if __name__ == "__main__":
    main()
