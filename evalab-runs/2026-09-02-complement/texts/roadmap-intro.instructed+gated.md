# Roadmap

We publish this roadmap because the alternative is a support queue where people ask what we're building and we answer one at a time. Here is what the next three quarters look like from inside the team.

Two things drive the order of work. The first is what breaks. Our build cache invalidates too eagerly on monorepos above roughly 400 packages, and that shows up in more support tickets than every feature request combined, so cache correctness comes before anything new. The second is what people have asked for repeatedly and we've deferred: a real local debugging story for remote runners, and permissions that can be scoped below the org level.

Dates here are quarters, not days. A quarter means we expect to ship inside those three months; it does not mean we've committed to a release date. Items sometimes move backward, and when they do we say so in the changelog rather than quietly editing this page.

What's absent matters too. There is no plan for a hosted CI product, no plugin marketplace, and no GUI for the config file. Those get asked about often enough that leaving them off is itself information.

Each item links to its tracking issue. Comment there — that thread is where the maintainer working on it will read.
