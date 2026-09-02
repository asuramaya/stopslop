# Paying down debt in billing and notifications

## The ask

We want twenty-five percent of engineering capacity in Q4, roughly one engineer-week per person per month, dedicated to the billing and notification services.

## What we would fix

Three things, in priority order. The billing service has no integration test suite. Every change there gets manually verified against staging, which costs us about four hours per release and still let two production incidents through in August. We want to build the test harness and backfill coverage on the payment paths. The notification service still runs on a queue library we stopped supporting in 2024, with no maintainer upstream and no security patches since March. Migrating it to the queue we use everywhere else removes a dependency we cannot patch.

Third, our deploy pipeline runs 41 minutes, and about 28 of those are a serialized test stage that can be parallelized. Cutting the pipeline to roughly 15 minutes gives every engineer back real time on every deploy.

## What it costs

A quarter of capacity means roughly two fewer medium features shipped in Q4. We have discussed which two with product: the reporting export, and the second phase of the admin redesign. Both can move to Q1 without contractual exposure.

## What we get back

Faster release cycles on billing. One fewer unsupported dependency. A deploy loop that stops eating an hour of engineering attention a day.

We will report progress at the existing biweekly engineering review, with the three items tracked separately so you can see whether the investment landed.
