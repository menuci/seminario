// kernel-widget.js
// Interactive OU seed-dispersal kernel for the Quarto/reveal.js slides.
// Port of the numerics in viz_v4.py (sin^2-mapped Gauss-Legendre quadrature over
// the gut-passage time), drawn as plain SVG: no Plot, no d3, no CDN -> works offline.
//
//   K(x_d | x_e) = (1/sigma_r) * sum_j W_j N(y; y_e e^{-u_j}, 1 - e^{-2 u_j}),
//   u_j = L_j / beta,  y = x_d / sigma_r,  home-range centre mu = 0.

const N_QUAD = 600;          // Gauss-Legendre nodes (same as viz_v4.py)
const N_X = 1000;            // x grid points (same as viz_v4.py)
const NSIGMA = 6;            // x range: [min(0,x_e) - 6 sigma_r, max(0,x_e) + 6 sigma_r]
const CUSP_HMIN = 1e-5;      // smallest offset from x_e, in units of sigma_r
const STEPS = 2000;          // slider resolution
const VAR_EPS = 1e-30;
const SQRT_2PI = Math.sqrt(2 * Math.PI);

const C = {
  kernel: "#4dd0e1", stationary: "#9e9e9e", xe: "#ef5350", mu: "#f0f0f0",
  text: "#e6e6e6", muted: "#a8a8a8", axis: "#8a8a8a", grid: "rgba(255,255,255,0.10)",
//  beta: "#f5182b",
};

// ----------------------------------------------------------------- quadrature
function gaussLegendre(n) {
  const x = new Float64Array(n), w = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let z = Math.cos(Math.PI * (i + 0.75) / (n + 0.5)), dp = 1;
    for (let it = 0; it < 100; it++) {
      let p0 = 1, p1 = z;
      for (let k = 2; k <= n; k++) { const p2 = ((2 * k - 1) * z * p1 - (k - 1) * p0) / k; p0 = p1; p1 = p2; }
      dp = n * (z * p1 - p0) / (z * z - 1);
      const dz = p1 / dp;
      z -= dz;
      if (Math.abs(dz) < 1e-15) break;
    }
    x[i] = z; w[i] = 2 / ((1 - z * z) * dp * dp);
  }
  return { x, w };
}

// p = 1 - e^{-beta u} = sin^2(pi s / 2), Gauss-Legendre in s on (0, 1).
function sin2Rule(n) {
  const { x, w } = gaussLegendre(n);
  const L = new Float64Array(n), W = new Float64Array(n);
  for (let j = 0; j < n; j++) {
    const s = 0.5 * (x[j] + 1), oms = 0.5 * (1 - x[j]);
    const sh = Math.sin(0.5 * Math.PI * s), ch = Math.sin(0.5 * Math.PI * oms);
    const p = sh * sh;
    L[j] = p < 0.5 ? -Math.log1p(-p) : -2 * Math.log(ch);
    W[j] = 0.5 * w[j] * Math.PI * sh * ch;
  }
  return { L, W };
}

const RULE = sin2Rule(N_QUAD);
const M_ = new Float64Array(N_QUAD), H_ = new Float64Array(N_QUAD), C_ = new Float64Array(N_QUAD);

function kernel(x, xe, beta, sigma) {
  const ye = xe / sigma;
  for (let j = 0; j < N_QUAD; j++) {
    const u = RULE.L[j] / beta;
    const v = Math.max(-Math.expm1(-2 * u), VAR_EPS);
    M_[j] = ye * Math.exp(-u);
    H_[j] = 0.5 / v;
    C_[j] = RULE.W[j] / (SQRT_2PI * Math.sqrt(v));
  }
  const out = new Float64Array(x.length);
  for (let i = 0; i < x.length; i++) {
    const y = x[i] / sigma;
    let acc = 0;
    for (let j = 0; j < N_QUAD; j++) { const d = y - M_[j]; acc += C_[j] * Math.exp(-H_[j] * d * d); }
    out[i] = acc / sigma;
  }
  return out;
}

function stationary(x, sigma) {
  const out = new Float64Array(x.length), k = 1 / (SQRT_2PI * sigma);
  for (let i = 0; i < x.length; i++) { const z = x[i] / sigma; out[i] = k * Math.exp(-0.5 * z * z); }
  return out;
}

