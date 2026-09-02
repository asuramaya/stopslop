**Proposal: dedicate Q4 engineering capacity to paying down technical debt**

We're asking leadership to allocate one quarter — roughly [X] engineer-weeks — to debt reduction rather than new feature work.

The case for doing this now rests on one number. Over the past four quarters, our median time from ticket to deploy has grown from [A] days to [B]. The cause isn't headcount. It's that the [service/module] has accumulated three overlapping data access patterns, a test suite that takes [N] minutes and fails intermittently, and a deploy path with manual steps that only two people know. Every new feature now pays a tax to route around all of this. That tax compounds.

The work itself is concrete. We'd consolidate the data access layer onto one pattern. We'd cut test runtime and fix the flaky cases, so people trust a red build again. We'd automate the remaining manual deploy steps and document the rest. We'd scope this as ordinary tracked work with weekly demos, not an open-ended cleanup.

The cost is roughly [N] features slipping a quarter. We've listed them in the appendix with our read on which are genuinely time-sensitive; two are, and we propose carving those out and shipping them anyway.

We'd measure success three ways. Cycle time back under [A] days. Build failures that reflect real breakage. Onboarding a new engineer to first merged PR in under a week.

The alternative is that we keep paying interest. Our estimate is that another year of this puts the [service] into rewrite territory, which costs far more than a quarter and carries real risk of shipping nothing during it.

Happy to walk through the details.
