## Design Philosophy

We built this API around a simple idea: you should never have to guess what a call does.

Every endpoint does one thing, names it plainly, and returns a response that matches the request's shape. If you can predict the URL, you can probably predict the payload too. We chose REST over more elaborate alternatives because most integrations need one, in most cases, and this keeps that case fast. Resources map to nouns, methods map to verbs, and status codes carry real information — a 409 means something specific happened, not "an error occurred."

Versioning lives in the URL, not in headers you have to remember to set. Breaking changes get a new version; everything else ships in place. We add fields instead of restructuring existing ones, and we document every deprecation with a removal date, not a vague warning. Errors return a machine-readable code and a human-readable message in the same body, so you can branch on one and log the other without parsing prose.

None of this is unusual, and an API you already understand is one you can build on without re-reading the docs every time.
