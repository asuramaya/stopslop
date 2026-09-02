# Breaking up the monolith: what the migration diagrams leave out

Three years ago our billing platform was 400,000 lines of Rails in one deployable unit. Today it's fourteen services. The arrow between those two sentences hides most of the work, and that's what this talk is about.

I'll walk through the decomposition in the order we actually did it, including the two services we merged back after eight months because the boundary was wrong. We'll look at how we picked the first seam (not the one the domain model suggested), what happened to our test suite when in-process calls became network calls, and the six weeks we spent on distributed tracing before anyone could debug an incident again.

There's a section on the costs nobody budgets: on-call rotation redesign, the schema migration that had to run against four databases at once, and the latency we added to checkout before we clawed it back.

The talk assumes you've read the standard advice and want to know how it survives contact with a real codebase and a real deadline. You'll leave with a checklist for deciding whether a given seam is ready to cut, and a clearer sense of when the answer is that your monolith is fine.
