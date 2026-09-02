## How we work

We ship to production most weekdays. A change goes out behind a flag, we watch the error rate and the p95 for an hour, and then we widen it. Nobody waits two weeks for a release train.

Code review is required and it is not a rubber stamp. The median review takes under four hours and usually comes back with questions about the approach, not the formatting. A linter handles formatting. Reviewers are expected to say "I don't understand this" out loud, and authors are expected to treat that as a defect in the code rather than in the reader. That norm took a while to hold, and it is the one we defend hardest, because a reviewer who stays quiet to avoid looking slow is worse than no reviewer at all.

On-call rotates weekly across the whole team, including the people who wrote the service. Get paged twice for the same cause and fixing that cause becomes the next sprint's work, ahead of feature commitments. Postmortems name systems and decisions, not people.

Roughly a fifth of each quarter goes to work engineers pick themselves: the migration everyone keeps deferring, the test suite that takes eleven minutes, the internal tool that would save the support team an hour a day. It is scheduled, not squeezed into evenings.

We are remote-first with four core hours of overlap, 10am to 2pm Eastern. Design decisions get written down before they get built, and the document is where the argument happens, so people in other time zones can join it. We hire people who explain their reasoning and change their minds when the evidence moves.
