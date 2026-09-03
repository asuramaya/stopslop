## Design Philosophy

We built this API around one constraint: you should never have to guess what happens next. Every endpoint returns the same shape whether it succeeds or fails, so your error handling doesn't fork into special cases. Every resource has one canonical representation, fetched the same way regardless of where it sits in the hierarchy.

We chose explicit over clever. There's no magic pluralization, no implicit type coercion, no endpoint that behaves differently based on a header you forgot you set. If two things look the same, they work the same. If they work differently, they look different in the URL or the payload, not buried in documentation you have to memorize.

Versioning is a promise, not a suggestion. A field we've shipped stays until we deprecate it with a migration path and a sunset date, not until we decide it's ugly. We'd rather ship an awkward field name than break a contract you built a business on.

None of this makes the API smaller. It makes it predictable. When you're debugging a production issue at 2 a.m., predictable is the only feature that matters. Everything else — naming, pagination, auth — follows from that one priority.
