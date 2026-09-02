A note first: I don't have a real customer to write about, so this is a composed example. Swap in your own company, product name, and numbers — the structure is what's reusable.

---

**Mirefield Logistics: from Thursday releases to whenever it's ready**

Mirefield Logistics builds freight-matching software for about 4,000 regional carriers. Until last March they released on Thursday afternoons and kept Friday open to clean up whatever Thursday broke.

The holdup was never the code. A merged change waited eleven days on average before it reached customers, most of that queued behind a manual QA sign-off and a release checklist that one engineer, Dana Okonjo, largely kept in their head. When Okonjo took two weeks of leave in February, releases stopped too.

Mirefield started with one service — the carrier notification API, low traffic, cheap to roll back — and put its pipeline on [Platform] in March. The test suite went in first. Then the checklist, one step at a time, until the document was empty and the pipeline did the work. Three more services followed by June; the remaining nine by October.

A year in, Mirefield ships roughly 40 times a week instead of three. Median time from merge to production is 26 minutes. The change failure rate did rise in the first quarter, from 4% to 7%, and the team spent that quarter improving rollback and alerting rather than adding review gates. It now sits at 3%, and the average incident is resolved in 12 minutes instead of two hours.

"We used to plan features around the release calendar," Okonjo says. "Now nobody asks when a thing ships. It ships when it's done, and if it's wrong we find out in an hour instead of a week."
