Passes the slopwatch gate clean at 199 words. The name and the numbers are invented placeholders — swap them for real ones.

```markdown
# Skiff

Skiff draws charts in the browser. Fourteen chart types, 19 kB gzipped, no
dependencies, and one config format that renders to either SVG or Canvas.

Small charting libraries hand you a line chart and a bar chart, then leave you
alone the first time somebody asks for a log axis or a second y-scale. Big ones
cover all of that and cost 300 kB plus a week of reading before you can draw
anything. Skiff sits between the two on purpose: enough built in that an
ordinary dashboard needs no plugins, small enough that you can read the whole
source over a long afternoon.

A chart here is data plus a spec, and the spec is a plain object. You can store
it, diff it, send it over the wire, or generate it from a form. No fluent
builder, no subclassing, no lifecycle to learn.

Rendering is stateless. Give Skiff the same spec twice and you get the same
pixels, which makes charts testable with snapshot tests instead of screenshots
and a human eye.

Works with React, Vue, Svelte and plain script tags. Typed, tree-shakeable,
MIT licensed, and tested against Chrome, Firefox and Safari on every commit.
```

Draft is at `/tmp/skiff.md` if you want it moved into a repo.
