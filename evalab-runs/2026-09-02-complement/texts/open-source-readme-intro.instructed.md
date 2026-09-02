# Plotwright

A charting library for people who have read the source of their charting library.

Plotwright draws to SVG from a plain data array and a spec object. There is no chart type enum. A bar chart is a rectangle mark bound to a band scale; a scatter is a point mark on two linear scales. The same six marks compose into roughly forty of the chart types other libraries ship as separate constructors, and into the ones they don't.

The core is 14 kB minified and gzipped, with no runtime dependencies. Scales, axes, and the layout solver are separate entry points, so a sparkline import pulls in about 4 kB.

Rendered output is static SVG by default. That means it works in an email client, in a PDF pipeline, and in a server-rendered page with JavaScript disabled. Interaction is opt-in: import the `hover` module and you get a tooltip layer and pointer events, at a cost of 3 kB.

Axes carry accessible labels, and every mark accepts an `aria` field that lands on the element. Color defaults come from a palette checked for contrast against both light and dark backgrounds, and for the three common forms of color vision deficiency.

Works in the browser, in Node, and in Deno.
