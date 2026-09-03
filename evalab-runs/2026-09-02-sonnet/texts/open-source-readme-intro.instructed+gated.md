Plotter renders charts in the browser on a canvas backend, with no dependencies. Add a data array and a container element, and it draws the axes, scales, and marks.

Most charting libraries require a configuration language before you can plot a line. Plotter takes a JavaScript array of objects and a field name and draws the chart. Options exist for axis labels, color scales, and tooltips, but none are required to get a working chart on screen.

The library handles line, bar, area, and scatter charts, plus stacked and grouped variants for bar and area, and all of them share the same data format. Switching from a bar chart to a line chart means changing one string, not rewriting the configuration.

Rendering happens on an HTML canvas, not SVG. On a five-year-old ThinkPad T480, a chart with 50,000 points redraws in under 16ms.

The bundle is 12KB gzipped with zero runtime dependencies. It works with React, Vue, Svelte, or plain script tags, because the core API only touches a canvas element and a data array — framework bindings are thin wrappers around that.
