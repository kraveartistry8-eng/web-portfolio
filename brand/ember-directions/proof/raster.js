// Ember satin proof (14 Oct 2026): the live guide drawn into images by the browser itself, so the satin, c3 and the raking
// light can work on its pixels as the prototype does on its captures. Each sheet is serialised with the page's own stylesheet
// and fonts into an SVG foreignObject and drawn to a canvas. The real HTML stays in the page for links, selection and readers.
const Raster = (() => {
  let fontCSS = null;
  const dataURLs = new Map();
  const toDataURL = async url => {
    if (!dataURLs.has(url)) dataURLs.set(url, fetch(url).then(r => r.blob()).then(b => new Promise(res => { const f = new FileReader(); f.onload = () => res(f.result); f.readAsDataURL(b); })));
    return dataURLs.get(url);
  };
  // the page's stylesheet, with the Google fonts it links inlined, since an SVG image may not load anything itself
  async function styles() {
    if (fontCSS) return fontCSS;
    let css = "";
    for (const l of document.querySelectorAll('link[rel="stylesheet"]')) {
      let t = await (await fetch(l.href)).text();
      for (const u of new Set([...t.matchAll(/url\((https:[^)]+)\)/g)].map(m => m[1]))) t = t.split(u).join(await toDataURL(u));
      css += t + "\n";
    }
    for (const s of document.querySelectorAll("style:not([data-proof])")) css += s.textContent + "\n";
    return (fontCSS = css);
  }
  // one sheet, as it is laid out now. ground: only the sheet's own background, with everything on it hidden
  async function sheet(el, { dpr = 1, ground = false } = {}) {
    // inside an SVG image the viewport is the image, so heights in viewport units are fixed to the real window's in px,
    // and the image is at least as tall as the window, so media queries on height read the same
    const r = el.getBoundingClientRect(), W = Math.ceil(r.width), H = Math.ceil(r.height), VH = Math.max(H, innerHeight);
    const css = (await styles()).replace(/(-?\d*\.?\d+)(svh|dvh|lvh|vh)\b/g, (m, n) => (+n * innerHeight / 100).toFixed(2) + "px");
    const clone = el.cloneNode(true);
    await Promise.all([...clone.querySelectorAll("img")].map(async im => { im.setAttribute("src", await toDataURL(new URL(im.getAttribute("src"), document.baseURI).href)); im.removeAttribute("srcset"); im.removeAttribute("loading"); }));
    if (ground) for (const c of clone.children) c.style.setProperty("visibility", "hidden", "important");
    const deck = document.querySelector(".deck");
    const html = `<html xmlns="http://www.w3.org/1999/xhtml" class="${document.documentElement.className}"><head><style><![CDATA[${css}]]></style></head>` +
      `<body class="${document.body.className}" style="margin:0;width:${W}px;overflow:hidden"><main class="${deck.className}">` +
      new XMLSerializer().serializeToString(clone) + `</main></body></html>`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${VH}"><foreignObject x="0" y="0" width="${W}" height="${VH}">${html}</foreignObject></svg>`;
    const im = new Image(); im.decoding = "sync";
    im.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
    await im.decode();
    const c = document.createElement("canvas"); c.width = Math.round(W * dpr); c.height = Math.round(H * dpr);
    const g = c.getContext("2d");
    g.drawImage(im, 0, 0, W, H, 0, 0, c.width, c.height);
    // WebKit decodes the photographs inside an SVG image only after its first draw, so it is drawn again once they are in
    if (clone.querySelector("img") && /AppleWebKit/.test(navigator.userAgent) && !/Chrome|Chromium/.test(navigator.userAgent)) {
      for (let k = 0; k < 2; k++) { await new Promise(r => setTimeout(r, 60)); g.clearRect(0, 0, c.width, c.height); g.drawImage(im, 0, 0, W, H, 0, 0, c.width, c.height); }
    }
    return c;
  }
  return { sheet, styles };
})();
