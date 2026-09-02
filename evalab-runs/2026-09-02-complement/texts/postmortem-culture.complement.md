**Proposal: postmortems stop naming the person**

Right now, the first question after an incident is who did it. We get an answer, the answer goes in the ticket, and the writeup ends there. That format costs us the part we actually need.

The person who understands an outage best is usually the person who caused it. If saying what happened means being the named cause in a document their manager reads, they will write less. Not because they're hiding anything, but because a shorter account is safer than a complete one. So we end up knowing who ran the migration and not knowing that the runbook had two steps in the wrong order, or that the staging database has been diverging from production since spring.

Look at the checkout outage in June. The ticket says a bad config was deployed. It doesn't say the config validator only runs in CI and the hotfix path skips CI. That gap is still there.

What I'm asking for: incident writeups describe the system, and people appear by role rather than by name. Timeline, contributing factors, action items with owners and dates in the normal backlog. Someone outside the affected team runs the review.

This still allows accountability. Repeated carelessness is a management conversation, and it can stay one. It just doesn't belong in the document we're using to fix the pipeline.

I'd like to try it on the next three incidents and compare the writeups to the last three. If they aren't more useful, we drop it.
