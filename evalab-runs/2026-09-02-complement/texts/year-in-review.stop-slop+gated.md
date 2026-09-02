# 2025 in Review

We shipped the payments migration in March, three weeks past the date we gave in January. A Stripe webhook ordering bug caused the delay. Priya found it on a Tuesday night while she replayed production traffic against staging, then spent two days writing the idempotency layer we should have written in the first place. Nobody has paged us about payments since June.

The on-call rotation changed twice. The first version, four people on a weekly cycle, burned Marcus out by April. We moved to eight people on a two-week cycle and split the pager between platform and product alerts. Median alerts per shift dropped from 31 to 9. Most of that came from deleting alerts nobody acted on. We fixed four of them.

We started the search rewrite in July and stopped in September.

Deng measured the actual query mix instead of the one we assumed, and the Elasticsearch cluster we wanted to replace cost less than the Postgres full-text version we prototyped. We wrote up what we learned and moved the two engineers to the billing backlog.

Two people joined. Ana came from the data team in February and rewrote the ingestion pipeline that had been failing every third Sunday. Tomas started in August and has been fixing the flaky tests nobody else wanted to touch, which beats what most of us managed in our first quarter. Both of them ask better questions in code review than we were asking a year ago, and the review queue has been shorter since Ana started closing hers on the same day.

Next year we want the deploy pipeline under ten minutes. It sits at 34 today.
