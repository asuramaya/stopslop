# Engineering culture

We ship small changes often. Most pull requests here are under 300 lines, and the median time from first commit to production is under two days. That pace is deliberate: small changes are easier to review honestly and easier to undo when we get them wrong.

Code review is mandatory and it is not a rubber stamp. Reviewers are expected to ask why a thing exists, not only whether it compiles. We keep the tone direct. Disagreeing with a design in writing is normal, and the author decides after hearing the argument — we do not escalate to a manager to settle technical questions.

Every engineer carries a pager for one week out of every six or seven, depending on team size. If you build it, you answer for it at 3am. In practice this shapes design more than any style guide does. Nobody adds a background job with no alerting when they know whose phone it wakes.

We write things down. Design docs before large projects, incident reviews after outages, and a decision log that explains why we chose Postgres over the alternative someone will inevitably propose again in eighteen months. The reviews are blameless in the specific sense that we ask what made the mistake easy to make.

About a fifth of our engineering time goes to work no customer asked for: dependency upgrades, test flakiness, deleting dead code paths. It is on the roadmap with everything else, not squeezed into gaps.

We are remote-first across eight time zones, which means most decisions happen in text and meetings are the exception. Expect fewer interruptions and more reading.
