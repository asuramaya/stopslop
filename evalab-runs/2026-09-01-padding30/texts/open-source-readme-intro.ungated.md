Passes the repo's own `slopwatch` gate. Name and numbers are placeholders — swap them for your real bundle sizes.

---

# Plotwright

Most charting libraries make you choose. Either you get a `<BarChart>` that renders in one line and then fights you the moment the design changes, or you get d3 — total control, and a week of your life gone to axis math.

Plotwright splits that at the layer where it matters. Scales, layout, and tick generation live in a pure-JS core with no DOM and no framework. On top sits a thin renderer, SVG or Canvas, which you can bypass entirely if you'd rather draw the marks yourself.

What that buys you:

- About 14 kB gzipped for the core, 22 kB with the SVG renderer.
- Charts render on the server. No canvas shim, no headless browser.
- Every visual decision is a value you can read and override. Tick positions, band widths, stack offsets: all of it is data before it's pixels.
- Types that describe your data, not our config object.

Plotwright doesn't do dashboards, and it won't pick your colors. It draws charts and gets out of the way.

---

Two things to check against your actual library: the d3-vs-components framing only lands if your core really is renderer-free, and the last line is a positioning claim you'll be held to — cut it if you do plan on a dashboard layer.
