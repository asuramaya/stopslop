**Nomination: [Team name]**

Eighteen months ago a release took most of a day. Someone owned the checklist, someone else watched the graphs, and if anything went wrong the rollback was a manual sequence nobody wanted to run at 11pm. Deploys got batched because they were expensive, and batching made each one riskier. That was the baseline everybody had stopped questioning.

[Team] took it apart. They rewrote the pipeline so builds are reproducible, pulled environment config out of the deploy scripts, and added canary steps with a rollback that works and gets tested. None of it was glamorous. Most of it was reading old bash and asking why. Median deploy time went from [X hours] to [Y minutes], and we ship [N] times a week now instead of [M]. Change-failure rate dropped [Z%], which matters to me more than the frequency does.

What I'd point to beyond the metrics is the effect on everyone else. Teams that used to avoid Fridays deploy on Fridays. New engineers ship in their first week. [Team] fixed something the rest of us had quietly learned to live with, and they did it without asking anyone else to change how they work.
