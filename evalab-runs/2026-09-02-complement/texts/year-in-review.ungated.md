Here's a draft. I don't know your team's actual year, so the specifics below are invented — swap them for your real numbers before you post; the shape should hold.

---

**A year of doing less, on purpose**

We started January with 41 open services and a habit of adding one every time somebody asked a question we couldn't answer. We're ending with 29.

That's the year, honestly. The rest is detail.

The migration off the legacy job runner took seven months instead of the three we scoped, which is roughly what everybody privately expected and nobody said out loud in planning. Worth writing down: the slip wasn't the runner. It was the 60-odd cron entries nobody owned, each of which turned into a small archaeology project. Kira's spreadsheet of "who last touched this" saved us weeks.

p99 checkout latency went from 840 ms to 310 ms. Most of that came from one change — caching the entitlement lookup — which took an afternoon and sat in someone's backlog for eleven months. There's a lesson in that and I don't love it.

We shipped the new onboarding flow, killed the old one, and resisted three separate requests to keep the old one around "just for enterprise." Deleting it felt better than shipping it.

Two people joined, one left, and we finally wrote down how we do on-call instead of explaining it verbally to each new hire.

Next year: the search index, the last four services on the old runner, and fewer meetings about meetings.

Thanks for a good one.

---

Around 250 words. If you send me the real numbers, incidents, and names, I'll rewrite it against them.
