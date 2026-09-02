# 2025 in review: platform engineering

We spent most of this year paying down the migration we started in 2024, and it took longer than the plan said it would. The old billing service came off the monolith in March, four months later than the original date. The delay was mostly ours: we underestimated how many internal callers were reaching into billing tables directly. There were 47 of them. We found the last one in production traffic logs two weeks after we thought we were done.

What went well: incident count dropped from 31 to 12 year over year, and the median time to first responder went from 14 minutes to under 4. Most of that came from a boring change, which was giving every alert an owning team and deleting the ones nobody would claim. We deleted about a third.

The deploy pipeline is faster. Median CI run went from 22 minutes to 9 after we split the test suite and stopped running browser tests on every commit. Some of you have told us the flaky-test problem is still bad, and you're right. We know about roughly 60 tests that fail more than 1% of the time, and we have not fixed them.

Next year we want to finish the read-path migration for the search index, get on-call rotations down to one week in six across all four teams, and do something real about the flakes. Alex is writing up the flaky-test plan and will share it in January.

Thanks for a hard year. The billing cutover weekend, in particular, was a lot of unglamorous work by people who did not have to volunteer for it.
