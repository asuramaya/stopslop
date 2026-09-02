Written as an illustrative case study — the company, people, and numbers are invented, since I have no real customer data to draw on. Swap in your own.

## How Meridian Freight lost its Thursday night window

Meridian Freight writes dispatch software for regional trucking fleets. Through 2024 they shipped every second Thursday, in a four-hour window starting at 8 p.m., which was when the load boards went quiet. Two engineers stayed up for it. A rollback meant restoring a snapshot and phoning their three largest customers before those customers phoned support. "The release itself was never the scary part," says Dana Okoro, who runs platform engineering. "The scary part was that we'd stacked eleven weeks of work into one night and then pushed it all at once."

They moved to Corvid Deploy in March 2025.

The tooling turned out to be the easy half. First they had to break one release train into fourteen service pipelines, so that a change to invoicing didn't have to wait on the routing engine. After that, every merge to `main` goes out to a canary holding 5% of traffic. If the error rate climbs above baseline for twenty minutes, it reverts, and nobody has to be awake.

Eighteen months on, Meridian ships around forty times a week, up from twenty-six releases a year. Median time from merge to production fell from nine days to fifty-one minutes. Change failure rate dropped from 22% to 4%, and when something does break, restoring service takes eleven minutes instead of three hours.

Okoro is blunt about the cost. The migration ran seven months, and two of those went to fixing a flaky test suite rather than to the platform.

"You can't deploy forty times a week on tests you don't believe."
