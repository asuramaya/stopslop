## Design philosophy

This API is built around a small number of nouns and a fixed set of verbs. If you know how to list, read, create, and delete one resource, you know how the rest behave. New capabilities arrive as new resources rather than as new argument shapes on existing endpoints.

Every response is complete on its own. We do not return partial objects that require a second call to interpret, and we do not vary a field's type based on context. A field that is a string is always a string; a field that can be absent is documented as nullable and is always present as `null`.

Errors are part of the interface, not an afterthought. Each failure returns a stable machine-readable `code`, an HTTP status that matches its category, and a human-readable message you are free to log but should never parse.

Backward compatibility is a constraint on our side, not yours. We add fields and enum members without warning, so clients must ignore what they do not recognize. We remove nothing from a published version. Breaking changes go into a new dated version, and old versions stay reachable for at least eighteen months after their successor ships.

Defaults favor correctness over convenience. Pagination is mandatory, writes require an idempotency key, and timestamps are UTC in RFC 3339.
