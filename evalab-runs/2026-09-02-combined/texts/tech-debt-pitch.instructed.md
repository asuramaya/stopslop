# Proposal: one quarter of engineering capacity for debt paydown

## What I'm asking for

25% of engineering time for Q4 — roughly one engineer-quarter per team of four, drawn as a standing allocation rather than a freeze.

## Why now

Three numbers explain the request better than any argument I can make.

Our median PR now takes 4.2 days from open to merge, up from 1.8 days a year ago. CI runs 41 minutes, and 30% of runs fail on flakes rather than real defects, so most engineers push, context-switch, come back, and retry. In the last two quarters we shipped 11 incidents traced to the same three subsystems: the billing reconciler, the auth session store, and the notification fan-out. Those three carry 60% of our on-call pages and none of them have owners on the current org chart.

The cost is already being paid. It is being paid in slipped dates and in the two engineers who cited on-call load in their exit conversations. The choice is whether we pay it deliberately.

## What the quarter buys

Rewrite the billing reconciler against the schema we actually use, not the 2023 one. Cut CI to under 12 minutes by splitting the integration suite and killing the shared test database. Retire the notification fan-out in favor of the queue we already run for exports.

## How we'll know it worked

Median PR time back under two days. CI flake rate under 5%. Pages from those three subsystems down by half. I'll report these monthly, and if the numbers haven't moved by the end of month two, we stop and reassess rather than defending the plan.

## What we give up

Two roadmap items slip a quarter. I'd propose the partner API and the admin redesign, both of which have soft external commitments. I want that trade discussed openly rather than absorbed silently.
