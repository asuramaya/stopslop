## Plot

Plot is a charting library for JavaScript. It draws line, bar, scatter, and area charts from plain arrays of numbers, and it renders to SVG so the output works in any browser without a canvas fallback.

Most charting libraries make you configure a scale, an axis, and a legend before you see a single pixel. Plot infers all three from your data by default. Pass it an array of `{x, y}` points and it picks sensible ranges, tick counts, and colors on its own. You override any of that with explicit options when the defaults are wrong, but you rarely need to.

The library ships as a single ES module with no dependencies. It weighs under 12kB gzipped, and it works with React, Vue, or no framework at all, since the output is inert SVG you can style with normal CSS.

Plot handles the charts most projects actually need: time series, grouped and stacked bars, scatter plots with size and color encoding, and small multiples for comparing categories side by side. It does not try to replace a full visualization grammar like Vega or D3. If you need those, use them. If you need a chart on a page by lunchtime, start here.
