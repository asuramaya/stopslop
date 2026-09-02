## Design philosophy

Every response has the same shape, and every error carries the same three fields: a stable machine code, a message for humans, and the field path that caused it. Write one error handler on day one and never revisit it.

We prefer explicit over inferred. An unknown field is a 400.

The API will not guess your timezone, coerce a string into a number, or quietly ignore a key it does not recognise. That strictness costs you a few minutes during integration, and it spares you the class of bug that only surfaces in production, three weeks later, on someone else's data. Resources are nouns and the verbs belong to HTTP, so there are no `/performAction` endpoints, no `POST` that reads and no `GET` that writes. If you can guess the URL from the resource name, you guessed right.

Nothing that works today stops working tomorrow. Versions are dated, old versions stay live, and additive changes ship without a version bump. We will add fields to responses; we will not remove or retype them.

Pagination is cursor-based on every list endpoint, including the ones you expect to stay small. Offsets drift under concurrent writes. Cursors do not.
