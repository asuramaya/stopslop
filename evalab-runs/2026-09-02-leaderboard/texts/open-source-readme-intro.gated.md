Passes the slopwatch gate clean. The draft runs about 205 words, and since I invented the name and the specifics, swap them for your real numbers.

# Kite

Kite is a charting library for people who are tired of reading configuration docs.

Give it data and a chart type. It hands back an SVG. There is no canvas, no shadow DOM, no runtime theme engine, so the output is plain markup you can open in devtools and restyle with a stylesheet you already wrote. The whole library is 11 kB gzipped, with no dependencies.

It renders on the server without a headless browser, so a chart can land in an email, a PDF, or an RSS reader instead of only inside a React app.

We wrote it after pulling a big charting dependency out of the same internal dashboard three times. Features were never the problem. The problem was that every escape hatch opened onto another abstraction, and changing a tick label meant learning a plugin API. So Kite has no plugin API. Twelve chart types, one function each, and a scales module you can import on its own if you want to draw the marks yourself. When Kite cannot do what you need, it gets out of the way and gives you the coordinates.

Line, bar, area, scatter, histogram, and eight more. MIT licensed. Works in any framework, or none.

Swap out the name, the 11 kB, the twelve chart types, and the dashboard anecdote. If any of those claims isn't true, cut the sentence rather than softening it. The pitch works because the numbers are checkable.
