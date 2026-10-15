// The raking light (A, at a third), moved from brand/ember-directions/satin-combined.html: the splat program and its field,
// and the display program with only mode 0, the raking light, in live
// mode: it reads c3's frame each frame as the page and draws to the one visible canvas. Modes 1 to 10, the fold and sheet
// programs and their tables are removed; every number that mode 0 uses is unchanged. The keep mask is removed too: the
// prototype builds it, but mode 0 never reads it (the plan asked for it; the prototype wins).

const SET_A = { life: 900, r: 56, rs: 40, grow: 0.25, fade: 1.3 };   // life ms, radius px, radius per speed, growth with age, how fast light fades (power)
const GAIN = 0.33;   // picked by eye, 14 Oct: a third

// returns null when WebGL2 (or a float colour buffer for the field) is not available
export function createRake(glc, { mediump = false } = {}) {
  const gl = glc.getContext("webgl2", { premultipliedAlpha: false, antialias: false });
  if (!gl) return null;
  if (!gl.getExtension("EXT_color_buffer_float") && !gl.getExtension("EXT_color_buffer_half_float")) return null;
  const P = mediump ? "precision mediump float;" : "precision highp float;";
  let W = 1, H = 1, DPR = 1, img = null;

  function sh(type, src) { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(s); return s; }
  function prog(vs, fs) { const p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw gl.getProgramInfoLog(p); return p; }
  // splat: a gaussian per trail point. r = light (fades with age), g = light x age (for the cooling colour), b, a = light x the way it travels
  const splat = prog(`#version 300 es
in vec2 corner; in vec2 ctr; in vec4 pa; in float pw;   // pa: radius, light, age, light x cos of travel; pw: light x sin of travel
uniform vec2 res; uniform float aniso; out vec2 q; out vec4 v;
void main(){ q = corner; v = vec4(pa.yzw, aniso > 0. ? 0. : pw);
  vec2 c = corner * pa.x;
  if (aniso > 0.) { c = vec2(corner.x * pa.x * aniso, corner.y * pa.x); float a = -pw; c = mat2(cos(a), sin(a), -sin(a), cos(a)) * c; }
  vec2 p = ctr + c; gl_Position = vec4(p / res * 2.0 - 1.0, 0.0, 1.0); }`,
`#version 300 es
${P} in vec2 q; in vec4 v; out vec4 o;
void main(){ float g = exp(-dot(q, q) * 3.1); o = vec4(v.x * g, v.x * v.y * g, v.z * g, v.w * g); }`);
  const show = prog(`#version 300 es
in vec2 corner; out vec2 uv; void main(){ uv = corner * 0.5 + 0.5; gl_Position = vec4(corner, 0.0, 1.0); }`,
`#version 300 es
${P}
uniform sampler2D page, ground, field; uniform vec2 res; uniform vec4 rect; uniform float px; uniform float gain;
in vec2 uv; out vec4 o;
const vec3 F0 = vec3(216.,178.,96.)/255., F1 = vec3(188.,111.,76.)/255., F2 = vec3(137.,58.,80.)/255., F3 = vec3(52.,29.,94.)/255., INK = vec3(8.)/255.;
vec3 fall(float t){ t = clamp(t, 0., 1.) * 4.; if (t < 1.) return mix(F0, F1, t); if (t < 2.) return mix(F1, F2, t - 1.); if (t < 3.) return mix(F2, F3, t - 2.); return mix(F3, INK, t - 3.); }
float lum(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
vec2 iuv(vec2 frag){ vec2 p = vec2(frag.x, res.y - frag.y); return (p - rect.xy) / rect.zw; }   // screen px (top-left origin) to image uv
vec3 tex(sampler2D s, vec2 frag){ return texture(s, iuv(frag)).rgb; }
// the page as drawn: c3's frame (a viewport-sized canvas, top row first)
vec3 texP(vec2 frag){ return texture(page, vec2(frag.x / res.x, 1. - frag.y / res.y)).rgb; }
vec3 screen(vec3 a, vec3 b){ return 1. - (1. - a) * (1. - b); }
void main(){
  vec2 f = gl_FragCoord.xy;
  vec3 pg = texP(f), gd = tex(ground, f);
  vec4 fl = texture(field, uv);
  float L = fl.r, age = fl.g / max(fl.r, 1e-4);
  float dark = smoothstep(.42, .22, lum(gd));
  vec3 outc = pg;
  {   // A: raking light, on edges only
    vec2 gr = vec2(0.);   // the edge at two widths, so the light is a soft rim and not a drawn outline
    for (int k = 1; k <= 2; k++) { float e = px * 1.5 * float(k);
      gr += .5 * vec2(lum(texP(f + vec2(e, 0.))) - lum(texP(f - vec2(e, 0.))), lum(texP(f - vec2(0., e))) - lum(texP(f + vec2(0., e)))); }
    float edge = clamp(length(gr) * 2.6, 0., 1.);
    vec2 n = length(gr) > 1e-4 ? normalize(gr) : vec2(0.);   // points toward the brighter side, in page orientation
    vec2 u = length(fl.ba) > 1e-5 ? normalize(fl.ba) : vec2(0.);   // the way the light is travelling, in page orientation
    vec2 outw = lum(pg) > lum(gd) ? -n : n;   // out of the type or panel, toward the ground
    float face = smoothstep(.15, .7, dot(outw, -u));   // edges facing the oncoming light take it; the far sides stay dark, so nothing is ringed
    // small type on a light ground keeps its edges: if the dark side of the edge is back to ground within 4 px, it is a thin stroke
    vec2 into = -vec2(n.x, -n.y) * 4. * px;
    float thin = 1. - smoothstep(.10, .24, distance(texP(f + into), tex(ground, f + into)));
    vec3 warm = screen(F0, vec3(.18, .12, .05));
    vec3 pale = screen(F0, vec3(.62, .55, .42));   // on gold the light has to be paler than the ground to read as light
    vec3 col = mix(mix(pale, warm, dark), fall(age * .9), clamp(age * 1.3, 0., 1.) * mix(.55, 1., dark));
    float obj = smoothstep(.05, .2, distance(pg, gd));   // light lands on the object's own edge, never on the ground beside it
    float I = min(1., clamp(L, 0., 1.6) * edge * face * obj * mix(1.1, 2.2, dark) * (1. - thin * (1. - dark) * .9)) * gain;
    bool bright = lum(pg) > lum(gd) + .08;
    vec3 tint = mix(F0, screen(F0, vec3(.25, .2, .1)), .5);   // light type turns gold on its lit edge rather than whiter
    outc = bright ? mix(pg, mix(tint, col, clamp(age * 1.3, 0., 1.)), I * .85) : screen(pg, col * I);
  }
  o = vec4(outc, 1.);
}`);
  const quad = new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]);
  const qbuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qbuf); gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
  const ibuf = gl.createBuffer();
  const tPage = gl.createTexture(), tGround = gl.createTexture(), tField = gl.createTexture(), fbo = gl.createFramebuffer();
  let FW = 1, FH = 1;
  function texParams(t, filter) { gl.bindTexture(gl.TEXTURE_2D, t); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); }
  const nat = im => [im.naturalWidth || im.width, im.naturalHeight || im.height];
  function cover(w, h) {
    const [nw, nh] = nat(img), s = Math.max(w / nw, h / nh);
    return [0, 0, nw, nh, (w - nw * s) / 2, 0, nw * s, nh * s];
  }
  // the page and ground views
  function upload(page, gimg) {
    img = page;
    for (const [t, im] of [[tPage, img], [tGround, gimg]]) { texParams(t, gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im); }
  }
  // attribute and uniform locations, looked up once; the splat buffer, grown when needed
  const aS = Object.fromEntries(["corner", "ctr", "pa", "pw"].map(n => [n, gl.getAttribLocation(splat, n)]));
  const uS = { res: gl.getUniformLocation(splat, "res"), aniso: gl.getUniformLocation(splat, "aniso") };
  const aShow = gl.getAttribLocation(show, "corner");
  const uShow = Object.fromEntries(["page", "ground", "field", "res", "rect", "px", "gain"].map(n => [n, gl.getUniformLocation(show, n)]));
  let v = new Float32Array(0);
  // c3's frame becomes the page the raking light reads from and draws on
  function setPage(c2) { gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tPage); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c2); }
  function size(w, h, dpr) {
    W = w; H = h; DPR = dpr; glc.width = W * DPR; glc.height = H * DPR;
    FW = Math.max(1, Math.round(glc.width / 2)); FH = Math.max(1, Math.round(glc.height / 2));
    texParams(tField, gl.LINEAR); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, FW, FH, 0, gl.RGBA, gl.HALF_FLOAT, null);
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tField, 0); gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  }
  function draw(now, trail) {
    if (!img) return;
    const o = SET_A;
    // the field, at half resolution
    if (v.length < trail.length * 54) v = new Float32Array(trail.length * 54 * 2); let k = 0;
    const s = FW / W;   // css px to field px
    for (const p of trail) {
      if (now - p.t >= o.life) continue;
      const age = (now - p.t) / o.life, r = (o.r + o.rs * p.sp) * (1 + age * o.grow);
      const peak = 10 / (r * 0.64);   // a stroke reads the same at any radius: overlapping splats along the path sum to about one
      const lightv = peak * (1 - age) ** o.fade;
      const b3 = lightv * Math.cos(p.ang), b4 = lightv * Math.sin(p.ang);   // which way the light is travelling
      const cx = p.x * s, cy = (H - p.y) * s, rr = r * s;
      for (let i = 0; i < 6; i++) { v[k] = quad[i * 2]; v[k + 1] = quad[i * 2 + 1]; v[k + 2] = cx; v[k + 3] = cy; v[k + 4] = rr; v[k + 5] = lightv; v[k + 6] = age; v[k + 7] = b3; v[k + 8] = b4; k += 9; }
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo); gl.viewport(0, 0, FW, FH); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    if (trail.length) {
      gl.useProgram(splat); gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      gl.bindBuffer(gl.ARRAY_BUFFER, ibuf); gl.bufferData(gl.ARRAY_BUFFER, v.subarray(0, k), gl.DYNAMIC_DRAW);
      gl.enableVertexAttribArray(aS.corner); gl.vertexAttribPointer(aS.corner, 2, gl.FLOAT, false, 36, 0);
      gl.enableVertexAttribArray(aS.ctr); gl.vertexAttribPointer(aS.ctr, 2, gl.FLOAT, false, 36, 8);
      gl.enableVertexAttribArray(aS.pa); gl.vertexAttribPointer(aS.pa, 4, gl.FLOAT, false, 36, 16);
      gl.enableVertexAttribArray(aS.pw); gl.vertexAttribPointer(aS.pw, 1, gl.FLOAT, false, 36, 32);
      gl.uniform2f(uS.res, FW, FH);
      gl.uniform1f(uS.aniso, 0);
      gl.drawArrays(gl.TRIANGLES, 0, k / 9); gl.disable(gl.BLEND);
      for (const n of ["corner", "ctr", "pa", "pw"]) gl.disableVertexAttribArray(aS[n]);
    }
    // the page with it
    gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, glc.width, glc.height); gl.useProgram(show);
    gl.bindBuffer(gl.ARRAY_BUFFER, qbuf); const ac = aShow;
    gl.enableVertexAttribArray(ac); gl.vertexAttribPointer(ac, 2, gl.FLOAT, false, 0, 0);
    [[tPage, "page"], [tGround, "ground"], [tField, "field"]].forEach(([t, n], i) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t); gl.uniform1i(uShow[n], i); });
    const [, , , , dx, dy, dw, dh] = cover(glc.width, glc.height);
    gl.uniform2f(uShow.res, glc.width, glc.height);
    gl.uniform4f(uShow.rect, dx, dy, dw, dh);
    gl.uniform1f(uShow.px, DPR);
    gl.uniform1f(uShow.gain, GAIN);
    gl.drawArrays(gl.TRIANGLES, 0, 6); gl.disableVertexAttribArray(ac);
  }
  function dispose() { const x = gl.getExtension("WEBGL_lose_context"); if (x) x.loseContext(); }
  return { canvas: glc, size, upload, setPage, draw, dispose };
}
