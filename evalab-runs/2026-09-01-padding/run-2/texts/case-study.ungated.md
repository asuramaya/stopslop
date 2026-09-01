255 words, and it passes this repo's own slopwatch gate.

---

# Case study: Brightwell Logistics

Brightwell Logistics runs freight-tracking software for about 400 regional carriers. Until early 2024, its engineers shipped on a fixed calendar: one release every three weeks, cut on a Tuesday, deployed Thursday night, with two people on call watching the rollout until midnight.

The cadence was not the real problem. The problem was what it did to the work in between. Changes piled up behind the release cut, so any failure meant bisecting three weeks of commits. Engineers batched risky changes with safe ones because there was no cheap way to ship a single fix.

Brightwell moved to Conveyor in March 2024. The first six weeks were mostly unglamorous plumbing: consolidating four CI configurations into one, adding health checks to services that had never had them, and writing rollback steps for the two databases nobody wanted to touch.

A year later:

- Deploys went from roughly 17 a year to four or five a week.
- Median time from merge to production fell from 11 days to under an hour.
- Change failure rate rose a little, 3% to 4%. Mean time to recovery dropped from six hours to 22 minutes.

"We expected the deploy count to go up," said Dana Okafor, VP of Engineering. "What surprised us was the arguments that stopped happening. Nobody negotiates for a slot in the release train anymore."

Brightwell still cuts a coordinated release for schema migrations, and still freezes deploys during peak shipping weeks in December. Everything else goes out when it is ready.

---

The company, platform, person, and numbers are invented — swap in real ones before this goes anywhere public. The draft is at `/tmp/casestudy.md` if you want it in the repo instead.
