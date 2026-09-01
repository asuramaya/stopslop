**The Second Year Is the Hard One: What We Learned Breaking Up a Rails Monolith**

We split our monolith into 14 services. Eighteen months later we merged four of them back.

This talk is about what the migration diagrams leave out. The first extraction always goes fine — you pick a bounded context with clean edges, stand it up, cut traffic over, and everyone claps. Then you reach the parts of the codebase nobody understands: the joins that cross five tables, the billing flow that touches everything. That's where the schedule dies.

I'll walk through three decisions we got wrong. We extracted along team boundaries instead of data ownership. We kept a shared database "temporarily" for eleven months. We filed distributed tracing under phase two. Each cost us roughly a quarter. I'll also cover the two calls that paid off: keeping the strangler-fig proxy far longer than planned, and refusing to ship any service without a named on-call owner.

You'll leave with a way to sequence extractions by how tangled the data is rather than by how eager the team is, plus the specific metrics we watched to decide when to stop splitting.

For engineers and tech leads weighing the move, or already stuck halfway through it.

---

~205 words. The numbers (14 services, eleven months, four merged back) are placeholders — swap in your real ones, since the concreteness is what makes this land with a program committee.
