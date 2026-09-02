Version 2.0 of the client went up on npm this morning. Two changes will break your code, and one will shrink your bundle.

Every method now returns a promise. The callback signatures from 1.x are gone. We kept a shim in 1.9 for six months, watched installs of it drop under two percent, and then cut it. Responses carry types. If you write TypeScript, `client.users.get()` hands you a `User` object instead of `any`. We generate those types from the same OpenAPI spec that builds the docs, so a server change shows up in your editor the day we ship it.

Retries were on by default in 1.x with a backoff you had no way to configure. Pass a `retry` object to the constructor and you set the attempt count and the backoff curve. You also pick which status codes trigger a retry, so a 429 can behave differently from a 503.

For migration, run `npx api-client-codemod` against your source. It rewrites callback calls into awaits and leaves a `// TODO(v2)` comment anywhere the pattern is too tangled to convert. On our own test app it handled 340 of 361 call sites. The remaining 21 took an afternoon.

We dropped the bundled polyfills, which took the minified size from 41kb to 26kb.

Node 18 is the floor now. If you run 16, stay on 1.9 until you upgrade. The full changelog lists the smaller items, including the pagination helper that Priya contributed in March and the fix for header casing on HTTP/2 that we owe to a bug report from the Datadog team.
