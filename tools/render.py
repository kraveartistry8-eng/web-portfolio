from playwright.sync_api import sync_playwright
import pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
# An optional source path, defaulting to the roadmap so the existing pipeline is
# unchanged when called with no arguments.
src=ROOT/(sys.argv[1] if len(sys.argv)>1 else "2026-10-02-shopify-roadmap.html")
out=src.with_suffix(".pdf")
# A document that paints its own full-bleed ground controls its own padding; Letter
# margins would print as white borders around it.
FULL_BLEED=src.name.startswith("2026-10-07-afterglow-guidelines")
MARGIN=({"top":"0","bottom":"0","left":"0","right":"0"} if FULL_BLEED
        else {"top":"0.55in","bottom":"0.55in","left":"0.6in","right":"0.6in"})
errs=[]
with sync_playwright() as pw:
    b=pw.chromium.launch()
    pg=b.new_page()
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(src.as_uri()); pg.wait_for_timeout(900)
    pg.emulate_media(media="print")
    pg.pdf(path=str(out), format="Letter", print_background=True,
           margin=MARGIN)
    b.close()
print("console errors:", errs or "none")
print("pdf written:", out)
