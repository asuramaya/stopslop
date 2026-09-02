Draft below — 200 words, and it passes the repo's own `slopwatch` ruleset clean. Names, companies, and numbers are placeholders; swap in real, permissioned quotes before this ships.

## From the teams on call

> "We used to grep across twelve boxes at three in the morning. Now I run one query and get the whole request path in front of me. Our median time to find the failing service dropped from about forty minutes to under ten."
>
> — Priya Raghunathan, SRE Lead, Northbound Freight

> "The part I did not expect was the bill. We keep ninety days of logs for less than we paid for thirty, and nobody has asked me to trim retention since."
>
> — Marcus Oyelaran, Platform Engineer, Cadence Health

> "Rollout took two afternoons. The agent shipped with our existing config management, and the parsers picked up our old log format without anyone writing a regex for it."
>
> — Dana Whitmore, Director of Infrastructure, Pellworth Analytics

> "I search during the incident call now instead of after it. That sounds like a small change. It changed how the calls go."
>
> — Tomás Ferreira, Incident Commander, Grayline Media

> "We had one auth service writing forty gigabytes a day of noise. The pattern view found it in an afternoon. That one fix paid for the year."
>
> — Ilse Brandt, Staff Engineer, Verano Payments

Read the full case studies →

Each quote carries a different buying objection — search speed, cost, migration effort, workflow fit, waste — so the section works whether a reader stops at the first one or all five. File is at `/tmp/testimonials.md` if you want it moved into the site tree.
