Charting library for JavaScript. Renders line, bar, area, and scatter plots straight into SVG or canvas, with no build step and no dependency on a UI framework.

Most charting libraries make you choose between two bad options: a black-box component that takes ten props to get right, or a low-level primitives library where you're writing axis math by hand. This one sits in between. You get a small set of composable layers — scales, axes, marks, legends — that you stack to build the exact chart you need, but each layer ships with sane defaults so a basic line chart is three lines of code.

It's built for people who read data more than they write chart code: analysts wiring up a dashboard, engineers adding a sparkline to a product page, researchers plotting results before a paper is due. The API is the same whether you're rendering one chart or embedding two hundred in a report.

No canvas-vs-SVG lock-in, no CSS-in-JS tax, no 40kb of unused chart types you'll never render. Pick the marks you need, import only those, and ship.

Install it, read the five-minute guide below, and you'll have a working chart before your coffee's cold.
