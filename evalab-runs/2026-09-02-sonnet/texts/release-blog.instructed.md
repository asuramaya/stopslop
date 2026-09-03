Version 2.0 of the client is out today. The rewrite touches the transport layer, the retry logic, and the type generation — the three places that generated most of the support tickets against 1.x.

Requests now share a single connection pool across the client instance instead of opening one per call. On a batch job hitting the same host repeatedly, that cut median latency by 40% in our benchmarks. Retries changed too: 1.x retried on any 5xx with a fixed 1-second delay, which meant a struggling server got hammered by every client at once. 2.0 uses exponential backoff with jitter, and it stops retrying once a request has been running longer than the configured timeout.

The type definitions are generated straight from the OpenAPI spec now, not maintained by hand. In 1.x, the types drifted from the actual API every few releases, and someone would open an issue about a field marked required that the server never actually required. That class of bug is gone, because the types are rebuilt on every spec change as part of the release pipeline.

Breaking changes: the `Client` constructor now takes a config object instead of positional arguments, and `client.request()` returns a `Result` type instead of throwing on 4xx responses. Both changes are mechanical — the migration guide has a find-and-replace for the constructor, and a codemod for the `Result` handling that covers most call sites.

Install it with `npm install api-client@2`. 1.x stays on the `v1` npm tag and gets security patches for six months.
