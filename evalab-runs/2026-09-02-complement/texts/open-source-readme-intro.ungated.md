# Plotline

Plotline draws charts in the browser from plain arrays of objects. It is 14 kB gzipped, has no runtime dependencies, and renders SVG, so the output inherits your CSS, survives a print stylesheet, and can be read in devtools like any other markup.

```js
import { chart } from 'plotline'

chart('#sales', data, { x: 'month', y: 'revenue', color: 'region' })
```

That is the whole API surface for the common case. You name the fields; Plotline picks scales, axes, and a legend from the data types it finds. Everything it picked is a value you can override, one option at a time, without dropping into a different mental model.

Nine mark types ship in the core: bar, line, area, point, rule, tick, arrow, band, and text. Anything else is a plugin, and plugins get the same scale and layout objects the built-in marks use.

Plotline came out of a dashboard rewrite where the existing library's config file had grown past 400 lines for six charts. The design goal is that the config stays roughly as long as the thing you are describing.

Requires no build step. Works in a script tag, a bundler, or on the server for static SVG.
