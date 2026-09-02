## Design Philosophy

We built this API around a few commitments that shape every endpoint.

Resources are nouns, and the HTTP verbs do the work. `GET /invoices/42` returns an invoice. `DELETE` removes it. You can guess most of the surface after reading three or four endpoints, which is the point.

Every write is idempotent when you supply an idempotency key. Retry a failed request as many times as you need; a duplicate key returns the original response rather than creating a second charge. Network failures are common, and the client should not have to reason about partial state.

Errors carry machine-readable codes alongside human-readable messages. Your handler branches on the code. Your logs show the message. We treat the code list as part of the contract, so codes are added but never repurposed.

We version at the URL root and keep old versions running for eighteen months after a successor ships. Within a version, we add fields and never remove or rename them, so a client that ignores unknown keys keeps working.

Responses stay flat. Where a nested object would save a round trip, we offer an `expand` parameter instead of guessing which shape you want. Defaults favor the small payload.
