# sparrow

I lost a Thursday to a stacked bar chart whose axis labels kept clipping. The fix turned out to be a 40-line theme override, inside a library that ships 190kB of JavaScript to draw twelve rectangles on a screen. So I wrote this instead.

sparrow renders charts as plain SVG. 9kB gzipped, zero dependencies, no canvas layer, and no config object with 300 keys nested four deep. You style it with CSS, because it's already in the DOM and there's nothing clever stopping you.

```js
import { bars } from 'sparrow'
bars('#sales', data, { x: 'month', y: 'revenue' })
```

That's the whole API surface for a bar chart. Line, area, scatter and heatmap work the same way, and if you want something we don't ship, the scale and axis primitives are exported so you can assemble it yourself in maybe thirty lines.

What it won't do: 3D anything, real-time streaming above roughly 10k points, or Excel-style pie charts with exploding slices. Those are real limits, not a roadmap.

Does the world need another charting library? Probably not. But I wanted one I could read the source of in an afternoon, and now that exists.
