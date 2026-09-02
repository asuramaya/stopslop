## Nomogram

Nomogram draws charts from data you already have, in about 12 KB of JavaScript with no runtime dependencies.

Most charting libraries ask you to learn a configuration language first. You describe a chart as nested option objects, then spend an afternoon finding out which of the forty keys controls the axis tick you want to move. Nomogram makes a different bet, which is that you pass an array of records and say which field maps to x, which to y, and which to color. Everything else is a default you can override with a function.

```js
import { plot } from 'nomogram'

plot(sales, { x: 'month', y: 'revenue', color: 'region', type: 'line' })
```

That call renders SVG. There is no canvas fallback, no virtual DOM, and no wrapper for your framework, because the output is a DOM node you can put anywhere. React, Svelte, a static site generator, or a `<script>` tag in an HTML file all work the same way.

Scales, legends, and axes are separate exports. If the high-level `plot` doesn't fit your case, drop one level down and compose the pieces yourself instead of fighting an options object.

Nomogram handles roughly 50,000 points before you should reach for something WebGL-based. It is MIT licensed and works in any browser with SVG and ES2020.
