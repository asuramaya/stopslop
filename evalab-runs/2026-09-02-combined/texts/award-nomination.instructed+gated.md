I nominate the Platform Delivery team for the deployment overhaul shipped this spring.

Before their work, releasing a service meant a two-hour window, a shared checklist in a wiki page nobody trusted, and at least one engineer awake at an hour they had not agreed to. Rollbacks were manual and took roughly forty minutes, which meant people delayed shipping until Thursday and then delayed again until Monday.

The team rebuilt the pipeline around a single deploy command with automatic health gating. Median time from merge to production went from 96 minutes to 11. Rollback is now one command and completes in under 90 seconds, which we have exercised four times in real incidents. Deploys per week across all services rose from 14 to 61, and the change failure rate dropped from 9% to 4%.

What I want to highlight is how they did it. They spent the first three weeks interviewing the teams who would be affected rather than writing code, and the migration path they designed let each service move on its own schedule. No team was forced into a cutover date. That patience is why adoption reached every service without a mandate from leadership.

I recommend this team for the engineering excellence award.
