A note first: you didn't name a company, so this is a composite — the numbers are illustrative, not from a real account. Swap in real ones before it goes anywhere public.

---

**Halversen Freight: from six-week releases to twelve deploys a day**

For most of 2023, Halversen shipped software the way it moved pallets — in bulk, on a schedule, with a lot of paperwork. Releases went out every six weeks. Each one took two engineers a full Thursday night, and about one in four had to be rolled back by Monday.

"We weren't slow because people were slow," says Priya Raghunathan, who runs platform engineering there. "We were slow because every release carried six weeks of unrelated changes. When something broke, you had forty commits to blame."

They moved to Fernway in March 2024. The migration itself was unglamorous: eleven weeks, mostly spent untangling a build script that nobody had touched since 2019.

What changed was batch size. Merges now go to production behind a feature flag within about nine minutes. Halversen went from 8.7 deploys a month to roughly twelve a day across its 40-odd services.

The rollback rate dropped to 3%. That surprised the team more than the speed did — smaller changes turn out to be easier to reason about, and a bad one gets caught by a canary before most customers see it.

Thursday nights are free now. On-call pages fell by about two thirds in the first year, and the two engineers who used to babysit releases are working on the carrier-rate API instead.

Halversen's next target is the deployment approval queue, which still adds a day for anything touching billing.
