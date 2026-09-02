# Nomination: platform delivery team

I'm nominating the platform delivery team for their work on our release pipeline this year.

In January, shipping a service to production took a four-hour window, two engineers on a bridge call, and a hand-written rollback plan that nobody had tested. We deployed on Tuesdays because Tuesday was the day someone had time to babysit it. Everyone knew this was bad. This team is the one that fixed it.

They rebuilt the pipeline around progressive rollout: every deploy goes to 5% of traffic, sits behind automated health checks for ten minutes, then proceeds or reverts on its own. Median deploy time is now eleven minutes. We went from 40 releases a quarter to just over 300, and change-failure rate dropped from 14% to 3%.

What I want to highlight is how they did it. They migrated 60-odd services one at a time, sitting with each owning team through their first three deploys instead of publishing a wiki page and declaring victory. That is slow, unglamorous work, and it is why adoption stuck.

The team is Priya Raghunathan, Tom Bierce, Anneke Vos, and Marcus Oyelaran. They deserve the award.
