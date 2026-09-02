# Plotwright

A charting library for people who have to ship the chart today.

Most chart libraries hand you a config object with 200 keys and let you find out at runtime which twelve you needed. Plotwright inverts that. You describe the data and the question you're asking of it, and the library picks the encoding, the axis treatment, and the color scale. When it guesses wrong, every one of those choices is a prop you can override.

```js
import { chart } from 'plotwright'

chart(revenue, { x: 'month', y: 'usd', by: 'region' })
```

That renders a multi-series line chart with a formatted currency axis, a legend ordered by final value, and colors that stay distinguishable in both light and dark themes and for the most common forms of color blindness.

The core is 14 kB gzipped with no dependencies. It renders to SVG on the server and hydrates only if you attach interaction. Time formatting comes from `Intl`, not a bundled locale table, so adding Japanese costs nothing.

Plotwright covers the chart types that appear in real dashboards: line, area, bar, stacked bar, scatter, histogram, heatmap. There is no chord diagram and no 3D surface plot. If you need those, D3 is underneath and we export the scales.

Works with React, Vue, Svelte, and plain DOM. MIT licensed.