// --------------------------------------------------------------------- grid
const linspace = (a, b, n) => Array.from({ length: n }, (_, i) => a + (b - a) * i / (n - 1));
const geomspace = (a, b, n) => {
  const la = Math.log(a), lb = Math.log(b);
  return Array.from({ length: n }, (_, i) => Math.exp(la + (lb - la) * i / (n - 1)));
};

// Uniform grid + geometric grading at x_e (resolves the cusp at every scale) + cluster at 0.
function makeGrid(xe, sigma) {
  const lo = Math.min(0, xe) - NSIGMA * sigma, hi = Math.max(0, xe) + NSIGMA * sigma;
  const nGeo = Math.max(Math.floor(0.4 * N_X / 2), 8);
  const nMu = Math.max(Math.floor(0.1 * N_X), 8);
  const nUni = Math.max(N_X - 2 * nGeo - nMu, 16);
  const hmin = CUSP_HMIN * sigma;
  const pts = [
    ...linspace(lo, hi, nUni),
    ...geomspace(hmin, xe - lo, nGeo).map(h => xe - h),
    xe,
    ...geomspace(hmin, hi - xe, nGeo).map(h => xe + h),
    ...linspace(-NSIGMA, NSIGMA, nMu).map(t => t * sigma),
  ].filter(v => v >= lo && v <= hi).sort((a, b) => a - b);
  const x = [];
  for (const v of pts) if (x.length === 0 || v !== x[x.length - 1]) x.push(v);
  return { x: Float64Array.from(x), lo, hi };
}

// -------------------------------------------------------------------- ticks
function niceTicks(a, b, n) {
  const step0 = (b - a) / n, mag = 10 ** Math.floor(Math.log10(step0)), r = step0 / mag;
  const step = mag * (r >= 7.07 ? 10 : r >= 3.16 ? 5 : r >= 1.41 ? 2 : 1);
  const dec = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
  const out = [];
  for (let v = Math.ceil(a / step - 1e-9) * step; v <= b + 1e-9 * step; v += step) {
    out.push({ v, s: (Math.abs(v) < step / 2 ? 0 : v).toFixed(dec) });
  }
  return out;
}

const fmtBeta = v => String(Number(v.toPrecision(3)));
const SVGNS = "http://www.w3.org/2000/svg";
let uid = 0;

