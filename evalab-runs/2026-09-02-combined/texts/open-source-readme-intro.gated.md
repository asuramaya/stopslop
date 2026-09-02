# Plotwright

Plotwright draws charts from plain arrays and returns SVG. There is no canvas, no virtual DOM, no chart instance you have to keep alive and tear down on unmount. You call a function, you get markup, you put the markup wherever markup goes.

Most charting libraries assume they own the page. They mount into a div, attach resize observers, and hand you a config tree three levels deep before you can change an axis label. Plotwright assumes the opposite. It produces a string. Style it with CSS, serve it from a worker, paste it into an email — after the function returns, none of it is ours.

The tradeoff is worth stating up front. You do not get animated transitions, and you do not get built-in pan and zoom. If you need those, D3 or ECharts is the better answer. What you get instead is 14 kB, zero dependencies, and byte-identical output on a server and in a browser, which is what we needed for reports that had to look the same as a PDF, as a web page, and in somebody's inbox.

So far it covers line, area, bar, stacked bar, scatter, histogram, box, heatmap, and sparkline charts.
