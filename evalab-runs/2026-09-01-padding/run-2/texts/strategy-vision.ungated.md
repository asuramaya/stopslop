## Vision

Two years from now, shipping a new service here should be boring.

Today it isn't. A team starting something new spends its first six weeks on work that has nothing to do with the product: wiring up auth, copying a half-stale deploy pipeline from a neighboring repo, guessing at the right way to emit metrics, discovering on-call practices by being paged. We have paid that six weeks something like fourteen times in the last year. That is most of an engineer-decade spent re-deriving decisions we already made.

The bet is that we stop paying it. By the end of the second year, a team should be able to go from an empty repo to production traffic in under a day, on paved defaults that already carry logging, tracing, secrets, rollback, and a working on-call rotation. Not because someone wrote a wiki page about how to do it, but because the path of least resistance does it for them.

That means treating the platform as a product with real users — our own engineers — and holding it to the same bar. It has a roadmap. It has SLOs. It can be abandoned for something better if it fails to earn its keep.

We are explicit about the cost. Roughly 15% of engineering capacity moves to platform work, and product roadmaps get slower for the first three quarters. We think that trade pays back sometime in year two and compounds after. If it doesn't, the metrics below will say so, and we'll unwind it.
