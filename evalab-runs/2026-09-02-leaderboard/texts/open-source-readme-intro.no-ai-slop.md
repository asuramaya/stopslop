# Plotwell

Plotwell draws charts in the browser from plain arrays and a small options object. It's 14 kB gzipped, renders to SVG or Canvas, and pulls in no dependencies.

```js
import { line } from 'plotwell'

line('#sales', data, { x: 'month', y: 'revenue' })
```

That gives you axes, gridlines, a legend, and tooltips on hover. Swap `line` for `bar`, `area`, or `scatter` and the rest of the call stays identical.

Everything is a plain object, so you can diff a chart config in code review, store it in a database, or generate it from a query. There is no builder chain and no plugin registry to learn.

Charts redraw at 60fps up to about 50,000 points on Canvas. Past that, pass `{ decimate: true }` and Plotwell downsamples with LTTB before drawing.

What it doesn't do: maps, 3D, network graphs, or anything with a WebGL backend. If you need those, use D3 or Plotly. Plotwell covers the eight chart types that show up in most dashboards and tries to make them look right by default.

```
npm install plotwell
```

Works with React, Vue, Svelte, and no framework at all. Read the [15-minute tutorial](docs/tutorial.md) or browse the [gallery](https://plotwell.dev/gallery).
