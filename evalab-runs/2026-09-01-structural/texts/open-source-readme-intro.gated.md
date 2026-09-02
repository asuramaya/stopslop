# Axle

Most charting libraries make you pick a side. Either you get a `<BarChart>` that renders in one line and fights you the moment the design changes, or you get a low-level grammar of graphics that costs you an afternoon on axis ticks.

Axle keeps both layers, and makes both public.

The scales, tick placement and layout math live in a pure-function core with no DOM dependency: call `linearScale()`, get numbers back. The marks are plain SVG components on top of that. Use the presets until they stop fitting, drop down a level, keep everything else where it is.

Some specifics:

- 14 kB min+gzip for the core, 9 kB more for a bar chart
- Renders to SVG on the server; hydrates only if you add interaction
- No global theme object. Charts read CSS custom properties, so dark mode is a media query.
- Types are generated from your data shape, so `y="reveune"` fails the build

Axle is not a D3 replacement. If you are drawing a hexbin sankey, use D3. This covers the nine or so chart types that fill most dashboards, and stays out of your way for the rest.
