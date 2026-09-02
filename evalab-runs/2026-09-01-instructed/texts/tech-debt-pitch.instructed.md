# Proposal: one quarter of engineering capacity for debt paydown

## What I'm asking for

Q3 engineering time, one quarter of total capacity, dedicated to reducing accumulated technical debt in the billing and ingestion services. Concretely: roughly 2.5 engineer-months per month across the team, tracked as its own workstream rather than absorbed into feature sprints.

## Why now

Three numbers from the last two quarters. Median PR cycle time in the billing service went from 1.8 days to 4.3 days. We shipped 11 rollbacks last quarter, 8 of which touched the ingestion pipeline's retry logic. And onboarding time for the two engineers who joined in April was six weeks to first independent ship, against a three-week target in 2024.

The common cause is that the ingestion path has four overlapping retry mechanisms written between 2022 and 2025, none of which knows about the others. Every feature that touches it has to reason about all four. That is where the cycle time went.

## What the quarter buys

Consolidation of the retry layer into one mechanism, removal of the deprecated v1 billing adapter (still called by 3 internal services, all of which have v2 paths already written), and test coverage on the ingestion path, which currently sits at 34% line coverage.

## The cost of saying no

Feature velocity stays where it is, which we have been treating as the floor. My read is that it keeps degrading, and the retry consolidation gets harder each quarter that another mechanism is added on top.

I'd like thirty minutes to walk through the ingestion analysis before the Q3 planning lock.
