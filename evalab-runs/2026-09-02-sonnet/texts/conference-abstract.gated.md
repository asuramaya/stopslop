Monolith to Microservices, What Actually Broke

Two years ago our team split a ten-year-old Rails monolith into fourteen services. This talk skips the architecture diagrams and gets into what the migration guides leave out.

We cover the decision to migrate at all — the business pressure that justified it, and the parts of the codebase we deliberately left alone because splitting them wasn't worth the risk. We used the strangler fig pattern to peel off services one at a time, kept the monolith and new services talking to each other without a distributed transaction nightmare, and ran a data migration that took three times longer than we estimated.

The middle section covers the failures. A service boundary we drew in the wrong place and had to redraw six months later. An on-call rotation that got worse before it got better. Latency we didn't notice until customers did.

You leave with a concrete checklist for deciding whether your team needs microservices at all, a way to estimate migration timelines that accounts for the parts nobody plans for, and a clearer sense of the operational cost you're signing up for — not just the code.

Aimed at engineers and tech leads considering or mid-way through a similar migration.
