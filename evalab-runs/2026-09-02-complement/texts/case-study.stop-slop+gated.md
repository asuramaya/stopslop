Meridian Freight sells load-matching software to 4,000 trucking companies across the Midwest. Until March 2024, its 40 engineers shipped to production once every three weeks. Each release cost a Saturday. Two platform engineers sat in a conference room, ran migrations by hand, watched dashboards until Sunday morning, and rolled back about one release in five.

Karen Osei, who runs platform engineering, tried to fix the release process twice with internal tooling and abandoned both attempts. In April her team bought Harbor, a continuous delivery platform, and spent six weeks moving 130 services onto it.

Osei's engineers wrote their pipelines as code and put every service behind a feature flag. A developer now pushes a branch, waits for a canary to take 5 percent of traffic for ten minutes, and promotes the build without asking anyone. When error rates climb past the threshold Harbor sends the traffic back to the previous version in under a minute, and the developer reads the diff on Monday instead of paging Osei at 2 a.m.

Meridian went from 17 production deploys a quarter to 14 a day. Lead time from merge to production fell from 19 days to under four hours. Failed changes dropped from 20 percent to 3 percent, and median recovery time went from six hours to 11 minutes.

"I stopped scheduling my weekends around our release calendar," Osei said. "So did the 12 people who used to be on that rotation."

Meridian still batches its schema migrations into a Tuesday window. Osei plans to tackle that next year.
