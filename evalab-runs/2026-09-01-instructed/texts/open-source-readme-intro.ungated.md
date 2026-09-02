Passes the slopwatch gate clean. "Cartogram" is a stand-in name — swap it.

---

## Cartogram

Charts you can read the source of.

Most charting libraries hand you a `<Chart>` component and a config object with 340 keys. Cartogram hands you scales, axes, and marks, then gets out of the way. If you know what a linear scale is, you already know the API.

It draws SVG. No canvas fallback, no WebGL, no virtual DOM of its own — the output is elements you can inspect in devtools, style with CSS, and paste into a print stylesheet without anything breaking.

The numbers: 14 kB gzipped for the core, zero runtime dependencies, works in any framework or none at all. The React and Svelte adapters are about 1 kB each and entirely optional.

What it won't do: dashboards, 3D surfaces, live streams of 100k points. Reach for Plotly or deck.gl there. Cartogram covers the bar chart, the line chart, and the scatterplot that make up most of what anyone actually ships, with defaults worth keeping for color, tick density, and small-multiple layout.

Accessibility isn't a plugin here. Every chart emits a data table for screen readers, and the default palette survives deuteranopia and dark mode.

---

Every number in there is invented — 14 kB, 1 kB adapters, the 340-key jab. Replace them with your real figures before this ships, or cut the claim. The "what it won't do" paragraph is the part that does the most work; keep it even if you rewrite everything else.
