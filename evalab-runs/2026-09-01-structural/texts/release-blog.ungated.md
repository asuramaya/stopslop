You didn't name the library, so I picked a placeholder (`fetchkit`) and invented concrete details — swap the numbers and names for your real ones.

---

## fetchkit 2.0

The 1.x retry logic was a lie. It said "exponential backoff," and it did back off, but every client in your fleet backed off on the same schedule — so they all came back at once and knocked the API over a second time. That bug is why 2.0 exists.

**What changed:**

Retries are now jittered by default (full jitter, per the AWS architecture blog's version), and `Retry-After` headers are honored instead of ignored. If you liked the old behavior, `retry: { jitter: false }` gets it back.

Requests are cancellable. Every call accepts an `AbortSignal`, and `client.close()` drains in-flight work rather than dropping it on the floor.

We dropped the bundled HTTP layer. 1.x shipped its own transport, which meant we were maintaining a worse copy of `undici`. 2.0 uses whatever `fetch` your runtime provides — Node 20+, Bun, Deno, Cloudflare Workers. Install size went from 4.1 MB to 96 KB.

Types are generated from your OpenAPI spec now, not hand-written. `npx fetchkit codegen ./openapi.yaml` and your response bodies stop being `any`.

**Breaking changes:** four of them. `client.request()` returns a `Response`-shaped object instead of the parsed body; the `timeout` option moved to `signal`; Node 18 is out; the `plugins` array is now a `use()` call.

The [migration guide](/docs/migrate-2) covers each one with a before/after. A codemod handles the first three. Budget an afternoon for a mid-sized codebase.

`npm i fetchkit@2`
