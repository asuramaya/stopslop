## Design philosophy

We built this API for developers who have already read too many bad ones. Three commitments shape it.

**Predictable beats clever.** Resources live at plain URLs. Verbs mean what HTTP says they mean. Every list endpoint paginates the same way, every timestamp is RFC 3339 in UTC, and every identifier is an opaque string you should never parse. Once you have learned one endpoint, you have mostly learned the rest, and you can guess the shape of a call before you look it up.

**Errors carry their own instructions.** A failure response tells you which field was wrong, what we expected there, and whether retrying will help. We would rather return a longer error body than send you to a support forum. Rate limits arrive as headers on every response, not as a surprise at the moment you exceed them.

**Your integration keeps working.** We add fields; we don't remove or repurpose them. Breaking changes get a new version, a migration guide, and twelve months of overlap with the old one. Deprecations show up in response headers long before they show up in an outage.

Where these principles conflict, we favor the one that costs you the least at 3 a.m.
