No specific API was named, so I've written it against a generic REST API with placeholder specifics (the `GET /orders/{id}` example, the twelve-month deprecation window) for you to swap out.

## Design philosophy

We made three promises before writing the first endpoint, and we check every new one against them.

Predictable over clever. Resources are nouns, verbs are HTTP methods, and errors come back in one shape no matter which route produced them. If you can guess what `GET /orders/{id}` returns without opening the reference, we did our job. We would rather ship a narrow endpoint that behaves the same at 3 a.m. as it does in a demo than a flexible one you have to test before you can trust it.

Explicit over implicit. Nothing is inferred from your account settings, your locale, or the order you sent fields in. Defaults exist, but they are written down and they never change quietly. Pagination is always requested, never assumed.

Additive change only. Fields get added; they do not get removed or repurposed under the same name. When a breaking change is unavoidable, it ships as a new dated version, and the old one keeps working for twelve months after we announce its retirement.

The cost is real. Some workflows take two calls where one would do, and some responses carry fields you will never read. We think that trade is worth it: an API you have to re-learn is worse than one that's a little verbose.
