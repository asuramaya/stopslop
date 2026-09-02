`@northwind/client@2.0.0` went to npm about an hour ago.

Most of the work went into one thing that had been bugging me since last spring. In 1.x, `list()` returned an array and quietly stopped at page one. People hit that constantly. I hit it constantly, on our own dashboard, and burned a whole Thursday in April convinced the API had dropped records. It hadn't. My client had.

So `list()` now returns an async iterator and walks every page. `for await (const order of client.orders.list())` does what you'd expect. Want the old shape? Call `.page()` and you get one page plus a cursor.

That's a breaking change, obviously. Anywhere you wrote `const rows = await client.orders.list()` you now get an iterator back, and `rows.length` is undefined. There's a codemod in `scripts/v2-codemod.ts`. It caught 90-something percent of the call sites in our repo and missed basically everything that assigned the result to a variable first, so read the diff before you commit it.

Retries changed too, less dramatically. 429s honor `Retry-After` now instead of the old fixed 250ms backoff, which was a bad default that I wrote and then defended for two years.

Node 18 is dropped. 20 and up.

The part I'm still unsure about is whether the iterator should buffer ahead. Right now it fetches page N+1 only once you've drained page N, so a slow consumer means a slow crawl. Buffering makes it quicker and makes cancellation messier. Tell me which side you'd rather be on.
