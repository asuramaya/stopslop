# Axil

Axil turns an array of objects into an SVG chart in four lines.

```js
import { line } from 'axil'

line(document.querySelector('#sales'), rows, { x: 'month', y: 'revenue' })
```

That call reads your data, picks the scales, draws the axes, and labels the ticks. Pass a fourth argument when you want to override one of those choices.

Axil ships line, bar, area, and scatter charts. Each one takes the same two things: your rows and a field mapping. You learn one signature and you know the whole library.

Axil writes plain SVG elements with predictable class names, so you style charts in your own stylesheet. Skip the theme object and the canvas escape hatch. Change `.axil-tick text` in the CSS file you already have.

The core weighs 11 kB gzipped and pulls in nothing else. Your bundler drops the chart types you never import.

Axil touches the one DOM node you hand it, which makes it work under React, Vue, Svelte, or a script tag in a static page. The React wrapper adds 400 bytes and wraps a `useEffect`.

We wrote Axil after five years of maintaining a D3 wrapper that nobody on the team wanted to open. MIT licensed. Read the [API reference](docs/api.md) or run `npm i axil`.
