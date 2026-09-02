# Fetchwright 2.0

Fetchwright 2.0 is on npm today. The retry logic is no longer a lie, TypeScript types come from your OpenAPI spec, and the callback API is gone.

1.x retried on any thrown error, which meant it happily replayed non-idempotent POSTs after a timeout. 2.0 retries idempotent methods only, honors `Retry-After`, and backs off with jitter. If you want the old behavior, pass `retry: { methods: 'all' }` and accept the consequences. Point `fetchwright generate` at an OpenAPI 3.1 document and you get a typed client: paths, params, request bodies, response unions per status code. No more casting `unknown`. Every method now returns a promise, and `AbortSignal` replaces the old `cancel()` handle. That last one is the break that will cost you the most time, so there is a codemod: `npx fetchwright-codemod v2`.

The bundle shrank from 41 kB to 12 kB minified, mostly by dropping the bundled polyfills. Node 18 and any browser from the last three years already have what we were shipping.

We did not rename the package. 1.x keeps getting security patches through March 2027.

The migration guide walks through each break with before and after. Most projects we tested took under an hour. The codemod handled the callback conversion everywhere except where someone was threading a callback through two layers of their own abstraction.

Bug reports welcome on GitHub.
