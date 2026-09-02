# Proposal: one quarter of engineering capacity for debt paydown

## What I'm asking for

Q1 2027: the platform team (6 engineers) works on internal systems only. No new customer-facing features from that team for 13 weeks. Product teams continue shipping.

## Why now

Our median PR takes 4.2 days from open to merge. Eighteen months ago it was 1.1 days. The cause is not review latency, which has held steady at 6 hours. It's CI: the main test suite takes 71 minutes and fails spuriously on roughly one run in five, so most PRs get re-run two or three times before they land.

Three things drive that. The test suite shares one Postgres instance across parallel workers, which produces the flakes. The billing module has 340 files with no clear ownership, and any change to it triggers a full-suite run. And we are two majors behind on the ORM, which blocks the connection-pool work that would let us isolate test databases per worker.

Each of these has been on the backlog for a year. Each gets two days of attention when someone is annoyed enough, then gets dropped when a feature deadline arrives. They need a block of time, not slack time.

## What you get back

Target: 20-minute CI, flake rate under 2%, median PR under one day. If we hit that, every product team gets back roughly a day per engineer per week that currently goes to waiting and re-running. Across 34 engineers that pays for the quarter by June.

## What it costs if we don't

The three engineers who have left since March all named CI in their exit conversations. I can't promise the next three won't.
