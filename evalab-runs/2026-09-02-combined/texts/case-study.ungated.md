Draft (255 words), passing this repo's `slopwatch` gate:

---

**Ravenscroft Logistics cut its release cycle from 30 days to under an hour**

Ravenscroft Logistics matches freight loads for around 1,400 regional carriers. Its engineering group of 22 shipped once a month, on the last Thursday, in a four-hour window that usually ran past midnight. Each release bundled six weeks of merged work. When something broke, nobody could say which of the 90 changes did it.

"We weren't slow because we wrote code slowly," says Dana Okwuosa, VP of Engineering. "We were slow because everything queued behind one door."

The team adopted the platform in March 2025 and spent the first six weeks on the unglamorous part: splitting the monolith's test suite into stages that finish in eleven minutes, replacing hand-edited YAML with one shared pipeline definition, and putting database migrations behind expand-and-contract rules so a rollback never strands the schema.

Deploys now trigger on merge to main. A change reaches production in 38 minutes, gated by automated tests and a canary that watches error rate and p99 latency for ten minutes before full rollout.

Results after nine months:

- 41 production deploys per week, up from one per month
- Change failure rate down from 18% to 4%
- Mean time to restore: 26 minutes, previously 5 hours
- On-call pages during release windows: gone, along with the windows

The team hasn't held a release-planning meeting since May. Okwuosa's next target is the one manual step left, a compliance sign-off for changes that touch billing, which she wants replaced by an automated policy check.

---

The company, the quote, and every number are invented — I have no real customer data, so treat this as a template to fill with actual figures. The product name is left as "the platform" for you to swap in. Draft is at `/tmp/casestudy.md`.
