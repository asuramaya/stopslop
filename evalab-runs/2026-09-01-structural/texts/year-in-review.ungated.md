Your repo only has a month of history, so I wrote this as a swappable draft — bracketed slots are yours to fill.

---

## The year we finally said no

Twelve months ago we had [14] active projects and no honest way to rank them. We killed [six]. That turned out to be the year's real work; everything below is downstream of it.

**The migration.** [Postgres 14 → 16] took nine weeks, not the four we scoped. Three undocumented consumers were still reading the old schema. We found them the way you always find them — by breaking them, on a Tuesday, at [11:40am]. Postmortem is [here].

**Latency.** p99 on [checkout] went from [1.9s to 340ms]. Most of that was one N+1 query that had been there since [2023]. No architecture was harmed.

**On-call.** Pages dropped [62%]. Half the win came from deleting alerts that nobody had acted on in a year. Deleting an alert felt reckless every single time. It wasn't.

**What went badly.** [Project Atlas] shipped four months late and we still don't have a clean story for why. The honest version: three people said in [March] that the estimate was wrong, and no one wrote it down anywhere that mattered. We've changed how estimates get recorded. Ask [name] if you want the details.

Some numbers, without commentary: [1,204] PRs merged, [11] incidents, [2] of them customer-visible, [4] new engineers, [0] departures.

Next year we want fewer projects, earlier. If you're carrying something you think should be on the kill list, bring it to [planning on Jan 12].
