# Plotline

Plotline draws charts in the browser. It ships eleven chart types, weighs
14 kB gzipped with no dependencies, and renders to SVG or Canvas from the
same API.

Most charting libraries make you choose. The small ones give you a line
chart and a bar chart and then leave you writing raw SVG the first time a
designer asks for a second y-axis. The large ones hand you a configuration
object with four hundred keys, and you spend an afternoon in the docs
finding out which three of them control the axis labels.

Plotline takes a middle position. Every chart is a function that takes
data and returns a scene graph you can inspect, modify, and hand back. If
the built-in bar chart is close but wrong, you do not file an issue and
wait. You copy thirty lines out of `src/charts/bar.js` and change the two
that matter.

```js
import { line } from 'plotline'

const accessors = { x: d => d.month, y: d => d.revenue }
line(document.querySelector('#chart'), sales, accessors)
```

Axes, scales, and legends are separate modules. Import the ones you use.
Tooltips and animation are opt-in, and both are under 2 kB.
