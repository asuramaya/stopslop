# Design philosophy

This API is built around one constraint: you cannot see our servers, so every response has to tell you what happened without you having to guess. Three commitments follow from that.

Errors are data, not exceptions. A failed request returns the same envelope shape as a successful one, with a machine-readable `code`, the field that caused the problem, and a plain-language `detail`. You never parse a stack trace or an HTML page. This holds for authentication failures, rate limits, and validation errors alike, so one error handler covers the whole surface and you can write it once. The shape is documented under Errors, and it has not changed since v2.

Endpoints are nouns, and they stay nouns. `/invoices/{id}` returns an invoice. It does not return an invoice plus the customer plus the last twelve payments because some client screen happened to need all three. Composite reads belong to you, through `include=` parameters you control.

Nothing is removed without a year of overlap. A deprecated field keeps returning correct values for at least twelve months, and the `Sunset` header on every response carries the date. We broke this rule once, in 2021, for a security fix; the incident report is linked in the changelog. Deprecations are announced in the changelog before they appear in a header, and the SDKs emit a warning at the same time. If you pin a version, that pin holds until you move it.

The cost of these choices is verbosity. Payloads run larger than they need to be, and simple tasks sometimes take two calls instead of one. We accept that trade because an API that surprises you at 3 a.m. is worse than an API that makes you type more at noon.
