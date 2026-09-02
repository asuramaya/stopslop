# Slate

Slate draws charts in the browser from plain JavaScript objects. No build step, no wrapper components, no configuration file.

```js
import { line } from 'slate'

line('#chart', data, { x: 'date', y: 'revenue' })
```

That is a working chart. The rest of the library is what you reach for when the defaults stop fitting: custom scales, layered marks, event handlers, and an escape hatch that hands you the underlying SVG node.

We wrote Slate because most charting libraries ask you to learn a grammar before you can draw a line. D3 gives you complete control at the cost of writing fifty lines for a bar chart. Chart.js hides the details but fights you the moment you want something it did not anticipate. Slate aims for the space between them, with sensible output from one call and full access when you need it.

The core is 14kB gzipped with no dependencies. Tree-shaking drops that further if you only import a few chart types. Rendering is SVG by default, with a Canvas renderer for series above roughly 10,000 points.

Slate supports line, bar, area, scatter, and histogram charts today. Stacked and grouped variants ship for bar and area. Maps, network graphs, and 3D surfaces are out of scope and will stay that way.

Requires a browser with ES2020 support. Works with React, Vue, and Svelte through thin adapter packages, or with no framework at all.
