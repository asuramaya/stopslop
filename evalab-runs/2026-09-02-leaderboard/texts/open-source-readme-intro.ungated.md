# Tern

Tern draws charts in the browser. That's the whole scope.

Most charting libraries start small and end up as a plugin system wrapped around a 400-key options object. Tern takes the opposite bet: a handful of marks — line, bar, point, area, rule — that you compose. A stacked bar with a trend line and an annotation layer is three marks in one call, not a config tree with a `series[].overlay.type` branch.

The output is plain SVG. No canvas fallback, no shadow DOM, no wrapper components. Inspect an axis tick in devtools and you get a `<g>` with a class name you can target from your own stylesheet. Matching a design system means writing CSS, which you already know how to do.

14 kB gzipped, zero dependencies. Renders 50,000 points in roughly 30 ms on a 2019 ThinkPad. Past that you want canvas, and Tern says so in a console warning rather than quietly getting slower.

Accessibility isn't an add-on here. Every chart emits a keyboard-navigable data table behind `aria-describedby`, built from the same array you passed in.

Apache 2.0. React, Vue, and Svelte bindings live in this repo, each under 200 lines.
