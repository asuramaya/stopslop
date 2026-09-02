# What We Shipped, What Broke, and What We Learned

We closed 312 tickets this year. The number matters less than which ones.

January through March went to the billing rewrite. We inherited a service that computed invoices in three places and agreed with itself about two-thirds of the time. Priya mapped the discrepancies over two weeks, and we deleted two of the three paths. Support tickets about wrong invoice totals dropped from 40 a month to 4.

The June outage cost us six hours. A migration locked a table nobody expected it to lock, and our runbook pointed at a dashboard we had decommissioned in April. Marcus rewrote the incident procedure the following week and we now test the runbook quarterly. It caught a second stale dashboard in October.

We hired four engineers. Onboarding took an average of five weeks before someone shipped to production, down from nine. Most of that came from Dana's work on the local dev setup, which now runs in one command instead of a page of instructions.

Two things we got wrong. We spent five weeks on a caching layer that we turned off in August, because the queries it cached were slow for reasons caching could not fix. And we let the flaky test suite rot until September, when Sam spent three weeks on it and cut CI time by half. We should have paid that down in March.

Next year we want the deploy pipeline under ten minutes and the on-call rotation down to one page a week. Bring your own items to the January planning session.
