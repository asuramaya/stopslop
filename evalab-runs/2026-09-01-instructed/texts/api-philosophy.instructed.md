# Design philosophy

This API is built around a small number of nouns and the ordinary HTTP verbs that act on them. If you know what a resource is called, you can guess its URL, and if you can read one endpoint's response you can read all of them.

We optimize for predictability over convenience. There is no batch endpoint that behaves subtly differently from the single-item version, and no query parameter that changes the shape of the response body. When two designs conflict, we pick the one that produces fewer special cases in your code, even when that means one extra round trip.

Errors are part of the contract. Every failure returns the same envelope: a stable machine-readable `code`, a human-readable `message`, and a `details` object whose keys depend on the code. New codes get added; existing ones keep their meaning.

Compatibility is dated, not versioned by a number in the path. You pin an API date when you integrate, and that behavior stays fixed for you until you change the pin. Breaking changes ship as new dates with a migration note. Additive changes — new fields, new enum values, new endpoints — land inside your existing pin, so write clients that ignore fields they do not recognize.
