# Halcyon 2.0

Halcyon 2.0 is out on npm today. If you have been running 1.x since 2023, three things changed, and one of them will break your build.

Start with the breaking one. `client.request()` now returns a typed result object instead of throwing on non-2xx responses. Errors carry the status, the parsed body, and the request ID, so you stop reaching into `err.response.data` and hoping it parsed. Every call site that wraps a request in try/catch needs a look. The codemod in `@halcyon/migrate` handles the mechanical part.

Retries are built in now. 1.x left this to you, which meant most people either skipped it or wrote the same buggy exponential backoff. The default policy retries idempotent methods on 429 and 5xx, respects `Retry-After`, and caps at three attempts. You can replace the whole policy with a function if your API does something stranger.

The third change is the browser bundle, which dropped from 41 kB to 12 kB gzipped. We removed the bundled polyfills and now target native `fetch`. Node 16 is no longer supported for that reason.

Everything else stayed put. Same constructor, same auth helpers, same middleware hooks.

Migration takes about twenty minutes on a mid-size codebase, most of it spent on error handling. The [migration guide](https://example.com/halcyon/v2) walks through the codemod and the manual cases it can't reach.

1.x gets security patches through March 2027. After that it's frozen.

`npm install halcyon@2`
