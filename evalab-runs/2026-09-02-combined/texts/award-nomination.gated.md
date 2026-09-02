**Nomination: [Team Name] — Engineering Excellence Award**

A year ago, shipping to production meant a two-hour window on Thursday night, a checklist nobody fully trusted, and at least one person staying late to watch it go out. Rollback was a phone tree.

[Team Name] fixed that without asking anyone to stop shipping. They replaced the hand-run checklist with a pipeline that builds once and promotes the same artifact through staging and prod, so what we test is what we run. They added health-gated rollout, so a bad deploy halts itself instead of waiting for someone to notice. They wrote the rollback path first and exercised it in a game day before anyone depended on it.

Deploys went from weekly to about [40] a week.

Median time from merge to production fell from [three days] to [under an hour]. Change failure rate dropped, and mean time to recover is now [11 minutes], most of it automated. What I want to call out, though, is how they did it. They moved services over one at a time, sat with each owning team, and absorbed the migration work themselves instead of filing tickets. Nobody issued a mandate. People switched because the new path was easier.

Swap in the team name and your real metrics — the bracketed figures are placeholders.
