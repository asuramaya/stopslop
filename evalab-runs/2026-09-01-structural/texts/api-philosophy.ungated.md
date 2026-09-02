Since no specific API was named, I wrote it as a drop-in section with placeholder-free but generic commitments — swap the deprecation window and error-code details for your real ones. 195 words, and it passes this repo's own `slopwatch` gate:

## Design philosophy

This API is built around a small number of commitments, and most of the odd corners follow from them.

**Explicit over inferred.** The API never guesses what you meant. If a request is ambiguous, it fails with a message naming the ambiguity instead of picking a default that works nine times out of ten and silently corrupts the tenth.

**One way to say a thing.** Where two spellings of the same request were possible, we picked one. That costs you some convenience on your first afternoon and saves you the cost of reading someone else's code for years afterward.

**Errors are part of the interface.** Every failure carries a stable machine-readable code, a human sentence, and, where we can supply one, the field that caused it. Error codes are versioned with the same care as endpoints, because your retry logic depends on them.

**Slow to add, slower to remove.** New surface area is permanent in practice. We would rather ship a narrow endpoint and widen it once we have seen real traffic than ship a general one and live with its shape forever. Deprecations run twelve months, with the replacement available first.

Draft saved at `/tmp/philosophy.md`. Tell me the actual API and I'll make the commitments concrete (real error-code scheme, real versioning policy).
