# Plotwright

A charting library for people who have read the docs of three other charting libraries and given up.

Plotwright draws to SVG or Canvas from one API. You describe the data and the encoding — x, y, color, size — and it works out scales, axes, and legends. When the defaults are wrong, every one of them is a prop you can override, and the override never sends you into a nested config object four levels deep.

```js
import { plot } from 'plotwright'

plot({
  data: sales,
  x: 'month',
  y: 'revenue',
  color: 'region',
  mark: 'line',
})
```

The core is 14 kB minified and gzipped, with no dependencies. Marks live in separate entry points, so a bar chart does not ship the geographic projection code. Rendering is synchronous and deterministic: the same data produces byte-identical SVG, which makes snapshot tests possible.

Charts are keyboard-navigable and expose their data as a table to screen readers by default, without a plugin. Tooltips work on touch.

There is no theme marketplace and no chart wizard. There are 11 mark types, a scale system, and an escape hatch that hands you the raw SVG node.
