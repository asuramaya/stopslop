# Design philosophy

This API is built around four commitments.

**Resources, not procedures.** Endpoints map to nouns you can reason about: `/invoices`, `/customers`, `/refunds`. If you need to do something to a thing, that is a verb on the thing, not a new endpoint with a verb in its path.

**Every write is idempotent.** Send an `Idempotency-Key` header on any POST and retry as often as you like. We store the first response for 24 hours and replay it. Network timeouts are not your problem to solve twice.

**Explicit over implicit.** Nothing is inferred from context. We do not guess a currency from your account settings or a timezone from your IP. If a field affects the result, you send it, and the error tells you which one you missed.

**Additive changes only, within a version.** We add fields and optional parameters to a released version. We never remove a field, change a type, or narrow an enum. When we need a breaking change, it goes in a new dated version, and old versions stay live for at least 18 months after the successor ships.

The cost of these rules is verbosity. Our request bodies are longer than they would be with smart defaults, and the version header is required on every call. We think code you can read a year later is worth the extra bytes.