// ------------------------------------------------------------------- widget
export function kernelWidget({ xe = 7, beta = 0.2, sigma = 4, width = 1120, height = 545 } = {}) {
  const id = `kd${++uid}`;
  const M = { top: 40, right: 20, bottom: 70, left: 96 };
  const iw = width - M.left - M.right, ih = height - M.top - M.bottom;

  const params = [
    { key: "xe", label: "Feeding site x<sub>e</sub>", lo: -40, hi: 40, log: false, def: xe, fmt: v => v.toFixed(1) },
    { key: "beta", label: `<span style="color:${C.beta}">β</span> = ω<sub>d</sub>τ`, lo: 1e-4, hi: 1e2, log: true, def: beta, fmt: fmtBeta },
    { key: "sigma", label: "Home-range size σ<sub>r</sub>", lo: 0.2, hi: 15, log: false, def: sigma, fmt: v => v.toFixed(2) },
  ];
  const state = Object.fromEntries(params.map(p => [p.key, p.def]));

  const root = document.createElement("div");
  root.className = "kd-widget";
  root.innerHTML = `
<style>
  .reveal .cell-output-display:has(.kd-widget) { overflow: visible; }   /* never show a scrollbar around the widget */
  .kd-widget { max-width: ${width}px; margin: 0 auto; padding-bottom: 10px; color: ${C.text}; font-size: 22px; line-height: 1.2; }
  .kd-widget svg { display: block; width: 100%; height: auto; overflow: visible; }
  .kd-widget svg text { font-family: inherit; fill: ${C.text}; }
  .kd-widget .kd-controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0 44px;
                            padding: 0 ${M.right}px 0 ${M.left}px; }
  .kd-widget .kd-ctrl { display: flex; flex-direction: column; }
  .kd-widget .kd-ctrl label { display: flex; justify-content: space-between; align-items: baseline;
                              margin: 0; font-size: 22px; color: ${C.muted}; cursor: default; }
  .kd-widget .kd-val { color: ${C.text}; font-weight: 600; font-variant-numeric: tabular-nums; }
  .kd-widget input[type=range] { -webkit-appearance: none; appearance: none; width: 100%; height: 5px;
      margin: 10px 0 0; border-radius: 3px; cursor: pointer; outline: none;
      background: linear-gradient(to right, ${C.kernel} var(--p, 50%), #4a4a4a var(--p, 50%)); }
  .kd-widget input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none;
      width: 15px; height: 15px; border-radius: 50%; border: none; background: ${C.kernel}; }
  .kd-widget input[type=range]::-moz-range-thumb { width: 15px; height: 15px; border-radius: 50%;
      border: none; background: ${C.kernel}; }
  .kd-widget input[type=range]::-moz-range-track { background: transparent; }
  .kd-widget input[type=range]:focus-visible::-webkit-slider-thumb { box-shadow: 0 0 0 3px rgba(77,208,225,0.35); }
</style>
<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Dispersal kernel">
  <defs><clipPath id="${id}-clip"><rect x="0" y="-8" width="${iw}" height="${ih + 10}"/></clipPath></defs>
  <g transform="translate(${M.left},${M.top})">
    <g class="kd-gy"></g><g class="kd-gx" transform="translate(0,${ih})"></g>
    <line x1="0" x2="${iw}" y1="${ih}" y2="${ih}" stroke="${C.axis}" stroke-width="1.5"/>
    <line x1="0" x2="0" y1="0" y2="${ih}" stroke="${C.axis}" stroke-width="1.5"/>
    <g clip-path="url(#${id}-clip)">
      <line class="kd-mu" y1="-6" y2="${ih}" stroke="${C.mu}" stroke-width="2" stroke-dasharray="10 4 2 4"/>
      <line class="kd-xe" y1="-6" y2="${ih}" stroke="${C.xe}" stroke-width="2" stroke-dasharray="7 5"/>
      <path class="kd-stat" fill="none" stroke="${C.stationary}" stroke-width="2" stroke-dasharray="8 6"/>
      <path class="kd-kern" fill="none" stroke="${C.kernel}" stroke-width="3.5" stroke-linejoin="round"/>
    </g>
    <text class="kd-mu-lab" y="22" font-size="22" style="fill:${C.mu}">μ = 0</text>
    <text class="kd-xe-lab" y="22" font-size="24" font-style="italic" style="fill:${C.xe}">x<tspan baseline-shift="sub" font-size="17">e</tspan></text>
    <g class="kd-legend" font-size="21">
      <line x1="0" x2="40" y1="0" y2="0" stroke="${C.kernel}" stroke-width="3.5"/>
      <text x="52" y="7">K(x<tspan baseline-shift="sub" font-size="15">d</tspan><tspan baseline-shift="0"> | x</tspan><tspan baseline-shift="sub" font-size="15">e</tspan><tspan baseline-shift="0">)</tspan></text>
      <line x1="0" x2="40" y1="32" y2="32" stroke="${C.stationary}" stroke-width="2" stroke-dasharray="8 6"/>
      <text x="52" y="39">stationary N(0, σ<tspan baseline-shift="sub" font-size="15">r</tspan><tspan baseline-shift="super" font-size="15">2</tspan><tspan baseline-shift="0">)</tspan></text>
    </g>
    <text x="${iw / 2}" y="${ih + 62}" text-anchor="middle" font-size="23">deposition site x<tspan baseline-shift="sub" font-size="17">d</tspan></text>
    <text transform="translate(${-M.left + 24},${ih / 2}) rotate(-90)" text-anchor="middle" font-size="23">K(x<tspan baseline-shift="sub" font-size="17">d</tspan><tspan baseline-shift="0"> | x</tspan><tspan baseline-shift="sub" font-size="17">e</tspan><tspan baseline-shift="0">)</tspan></text>
  </g>
</svg>
<div class="kd-controls"></div>`;

  const q = s => root.querySelector(s);
  const gx = q(".kd-gx"), gy = q(".kd-gy"), pK = q(".kd-kern"), pS = q(".kd-stat");
  const lXe = q(".kd-xe"), lMu = q(".kd-mu"), tXe = q(".kd-xe-lab"), tMu = q(".kd-mu-lab");
  const legend = q(".kd-legend"), legendW = 300;

  const svgEl = (tag, attrs, text) => {
    const e = document.createElementNS(SVGNS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  };

  function draw() {
    const { xe, beta, sigma } = state;
    const { x, lo, hi } = makeGrid(xe, sigma);
    const K = kernel(x, xe, beta, sigma), S = stationary(x, sigma);
    let ymax = 0;
    for (let i = 0; i < x.length; i++) ymax = Math.max(ymax, K[i], S[i]);
    ymax *= 1.08;
    const sx = v => (v - lo) / (hi - lo) * iw, sy = v => ih - v / ymax * ih;

    const path = Y => {
      let d = "";
      for (let i = 0; i < x.length; i++) d += (i ? "L" : "M") + sx(x[i]).toFixed(2) + "," + sy(Y[i]).toFixed(2);
      return d;
    };
    pK.setAttribute("d", path(K));
    pS.setAttribute("d", path(S));

    gx.replaceChildren(...niceTicks(lo, hi, 9).flatMap(t => [
      svgEl("line", { x1: sx(t.v), x2: sx(t.v), y1: 0, y2: -ih, stroke: C.grid }),
      svgEl("line", { x1: sx(t.v), x2: sx(t.v), y1: 0, y2: 7, stroke: C.axis, "stroke-width": 1.5 }),
      svgEl("text", { x: sx(t.v), y: 31, "text-anchor": "middle", "font-size": 19 }, t.s),
    ]));
    gy.replaceChildren(...niceTicks(0, ymax, 6).flatMap(t => [
      svgEl("line", { x1: 0, x2: iw, y1: sy(t.v), y2: sy(t.v), stroke: C.grid }),
      svgEl("line", { x1: -7, x2: 0, y1: sy(t.v), y2: sy(t.v), stroke: C.axis, "stroke-width": 1.5 }),
      svgEl("text", { x: -12, y: sy(t.v) + 6, "text-anchor": "end", "font-size": 19 }, t.s),
    ]));

    const pxe = sx(xe), pmu = sx(0);
    lXe.setAttribute("x1", pxe); lXe.setAttribute("x2", pxe);
    lMu.setAttribute("x1", pmu); lMu.setAttribute("x2", pmu);
    // labels sit just above the plot frame, right of their line; if x_e and mu
    // are close, mu's label goes to the left of its line so they never collide
    const place = (t, px, side) => {
      t.setAttribute("x", px + (side === "left" ? -8 : 8));
      t.setAttribute("text-anchor", side === "left" ? "end" : "start");
      t.setAttribute("y", -10);
    };
    const close = Math.abs(pxe - pmu) < 90;
    place(tXe, pxe, pxe > iw - 60 || (close && pxe < pmu) ? "left" : "right");
    place(tMu, pmu, close ? (pxe < pmu ? "right" : "left") : (pmu > iw - 90 ? "left" : "right"));
    // legend in the upper corner away from x_e
    const legendLeft = pxe > iw / 2;
    legend.setAttribute("transform", `translate(${legendLeft ? 24 : iw - legendW}, 30)`);
  }

  let pending = false;
  const schedule = () => { if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; draw(); }); } };

  const controls = q(".kd-controls");
  for (const p of params) {
    const toPos = v => {
      const t = p.log ? (Math.log10(v) - Math.log10(p.lo)) / (Math.log10(p.hi) - Math.log10(p.lo)) : (v - p.lo) / (p.hi - p.lo);
      return Math.round(Math.min(Math.max(t, 0), 1) * STEPS);
    };
    const toVal = pos => {
      const t = pos / STEPS;
      return p.log ? 10 ** (Math.log10(p.lo) + t * (Math.log10(p.hi) - Math.log10(p.lo))) : p.lo + t * (p.hi - p.lo);
    };
    const wrap = document.createElement("div");
    wrap.className = "kd-ctrl";
    wrap.innerHTML = `<label for="${id}-${p.key}"><span>${p.label}</span><span class="kd-val"></span></label>
      <input id="${id}-${p.key}" type="range" min="0" max="${STEPS}" step="1" value="${toPos(p.def)}">`;
    const input = wrap.querySelector("input"), val = wrap.querySelector(".kd-val");
    const show = () => {
      val.textContent = p.fmt(state[p.key]);
      input.style.setProperty("--p", `${100 * input.value / STEPS}%`);   // filled part of the bar
    };
    input.addEventListener("input", e => {
      e.stopPropagation();                 // keep the OJS runtime out of it
      state[p.key] = toVal(+input.value);
      show(); schedule();
    });
    // hand the arrow keys back to reveal.js once the slider is released
    input.addEventListener("pointerup", () => input.blur());
    // double-click restores the default value of this parameter
    input.addEventListener("dblclick", () => {
      state[p.key] = p.def; input.value = toPos(p.def); show(); schedule();
    });
    show();
    controls.append(wrap);
  }

  draw();
  return root;
}
