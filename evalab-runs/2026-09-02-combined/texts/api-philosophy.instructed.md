## Design philosophy

This API is boring on purpose. Every endpoint returns the same envelope, errors carry the same four fields, and pagination works identically whether you are listing invoices or audit events. Once you have written one integration against it, you have written all of them.

We prefer explicit over inferred. The API will not guess a currency from your account settings or silently coerce a string into a date. If a field is required, omitting it returns a 400 that names the field and the rule it broke, rather than a default that surprises you three weeks later in production.

Resources are nouns and methods are verbs, with no RPC-style escape hatches bolted on when the model gets awkward. When something genuinely does not fit REST, we say so in the reference and document the exception rather than pretending it is consistent.

Backwards compatibility is a contract, not an aspiration. Adding fields, adding optional parameters, and adding enum values are non-breaking changes you must tolerate; anything else gets a new dated version, and old versions stay live for 24 months after deprecation.

Finally, we optimise for the reader over the writer. Verbose field names, no abbreviations, no cleverness in the JSON. You will read this response body far more often than we will type it.
