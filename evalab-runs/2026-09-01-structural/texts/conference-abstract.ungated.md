**We Broke Up Our Monolith. Here's What It Cost.**

Three years ago our Rails monolith took 40 minutes to deploy, and one bad migration could take down billing, search, and onboarding at the same time. We decided to split it. This talk is the honest version of what happened next.

I'll walk through the sequence we actually followed: picking the first service by blast radius rather than by domain purity, running the strangler pattern for eighteen months longer than planned, and the six weeks we spent discovering that the database was the real monolith. We'll look at concrete numbers for deploy frequency, on-call pages, and infrastructure spend, before and after.

Some of it worked. Deploys dropped to four minutes and teams stopped queueing behind each other. Some of it didn't. We built two services we later merged back, and we underestimated the cost of distributed tracing by roughly a year of engineering time.

You'll leave with a checklist for deciding whether your monolith is the actual problem, a migration order that doesn't require a feature freeze, and a short list of things we'd do differently. Aimed at engineers and tech leads who have been handed this decision and want more than a vendor slide deck.
