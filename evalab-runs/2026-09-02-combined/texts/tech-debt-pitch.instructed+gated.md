Proposal to allocate 25% of engineering capacity to debt reduction in Q4

I'm asking for one engineer-quarter out of every four — roughly 6 of our 24 engineers' time, or one full sprint per person across the quarter — dedicated to paying down technical debt in the billing and notification services.

The case is in our own numbers. Over the last two quarters, 41% of closed engineering tickets were bug fixes or incident follow-ups, up from 26% the year before. Median time to ship a small billing change is now 9 days, against 3 days for the same class of change in the catalog service. Three of our last five Sev-1 incidents traced back to the same untested payment retry path. Every one of those figures comes from Jira and the incident log; I'm happy to share the queries.

The quarter buys test coverage on the payment retry and webhook paths, removal of the second ORM we've been half-migrating off since 2024, and a split of the notification monolith's scheduling logic into a service the on-call rotation can actually reason about at 3am.

The cost is real. Two roadmap items — the merchant dashboard refresh and SSO for enterprise accounts — slip by about six weeks. I'd rather name that trade now than discover it in December.

I'll report progress against three measures at quarter's end: bug-fix share of closed tickets, median cycle time for billing changes, and Sev-1 count. If those don't move, we stop and try something else rather than asking for the same allocation again.
