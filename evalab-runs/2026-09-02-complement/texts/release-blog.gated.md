You didn't give me a library or specifics, so I invented a plausible one (Fetchkit, a TypeScript HTTP client) — swap the name and details for yours. 249 words, passes the slopwatch gate clean.

# Fetchkit 2.0

Fetchkit 2.0 is on npm today. It is a rewrite of the request layer, and it breaks things on purpose.

The largest change is that retries, timeouts and backoff belong to the client now. You set the policy once when you construct the client, and every call inherits it. In 1.x most people wrapped calls in their own retry loops, and a good share of those loops retried on 400s or hammered a failing server with a fixed 100ms delay. That code can go.

The second change is generated types. Point `fetchkit generate` at your OpenAPI document and you get a client where each endpoint's response shape is known at compile time. Casting away from `unknown` was the most common complaint we got on the 1.x issue tracker, and it should now be unnecessary.

Three things break. `client.request()` no longer accepts a callback, so pass a promise handler instead. Errors are a single `FetchkitError` class with a `status` field, rather than the four classes 1.x threw. And the default timeout dropped from 60 seconds to 10, which will surface hangs you did not know you had.

Node 18 is the minimum. We dropped the polyfill for global fetch along with it, which took about 40KB out of the install.

The migration guide walks through the three breaks with before and after code, and a codemod handles the callback change for you. If you hit something the guide misses, open an issue and we will add it.

Draft is at `/tmp/post.md`. Tell me the real name, the actual breaking changes, and the version floor, and I'll rewrite it against those.
