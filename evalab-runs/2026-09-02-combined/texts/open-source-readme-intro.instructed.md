# Vela

Vela draws charts in the browser from plain JavaScript arrays. No build step, no wrapper components, no configuration object with forty keys you have to learn before the first line appears on screen.

```js
import { line } from 'vela'

line('#chart', data, { x: 'date', y: 'revenue' })
```

That's the whole API for a line chart. Bars, areas, scatter, and stacked variants follow the same shape: a selector, your data, and a mapping from field names to visual roles.

Most charting libraries make you choose between a canvas you draw on yourself and a component that renders one specific picture. Vela sits between them. Every chart returns a handle you can reach into — the scales, the axes, the SVG nodes — so adding an annotation layer or a custom tooltip means writing seven lines of DOM code, not filing a feature request.

The bundle is 14 kB minified and gzipped, with no dependencies. Charts render server-side to static SVG when you need them in an email or a PDF. Axis labels, colors, and tick formats read from CSS custom properties, so a chart inherits your site's theme instead of shipping its own.

Vela is MIT licensed. It renders roughly 50,000 points before frame times pass 16 ms; past that, use the WebGL renderer in `vela/gl`.
