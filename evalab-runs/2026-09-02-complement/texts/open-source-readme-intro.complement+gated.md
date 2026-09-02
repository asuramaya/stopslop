# Vega

A charting library for people who have to ship a dashboard by Friday.

Vega draws line, bar, area, scatter, and stacked charts from plain JavaScript arrays. There is no data-frame wrapper to learn and no config object three levels deep. You pass an array of objects, name the fields you want on each axis, and get back an SVG element you can drop into the page.

```js
import { line } from 'vega'

document.body.append(
  line(sales, { x: 'month', y: 'revenue' })
)
```

The whole library is 14 kB minified and gzipped, with no dependencies. Tree-shaking works, so if you only import the bar chart you only ship the bar chart, about 6 kB.

Charts resize with their container, redraw when you hand them new data, and render on the server for static output. Axis ticks, number formatting, and legends have defaults that look reasonable, and every one of them takes an override when the defaults are wrong for your data. Colors ship as a palette tested for contrast in light and dark themes, and against the three common forms of color vision deficiency. Tooltips and legends carry ARIA roles, and keyboard users can tab through data points.

Vega runs on any framework or none. React, Vue, and Svelte wrappers live in separate packages so the core stays small. MIT licensed. Read the [quickstart](docs/quickstart.md) or browse the [gallery](https://vega.dev/gallery).
