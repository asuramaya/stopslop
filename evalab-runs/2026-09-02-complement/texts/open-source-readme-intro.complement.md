# Plotline

Plotline draws charts in the browser from an array of objects and a short options block. It ships as one ES module with no dependencies, weighs about 14 kB gzipped, and renders SVG you can inspect, style with CSS, and hand to a printer.

```js
import { line } from 'plotline'

line(document.querySelector('#chart'), sales, {
  x: 'month',
  y: 'revenue',
  color: 'region',
})
```

That covers line, bar, area, scatter, and histogram. Each takes the same three arguments, so moving between chart types means changing one function name.

Axes, ticks, and legends come from the data by default. When the defaults are wrong, every piece is a slot you can replace with your own function that returns an SVG node. There is no theme system to learn and no plugin registry to register against.

Charts render server-side to a string, which keeps first paint free of layout shift. Tooltips, zoom, and brushing are separate imports, so a static dashboard never pays for them.

Plotline works with React, Vue, Svelte, and plain DOM code, because it only asks for an element. It handles dates, log scales, missing values, and right-to-left text.

MIT licensed. Requires Node 18 or any browser from the last three years.
