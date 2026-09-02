Passes the slopwatch gate clean. One flag up front: you didn't name a customer, so Bridgewell, Okonkwo, and every number below are invented placeholders — swap in real figures before this goes anywhere public.

---

**Bridgewell Logistics: from four releases a year to thirty-eight a week**

Freight software isn't glamorous. Bridgewell Logistics runs the dispatch system behind about 4,000 trucks, and until 2023 every change to it went out in a Saturday-night window four times a year. Rollbacks meant phone calls.

"We had a fix for a routing bug sitting in a branch for eleven weeks," says Dana Okonkwo, who runs platform engineering there. "Nobody could tell me why. It just wasn't Saturday yet."

They moved to the platform in March 2024. The first six months were plumbing: splitting a 90-minute test suite into parallel shards, putting database migrations behind expand-and-contract, and building a staging environment that actually resembled production. Only then did they turn on automatic promotion.

The numbers now: 38 deploys a week, median 22 minutes from merge to production, change-failure rate 4.1%. The Saturday window is gone. Two engineers who used to rotate through it have their weekends back.

What surprised them was where the gain landed. Okonkwo expected features to ship faster. What she got was cheaper experiments. A pricing change that would once have eaten a quarter of planning now ships on a Tuesday and gets reverted on Wednesday if the margin data looks wrong.

"The deploy count is the headline, but it's a proxy," she says. "The real thing is that being wrong got cheap."

Bridgewell still batches database changes by hand, and nobody there is in a hurry to change that.

---

~245 words. The last line is doing deliberate work — a case study that admits one thing the customer still does the old way reads as reported rather than sold. Cut it if your marketing team wants an unbroken win.
