PostgreSQL 15 migration

The migration to PostgreSQL 15 is done. Zero incidents, no rollbacks. Query latency dropped 22% on our most-used endpoints, cache hit rates up 8%, and load testing shows we handle peak traffic fine.

New engineers

Sarah and Miguel joined this month. Sarah's got five years of backend experience from payments and is already shipping code on the API team. Miguel came over from analytics and is ramping up on platform. Both are getting their environments set up this week.

Recommendation service update

The recommendation service launch is now October instead of August. We found data consistency issues in the ingestion pipeline during testing that needed a bigger redesign than we planned. We're fixing it before it hits production. The job queue refactor is 40% done and heads to code review next week, and incident response automation is wrapping up. Both ship in September.

Big thanks to the folks who covered on-call while the rest of us were heads-down on the migration.
