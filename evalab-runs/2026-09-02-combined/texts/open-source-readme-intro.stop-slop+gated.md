# Hatch

Hatch draws charts in the browser from an array of rows and a small config object. You say which field goes on x, which goes on y, and it hands back SVG that your own CSS controls.

```js
import { line } from '@hatch/core'

line(document.querySelector('#chart'), rows, { x: 'date', y: 'revenue' })
```

Most charting libraries make you learn a layout engine before you can move a legend three pixels. Hatch puts every mark, axis, and label in the DOM as an ordinary element with an ordinary class name, so you move the legend with flexbox and restyle the gridlines in your stylesheet next to everything else, the same way you would style a table or a nav bar. Print it, and it prints.

The core is 14 kB gzipped and pulls in no runtime dependencies. Line, bar, area, and scatter live there.

Maps, hexbins, and the WebGL renderer sit in separate packages that you add when a project needs them, so a dashboard with two line charts ships two line charts. Hatch runs against React, Vue, Svelte, and a bare HTML file, because it touches nothing but the element you hand it. There is one adapter per framework, each under 200 lines, and you can read all of them in an afternoon.
