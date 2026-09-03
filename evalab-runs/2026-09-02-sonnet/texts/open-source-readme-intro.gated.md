Plotline renders charts from plain data, without a config object between you and the result. You describe what the data means; the library picks defaults that work for most cases and lets you override anything.

Most charting libraries make you choose between two extremes: a high-level API that covers ten chart types and stops there, or a low-level canvas/SVG toolkit where every axis and tick mark is your responsibility. Plotline sits between them. Common charts (line, bar, scatter, area) take five lines of code. Anything unusual — a custom scale, a second axis, a non-standard tooltip — is a documented extension point, not a fork of the source.

The renderer defaults to SVG and switches to canvas past 10,000 points, so the same code handles a dashboard tile and a million-row scatter plot. Charts resize with their container by default, with no manual redraw call required.

Plotline ships with no dependencies beyond the DOM. It works in React, Vue, Svelte, or a script tag, because it never assumed a framework in the first place.

```js
import { chart } from "plotline";

chart("#app", { data, x: "date", y: "revenue" });
```

That call produces a line chart, axis labels included.
