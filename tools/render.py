from playwright.sync_api import sync_playwright
import pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
src=ROOT/"2026-10-02-shopify-roadmap.html"
out=ROOT/"2026-10-02-shopify-roadmap.pdf"
errs=[]
with sync_playwright() as pw:
    b=pw.chromium.launch()
    pg=b.new_page()
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(src.as_uri()); pg.wait_for_timeout(900)
    pg.emulate_media(media="print")
    pg.pdf(path=str(out), format="Letter", print_background=True,
           margin={"top":"0.55in","bottom":"0.55in","left":"0.6in","right":"0.6in"})
    b.close()
print("console errors:", errs or "none")
print("pdf written:", out)
