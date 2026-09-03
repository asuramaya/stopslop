## Charts that render 60fps with 100,000 points

Most JavaScript charting libraries hit a wall around 5,000-10,000 points: frame rates drop, pan and zoom stutter, tooltips lag behind the cursor. This library renders to WebGL instead of SVG or Canvas 2D, so a scatter plot with 100,000 points redraws at 60fps on a 2019 laptop.

The API stays close to what you already know. A chart is a declarative spec — data, marks, scales, encodings — and the library handles the render pipeline underneath. Line charts, bar charts, scatter plots, and heatmaps share one configuration format, so switching mark types is a one-line change, not a rewrite.

Zoom and pan work out of the box, with axes and gridlines that update in real time as you drag. Tooltips read directly from the GPU buffer, so hover state stays in sync with the data even during a fast pan.

It ships with TypeScript types for every option, tree-shakes down to under 40kb for a basic line chart, and has zero required dependencies. Bring your own React, Vue, or vanilla DOM wrapper — the core library only touches a canvas element you give it.
