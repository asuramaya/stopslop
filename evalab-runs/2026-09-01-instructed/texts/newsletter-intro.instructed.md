# The interest payments came due

Last quarter we shipped the checkout rewrite three weeks late. The postmortem blamed scope, but the honest cause was older: a payments module that four people had patched around and nobody had read end to end since 2023. Every new feature there cost roughly twice what the estimate said, and we kept estimating as if it didn't.

So this month we're writing about technical debt, with less abstraction than usual. Priya walks through the auth service migration and what it actually cost to unwind six years of conditional logic — including the two weeks she spent just building a test harness before she could safely change anything. Marcus makes the case that some of our debt is fine and we should stop apologizing for it, using the internal admin tools as his example.

We also pulled numbers. Across the four services we track build health on, time-to-first-commit for a new engineer ranges from two days to five weeks. That spread is not about the engineers.

None of this resolves into a policy. We are not announcing a debt sprint or a rewrite. The goal is narrower: get better at naming which debt is charging us interest and which is sitting quietly, and stop treating those as the same problem.
