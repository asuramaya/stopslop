Passes the repo's own slopwatch gate, clean. 182 words.

---

# Plotwright

Every charting library starts the same way: a bar chart in four lines, a demo page full of gradients, and then you need a second y-axis and the whole thing falls apart.

Plotwright is built the other way round. The core is a layout engine and a scale system, about 12 kB gzipped, and the chart types are thin wrappers over it. When a preset stops fitting, you drop one level down instead of forking the library.

What that buys you:

- Axes, legends, and annotations are ordinary components. Compose them.
- Scales are plain functions. `scaleTime(domain, range)` returns a function you can call. No adapter layer, no plugin registry.
- One spec renders to SVG or Canvas. Canvas takes the 200k-point scatter; SVG keeps everything else selectable and readable by a screen reader.
- Zero runtime dependencies.

It is opinionated about two things. Colors default to an Okabe-Ito palette that survives grayscale printing and the common color-vision deficiencies. And there are no animated entrances, because data should not slide in from the left.

React 18+ and vanilla JS. MIT.

---

The name, the 12 kB figure, the 200k-point threshold, and the React version are placeholders — swap in your real numbers, since specifics are what keep the pitch from reading as filler.
