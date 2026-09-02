**Meridian Freight Systems cut release lead time from six weeks to a day**

Meridian Freight Systems runs the dispatch and billing software behind about 4,000 trucks across the Midwest. Until early 2024, the engineering team shipped on a six-week cycle. Every release meant a Saturday night maintenance window, a rollback plan printed and taped to the wall, and two engineers on call who had spent the previous Thursday reconciling merge conflicts across eleven long-lived branches.

"We weren't afraid of writing code," said Priya Raghunathan, who leads platform engineering. "We were afraid of the Saturday."

Meridian adopted Harbor CD in March 2024 and spent the first quarter on plumbing rather than on features: container builds for the four services that still deployed from a shared VM, a test suite that ran in under nine minutes, and blue-green routing at the load balancer so a bad release could be reversed by flipping traffic instead of restoring a database.

The numbers a year in:

- 214 production deploys in the first six months, against 9 in the six months prior
- Median lead time from merge to production of 41 minutes
- Change failure rate of 4.1 percent, down from 22 percent
- Zero scheduled maintenance windows since June 2024

The billing team saw the sharpest change. A pricing correction that once waited for the next window now goes out the same afternoon a dispatcher reports it, which removed a recurring source of customer credits.

Meridian is now moving its EDI integration layer onto the same pipeline. That work is slower, since partner carriers test against fixed endpoints, and the team expects it to run through mid-2026.
