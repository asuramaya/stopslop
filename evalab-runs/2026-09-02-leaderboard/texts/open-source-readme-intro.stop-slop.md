# Kesh

Kesh turns an array of objects into an SVG chart you can style with CSS.

```js
import { line } from 'kesh'

document.body.append(line(sales, { x: 'month', y: 'revenue' }))
```

That call returns a real SVG element. You can inspect the axis ticks in devtools, set their color from your stylesheet, and hand the same markup to a server renderer for email or PDF.

We wrote Kesh after ripping a 340 KB dependency out of our dashboard. It shipped its own tooltip engine and its own opinion about fonts, and we spent more time overriding it than drawing anything. Kesh weighs 11 KB gzipped and pulls in nothing else. It draws bars, lines, areas, scatter plots, and histograms, and you build the rest from the same primitives the built-ins use: scales, axes, marks.

The API sits close to your data. Describe the chart as one mark per row, x from this field, y from that one, and you can write it without reading past this section.

Kesh runs in browsers from 2021 onward and in Node 18 or later. It ships TypeScript types and a 20-line React wrapper, and it keeps its hands off global state.

Start with [Getting Started](docs/getting-started.md).
