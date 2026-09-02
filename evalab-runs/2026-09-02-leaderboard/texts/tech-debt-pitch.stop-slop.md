# Proposal: One Quarter of Engineering Time for Debt Paydown

**To:** Leadership
**From:** Platform Engineering

I am asking for one quarter of engineering time, roughly 25% of the team's capacity across Q4, to pay down debt in the billing and provisioning services.

Three numbers make the case. Our median PR now sits eight days in review, up from two days last year, because five engineers understand the billing service and four of them are on other teams. We shipped 31 hotfixes to provisioning in the last six months; 19 of them touched the same four files. Onboarding a new backend engineer takes seven weeks before their first production change, and two of those weeks go to reading undocumented retry logic.

The work splits into two tracks. First, we replace the hand-rolled retry and idempotency layer in provisioning with a single library and delete the four duplicate implementations. Second, we cut the billing service's 40-minute test suite to under ten minutes by removing shared database fixtures, which lets engineers run it before pushing instead of after.

We will keep shipping product during this quarter. The 25% comes off feature velocity, and I expect Q4 roadmap items to slip by two to three weeks. I would rather absorb that now than in Q1, when the migration to the new pricing model lands on top of the same code.

I will report progress against the three numbers above every two weeks. If we do not move the review time and the test suite runtime by mid-quarter, cut the effort and reassign the team.
