One quarter of engineering time for debt paydown

We want Q1 engineering capacity, roughly 25% across the platform team, to fix the parts of the codebase that slow every feature we ship.

Three numbers make the case. Our median PR now takes 4.2 days from open to merge, up from 1.8 days a year ago. CI runs 38 minutes, and 1 in 6 runs fails for reasons unrelated to the change. On-call paged 47 times last quarter, and 31 of those pages traced back to the billing service and the legacy sync job.

We propose three workstreams. Split the billing service's shared write path so the two teams touching it stop blocking each other. Replace the sync job's polling loop with the queue we already run for notifications. Cut CI to under 12 minutes by parallelizing the integration suite and deleting the 200 tests nobody has looked at since 2024.

Two roadmap items slip a quarter under this plan. We suggest the reporting redesign and the second SSO provider, both of which have soft customer commitments we can move.

In exchange, we estimate feature work speeds up 20-30% starting Q2, and on-call volume drops by half. We will report progress against PR cycle time and page count every two weeks, and if the numbers do not move by week six, we hand the capacity back.

Marta and I have scoped each workstream to two engineers. We can start the week of January 12 and would like a decision by December 20 so we can plan hiring around it.
