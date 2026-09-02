# 2025 in Review: Platform Engineering

We spent most of this year on the parts of the system nobody demos.

The January migration off the shared Postgres instance took eleven weeks instead of the six we budgeted. The overrun came from foreign keys we didn't know existed, discovered one at a time. We now run per-service databases, and the on-call pages that used to cascade across four teams stay in one.

Build times went from 14 minutes to 3:40 after Priya rewrote the CI cache layer in March. That change alone gave the team back roughly 90 engineer-hours a month, which is the single largest thing we shipped by that measure.

We killed three services. The notification relay, the old image resizer, and the internal feature-flag proxy all had replacements running alongside them for more than a year. Deleting them removed 41,000 lines and two recurring alerts.

What didn't go well: the search reindex project. We scoped it in April, staffed it in June, and shelved it in September when the vendor changed their pricing model. We had 40 percent of the work done and no path to finishing it. The lesson we're taking into next year is to check contract terms before writing code against a third party, not after.

Incident count dropped from 31 to 19 year over year. Median time to resolution stayed flat at 47 minutes, which we'd like to move.

Next year's first project is the auth service rewrite. Design doc goes out January 8.
