# Northwind Freight went from six-week trains to daily releases

Northwind Freight builds dispatch software for about 1,400 regional trucking companies. Until March 2024, its 38 engineers shipped on a six-week release train. Each cut-off meant a two-day code freeze, a manual regression pass, and a Saturday night deploy window that ran until 4 a.m. more often than not.

"We weren't slow because people worked slowly," said Priya Raghunathan, VP of Engineering. "We were slow because merging six weeks of everyone's work took a week to untangle."

The team adopted Helix CD in April 2024 and spent the first quarter on the unglamorous part: splitting the monolith's test suite so it ran in 11 minutes instead of 90, and putting every environment behind the same pipeline definition. Feature flags came next, which let unfinished work merge to main without reaching customers. None of that changed a single line of product code, and Raghunathan says it was the hardest quarter to justify to the rest of the business, because for twelve weeks the release cadence looked exactly the same from outside engineering. What changed underneath was that a deploy stopped being an event someone had to staff.

By September 2024, Northwind was deploying to production 4 to 6 times a day, up from 8 releases a year. Change failure rate went from 22 percent to 6 percent. Median time to restore dropped from just over 5 hours to 24 minutes, mostly because a rollback now reverts one small change instead of six weeks of them. In support, bug fixes that used to wait for the next train reach customers the same week they're reported, and the backlog fell by roughly a third over two quarters.

"The Saturday deploys are gone," Raghunathan said. "That's the part the team mentions, not the metrics."
