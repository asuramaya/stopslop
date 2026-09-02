# Plotline

Plotline draws SVG charts from arrays of numbers. Pass it data and a DOM node, get back elements you style with CSS.

```js
import { render, line, axis } from 'plotline'

render('#revenue', [
  axis({ x: 'month', y: 'usd' }),
  line(data, { stroke: 'var(--brand-500)' }),
])
```

Twelve functions, 9kb gzipped, zero dependencies. Compose the twelve instead of hunting through a config object with four hundred keys.

Three things shaped the design. Charts render to SVG nodes you own, so your stylesheet controls color and type, and your CSS transitions animate them. Every function takes data first and options second, which makes them work under `map` and `pipe` without wrappers. The render step runs in Node, so your server can send a finished chart in the HTML instead of a spinner.

Plotline handles line, bar, area, scatter, and stacked variants of each. Axes support time, linear, log, and band scales. For anything past that, `custom()` hands you the scale functions and gets out of the way.

React, Vue, and Svelte adapters live in the same repo and stay at one version. Nothing here reaches for a global, so two copies on a page coexist.

Read [the tutorial](docs/tutorial.md) or copy an example from [examples/](examples/).
